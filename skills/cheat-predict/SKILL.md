---
name: cheat-predict
description: Write an immutable blind-prediction log for the final draft. This is the core action of cheat-on-content's whole calibration loop—once the prediction section is written it's immutable, enforced by a hook. **Auto-detection**: if the target file already has a `## Prediction` / `## Prediction v1` section (called by cheat-shoot in v2 mode), switch to appending `## Prediction v2` rather than overwriting. **Scoring is delegated via the Task tool to the `cheat-score-blind` sub-agent** (context-isolated channel B); the main Claude writes to disk after review. Triggers: "start prediction" / "score and predict this draft" / "write the prediction log".
argument-hint: <script-path> [— mode: v1|v2] [— prediction-file: <path>] [— skip-blind]
allowed-tools: Bash(*), Read, Write, Edit, Glob, Task
---

# /cheat-predict — AI-led blind prediction + user review

**This tool is a "cheat device"—the AI does the judging for you.** So cheat-predict's core is:
- **Claude itself** reads the draft + scores 7 dimensions + gives bucket + probability distribution + counterfactual scenarios
- The user **reviews** and replies "ok" to accept, or points out which dimension / which judgment is wrong
- Default takes the fast path: user replies ok directly → write to disk
- Slow path: user challenges a dimension → Claude revises → review again → until confirmed

It's not the user writing everything from the 7 dimensions to the probability distribution themselves—then Claude would be just a "formatter", losing the tool's core value.

**Strictly follow [shared-references/blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)**—having seen any subsequent data, you can't write a prediction, only log a reconstructed one.
Full component list: [shared-references/prediction-anatomy.md](../../shared-references/prediction-anatomy.md).
Confidence derivation table: [shared-references/state-management.md](../../shared-references/state-management.md).

## Overview

```
[user: start prediction scripts/<id>.md]
  ↓
[Phase 0: blind check self-check]              ← refuse on violation
  ↓
[Phase 0.7: mode detection — v1 (new) or v2 (append)]
  ↓
[Phase 1: read script + rubric + state + derive confidence]
  ↓
[Phase 2: **delegate to the cheat-score-blind sub-agent** (Task tool) for the 9-dim blind score + per-dim confidence]
  ↓
[Phase 2.5: main Claude reviews the blind output — if any dimension |delta| ≥ 2 vs the main estimate, pop user adjudication]
  ↓
[Phase 3: **Claude itself** finds anchor comparisons]
  ↓
[Phase 4: **Claude itself** gives bucket + probability distribution + central estimate]   ← flatter distribution when confidence is low
  ↓
[Phase 5: **Claude itself** writes counterfactual scenarios + key calibration hypothesis]
  ↓
[Phase 5.5: **user review**—show the full draft, wait for "ok" or a challenge]
  ↓
   ├─ "ok" → Phase 6 write to disk
   └─ "dimension X should be Y not Z" → Claude revises → review again → loop
  ↓
[Phase 6: write to disk — v1 writes a new file / v2 appends to the existing file before ## Retro]
  ↓
[Phase 7: update state.in_progress_session]
```

## Constants

