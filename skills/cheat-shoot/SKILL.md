---
name: cheat-shoot
description: Register that a video has been shot. **Create the video folder + ask whether the actual filmed script matches scripts/<id>.md + buffer +1.** Paired with cheat-publish: shooting enters the queue, publishing leaves it. Triggers: "shot" / "shot X" / "shot it" / "filmed X" / "done recording".
argument-hint: <scripts-path-or-id>
allowed-tools: Bash(*), Read, Write, Edit, Glob
---

# /cheat-shoot — register a completed shoot + create the video folder + (on script change) trigger a v2 prediction

Advances a video from "prediction written, not shot" to "shot, not published". This step:
1. **Creates `videos/<same id>/`** (if it didn't exist)
2. **Asks the user**: "does the script you actually used while filming match `scripts/<id>.md`?"
3. Computes the diff—above V2_TRIGGER_THRESHOLD (default 30%) → **delegate to `/cheat-predict — mode: v2`** to append a `## Prediction v2` section to the original prediction file
4. Adds the video folder to the state.shoots queue, buffer +1

cheat-shoot itself does **not** write prediction content—all prediction-writing logic is in cheat-predict. cheat-shoot only detects script changes + dispatches.

Why a separate skill:
- The buffer-alert system needs to clearly distinguish "shot" vs "published". Videos can be shot in batches (5 in one day) and published spread out (1 per day)
- "The actual filmed script" ≠ "the pre-shoot draft" is the norm. This step is the entry point that makes the diff explicit, triggers the v2 re-judgment, and collects the "user script-change pattern" signal
- The difference between a v2 prediction and a v1 prediction is itself rubric-upgrade evidence—e.g. v1 gave ER=4, v2 gives ER=5 (the user rewrote the script to be higher in hook strength), which tells the rubric "this user's ER threshold is inconsistent with my current formula"

## Overview

```
[user: shot scripts/2026-05-04_abc123_stop-expecting.md]
  ↓
[Phase 0: parse the path + verify the prediction already exists]
  ↓
[Phase 1: check whether already registered (avoid duplicates)]
  ↓
[Phase 2: create videos/<id>/ + ask "does the actual filmed script match?"]
  ↓
[Phase 3: write videos/<id>/script.md]
  ↓
[Phase 4: append state.shoots]
  ↓
[Phase 5: output buffer status]
```

## Constants

- **REQUIRE_PREDICTION = true** — a v1 prediction file must exist before shooting
- **V2_TRIGGER_THRESHOLD = 0.30** — char-level diff after normalization above 30% → suggest a v2 re-judgment by default; below 30%, ask the user whether they still want v2
- **DIFF_METRIC = char_levenshtein_normalized** (**default**) — invoked via [`tools/diff_pct.py`](../../tools/diff_pct.py): first normalize (strip markdown headers / dividers / list markers / decorative punctuation / collapse all whitespace), then compute char-level Levenshtein / max(len_a, len_b). Preferred backend `rapidfuzz`, fallback `difflib.SequenceMatcher` (stdlib, always available). **The old line-level metric false-positives severely in colloquial-transcription scenarios** (draft is long markdown sentences vs whisper-transcribed short fragments; content barely changes but line-level computes ~200% diff)—fixed in PR #14
- **DIFF_METRIC=lines** — legacy fallback: when python3 is entirely unavailable or tools/diff_pct.py can't be found, downgrade to the `diff -u | grep '^[+-]' | wc -l` algorithm

## Inputs

| Required | Source |
|---|---|
| `<scripts-path-or-id>` | user argument; if missing, ask |
| `.cheat-state.json` | state file |
| `scripts/*.md` | pre-shoot drafts |
| `predictions/*.md` | verify the corresponding prediction exists |

## Workflow

### Phase 0: parse + verify

1. Parse the path the user gave—support several forms:
   - full path `scripts/2026-05-04_abc123_stop-expecting.md`
   - shorthand `2026-05-04_abc123_stop-expecting`
   - id shorthand `abc123` → glob `scripts/*_abc123_*.md` to find the match
2. Verify `scripts/<id>.md` exists: doesn't exist → error "pre-shoot draft not found"
3. Verify there's a corresponding prediction `predictions/<same name>.md`:
   - doesn't exist → **refuse registration**, prompt "run /cheat-predict to write the prediction first, otherwise it violates the blind-prediction principle—you can't write the prediction after shooting, that's writing it having seen the footage"
   - exists → pass

### Phase 1: check for duplicates

Read `.cheat-state.json`, check whether `shoots[]` already contains this id:
- already exists → warn "already registered (X days ago). Re-register, or publish with /cheat-publish?"
- doesn't exist → proceed to Phase 2

### Phase 2: create the video folder + ask about script consistency

1. Create the directory `videos/<id>_<short>/` (same naming as scripts/ + predictions/)
2. **Ask the user**:

```
When you filmed "<title>", does the script you actually used match scripts/<id>.md?

a) Matches—filmed per the draft
b) Changed some—can you show me the actual filmed script? I'll re-score once (v2 prediction)
c) Heavily changed, basically another piece → use the _redo flow:
   scripts/<id>_redo.md → re-run cheat-predict → then cheat-shoot (original prediction archived and decoupled)
```

### Phase 3: write videos/<id>/script.md + (path b) trigger a v2 prediction

**Path a (matches)**:
- `cp scripts/<id>.md → videos/<id>/script.md`
- `script_consistency = consistent`
- no re-judgment, proceed to Phase 4

**Path b (changed)**:
1. Ask the user for the actual filmed script—pasted text / file path / transcription file
2. If the user provides it → write to `videos/<id>/script.md`
3. If the user didn't keep it (ad-libbed) → mark `script_lost`, write a placeholder file + warn "v2 re-judgment skipped—next time recommend keeping the script (even a voice-memo transcription)", proceed to Phase 4
4. If provided: compute the diff
   ```bash
   # Resolve the pattern-first source root (cheat-shoot is symlink-installed)
   SKILL_REAL="$(readlink -f ~/.claude/skills/cheat-shoot 2>/dev/null || readlink ~/.claude/skills/cheat-shoot 2>/dev/null)"
   if [[ -n "$SKILL_REAL" ]]; then
     REPO_ROOT="$(cd "$SKILL_REAL/../.." && pwd)"
     DIFF_TOOL="$REPO_ROOT/tools/diff_pct.py"
   fi

   if [[ -n "${DIFF_TOOL:-}" && -f "$DIFF_TOOL" ]] && command -v python3 >/dev/null 2>&1; then
     # default char-level Levenshtein on normalized text (rapidfuzz preferred, difflib fallback)
     diff_pct=$(python3 "$DIFF_TOOL" "scripts/<id>.md" "videos/<id>/script.md")
   else
     # legacy line-level fallback—only used when neither python3 nor diff_pct.py is available
     added=$(diff -u scripts/<id>.md videos/<id>/script.md | grep -c '^+')
     removed=$(diff -u scripts/<id>.md videos/<id>/script.md | grep -c '^-')
     total_orig=$(wc -l < scripts/<id>.md)
     diff_pct=$(( (added + removed) * 100 / total_orig ))
     echo "⚠️  fell back to line-level diff—colloquial transcription inflates diff_pct and may falsely trigger v2"
   fi
   ```

   **Why normalize + char-level**: line-level diff computes ~200% difference in the creator's real scenario (draft is long markdown sentences, filmed script is whisper-transcribed colloquial short lines) while content barely changes. Char-level Levenshtein, after normalization, stably reflects the **content** difference rather than the formatting difference. See [`tools/diff_pct.py`](../../tools/diff_pct.py) + `tools/diff_pct_test.sh` (3 fixtures pass on both backends).
5. **Determine v2 trigger**:
   - `diff_pct >= 30` → suggest a v2 re-judgment by default, **proactively call** `/cheat-predict — mode: v2 — prediction-file: predictions/<id>.md` passing `videos/<id>/script.md` as input. cheat-predict runs v2 mode and appends `## Prediction v2`
   - `diff_pct < 30` → ask the user: "only N% of the content changed, re-judge? Default no (the v1 prediction is still valid)". User says yes → call as above; user says no → skip v2, continue to Phase 4
6. After cheat-predict finishes writing v2 to disk, control returns to cheat-shoot and proceeds to Phase 4

**Path c (heavily changed)**:
- Don't write `videos/<id>/script.md`, prompt to use the `_redo` flow
- Exit cheat-shoot (don't proceed to Phase 4)

### Phase 4: state update

```json
{
  "shoots": [
    ...,
    {
      "video_folder": "videos/2026-05-04_abc123_stop-expecting/",
      "prediction_file": "predictions/2026-05-04_abc123_stop-expecting.md",
      "scripts_path": "scripts/2026-05-04_abc123_stop-expecting.md",
      "shot_at": "<ISO timestamp>",
      "script_consistency": "consistent" | "modified" | "lost",
      "script_diff_pct": <0-100 int or null>,
      "v2_prediction_written": <true/false>,
      "script_hash_at_shoot": "<sha256:12 of videos/<id>/script.md>"
    }
  ]
}
```

`v2_prediction_written: true` means the prediction file now has a `## Prediction v2` section, and cheat-retro should read v2 to compute deviation; `false` means it continues to use v1.

### Phase 5: output buffer status

After reading state, immediately compute buffer + color (per the derivation rules in [cadence-protocol.md](../../shared-references/cadence-protocol.md)):

```
✅ Shoot registered: videos/2026-05-04_abc123_stop-expecting/
   Prediction file: predictions/2026-05-04_abc123_stop-expecting.md

📦 Current buffer: 3 pieces (🟢 green, normal)
   At your cadence (every other day) = 6 days of buffer, steady rhythm.

Next step: shoot other candidates / wait for the next publish day / do nothing
```

If the buffer color changed (e.g. from green to blue) → highlight a reminder:
```
📦 Current buffer: 6 pieces (🔵 blue, **backed up**)
⚠️  Suggest pausing shooting, focus on shipping inventory + retro.
   At your cadence (daily) = 6 days in reserve, past the healthy ceiling.
```

## Key Rules

1. **Don't write the prediction**—shot ≠ published. The prediction is locked in /cheat-predict; shooting is just an event
2. **Don't touch video-folder content**—neither script.md nor draft-v0.md is edited
3. **A prediction must exist first**—otherwise it violates blind prediction (writing the prediction after seeing the footage = data leaking into the judgment)
4. **Buffer computed in real time**—recompute immediately after each shoot / publish; state.shoots is the source of truth
5. **Supports batches**: the user can say "shot X / shot Y / shot Z" three times in a row to register consecutively

## Refusals

- "Shot X, but I never ran cheat-predict" → refuse. The v1 prediction **must be written before shooting**—writing it after shooting gets induced into post-hoc edits by the footage. Run /cheat-predict to write v1 first, then come to /cheat-shoot. (A v2 re-judgment is a different matter—only allowed when v1 already exists + the script changed after shooting)
- "I don't have a video folder, I just filmed" → ask the user → help create the video folder + remind them to go through the full flow next time; mark `ad_hoc: true` at registration
- "I changed the script but just overwrite v1, don't keep a v2 section" → refuse. v1 is the archive, v2 is the current judgment—append, don't overwrite. Keeping both sections is key evidence for rubric learning

## Integration

- Upstream: `/cheat-predict` finishes writing the prediction → the user films → `/cheat-shoot` registers
- Downstream: `/cheat-publish` removes the corresponding item from state.shoots at publish time
- The buffer number on the `/cheat-status` dashboard comes directly from `state.shoots.length`
- `/cheat-recommend` reads the buffer color to adjust its recommendation strategy
- The SessionStart hook reads the buffer color to decide the first line of its report

## state.shoots data structure

```json
{
  "shoots": [
    {
      "video_folder": "videos/2026-05-04_abc123_stop-expecting/",
      "prediction_file": "predictions/2026-05-04_abc123_stop-expecting.md",
      "shot_at": "2026-05-04T18:30:00+08:00",
      "ad_hoc": false  // true if user shot without going through full flow
    }
  ]
}
```

Sorted ascending by `shot_at`—earliest shot first. `/cheat-status` shows the days-since-shoot warning for the earliest item (to avoid a video shot 30 days ago and not published).
