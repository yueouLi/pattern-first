#!/usr/bin/env bash
#
# pattern-first / prediction-immutability hook
#
# Wires PreToolUse(Edit|Write) → blocks any edit that touches the
# '## Prediction' section of a file under predictions/.
#
# Allows:
#   - Writing brand-new prediction files
#   - Editing the file's metadata header (above first ##)
#   - Appending to the '## Retro' section
#   - Touching files outside predictions/
#
# Blocks:
#   - Any change to lines between '## Prediction' and the next H2
#
# Bypass (rare, for true formatting-only fixes):
#   CHEAT_BYPASS_IMMUTABILITY=1 — single-shot bypass; logs a warning to stderr
#
# Requirements: bash 3+, jq, diff. Mac default install has all of these.
#
# Exit codes:
#   0 = allow tool call to proceed
#   1 = block tool call (Claude Code will surface stderr to the model)

set -uo pipefail

# Single-shot bypass — opt-in, logs prominently
if [[ "${CHEAT_BYPASS_IMMUTABILITY:-0}" == "1" ]]; then
  echo "[pattern-first] ⚠️  IMMUTABILITY BYPASS active (CHEAT_BYPASS_IMMUTABILITY=1)" >&2
  echo "[pattern-first] ⚠️  This should only be used for pure markdown-formatting fixes." >&2
  echo "[pattern-first] ⚠️  Bypass will be visible in git history." >&2
  exit 0
fi

# Read tool call payload from stdin (Claude Code passes JSON)
input=$(cat)
if [[ -z "$input" ]]; then
  # No input — let it through (defensive default; nothing to check)
  exit 0
fi

# Extract tool name and file path
tool_name=$(printf '%s' "$input" | jq -r '.tool_name // empty' 2>/dev/null || echo "")
file_path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")

# Only intercept Edit and Write
if [[ "$tool_name" != "Edit" && "$tool_name" != "Write" ]]; then
  exit 0
fi

# Only intercept files under predictions/
if [[ -z "$file_path" ]]; then
  exit 0
fi

case "$file_path" in
  */predictions/*.md|predictions/*.md)
    : # match — continue checking
    ;;
  *)
    exit 0
    ;;
esac

# Allow Write if the file does not yet exist (creating new prediction)
if [[ "$tool_name" == "Write" && ! -f "$file_path" ]]; then
  exit 0
fi

# For Edit — extract the old_string and new_string and check whether either touches
# the prediction section.
#
# Strategy: compute the byte range of the '## Prediction' section
# in the file BEFORE the edit, then check whether the old_string lies inside that
# range. If yes — block.

if [[ "$tool_name" == "Edit" ]]; then
  old_string=$(printf '%s' "$input" | jq -r '.tool_input.old_string // empty' 2>/dev/null || echo "")
  if [[ -z "$old_string" ]]; then
    exit 0
  fi

  # Find prediction section bounds. Match '## Prediction' / '## Prediction v1'
  # / '## Prediction v2' / etc. — all version-suffixed prediction headings count as
  # prediction sections and are locked together. (The legacy Chinese '## 预测' is
  # also matched for backward compatibility with v0.1.0 files.)
  #
  # Section ends at the first NON-prediction '## ' heading (typically '## Retro').
  prediction_section=$(awk '
    /^## / {
      if ($0 ~ /^## (Prediction|预测)([^a-zA-Z]|$)/) {
        in_pred=1; print; next
      } else if (in_pred) {
        exit
      }
    }
    in_pred { print }
  ' "$file_path" 2>/dev/null || echo "")

  if [[ -z "$prediction_section" ]]; then
    # File has no prediction section — let the edit through.
    # (Could be a non-conforming prediction file or an edge case.)
    exit 0
  fi

  # Check whether old_string appears inside the prediction section.
  # We use grep -F (literal) on a temporary file because old_string may contain regex chars.
  pred_tmp=$(mktemp)
  printf '%s' "$prediction_section" > "$pred_tmp"

  if grep -qF -- "$old_string" "$pred_tmp" 2>/dev/null; then
    rm -f "$pred_tmp"
    cat >&2 <<EOF

[pattern-first] 🚫 BLOCKED: edit targets the '## Prediction' section of:
  $file_path

This violates principle #1 of pattern-first: predictions are immutable.
Once written, the prediction section can never be modified — only the
'## Retro' section can be appended to.

What to do instead:
  • If you want to redo the prediction with new info, create a NEW file:
      ${file_path%.md}_redo.md
    The original must be preserved.
  • If you noticed a factual mistake AFTER seeing data, document it in the
    '## Retro' section: "Correction: original probability X% should have been Y%".
  • If this is a pure markdown-formatting fix (no semantic change), you can
    bypass once with: CHEAT_BYPASS_IMMUTABILITY=1 (logs to stderr, visible in git).

See: shared-references/blind-prediction-protocol.md
EOF
    exit 1
  fi

  rm -f "$pred_tmp"
  exit 0
fi

# Write tool on an existing file — that's a full overwrite, definitely touches prediction section.
if [[ "$tool_name" == "Write" && -f "$file_path" ]]; then
  cat >&2 <<EOF

[pattern-first] 🚫 BLOCKED: Write would overwrite an existing prediction file:
  $file_path

Use Edit on the '## Retro' section to append retrospective content.
Use a new '_redo.md' file path to create a redo prediction.
The original prediction file must be preserved verbatim.

See: shared-references/blind-prediction-protocol.md
EOF
  exit 1
fi

exit 0
