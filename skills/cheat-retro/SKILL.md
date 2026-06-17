---
name: cheat-retro
description: T+N day data collection + retrospective + write new observations into rubric_notes.md. This is the feedback link of the calibration loop—a prediction without a retro is astrology. Triggers: "retro [path]" / "retro this" / "the T+3d data is in" / "fetch data [path]" / "retro this piece".
argument-hint: <prediction-file> [— window: 3|5|7] [— source: manual|adapter]
allowed-tools: Bash(*), Read, Edit, Write, Glob, Grep, Skill
---

# /cheat-retro — data collection and retrospective

Fetch the T+N day actual performance → compare against the prediction → distill new observations → write into rubric_notes.md. **Only appends to the `## Retro` section, never edits the prediction section.**

## Overview

```
[user: retro predictions/2026-05-04_...]
  ↓
[Phase 0: verify immutability + verify the time window]
  ↓
[Phase 1: fetch data (manual paste or adapter)]
  ↓
[Phase 2: write the actuals section + top-comment keywords]
  ↓
[Phase 3: validate/refute each prediction hypothesis]
  ↓
[Phase 4: distill new observations]
  ↓
[Phase 5: write to disk (append to the ## Retro section)]
  ↓
[Phase 6: write into the "Observation Log" section of rubric_notes.md]
  ↓
[Phase 7: detect whether a bump candidate is triggered → prompt the user to run /cheat-bump]
```

## Constants

- **RETRO_WINDOW_DAYS = 3** — default T+3d. Fast short-video platforms can set 1, long-form 7
- **DATA_SOURCE = manual** — manual: the user pastes numbers; adapter: call the corresponding platform adapter (requires configuration)
- **AUTO_PROPOSE_BUMP = true** — Claude proposes /cheat-bump when it judges a systematic deviation
  - **Default reference**: ≥3 consecutive same-direction deviations (high/low) → propose
  - **But Claude can propose earlier**: 1 extreme deviation (e.g. central 500k but actual 50k, ≥10x), proposes even without a "streak"
  - **And can go later**: 3 same-direction but each deviation is small (<25%), may be just noise rather than systematic
- **TOP_COMMENTS_N = 20** — fetch / paste the top N most-liked comments

> 💡 Override at call time: `/cheat-retro <file> — window: 7 — source: adapter`

## Inputs

| Required | Source |
|---|---|
| `<prediction-file>` or `<video-folder>` | user argument; if missing, from `pending_retros[0]` in `.cheat-state.json` |
| `rubric_notes.md` | user project root |
| `.cheat-state.json` | state file |

### Argument parsing (accepts both forms, same as cheat-predict)

What the user gives may be:
- **`predictions/2026-05-04_<id>_<short>.md`** → use this prediction file directly
- **`videos/2026-05-04_<id>_<short>/`** → find the corresponding prediction file (match by id) + write report.md into that video folder
- default → take the earliest from `pending_retros[0]`

## Workflow

### Phase 0: verify

1. Read `<prediction-file>`, confirm it exists
2. **Identify the valid prediction section**: scan all `## Prediction...` sections (may contain `## Prediction`, `## Prediction v1`, `## Prediction v2`, etc.):
   - take the **last** `## Prediction vN` as the basis for this calibration (if v2 exists, use v2; if only v1, use v1; a legacy single `## Prediction` is used directly)
   - the corresponding item's `v2_prediction_written` in state.shoots should match "whether a v2 section exists"—if inconsistent, warn (state and file are out of sync)
3. **Verify immutability**: cache the content of all `## Prediction...` sections in memory (for cross-check after Phase 5—**all sections are immutable**, not just the valid one)
4. Verify the file header has `Published at` → an unregistered one can't be retro'd, prompt the user to `/cheat-publish` first
5. Verify the time window: today - published_at >= RETRO_WINDOW_DAYS. Not enough → prompt "X days short", ask the user whether to still insist on the retro (mark `early_retro: true`)
6. Verify whether an existing retro section is already filled—if so, ask "supplement or correct?"
   - supplement → append a new subsection under the existing retro section, marked with the date
   - correct the prediction section (user delusion) → refuse

### Phase 1: fetch data

Two paths by the `state.data_collection` field—after fetching, **write to the video folder's `report.md`** (if the prediction is associated with a video folder), and parse a summary inline into the prediction's retro section.

#### Path A: `DATA_SOURCE=manual` (fallback)

