# Prediction Anatomy

Referenced by these sub-skills: `cheat-predict`, `cheat-retro`, `templates/prediction.template.md`.

**All predictions use a unified format**—7 required components + a retro section. The confidence level (derived from `calibration_samples`, see the confidence table in [state-management.md](state-management.md)) is annotated as a header field, telling the user how trustworthy this prediction is, **but doesn't change the prediction format itself**.

> **Why no cold-start-simple / complete split (an abandoned doubt of the old design)**:
> Splitting cold-start into a simplified version was based on the worry that "the first 5 pieces' bucket numbers are false precision". But the better solution is to **show a confidence level**—a weather forecast always reports a specific temperature plus a confidence, it doesn't withhold numbers just because the forecaster is inexperienced.
> The dual-version switch also introduced a complexity jump of "the 5th piece suddenly unlocks the full version"—a fractured UX. A unified format + progressive confidence annotation is smoother.

Reference real samples: the creator's project (private, with 25+ video calibrations)—the tool's design inspiration and rubric weights both come from this real-world testing.

---

## The 7 required components

### Component 1: File header

```markdown
# <title> — prediction log

**Article ID**: <12-char hash>  (sha256 of scripts/<id>.md initial content, first 12)
**Title**: <the piece's full title>
**Rubric Version**: **v0** | **v1** | **v2** | ...
**Prediction date**: 2026-05-04 (based on the final draft)
**Script Path**: scripts/2026-05-04_<id>_<short>.md
**Script Hash**: <sha256:12 of script content at predict time>
**Target Duration (s)**: 240  (derived from state.typical_duration_seconds)
**Actual Script Length**: 980 chars  (read from the Script Path file)
**Calibration Samples (at predict time)**: 3
**Confidence**: 🟡 fairly low (central ±40%, usable as one reference)
**Prediction Basis**: pre_shoot  ← or `post_shoot_pre_publish` (v2 section)
**Scored By**: claude  ← or `claude+user_override`
**BlindScored By**: subagent-v1  ← or `main-claude-self` / `mixed`
**BlindScore Disagreement**: <inline JSON, see below>
**User Override**: none  ← or list the overridden fields
**Data status at predict time**: **blind** (haven't seen any <platform> actual play data)
```

The `BlindScore Disagreement` field is an inline JSON array, **one line per dimension**, **delta=0 must also be recorded**:

```json
[
  {"dim": "ER",  "blind": 5, "self": 5, "delta": 0, "decided_as": 5},
  {"dim": "SR",  "blind": 3, "self": 4, "delta": 1, "decided_as": 3},
  {"dim": "AB",  "blind": 2, "self": 4, "delta": 2, "decided_as": 4, "user_decision": "b"},
  {"dim": "HP",  "blind": 5, "self": 5, "delta": 0, "decided_as": 5}
]
```

- `blind`: the score the sub-agent gave
- `self`: the main Claude's self-estimate (the internal estimate at the end of Phase 2, the one that wasn't written to disk is now written—this is a necessary honesty cost)
- `delta`: |blind - self|
- `decided_as`: the final value that enters the composite calculation
- `user_decision` (if any): the option `a` / `b` / `c <number>` at the Phase 2.5 user adjudication—only appears when delta ≥ DISAGREEMENT_THRESHOLD

