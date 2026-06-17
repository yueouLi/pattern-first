---
name: cheat-status
description: The cheat-on-content status dashboard. Shows current mode / rubric version / calibration progress / pending retros / pool status / whether to upgrade to SQLite / whether to bump the rubric. **Callable anytime, side-effect-free.** Triggers: "status" / "dashboard" / "what should I do now" / "how's progress".
allowed-tools: Bash(*), Read, Glob, Grep
---

# /cheat-status — status dashboard

Reads the state file + scans the user project → summarizes current progress → outputs a "what to do today" list.

## Overview

```
[user: status]
  ↓
[Phase 1: read .cheat-state.json + scan the filesystem]
  ↓
[Phase 2: compute derived metrics]
  ↓
[Phase 3: detect suggestion triggers (upgrade / bump / settle)]
  ↓
[Phase 4: output the dashboard]
```

## Constants

- **SQLITE_UPGRADE_THRESHOLD = 30** — suggest upgrading to SQLite when calibration_samples reaches N
- **CLEANUP_LINE_THRESHOLD = 600** — suggest a cleanup when rubric_notes.md exceeds N lines
- **STALE_PREDICTION_DAYS = 30** — prompt cleanup when an in_progress prediction has gone unpublished for N days

## Inputs

| Source | Use |
|---|---|
| `.cheat-state.json` | primary state |
| `predictions/*.md` | calibration sample count / pending retros |
| `candidates.md` | candidate-pool size |
| `rubric_notes.md` | line count / current version |
| `.cheat-cache/usage.jsonl` (if present) | meta-logging data, for "how many predictions since the last bump" |

## Workflow

### Phase 1: read state

```python
state = read_json('.cheat-state.json')
if not state:
    return "You haven't initialized yet. Run /cheat-init first."

predictions = glob('predictions/*.md')
candidates_count = parse_candidates_md_entries()
rubric_lines = wc -l rubric_notes.md
```

### Phase 2: derived metrics

| Metric | Algorithm |
|---|---|
| **Buffer count** | `len(state.shoots)` |
| **Buffer color** | derived per [cadence-protocol.md](../../shared-references/cadence-protocol.md): `buffer_days = buffer_count × target_publish_cadence_days`, `<1 red / 1-2 orange / 3-5 green / >5 blue`. If `target_publish_cadence_days=null` → color disabled |
| **Confidence level** | derived per the [state-management.md confidence table](../../shared-references/state-management.md): from the `calibration_samples` integer derive emoji + label |
| **Days since earliest shoot** | `now - state.shoots[0].shot_at`, used to warn "shot N days ago, not published" |
| Calibration sample count | number of files in predictions/ with a complete retro section (actuals non-empty) |
| Pending retros | the ones in state.pending_retros past RETRO_WINDOW_DAYS |
| Pool size | number of entries in candidates.md with tier!=skip |
| Predictions since last bump | number of predictions with published_at > state.last_bump_at |
| Same-direction-deviation queue | state.consecutive_directional_errors |
| in_progress staleness | now - state.in_progress_session.started_at (if any) |

### Phase 3: detect suggestion triggers

Check item by item by priority (high → low):

1. **Buffer color = 🔴 red** → first-line high-priority alert: "buffer is at 0/1 piece, the next publish day may have a gap—must shoot ≥1 piece today. Say 'recommend topics' and I'll only push the top 1 safe-score (no experimental)"
2. **Buffer color = 🔵 blue** → high-priority prompt: "buffer is backed up at N pieces. **Pause shooting**, ship inventory first + retro. Say 'shipped ...' and I'll dequeue"
3. **The earliest item in state.shoots has shot_at > 14 days** → "you have a video shot N days ago and not published—topical-timeliness loss risk; publish soon or abandon"
4. **in_progress stale** (>= STALE_PREDICTION_DAYS) → high-priority prompt "clean up or publish"
5. **Pending retros ≥ 1** → high-priority "you should retro X piece(s) today"
6. **`pool_status=none` + `calibration_samples=0` + >24h since init** → "🌱 it's been N days since you finished init but you haven't shot yet—is it because you have no topic? Run /cheat-seed, 5 minutes to get 5 candidates + 5 drafts" high-priority
7. **Claude judges a systematic-deviation signal** (**not a hard ≥3 same-direction**) → prompt "suggest running /cheat-bump"
   - **Default reference**: ≥3 consecutive same-direction deviations
   - **But Claude can go earlier**: 1 extreme deviation (≥10x) or 2 same-direction + strong reverse evidence in comments
   - **And can go later**: 3 same-direction but each magnitude <25% (may be just noise)
   - When prompting, explicitly mark: "this is [default-aligned] / [judgment-driven]"