- Ask the user: "paste this piece's current data: plays / likes / comments / shares / saves (order doesn't matter, as long as it's recognizable)"
- User pastes → parse and extract numbers
- **Mandatorily require top comments**: have the user paste TOP_COMMENTS_N comments (each with like count) from the platform backend or by directly opening the comment section into the conversation
  - User refuses / gives fewer than 5 → **refuse to continue**: "comments are the real signal—a meme burst like 'she's different' can only be seen from comments.
    A retro without comments = diagnosing illness by reading a thermometer. Paste the top 20 for me. If you really can't get them, tell me why (e.g. comments are off), I'll mark `comments_unavailable`, but this retro is worth less."
- Write the pasted raw data into `videos/<...>/report.md` (if there's a video folder)

#### Path B: `DATA_SOURCE=adapter`

Decide which to call by the prediction header's `Platform` field + state's `enabled_perf_adapters`:

| Platform | Adapter | How to call |
|---|---|---|
| `douyin` | `adapters/perf-data/douyin-session/` | `bash <skills-dir>/../adapters/perf-data/douyin-session/run.sh <aweme_id> <video_folder>` |
| `youtube` | `adapters/perf-data/youtube-data-api/` (TBD) | call the YouTube Data API (needs an API key) |
| `bilibili` | `adapters/perf-data/bilibili-stat/` (TBD) | call the Bilibili official stat endpoint |
| other | no adapter | gracefully degrade to Path A |

**Special handling for douyin-session**:
- video URL (e.g. `https://v.douyin.com/abc123`) → resolve the short link → extract the aweme_id
- before calling, confirm the cookie file exists (the adapter looks for `.auth/`); if not, prompt the user to run `python <adapter>/crawler.py login` first
- the adapter outputs to `<video_folder>/report.md` (the adapter's renderer.py already writes in this format)
- cheat-retro reads this report.md to parse the key data → writes a summary into the prediction's retro section

**Any adapter failure** (expired cookie / endpoint change / network) → **gracefully degrade to manual**, prompt the user: "adapter call failed, reason [X]. Switching to manual mode—paste the data below". **Don't block the flow.**

#### Common output

Regardless of Path A or B, in the end:
- `videos/<...>/report.md` contains the complete raw data (numbers + top comments)
- the prediction file's retro section contains a **summary** (key ratios + comment-keyword clustering + validation/refutation verdict)
- report.md is the data truth, the prediction retro section is the judgment truth

### Phase 2: write the actuals section + top-comment analysis

**Actuals data format** (refer to the retro-section format in [prediction-anatomy.md](../../shared-references/prediction-anatomy.md)):

```markdown
### Actuals
- Plays: 711k (high within the `300k-1M` bucket, **+42%** relative to the central 500k)
- Likes: 24k (like rate 3.38%)
- Comments: 899 (comment rate 0.126%)
- Saves: 5251
- Shares: 18k (share rate 2.53%, strong)
```

The derived ratios between data points (like rate, comment rate, share rate) must be computed—they're signals the raw play count alone can't expose.

**Top-comment keyword clustering**:
- Cluster the pasted N comments into 3–5 categories (high-like memes / concept references / off-topic noise / share-exposing hints / @-friend propagation, etc.)
- List representative comments (with like counts) for each category
- Report the proportions ("22% meme reuse, 35% concept reference, 5% off-topic")

### Phase 3: validate/refute

For each item in the prediction file (the reasoning-factor table, key calibration hypothesis, counterfactual scenarios), judge item by item:

```markdown
### Which predictions were validated ✅ / refuted ❌

**Validated ✅**:
- The key calibration hypothesis fully held: this piece 711k / "who asked you" 117k = 6.07x, far exceeding my bet of 1.5-2x
- ER=5 dominating emotional propagation → strong evidence for H1
- HP=5 verified: share rate 2.53% matches "punchlines being frequently quoted"

**Refuted ❌**:
- The central 500k was exceeded by +42%
- The counterfactual reasoning "must pair with a strong social issue to break 300k" is completely wrong
- The SR bet ("H2 SR should be raised") was reverse-refuted: SR contributes almost nothing in emotion-oriented scenarios
```

**Key discipline**:
- Each validation / refutation must cite specific data ("share rate 2.53%"), no vague wording like "basically matches"
- The counterfactual's "if it lands in bucket X it means..."—the bucket it actually landed in directly tells you which rubric hypothesis was tested; write it explicitly

### Phase 4: distill new observations (**two kinds, written into two files**)

#### 4a. Rubric observations (written into rubric_notes.md)

Observations related to scoring dimensions / formula / bucket boundaries:

```markdown
### New observations to write into rubric_notes.md

1. **ER's real weight in emotion-oriented scenarios should be ≥ ×2.0**: the 6x traffic ratio vs "who asked you" is v2 rubric's strongest counterfactual evidence
2. **Issue share impulse (TS) is a hidden dimension**: joker / "she's different" / filter reconstruction provide a safe self-deprecating identity, sharing doesn't expose one's situation, a TS=5 sample
3. ……
```

Each observation must be traceable to a specific data point (don't write "emotion is important"—write "ER5/SR2 vs ER3/SR4 at the same composite, traffic differs 6x").

#### 4b. Writing-pattern observations (written into script_patterns.md)

Diff `scripts/<id>.md` (the pre-shoot draft, possibly written by cheat-seed or the user) vs `videos/<id>/script.md` (the actual filmed script—the version the user provided at cheat-shoot), and find the parts that **changed and clearly affected traffic**:

| What the user did | Traffic impact | Propose appending a pattern? |
|---|---|---|
| Cut a section | actual ≥ central → "cutting it didn't hurt traffic"—verifies that section was redundant | Yes, add to the "user script-change history observations" table in script_patterns.md |
| Added a sentence / interaction hook | actual exceeds central → may be a new pattern | Yes, candidate Pattern N, marked ≥1 sample to be verified |
| Changed the style (e.g. softened the opening) | higher than similar samples → the style change worked | Yes, candidate Pattern N |
| Didn't touch the structure / the change is unrelated to traffic | — | Don't append |

Output format:

```markdown
### New pattern candidates to write into script_patterns.md

1. **User script-change pattern**: cut [section X] / added [Y]
   - Traffic impact: actual [N] vs central [M], [deviation / hit]
   - Suggestion: append to the "user script-change history observations" table in script_patterns.md

2. **New pattern candidate N**: [one-sentence description]
   - single-sample support
   - trigger condition: [when to use]
   - Suggestion: append to the "newly discovered Patterns" section at the end of script_patterns.md, marked ≥1 sample to be verified
```

Ask the user: "want to append these to script_patterns.md? (yes / no / which ones)". **Only append after user confirmation**—to avoid writing a single-point observation directly as a formal pattern.

> **Rubric evolution ≠ writing evolution**—the two are decoupled:
> - rubric_notes.md learns "which dimensions actually predict traffic"
> - script_patterns.md learns "what writing approach actually works"
> There may be overlap (e.g. the MS dimension and the "interaction hook" pattern), but they're recorded in two files because their **scope differs**—a rubric change affects all future scoring, a pattern change affects all future drafts.

If `videos/<id>/script.md` is **missing** (the user marked `script_lost` at cheat-shoot) → skip 4b, can't diff.
If `script_consistency = "consistent"` (the user didn't change the script when filming) → 4b is still meaningful (the diff may be empty), but you can quickly skip the detailed look.
If `script_consistency = "modified"` (the user changed it when filming) → **4b is the core**, focus on learning this change → traffic impact.

### Phase 5: write to disk in the ## Retro section

Use the Edit tool, **append only** to the existing `## Retro` section (if there's a placeholder `(to be filled)` line, delete it first):

```markdown
## Retro

**Retro date**: 2026-05-07 (publish T+3d)
**Fetch time**: 2026-05-07 09:30
**Data source**: manual paste

### Actuals
[Phase 2 content]

### Top comment keywords
[Phase 2 content]

### Which predictions were validated / refuted
[Phase 3 content]

### New observations to write into rubric_notes.md
[Phase 4 content]
```

**Verify again after writing**: read the saved file, the merged hash of **all** `## Prediction...` sections (v1 / v2 / legacy) should equal the merged hash cached in Phase 0. **Any section edited → error and roll back.**

### Phase 6: write into rubric_notes.md + script_patterns.md

#### 6a. rubric_notes.md (the output of Phase 4a)

Per the "observation-log template" format of [observation-lifecycle.md](../../shared-references/observation-lifecycle.md), append to the `## Observation Log` section of `rubric_notes.md`:

```markdown
### YYYY-MM-DD [title short-name] (id) — [one-sentence qualitative]
- Prediction: composite=X.XX, bucket=Y
- Actuals: plays / likes / comments / shares (with T+Nd annotation)
- Top comment keywords: [brief excerpt + like counts]
- Judgment: which dimension was validated/refuted? Why?
- Rubric adjustment: [if any, write "when scoring XX-type articles next time, change YY"]
- See: [predictions/<file>.md]
```

**Detect cross-sample patterns**: scan the existing "Observation Log" to see whether the new observation forms ≥2-sample support with an existing observation. On a hit, promote it to the "major cross-video observation" section per [observation-lifecycle.md](../../shared-references/observation-lifecycle.md).

#### 6b. script_patterns.md (the output of Phase 4b, **only written after user confirmation**)

If the user replied "yes" or selectively confirmed a few in Phase 4b:
- "user script-change pattern" → append to the "user script-change history observations" table in script_patterns.md
- "new pattern candidate N" → append to the "newly discovered Patterns" section at the end, **explicitly marked ≥1 sample to be verified**

The format for a new pattern candidate (same as the Pattern 11/12 examples in [script_patterns.template.md](../../templates/script_patterns.template.md)):

```markdown
### Pattern N (from [video short-name], single sample to be verified)

**Phenomenon**: [Phase 4b description]

**Mechanism**: [why it works—a guess based on this one observation]

**Trigger condition**: [when to use]

**To be verified**: needs ≥2 samples of support to be promoted to a formal pattern.
```

Promoting a cross-sample pattern to formal: scan the "newly discovered Patterns" section to see whether there's ≥2-sample support for the same phenomenon → promote to the core pattern library + remove the "to be verified" mark.

If the user said no to everything ("no") in Phase 4b → skip 6b, rubric_notes.md is still written as usual.

### Phase 7: detect a bump trigger

Read the `consecutive_directional_errors` field in `.cheat-state.json`, update by this retro's verdict direction:
- this prediction overestimated (actual < central -25%) → push `["high"]` + record deviation_magnitude (e.g. 0.5x / 0.3x)
- this prediction underestimated (actual > central +25%) → push `["low"]` + record deviation_magnitude
- within ±25% → don't push

**Claude judges whether to propose a bump** (not a fixed threshold):

```
Judgment dimensions:
1. Consecutive same-direction count (default reference: ≥3)
2. Single-time deviation magnitude (default reference: >2x or <0.5x counts as extreme)
3. Whether the deviation can be explained by a single missed dimension (e.g. ER or SR consistently off)
4. Whether the user repeatedly mentions the same phenomenon in retros

Any one strong enough → propose a bump:
- 3 consecutive same-direction, each a moderate deviation → propose
- 1 extreme deviation (e.g. ≥10x), even without a streak → propose ("one-off strong signal")
- 2 same-direction + consistent reverse evidence in comments → propose ("comment + data dual signal")

When not to propose:
- 3 same-direction but each very small (<25%) → may be just noise
- deviation spans multiple dimensions with no clear direction → bump doesn't know what to change
```

When proposing, output:

```
🚨 Detected [systematic deviation signal] / [extreme single-point deviation].

[brief description: N consecutive / 1 extreme / comment dual signal, etc.]

This may be a signal of rubric systematic deviation. Suggestion:
- run /cheat-bump to see whether the formula needs an upgrade
- or first see /cheat-status for a detailed analysis

Note: this proposal is [default-aligned: meets ≥3 same-direction] / [judgment-driven: 1 extreme 10x deviation]
```

Update the state file:
```json
{
  "calibration_samples": <+1>,
  "pending_retros": [<remove this one>],
  "last_retro_at": "<ISO>",
  "consecutive_directional_errors": [...]
}
```

## Key Rules

1. **The prediction section is immutable.** Phase 0 cache + Phase 5 verify are dual insurance. Any hash mismatch → error and roll back
2. **The data source must be annotated.** `Data source: manual paste` or `Data source: adapter:douyin-session` written into the retro section
3. **Observations are traceable.** Each new observation cites a specific data point
4. **Don't bump in the retro.** Phase 7 only **proposes** a bump; the actual upgrade goes through `/cheat-bump`—to avoid doing two things in one operation
5. **Mark an early retro.** Doing a retro before RETRO_WINDOW_DAYS → the state file records `early_retro: true`, and such a sample is downweighted at bump time

## Refusals

- "I've already seen this data, but pretend you haven't and do the retro at the blindness of prediction time" → a retro is by definition done after seeing the data; this phrasing itself isn't a violation, but confirm the user didn't reveal data before the prediction was written
- "Change the probability distribution in the prediction section to make the retro look more accurate" → refuse. Principle #1
- "Skip the observation distillation, just end it" → refuse. New observations are the only fuel for rubric evolution; without them the retro degrades into "a glance"
- "Just bump directly, don't go through /cheat-bump separately" → refuse. The bump flow has a complete cross-model audit + cleanup pass; retro is the trigger, not the executor

## Integration

- Prerequisite: `/cheat-publish` registered + the time window reached
- Downstream: accumulated `consecutive_directional_errors` reaching 3 → triggers a `/cheat-bump` proposal
- State field update: `calibration_samples` +1 (this is key to cheat-status showing progress)
- pending_retros: remove this one
- Tightly coupled with [observation-lifecycle.md](../../shared-references/observation-lifecycle.md): each retro is the entry point for adding observations