Required-field rules:
- `Rubric Version` required—looking back at a v2 prediction in the v3 era, without the version number you can't compare fairly
- `Data status at predict time` required—explicitly declaring blind is the precondition of the immutable promise
- `Script Path` required—points to `scripts/<id>.md` (the pre-shoot draft)
- `Script Hash` required—at cheat-shoot time hash `videos/<id>/script.md` again; on a mismatch → add an integrity warning to the retro section
- `Calibration Samples` + `Confidence` required—tell the reader how trustworthy this prediction is. **Confidence auto-derived** from calibration_samples (see state-management.md)
- `Prediction Basis` required—`pre_shoot` is the standard blind prediction; `post_shoot_pre_publish` is the v2 post-shoot re-judgment (still hasn't seen data, but soft-blind)
- `Scored By` required—tells the reader whether this prediction was fully automatic by Claude or the user intervened:
  - `claude`: Claude proactively scored + bucket + probability, the user reviewed and replied "ok" to accept
  - `claude+user_override`: the user challenged and changed some fields at the review stage
- **`BlindScored By` required**—who scored the dimensions this time:
  - `subagent-v1`: blind scores obtained via the Task tool calling the cheat-score-blind sub-agent (default, the Phase 2 path)
  - `main-claude-self`: the user's `--skip-blind` flag or Phase 2.5 choosing b (trust the main Claude's self-estimate)—simultaneously `state.last_prediction_self_scored=true`
  - `mixed`: at Phase 2.5 the user chose c to set individual dimensions, other dimensions still via the sub-agent