8. **calibration_samples crosses into a new confidence tier** (0→1, 2→3, 5→6, 10→11, 20→21) → prompt "🎉 confidence upgrade: <old tier> → <new tier>. The bucket central-estimate precision rises from ±X% to ±Y%". **Notification only, no action the user must confirm**—all skills already auto-adjust by calibration_samples
9. **calibration_samples crosses 5** → "your rubric shape is ready for its first formal bump. Review the observations section of rubric_notes.md to see if there's a pattern supported by ≥3 samples → run /cheat-bump"
10. **calibration_samples crosses 10** → "you can run /cheat-bump --bucket-only --scheme percentile to switch bucket boundaries to percentiles (always self-consistent)"
11. **calibration_samples crosses SQLITE_UPGRADE_THRESHOLD** and data_layer=markdown → "suggest running tools/md-to-sqlite.py"
12. **rubric_notes.md line count > CLEANUP_LINE_THRESHOLD** → "suggest settling the observations section (manually or triggered at the next bump)"
13. **calibration_samples ≥ 5 + pool_status=none** → "you can start building a topic pool"
14. **calibration_samples ≥ 15 + pool_status=none** → "strongly suggest building a pool: /cheat-trends or manually build candidates.md"
15. **state.hooks_installed=false** → "your immutability is a gentleman's agreement; suggest running /cheat-init to install the hook"
16. **state.last_bump_self_audited=true** → "the last bump was self-audited. Suggest configuring mcp__llm-chat__chat so the next bump goes through external audit"
17. **state.rubric_form_mismatch=true** → "your content_form is not opinion-video, but you used the built-in opinion rubric. The first few predictions will be less accurate; at the next bump, suggest adjusting the weights to fit your format"
18. **state.benchmark_status=pending** → "🎯 at init you said you'd find a benchmark account later but haven't yet. Run /cheat-learn-from to import ≥3 benchmark videos and the tool will have an anchor"
19. **state.benchmark_status=imported + Claude judges that the user's data signal now exceeds the benchmark** → "📊 your real data has become the primary signal; benchmark influence fades out"
    - **Default reference**: calibration_samples ≥ 10
    - **But Claude can go earlier**: N=5 but ≥3 of the user's (score, actuals) pairs are inconsistent with the benchmark pattern—meaning your account has walked off the benchmark's path
    - **And can go later**: N=15 but the user's samples are all very similar, not diverse enough → the benchmark still has signal value
    - The prompt is a **notification, not a gate**—benchmark.md is always kept as a sanity check, and cheat-seed can still read it

### Phase 4: output the dashboard

```
🎛️ cheat-on-content status (updated 2026-05-04 15:00)

Content form: opinion-video / duration 3-5min / cadence: every other day
Current rubric: v2 (last bump: 2026-04-22)
Calibration samples: 18 pieces
Confidence: 🟢 fairly high (central estimate ±15%, rubric shape stable)
Baseline: 42k median

📦 Buffer: 3 pieces (🟢 green)
   At your cadence (every other day) = 6 days of buffer, steady rhythm

📊 Progress bars
  [█████████████░░░░░] 18 / 30 → SQLite upgrade suggestion threshold
  [██████████░░░░░░░░] 18 / 10 → percentile buckets available (past threshold)

🎬 To-do (by urgency)
  🚨 Retro 1 piece (past T+3d)
     - predictions/2026-05-01_db063817_you-re-no-longer-in-the-relationship.md (T+3d reached)
  ⚠️  Same-direction deviation 3 times (high, high, high) → suggest /cheat-bump
  💤 in-progress prediction stale 35 days
     - predictions/2026-04-01_xxx.md → published but forgot to register? Or abandoned?

🔥 Candidate pool
  - candidates.md: 27 entries (tier1: 12, tier2: 9, tier3: 6)
  - since last trend fetch: 4 days — can run /cheat-trends again

📈 Health
  - rubric_notes.md: 412 lines (healthy, <600 alert line)
  - hooks_installed: ✅
  - external audit configured: ❌ → suggest configuring mcp__llm-chat__chat

Recommended next steps (by recommended priority):
1. /cheat-retro predictions/2026-05-01_db063817_you-re-no-longer-in-the-relationship.md  ← most urgent
2. /cheat-bump  ← handle the 3 same-direction deviations
3. Handle the stale in-progress (manually or reply "clean up in-progress")

See the main SKILL.md for the full command list.
```

Output style: **plain, concrete, clickable**. Each suggestion carries the exact command—the user should be able to copy-paste and run it directly.

## Key Rules

1. **Side-effect-free.** Read a lot, write nothing. Any state modification is another skill's job
2. **Don't pretend data is available.** State-file field missing → explicitly mark "unknown", don't guess
3. **Suggestions carry priority.** Showing 10 suggestions at once numbs the user—order by urgency
4. **Each suggestion carries a command.** Can't just say "time to bump"—give the exact entry point `/cheat-bump --propose "..."`

## Refusals

- "While you're at it, auto-run the retro for me" → refuse. status is read-only; retro is a separate action (avoid doing two things in one operation)
- "I don't want to see the rubric_notes line count, it's trivial" → still included in the output but collapsed to the bottom "Health" section—the presence of status info lets the user see it before things go wrong

## Integration

- Upstream: all other skills update .cheat-state.json on completion; status is the visualization of those updates
- Downstream: each suggestion routes to a specific sub-skill
- meta-logging hook (if enabled) → writes usage.jsonl; status uses it to compute "how many times since the last X"
