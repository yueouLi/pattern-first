#!/usr/bin/env bash
#
# pattern-first SessionStart hook
#
# Renders a 4-6 line status report at the start of every Claude Code session.
# Output is added to Claude's system context — Claude sees it before first reply.
#
# Silently exits if:
#   - Not in a pattern-first project (no .cheat-state.json)
#   - jq not available (status is markdown-readable; Claude can read state.json directly)
#
# Format:
#   📦 Buffer: N (color)
#   ⏰ Pending retros: N
#   🎯 Candidates top 3: ...
#   📅 Last trend fetch: N days ago
#   ⚠️ To-do: ...

set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
STATE_FILE="$PROJECT_DIR/.cheat-state.json"

# Silently skip if not a pattern-first project
if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

# Skip if jq missing (Claude can still read state.json himself in conversation)
if ! command -v jq >/dev/null 2>&1; then
  cat <<'EOF'
[pattern-first] SessionStart: jq not installed — skipping auto status report.
Claude can still read .cheat-state.json directly. Say "status" for full status.
EOF
  exit 0
fi

now_epoch=$(date +%s)
today_iso=$(date +%Y-%m-%d)

# --- Read state ---
state=$(cat "$STATE_FILE")
schema_version=$(echo "$state" | jq -r '.schema_version // "unknown"')
rubric_version=$(echo "$state" | jq -r '.rubric_version // "v0"')
calibration_samples=$(echo "$state" | jq -r '.calibration_samples // 0')
target_cadence=$(echo "$state" | jq -r '.target_publish_cadence_days // null')
buffer_count=$(echo "$state" | jq -r '.shoots // [] | length')
pending_retros_count=$(echo "$state" | jq -r '.pending_retros // [] | length')
last_trends_at=$(echo "$state" | jq -r '.last_trends_run_at // ""')
last_published_at=$(echo "$state" | jq -r '.last_published_at // ""')
hooks_installed=$(echo "$state" | jq -r '.hooks_installed // false')
form_severe_mismatch=$(echo "$state" | jq -r '.rubric_form_severe_mismatch // false')
last_prediction_self_scored=$(echo "$state" | jq -r '.last_prediction_self_scored // false')
last_self_scored_at=$(echo "$state" | jq -r '.last_self_scored_at // ""')

# --- Detect schema mismatch (read LATEST_SCHEMA from migrations/registry.md if reachable) ---
# Strategy: hardcode current LATEST_SCHEMA here (bumped by maintainer alongside cheat-init).
# If state.schema_version != LATEST_SCHEMA → suggest migrate (non-blocking).
LATEST_SCHEMA="1.4"
schema_mismatch=""
if [[ "$schema_version" != "$LATEST_SCHEMA" && "$schema_version" != "unknown" ]]; then
  schema_mismatch="⚠️  schema version mismatch: state=${schema_version}, skill expects=${LATEST_SCHEMA}. Suggest running /cheat-migrate (non-blocking; some new features may misbehave before migrating)."
elif [[ "$schema_version" == "unknown" ]]; then
  schema_mismatch="⚠️  state.schema_version field missing or corrupted. Suggest running /cheat-status to check the file, or back up and re-init."
fi

# --- Detect blind-skip contamination (triggered by cheat-predict --skip-blind or Phase 2.5 choosing b) ---
self_scored_warning=""
if [[ "$last_prediction_self_scored" == "true" && -n "$last_self_scored_at" ]]; then
  # Parse timestamp; tolerate +08:00 or Z suffix
  self_scored_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last_self_scored_at%%+*}" "+%s" 2>/dev/null || \
                      date -j -f "%Y-%m-%dT%H:%M:%SZ" "$last_self_scored_at" "+%s" 2>/dev/null || \
                      echo 0)
  if [[ $self_scored_epoch -gt 0 ]]; then
    days_since=$(( (now_epoch - self_scored_epoch) / 86400 ))
    if [[ $days_since -ge 7 ]]; then
      self_scored_warning="🚨 It's been ${days_since} days since the last \`--skip-blind\` self-scored prediction—the calibration pool's accumulated contamination risk is compounding. The next /cheat-predict through the sub-agent clears this prompt."
    else
      self_scored_warning="⚠️  The last prediction went through \`--skip-blind\` (self-scored ${days_since} days ago, not channel-B isolated). The next /cheat-predict on default clears this."
    fi
  fi
fi

# --- Derive confidence label (single source: the confidence table in state-management.md) ---
if   [[ $calibration_samples -eq 0 ]]; then
  confidence="🔴 very low (astrology-level, pure discipline training)"
elif [[ $calibration_samples -le 2 ]]; then
  confidence="🟠 low (central ±50%, directional sense beats absolute numbers)"
elif [[ $calibration_samples -le 5 ]]; then
  confidence="🟡 fairly low (central ±40%, usable as one reference)"
elif [[ $calibration_samples -le 10 ]]; then
  confidence="🟢 medium (central ±25%, can participate in decisions)"
elif [[ $calibration_samples -le 20 ]]; then
  confidence="🟢 fairly high (central ±15%, rubric shape stable)"
else
  confidence="🔵 high (central ±10%, can data-drive)"
fi