- **SCRIPTS_DIR = scripts/** — draft source directory
- **PREDICTION_DIR = predictions/** — output directory
- **BLIND_CHECK = strict** — strict (default) / lenient (warn only, not recommended) — related to the "seen data" boundary of [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)
- **BLIND_SCORING = on** (default) / off — whether to go through the [cheat-score-blind](../cheat-score-blind/SKILL.md) sub-agent. off equals the `--skip-blind` flag, marks `last_prediction_self_scored: true` for a cheat-status warning
- **DISAGREEMENT_THRESHOLD = 2** — when the single-dimension difference between blind and the main Claude's self-estimate |Δ| ≥ this value → Phase 2.5 pops user adjudication
- **BUCKET_PRESET = auto** — auto-derive: has baseline_plays → use baseline × {0.3 / 1 / 3 / 10 / 30}; no baseline → the platform generic default
- **MIN_ANCHORS = 2** — anchor comparison expects 2; when insufficient, explicitly mark an "anchor N/A" section (don't delete the section, don't omit)

> 💡 Override at call time: `/cheat-predict scripts/<id>.md — BLIND_CHECK: lenient` / `--skip-blind` (neither recommended)

## Inputs

| Required | Source |
|---|---|
| `<video-folder-path>` or `<script-path>` | user argument; if missing, ask |
| `rubric_notes.md` | user project root |
| `.cheat-state.json` | state file |
| `predictions/*.md` (optional) | historical predictions, as anchors |

### Argument parsing (Phase 0.5, before the blind check)

The path the user gives **should be** `scripts/<date>_<id>_<short>.md`. If not under scripts/:

| Form | Handling |
|---|---|
| `scripts/<date>_<id>_<short>.md` | standard path, use directly |
| `<id>` or `<short>` shorthand | glob `scripts/*_<id>_*.md` or `scripts/*<short>*.md` to find the match |
| any external .md file (e.g. `~/Desktop/my-draft.md`) | **warn + ask**: "recommend putting the draft at scripts/<date>_<id>_<short>.md for cheat-on-content to manage. Want me to cp it over and compute the id?" user agrees → create the standard path then continue |
| `videos/<id>/` path (user mistakes the video folder for where the draft lives) | prompt "the video folder is created after shooting—the pre-shoot draft is in scripts/. Which draft do you want to predict?" |

If scripts/<id>.md doesn't exist → error and ask "where is the draft you want to predict?"

## Workflow

### Phase 0: blind check self-check (**most critical**, terminate immediately on violation)

Execute per the "checklist a sub-skill must do" in [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md):

1. Ask the user about the piece's current publish status:
   - not published → pass
   - published < `RETRO_WINDOW_DAYS` days → ask "have you seen any subsequent data (plays/likes/comments)?"
     - user answers "haven't seen" → pass, mark `published_before_prediction: true` + `blind_status: confirmed_no_data_seen`
     - user answers vaguely → treat as "seen", handle per the next item
   - published ≥ `RETRO_WINDOW_DAYS` days → **immediately refuse to write a "prediction"**, suggest using the `_redo.md` path to log a reconstructed retrospective

2. Self-check whether the conversation history contains actual numbers with words like plays/reads/likes/comments/shares → on a hit, treat as data seen, handle per strict mode above

3. `BLIND_CHECK=lenient` mode: warn only + force the file header to mark `**Reconstructed retrospective — NOT a blind prediction**`, but still allow continuing

Pass → proceed to Phase 0.7.

### Phase 0.7: mode detection (v1 vs v2)

Determine whether this is a new prediction (v1) or a v2 append to an existing prediction (post-shoot script-change scenario).

**Explicit arguments take priority**: user/caller passes `— mode: v2` + `— prediction-file: <path>` → v2 mode directly.

**Auto-detection** (no explicit argument):
1. Infer the target prediction path: `predictions/<same naming as scripts/<id>>.md`
2. Read that path:
   - doesn't exist → **v1 mode**, proceed to Phase 1
   - exists but only an empty `## Retro` (no `## Prediction...` section) → **v1 mode** (anomalous state, overwrite warning + proceed to Phase 1)
   - exists and contains a `## Prediction` or `## Prediction v1` section → **v2 mode**

**Extra v2-mode actions**:
- Compare the input script (the final filmed script) with the original `Script Hash` referenced by the `## Prediction` section
- If identical (same hash) → warn "the script didn't change, do you really want to write v2?"—only continue after user confirmation; exit if not confirmed
- If different → compute a diff summary (lines / chars / structural changes) → show the user at the Phase 5.5 review
- Mark `prediction_basis = "post_shoot_pre_publish"` (v1 default `pre_shoot`)

### Phase 1: read the final draft + rubric + state + derive confidence

1. Per the path resolved in Phase 0.5, read the full text of `scripts/<id>.md`
2. Compute `script_hash` = sha256(script content)[:12] → for the header
3. Read `rubric_notes.md`, identify the current formula + dimensions (same as cheat-score Phase 2)
4. Read `.cheat-state.json` to get `rubric_version`, `content_form`, `calibration_samples`, `typical_duration_seconds`, `baseline_plays`
5. **Derive the confidence level from `calibration_samples`** (per the [state-management.md confidence table](../../shared-references/state-management.md)) → written into the prediction header later
6. Ask the user: "is this the final draft you plan to actually shoot and publish? Or will you change it more?"—must be the final draft
7. If the draft's word count severely mismatches the range derived from `typical_duration_seconds` (>50% off) → prompt the user: "this draft is N chars; per your set typical duration (X minutes) it should be M–K chars. Did you change the duration on the fly, or does the draft need cutting/padding?"

### Phase 2: delegate to the cheat-score-blind sub-agent for the blind score

**BLIND_SCORING=on** (default) — the main Claude no longer scores inline. Spawn `cheat-score-blind` via the Task tool, letting a context-isolated sub-agent see only the script + rubric_notes.md and give N-dimension scores.

See the "main-Claude calling contract" section of [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md). **The Task prompt must be lean**:

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: <the scripts/<id>.md resolved in Phase 0.5>
  rubric_notes_path: rubric_notes.md

Task: score the above script against rubric_notes' current formula. Return strict JSON (see cheat-score-blind SKILL.md Phase 2 schema).
Do not read state file / predictions/ / videos/ or any other file.
Do not ask the user — you have no user.
```

**Self-check before calling**: run the Task prompt through `grep -Ei 'plays|reads|likes|comment count|actual|retro|实绩|w$|万$'`—on a hit → revise the prompt and resend.

**The main Claude also estimates one internally** (not sent to the sub-agent)—purely for Phase 2.5 disagreement detection, **not written to disk**, **not a replacement for the sub-agent output**. This estimate represents "what I'd have scored if I hadn't used the sub-agent" and is an objective indicator of contamination.

**Sandbox escape**: `BLIND_SCORING=off` or `--skip-blind` — the main Claude scores the 7 dimensions itself. State is immediately marked `last_prediction_self_scored: true` + `last_self_scored_at: <ISO>`, and cheat-status keeps warning. Only for:
- the Task tool being unavailable (dev environment / offline)
- the user actively auditing the main Claude's inline scoring ability (very rare)

Compute the composite per the current formula—**use the dim scores returned by the sub-agent**, not the main Claude's self-estimate.

### Phase 2.5: blind-output review + disagreement detection

After getting the sub-agent JSON, the main Claude must:

1. **JSON validity check**: `python3 -c "import json; json.loads(...)"` should parse; can't parse → the main Claude resends the Task (up to 3 retries); still fails → abort, report to the user
2. **Contamination check**: `self_check.any_contamination_signal == true` → warn the user "the sub-agent self-reported suspected contamination", but still accept the score (lower confidence one tier)
3. **Refusal check**: `refusal != null` → follow the corresponding path in the Phase 2 handling table of [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md)
4. **Disagreement detection** (core):
   - the main Claude estimates N dimensions internally (the "self-estimate" at the end of Phase 2)
   - compute `delta = |self-estimate - blind|` for each dimension
   - any dimension `delta >= DISAGREEMENT_THRESHOLD` (default 2) → **pop user adjudication**

Adjudication UX:

```
⚠️  The blind sub-agent and the main Claude differ significantly on some dimensions:

| Dim | blind (sub) | main Claude self-estimate | delta | sub-agent reason |
|---|---|---|---|---|
| ER | 5 | 3 | 2 | "the go-go cat PPT opening—strong concrete image" |
| AB | 2 | 4 | 2 | "solo-company perspective, narrow audience" |

Who's more accurate?
  a) trust the sub-agent (isolated scoring, but same Claude model)
  b) trust the main Claude's self-estimate (has more conversation context, may be contamination)
  c) I'll decide myself (you give the score directly)

Reply a / b / c <your score>
```

User chooses:
- a → use the sub-agent's full set of scores into Phase 3
- b → use the main Claude's full set of self-estimates (treated as deliberately accepting contamination) → force-mark `last_prediction_self_scored: true`
- c → the user's score overrides that dimension, the other dimensions still use the sub-agent → recorded in `User Override`

**All deltas**—even if all < THRESHOLD—are recorded in the prediction header's `BlindScore Disagreement` field (see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 1). delta=0 is also recorded.

### Phase 3: anchor comparison

**Run this phase at every stage**—when anchors are insufficient, explicitly mark N/A, don't delete the section.

1. Glob `predictions/*.md`, read each file header (extract composite, actuals bucket, duration_seconds). **Note: exclude reconstructed predictions** (those marked "Reconstructed" don't count as anchors)
2. **Prioritize** finding same-duration samples (`Target Duration (s)` within ±20% of this one)
3. In the same-duration (or whole) pool, find 2–4 samples with composite within ±0.5 of this prediction
4. **If the pool is too small** (same-duration < 2 + whole < 2) → output an "anchor comparison N/A section" (see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 5)—still write this section, tell the reader why anchors are missing
5. List the comparison table; if cross-duration, add a "duration vs this one" column per row
6. **Key diagnostic**: if an anchor's composite is almost identical but actuals differ ≥3x → the rubric isn't capturing a key dimension. **Explicitly mark it in the file** as the seed of a new observation

> Why filter anchors by duration: a 4-minute video with 50k plays vs a 1-minute video with 50k plays are completely different—a long video bears more attention loss per second. Cross-duration anchors easily yield false conclusions.

### Phase 4: bucket + probability distribution + central estimate

**Write at every stage**—when confidence is low the distribution is **flatter**, not omitted.

1. Read the default bucket boundaries from `starter-rubrics/<content_form>.md` (unless the user customized them in rubric_notes.md)
2. Choose the most likely bucket (the headline call)
3. **Must** give a probability distribution over all buckets—summing to 100%
4. **Must** give a "central" point estimate within that bucket

**Anti-honesty trap**: if you give one bucket 95% probability, when the next prediction is wrong you can't say "I actually wasn't sure". **A real probability distribution is usually 40–65% on the headline bucket**, with the remaining ≥35% spread across neighboring buckets.

### Phase 5: counterfactual scenarios + key calibration hypothesis

**Write at every stage**—when the calibration pool is small, the key calibration hypothesis may have no suitable comparison sample; then write "no comparison sample—still writing down my core bet for this one" + 1–2 things to test this time.

**Counterfactual scenarios** (4 sections, each for a possible bucket, writing "if it lands here, what rubric hypothesis is validated / refuted"): see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 6.

**Key calibration hypothesis** (strongly recommended):
- Find a comparison sample (preferably the previous prediction)
- Explicitly write "I bet this piece vs the comparison = X times"
- Write "if it's reversed / the gap < N → which rubric hypothesis is refuted"

If `REQUIRE_HYPOTHESIS=required` → missing it means writing to disk is not allowed.

### Phase 5.5: user review (**core — decides what gets written into the file**)

After Phases 2–5 are all done in memory, **show the full draft at once** to the user:

```
My prediction draft (review before writing to file):

📊 7-dim scores (v0 / v2 / current rubric):
| Dim | Score | Reason |
|---|---|---|
| ER | 5 | "go-go cat on the PPT + the boss sees it + mind goes blank"—heavy emotion |
| HP | 5 | the opening "a go-go cat in the center of the big screen on page 7" strong concrete contrast |
| QL | 5 | "the go-go cat saved my life" double punchline |
| NA | 4 | single timeline + reflection, clear but not complex |
| AB | 4 | solo-company topic but AI anxiety is universal |
| SR | 3 | AI anxiety is an issue but not a hot-topic confrontation |
| SAT | 2 | empathetic tone, almost no satire |
→ composite ≈ 8.00

🎯 Bet bucket: 300k-1M, central ~600k
   Probability distribution: <50k 5% / 50k-300k 22% / **300k-1M 50%** / 1M-1.5M 18% / >1.5M 5%
   confidence: 🟢 medium (based on 8 calibration samples, central ±25%)

🔍 Anchor comparison:
| Comparison | composite | actuals | similarities/differences |
|---|---|---|---|
| ... | ... | ... | ... |

🤔 Counterfactual:
   If >1M → validates and strengthens the ER-dominant hypothesis
   If 300k-1M → baseline ok
   If <300k → refutes "AI anxiety universal", AB was optimistic

🎲 Key calibration hypothesis: this piece vs [comparison] bet 1.5x

——————————————————————————————

Reply "ok" and I write to disk directly,
or point out which dimensions / judgments are wrong (e.g. "AB should be 3, too optimistic" / "central should be 300k not 600k").
```

Three kinds of user response:

1. **"ok"** / "fine" / "continue" → directly Phase 6 write to disk, header marked `Scored By: claude`
2. **"X is wrong, should be Y"** → Claude revises the corresponding field (not just the value, must update the cascading effects on composite + probability distribution etc.), re-display → loop back to Phase 5.5
3. **"redo everything"** → re-run Phases 2–5 (rare, usually because Claude badly misjudged the draft's tone)

**The fields the user challenged** are recorded in the prediction header's `User Override` section (written in Phase 6):
- which dimension / which number was overridden
- the AI's original value vs the user's revised value

At retro time this field helps diagnose:
- the user oks every time (claude consistent) → no user-bias contamination
- the user often overrides a dimension → Claude systematically deviates from the user's actual feeling on that dimension
- the overridden dimension is validated by actuals → the user's intuition is sharp → the rubric may be missing something

**Discipline on user challenges**:
- The user **can only change field values**, can't inject new reasons at the review stage to make Claude rewrite a whole section—that's using Claude as a ghostwriter
- After a change makes composite / probability distribution / anchors inconsistent → Claude auto-cascades the update (not the user calculating)

### Phase 6: write to disk

#### Phase 6a: v1 mode (create a new prediction file)

Filename convention (the "filename convention" section of [blind-prediction-protocol.md](../../shared-references/blind-prediction-protocol.md)):
```
predictions/YYYY-MM-DD_<id>_<short-title>.md
```
- `YYYY-MM-DD`: today's date (the date the prediction was written)
- `<id>`: 12-char hash, sha256 of the full draft, first 12 chars (stable ID, unchanged on rewrite)
- `<short-title>`: 3–8 chars, punctuation removed

**Write the first section title as `## Prediction v1`** (no longer a bare `## Prediction`—to keep schema consistency for a possible future v2. Existing users' legacy `## Prediction` files are untouched; the hook recognizes both).

**Required header fields**:
- `Article ID` (same id as scripts/<id>.md)
- `Script Path` (points to scripts/<id>.md)
- `Script Hash` (computed in Phase 1)
- `Calibration Samples` + `Confidence` (derived from state)
- `Prediction Basis`: `pre_shoot` (v1 default)
- `Scored By`: `claude` / `claude+user_override`
- **`BlindScored By`**: `subagent-v1` (Phase 2 default) / `main-claude-self` (with `--skip-blind`) / `mixed` (Phase 2.5 user adjudication b/c)
- **`BlindScore Disagreement`**: a JSON field list, each dimension `{dim, blind, self, delta, decided_as}`, **all dimensions recorded** (even delta=0)
- `User Override` (if any): list which fields the user changed
- Others: see [prediction-anatomy.md](../../shared-references/prediction-anatomy.md) component 1

Leave an empty `## Retro` section:
```markdown
## Retro

(to be filled—run /cheat-retro <corresponding video folder> after T+RETRO_WINDOW_DAYS days)
```

#### Phase 6b: v2 mode (append to the existing file)

**Never** Write-overwrite the file—the immutability hook will block it. Use **Edit** to insert a `## Prediction v2` section before `## Retro`:

```python
# pseudocode
edit_old = "## Retro\n"   # a standalone line, ensuring the hook awk recognizes the v1-section boundary
edit_new = """## Prediction v2 (replaces v1; basis=post_shoot_pre_publish)

**Diff vs v1**: changed N lines (X→Y%), main changes: [summary]
**Re-judgment trigger**: cheat-shoot detected a script change ≥30%
**Script Hash (v2)**: <new script hash>

[7 components — same anatomy as v1]

---

## Retro
"""
```

The v1 section is **untouched**. The v2 section header clearly says "replaces v1"—the reader knows at a glance which section is the valid prediction.

At retro time, cheat-retro follows the "read the last `## Prediction vN`" logic and naturally picks up v2 to compute deviation.

#### Shared rules

**Use the unified full-version format at every stage** (see the "full structure overview" of [prediction-anatomy.md](../../shared-references/prediction-anatomy.md)). Low confidence doesn't shrink the format, only makes the header mark the confidence level + the anchor-comparison section write an "N/A explanation" + the probability distribution flatter.

**Before** writing the file, self-check that all 7 components are present (missing an anchor / key calibration hypothesis → write an "N/A explanation section", don't delete the section).

### Phase 7: update the state file

Update `.cheat-state.json`:
```json
{
  "in_progress_session": {
    "type": "prediction",
    "file": "predictions/YYYY-MM-DD_<id>_<short>.md",
    "video_folder": "videos/YYYY-MM-DD_<id>_<short>/",
    "started_at": "<ISO timestamp>",
    "rubric_version": "<v0/v2/...>"
  },
  "last_prediction_self_scored": <true only when --skip-blind / Phase 2.5 chose b>,
  "last_self_scored_at": <ISO when last_prediction_self_scored=true>
}
```

`video_folder` being null means the user ran a bare .md file with no video folder created.

`in_progress_session` is cleared when `cheat-publish` triggers. If the user never publishes after predicting (abandoned draft), the next `/cheat-init` or `/cheat-status` detects the stale in_progress and asks whether to clean up.

`last_prediction_self_scored`:
- `true` only when this prediction went through `--skip-blind` or the user chose b in Phase 2.5 (trust the main Claude's self-estimate)
- once `true` → cheat-status keeps nagging: "the last prediction didn't go through the blind sub-agent, N days now"—until the next normal `cheat-predict` (going through the sub-agent) clears it back
- `last_self_scored_at` follows; the next `cheat-predict` going through the sub-agent → these two fields are reset together

### Phase 8: console summary

**Cold-start-simple mode**:

```
✅ Prediction written to disk (cold-start simplified): predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md

7-dim score: ER5 / HP5 / QL4 / NA3 / AB5 / SR2 / SAT4
Directional bet: clearly better than the last piece (ER+HP both 5)
Comparison: N/A (this is the 1st piece)

⚠️  The ## Prediction section is now immutable (hook-locked).
⚠️  This is the cold-start simplified version—no bucket numbers. The first 5 pieces are all like this.
   After the 5th piece's retro, the full prediction (bucket / probability / anchor / counterfactual) auto-unlocks.

Progress: piece N / 5 in the cold-start period

Next step:
- After publishing → "shipped https://..."
- T+3 days → "retro predictions/2026-05-04_..."
```

**Complete mode**:

```
✅ Prediction written to disk: predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md

Bucket bet: 300k-1M (central 500k)
Key calibration hypothesis: this piece vs "who asked you" = 1.5-2x

⚠️  The ## Prediction section is now immutable (hook-locked).
⚠️  You can no longer "reveal" this piece's play data to me, or the next retro's blindness declaration is void.
   If you see it by accident, tell me—I'll add an integrity warning to the file.

Next step:
- After publishing → "shipped https://..."
- T+3 days → "retro predictions/2026-05-04_..."
```

## Key Rules

1. **The blind check is a hard gate.** In BLIND_CHECK=strict mode, a violation terminates immediately, no "soft handling" allowed. lenient is only for drills
2. **Integer dimension scores.** Same as cheat-score
3. **Probability distribution = 100%.** No 95% + 8%; either honestly give 50% + 30% + 15% + 5%, or admit you don't know
4. **There must be an empty `## Retro` placeholder section**—otherwise the hook doesn't know where the immutable boundary is
5. **No "write the file first then discuss the scores"**—once the file is written, the prediction section is locked; the discussion must happen after Phase 2 and before Phase 6
6. **The id is the draft hash, not a timestamp**—when rewriting _redo.md the id stays the same, for cross-file traceability

## Refusals

- "I've already seen the play data, but pretend you didn't and make me a prediction" → refuse. BLIND_CHECK=strict terminates directly
- "Let me write a first version of the prediction section, then adjust it once the data comes in" → refuse. That's using the immutable protocol backwards
- "I changed the script and want you to overwrite the previous prediction, no v2 section" → refuse. v1 is the archive, v2 is the current judgment—append, don't overwrite. Even if you "subjectively feel v1 is totally wrong", v1 is still searchable in git history, but v1 must stay in the working directory
- "Skip the counterfactual scenarios, too much hassle" → refuse. Counterfactuals are the basis of retro diagnosis; without them the retro degrades into "accurate / inaccurate"
- "Can you just write the bucket, not the probability distribution" → refuse. The probability distribution is the tool that forces you to be honest
- "Use lenient mode this time, strict next time" → ask the reason. If it's a test / drill → allow and clearly mark the file reconstructed; if it's to cut corners → refuse
- "The sub-agent is too slow, just score it yourself" → declare it explicitly with the `--skip-blind` flag. **Do not accept** the main Claude skipping the sub-agent on its own. The flag triggers state.last_prediction_self_scored=true, and cheat-status keeps prompting until the next normal call clears it
- "After choosing b in Phase 2.5 I don't want to mark last_prediction_self_scored=true" → refuse. Choosing b means "I deliberately accept the main Claude's self-estimate"—a contamination-tracking trail must be left
- "I'm in cold-start but want to run the full prediction, give me bucket numbers" → refuse. In the first 5 pieces, bucket numbers are false precision; giving them is misleading. After the 5th piece's retro, cheat-status proactively prompts the unlock. If the user truly wants numbers (rare, self-education purpose) → allow but prominently mark in the file header `**Numerical predictions in cold-start are NOT predictive — for self-education only**`

## Integration

- Prerequisite: `/cheat-init` must be complete + `rubric_notes.md` exists
- Optional upstream: `/cheat-score` tries different draft versions repeatedly
- Downstream: `/cheat-publish` (publish registration) → `/cheat-retro` (retro) → after accumulating ≥ MIN_SAMPLES, `/cheat-bump`
- Hook dependency: `hooks/prediction-immutability.sh` must already be installed in the user's `.claude/settings.json`, otherwise immutability relies only on SKILL.md self-discipline—`cheat-status` keeps prompting