- **`BlindScore Disagreement` required**—the JSON above. **All dimensions recorded** (even delta=0), no "only record the big differences" allowed. Reason: at retro time, analyzing "which kind of dimension the sub-agent and the main Claude systematically disagree on" by the delta distribution is an important signal for rubric evolution
- `User Override` required (if any)—list which fields changed from X to Y, with the user's reason. At retro time this field helps diagnose: the user's override validated by actuals (the user's intuition is sharp) → the rubric may be missing something

---

### Component 2: Input snapshot

Record the draft's state **at predict time**—especially the user's final changes.

```markdown
## Input snapshot

**Scores (vN)**: ER5 / HP5 / QL5 / NA3 / AB5 / SR2 / SAT4 → composite=**8.24**

**User rewrite highlights vs Claude's draft (if any)**:
- **Opening**: user cut the EWDM model name and build-up
- **Cut**: [specific paragraph / concept name / build-up]
- **Kept**: [key punchline / acknowledgments / body structure]
- **Rhythm**: about N% [tighter / looser] than the draft
```

> If the user wrote it from scratch (didn't use cheat-seed), write here "user-original draft, no Claude-draft comparison".

---

### Component 3: Prediction body ⭐ immutable section

This is the core of the immutable section. `hooks/prediction-immutability.sh` intercepts all Edits from this section to the next `##`.

```markdown
## Prediction

**Bucket**: `300k-1M`

**Internal probability distribution**:
- `<50k` → 3%
- `50k-300k` → 22%
- **`<headline bucket>` → 55%** (central ~500k)
- `>1M` → 17%
- `>1.5M` → 3%

**One-sentence reason**:
> ER=5+AB=5 crush is a universal audience; IS directly locks in; 7.3 days + zero-signal reversal + MVP punchline, a complete emotional curve; SR=2 with no social-issue backing is the ceiling bottleneck; expect 400-600k central.
```

Mandatory requirements:
- **Bucket** must be one of the 5 predefined
- **Probability distribution** must sum to 100%—the tool that forces you to be honest
- **Central** is the point estimate within that bucket, for the retro to judge "high / low"
- **One-sentence reason** condensed into a DB field, for cross-sample retrieval

**About the cold-start bucket**: few calibration_samples → the probability distribution **should be flatter** (e.g. 30/30/20/15/5 rather than 5/40/45/8/2). Low confidence doesn't mean skipping the bucket; it means having the appropriate uncertainty about the bucket.

---

### Component 4: Reasoning factors table

Each factor driving the judgment + direction + confidence + note.

```markdown
## Reasoning factors

| Factor | Direction | Confidence | Note |
|---|---|---|---|
| ER=5 | strong + | high | "scrolling chat logs at 3 a.m." extremely concrete |
| IS hook | strong + | high | "only affects people who X" locks the audience in one sentence |
| SR=2 | strong - | high | no social-issue backing, pure personal emotion has a limited ceiling |
| data+punchline route | medium ? | low | algorithm-friendliness unverified |
```

**Confidence** has three tiers: high (strong evidence + multiple anchors), medium (has a reason but few samples), low (by intuition).
- At retro time if a "low-confidence" factor is validated → strong intuition
- If a "high-confidence" factor is refuted → the rubric has a bug

---

### Component 5: Anchor comparison

Find 2-4 old samples with a close composite, list their actuals.

```markdown
## Anchor comparison

| Comparison sample | composite | actuals | similarities/differences |
|---|---|---|---|
| hamster | 9.41 | ~1.5M | composite 1.17 lower, but big route difference (analogy-teaching vs data+punchline) |
| housing price | 9.41 | 2.59M | SR differs by 3 (2 vs 5) |
| who asked you | 8.24 | T+8d 117k | same composite but ER 5 vs 3, SR 2 vs 4 |
```

The anchor's value: catch errors the formula can't.

**When calibration samples are insufficient** (< 2 published samples with a near composite):

```markdown
## Anchor comparison

The calibration pool has only N samples, no composite-±0.5 near samples. **Anchor comparison N/A**—
note this prediction's confidence is marked 🟡 fairly low / 🔴 very low, the bucket central is for reference only.
```

**Still write this section**—tell the reader why anchors are missing. Don't delete the section.

---

### Component 6: Counterfactual scenarios

For each possible bucket, write a section "if it lands here, what it means".

```markdown
## Counterfactual scenarios

**If it breaks `>X`** (X% expected):
- [what hypothesis is validated]
- [what hypothesis is refuted]
- [what rubric dimension might be added]

**If it lands in `headline bucket`** (X% expected):
- [what the baseline validates]

**If it drops to `<X`** (X% expected):
- [what core judgment is refuted]

**If `<<X`** (X% expected):
- [the possible explanation of an extreme scenario]
```

Why required: at retro time, **which bucket it actually landed in** directly tells you which rubric hypothesis was tested. Without counterfactual scenarios, the retro degrades into "accurate / inaccurate this time"—no diagnostic value.

---

### Component 7: Critical calibration hypothesis

Optional but strongly recommended: treat this prediction as an experiment, explicitly write "if X happens, it proves Y".

```markdown
## Critical calibration hypothesis (vs "who asked you")

Two pieces with the same composite=8.24, difference:
- how to stop expecting: ER=5 / SR=2
- who asked you: ER=3 / SR=4

**I bet: this piece > "who asked you" (ratio 1.5-2x)**

If it's reversed → SR's weight in the rubric should go up, ER's down
If the gap < 1.3x → the rubric is basically OK, the difference is within noise
```

The calibration hypothesis is the seed of a rubric upgrade—a single hypothesis validated by ≥3 samples → enters the bump candidates.

**When calibration samples are insufficient**: write "no comparison sample—still writing down my core bet for this one (even without an anchor)", then write one or two things to test this time. **Don't delete this section.**

---

### Component ∞: Retrospective — append only

Appended at T+N day retro after publishing. **Don't modify any character of the prediction section.**

```markdown
## Retro

**Retro date**: 2026-05-07 (publish T+3d)
**Fetch time**: 2026-05-07 09:30
**Data source**: manual paste / adapter:douyin-session

### Actuals
- Plays: 711k (high within the `300k-1M` bucket, **+42%** relative to the central 500k)
- Likes: 24k (like rate 3.38%)
- Shares: 18k (share rate 2.53%, strong)

### Top comment keywords
- "she's different" meme burst: 2266 likes topping the chart, 12+ variants throughout

### Which predictions were validated / refuted
**Validated ✅**:
- The critical calibration hypothesis fully held: this piece 711k / "who asked you" 117k = 6.07x
- ER=5 dominating emotional propagation → strong evidence for H1

**Refuted ❌**:
- The central 500k was exceeded by +42%
- My bet on SR was reverse-refuted: SR should go down in emotion-oriented scenarios

### New observations to write into rubric_notes.md
1. ER's real weight in emotion-oriented scenarios should be ≥ ×2.0
2. Issue share impulse (TS) is a hidden dimension
```

---

## Full structure overview

```
file: predictions/YYYY-MM-DD_<id>_<short>.md

# title — prediction log         ← Component 1: header (incl. confidence + script_hash + Prediction Basis + BlindScored By + BlindScore Disagreement)
(metadata block)

## Input snapshot                ← Component 2
(scores + user rewrite highlights vs Claude's draft)

## Prediction v1                 ← Component 3 ⭐ IMMUTABLE start (based on the pre-shoot draft)
(bucket + probability + central + one-sentence reason)

## Reasoning factors             ← Component 4
(table with direction + confidence)

## Anchor comparison             ← Component 5 (still write an "N/A section" when the pool is insufficient)

## Counterfactual scenarios      ← Component 6
(one "what it means" section per bucket)

## Critical calibration hypothesis  ← Component 7
(the explicit bet treating this prediction as an experiment)

## Prediction v2 (replaces v1)   ← (optional) triggered by cheat-shoot when post-shoot script change ≥30%, append not overwrite
(same 7-component structure + header with a Diff vs v1 summary)

## Retro                         ← append only, IMMUTABLE boundary
(actuals + top comments + validated/refuted + new observations)
```

### v1 / v2 section convention

- **New file**: cheat-predict writes `## Prediction v1` (no more bare `## Prediction`—to keep schema consistency for v2)
- **Legacy compatibility**: `## Prediction` files written in the v0.1.0 era are untouched; both the hook and cheat-retro recognize them
- **v2 trigger condition**: cheat-shoot detects the line-diff between the filmed script and `scripts/<id>.md` ≥ 30% ([V2_TRIGGER_THRESHOLD](../skills/cheat-shoot/SKILL.md)), calls `/cheat-predict — mode: v2 — prediction-file: <path>`
- **Append not overwrite**: the v2 section is inserted before `## Retro`. The v1 section is **never** modified (physically enforced by the hook)
- **Which is used for calibration**: cheat-retro reads the last `## Prediction vN` to compute deviation; v1 stays as a historical archive
- **Diff learning**: the field difference between v1 and v2 (e.g. ER 4→5) is the scoring change brought by the user's rewrite, evidence for a rubric upgrade

### Prediction Basis field

The prediction header must contain `Prediction Basis`:
- `pre_shoot` (v1 default, standard blind prediction)
- `post_shoot_pre_publish` (v2, soft-blind prediction—post-shoot script change but re-judged before publishing)

cheat-retro uses this field to separate the two data lines in score-curve / bump calibration, avoiding sample mixing.

---

## Sub-skill acceptance criteria

After `cheat-predict` finishes writing a prediction, it must self-check that all 7 components are present:
- Components 5 / 7, when calibration samples are insufficient, still write an "N/A section + explanation", **not allowed to skip directly**
- The header's `Calibration Samples` + `Confidence` are required—the reader sees at a glance how trustworthy this prediction is

When `cheat-retro` writes the retro section, it must first verify the file's 7 components:
- Missing a component → warn "this prediction is non-standard, the retro is worth less"
- The retro-section format is **independent** of the confidence level—a retro at any stage is the same format
- diff the `Script Hash` with the current `videos/<id>/script.md` hash → on a mismatch, add a `**Script changed between predict and shoot**` warning in the retro section

---

## Comparison with the old design (v1 user migration reference)

| v0 design (abandoned) | v1 design (current) |
|---|---|
| `prediction_complexity = cold-start-simple` uses a 3-component simplified version | field removed. All predictions use the unified 7-component version |
| `prediction_complexity = complete` uses 7 components | same—it was always 7 components |
| The 5th retro "unlocks the full prediction" | no unlock needed—always full. The confidence level auto-rises with calibration_samples |
| Cold-start skips bucket / anchor comparison / counterfactual | **don't skip**—if anchors are insufficient mark "N/A" explicitly, still write the bucket (the probability distribution needs to be honestly spread) |
| Use the mode=cold-start field to branch the flow | field removed. All skills go through the same flow, progressively showing confidence by calibration_samples |