# --- Compute buffer color ---
buffer_label=""
buffer_warning=""
if [[ "$target_cadence" == "null" ]] || [[ -z "$target_cadence" ]]; then
  # Flexible cadence: no color, just count
  buffer_label="📦 Buffer: ${buffer_count} pieces (flexible cadence, no alert)"
else
  buffer_days=$(( buffer_count * target_cadence ))
  if   [[ $buffer_days -lt 1 ]]; then
    buffer_label="📦 Buffer: ${buffer_count} pieces 🔴 red (by cadence ${target_cadence}d = <1 day in reserve)"
    buffer_warning="🚨 buffer alert: the next publish day may have a gap. Must shoot ≥1 safe-score today."
  elif [[ $buffer_days -le 2 ]]; then
    buffer_label="📦 Buffer: ${buffer_count} pieces 🟠 orange (by cadence ${target_cadence}d = ${buffer_days} days in reserve)"
  elif [[ $buffer_days -le 5 ]]; then
    buffer_label="📦 Buffer: ${buffer_count} pieces 🟢 green (by cadence ${target_cadence}d = ${buffer_days} days in reserve)"
  else
    buffer_label="📦 Buffer: ${buffer_count} pieces 🔵 blue (by cadence ${target_cadence}d = ${buffer_days} days, backed up)"
    buffer_warning="📦 buffer backed up: suggest pausing shooting, ship inventory first + retro."
  fi
fi

# --- Compute pending retros that are actually due ---
retro_window=3   # default RETRO_WINDOW_DAYS, hardcoded fallback (TODO: read from rubric_notes if present)
due_count=0
earliest_due=""
if [[ "$pending_retros_count" -gt 0 ]]; then
  # Walk pending_retros, check each prediction file's published_at
  while IFS= read -r pred_file; do
    pred_path="$PROJECT_DIR/$pred_file"
    if [[ -f "$pred_path" ]]; then
      pub_iso=$(grep -E '^\*\*Published at\*\*:' "$pred_path" 2>/dev/null | head -1 | sed -E 's/.*: *//')
      if [[ -n "$pub_iso" ]]; then
        pub_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${pub_iso%%+*}" "+%s" 2>/dev/null || echo 0)
        if [[ $pub_epoch -gt 0 ]]; then
          age_days=$(( (now_epoch - pub_epoch) / 86400 ))
          if [[ $age_days -ge $retro_window ]]; then
            due_count=$((due_count + 1))
            if [[ -z "$earliest_due" ]] || [[ "$pub_iso" < "$earliest_due" ]]; then
              earliest_due="$pub_iso"
            fi
          fi
        fi
      fi
    fi
  done < <(echo "$state" | jq -r '.pending_retros // [] | .[]')
fi

retro_label=""
if [[ $due_count -gt 0 ]]; then
  retro_label="⏰ Pending retros: ${due_count} (earliest: ${earliest_due%%T*})"
elif [[ "$pending_retros_count" -gt 0 ]]; then
  retro_label="⏰ Pending retros: ${pending_retros_count} (not yet T+${retro_window}d)"
else
  retro_label="⏰ Pending retros: none"
fi

# --- Top candidates (read first 3 H3 from candidates.md) ---
candidates_file="$PROJECT_DIR/candidates.md"
top_candidates=""
if [[ -f "$candidates_file" ]]; then
  # Extract first 3 H3 titles, format compactly
  top_candidates=$(grep -E '^### ' "$candidates_file" 2>/dev/null \
    | head -3 \
    | sed -E 's/^### \[[^]]+\] *//' \
    | tr '\n' '/' \
    | sed 's:/$::' \
    | sed 's:/: / :g')
fi
if [[ -z "$top_candidates" ]]; then
  candidates_label="🎯 Candidates: (empty—say 'fetch trends' or 'find a topic')"
else
  candidates_label="🎯 Candidates top 3: ${top_candidates}"
fi

# --- Last trends run ---
trends_label=""
if [[ -n "$last_trends_at" ]]; then
  trends_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last_trends_at%%+*}" "+%s" 2>/dev/null || echo 0)
  if [[ $trends_epoch -gt 0 ]]; then
    days_ago=$(( (now_epoch - trends_epoch) / 86400 ))
    trends_label="📅 Last trend fetch: ${days_ago} days ago"
  fi
fi

# --- Build the report ---
echo ""
echo "[pattern-first / SessionStart status report]"
echo ""
echo "$buffer_label"
echo "$retro_label"
echo "$candidates_label"
[[ -n "$trends_label" ]] && echo "$trends_label"

# Confidence indicator
echo "📈 Calibration samples: ${calibration_samples} | Confidence: ${confidence}"

# Warnings (high priority)
[[ -n "$buffer_warning" ]] && echo "" && echo "$buffer_warning"
[[ -n "$schema_mismatch" ]] && echo "" && echo "$schema_mismatch"
[[ -n "$self_scored_warning" ]] && echo "" && echo "$self_scored_warning"
if [[ "$form_severe_mismatch" == "true" ]]; then
  echo "❌ The rubric severely mismatches your content form—predictions are nearly meaningless."
fi
if [[ "$hooks_installed" != "true" ]]; then
  echo "⚠️  immutability hook not installed—your blind-prediction protection is a gentleman's agreement, not physically enforced."
fi

echo ""
echo "(Don't proactively start any action—wait for the user to decide. Say \"status\" for the full dashboard.)"
echo ""

exit 0
