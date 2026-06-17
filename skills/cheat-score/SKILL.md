---
name: cheat-score
description: Score a single draft against the rubric. **Console output only—writes no files, makes no prediction.** Triggers: "score this [path]" / "grade this draft" / "let me see a score first". A lightweight exploration step before cheat-predict.
argument-hint: <draft-path>
allowed-tools: Read, Glob, Grep
---

# /cheat-score — single-draft scoring

Scores but **does not predict**. The user uses it to quickly see a draft's composite and decide whether it's worth entering the formal prediction flow.

## Overview

```
[user: score this draft.md]
  ↓
[read draft.md + rubric_notes.md]
  ↓
[score each dimension 0-5 + write a one-line reason + compute composite]
  ↓
[console output: scores + composite + recommended next step]
  ↓
[done — writes no files]
```

## Constants

- **RUBRIC_PATH = rubric_notes.md** — source of the current rubric
- **OUTPUT_DETAIL = full** — full: includes per-dimension reasons; compact: scores table only

> 💡 Override at call time: `/cheat-score draft.md — OUTPUT_DETAIL: compact`

## Inputs

| Required | Source |
|---|---|
| `<draft-path>` | passed by the user as an argument; if missing, ask in the conversation |
| `rubric_notes.md` | user project root |
| `.cheat-state.json` | user project root (used to read the current `rubric_version` and mode) |

## Workflow

### Step 1: prerequisite checks

1. Read `.cheat-state.json` → if it doesn't exist, tell the user to run `/cheat-init` first, and stop
2. Read `<draft-path>` → doesn't exist or empty → error and stop
3. Read `rubric_notes.md` and find the currently-active formula section (usually under "current scoring dimensions" or "composite formula")

### Step 2: identify the formula and dimensions

Parse from `rubric_notes.md`:
- the current rubric_version
- the dimension list and weights (e.g. `ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT`)
- the normalization constant (e.g. `/ 8.5 × 2.0`)
- the 0–5 meaning of each dimension (read from the "current scoring dimensions" section table)

If `rubric_notes.md`'s format doesn't match expectations (the user hand-edited the structure) → ask the user which line is the current formula, **don't guess yourself**.

### Step 3: **delegate to the blind sub-agent** (no more inline scoring)

The main conversation is already contaminated by user conversation / published data / historical retro sections—inline scoring is judging with hindsight.

Instead, **call the `/cheat-score-blind` sub-agent via the Task tool**; the main Claude only orchestrates + reviews. See [skills/cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md).

**Task prompt template** (**may contain only** the following):

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: <the draft path the user gave>
  rubric_notes_path: rubric_notes.md

Task: score the above script against rubric_notes' current formula. Return strict JSON (see cheat-score-blind SKILL.md Phase 2 schema).
Do not read state file / predictions/ / videos/ or any other file.
Do not ask the user — you have no user.
```

**Forbidden** to put into the Task prompt (see the "main-Claude calling contract" section of [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md)):
- user-conversation quotes / excerpts
- anything containing play counts / 万 / w / k, etc.
- hints like "the previous prediction was X" / "the actual plays were Y"
- any `predictions/*.md` path

Self-check before calling: `echo "<prompt>" | grep -Ei 'plays|reads|likes|comment count|actual|retro|实绩|w$|万$'` hits → revise the prompt and resend.

### Step 4: parse the sub-agent's returned JSON + review

The sub-agent returns strict JSON. The main Claude:

1. Parses the dimensions section (with score + per-dim confidence + reason)
2. Verifies `self_check.any_contamination_signal == false`, otherwise warns
3. Computes the composite per the rubric_notes formula (formula logic on the main side, scores come from the sub-agent)
4. **Does not modify the sub-agent's dimension scores**—the score is display only. If the user pushes back ("AB should be 3 not 4"), the main Claude records it under `User Override` but the sub-agent's original score stays on file

If the sub-agent returns `refusal != null`:
- `blocked_contaminated_input` → report that the Task prompt contains forbidden fields, have the main Claude resend
- `script_path_invalid` → check the path
- `rubric_unparseable` → tell the user rubric_notes.md is corrupted
- `non_blind_warning` → still accept the dimensions (but all confidence = medium), warn

### Step 5: compute composite + output

Compute the composite per the current formula. Console output (OUTPUT_DETAIL=full):

```
📊 [draft.md short title] — score (rubric: v2)

| Dimension | Score | Reason |
|---|---|---|
| ER (Emotional Resonance)   | 5 | "scrolling chat logs at 3 a.m." extremely concrete |
| HP (Hook Potential)        | 5 | the IS line locks the audience in one sentence |
| QL (Quotable Lines)        | 5 | the MVP line "intermittent hope" stands alone |
| NA (Narrativity)           | 3 | flat narration, weak arc |
| AB (Audience Breadth)      | 5 | crush/ex are universal |
| SR (Social Resonance)      | 2 | purely personal emotion, no social backing |
| SAT (Satire Depth)         | 4 | self-referential irony in the acknowledgments section |

Formula: (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
composite = (5×1.5 + 2×1.5 + 5×1.5 + 5 + 3 + 5 + 4) / 8.5 × 2.0 = **8.24**

📍 Lands in the 300k–1M bucket (based on the starter-rubrics bucket boundaries)

Recommended next step:
- If you've finalized the draft and are ready to publish → say "start prediction"
- If you want to revise the draft → revise and score again (repeated scoring leaves no trace)
- If you want to see historical samples with a similar composite → say "find anchors with composite 8.0–8.5"
```

When OUTPUT_DETAIL=compact, output only the scores table + composite, without the reasons column.

### Step 6: things you must **never** do

- ❌ Write any file (including predictions/, rubric_notes.md, candidates.md)
- ❌ Give a bucket probability distribution (that's cheat-predict's job)
- ❌ Trigger "published" or "retro" logic
- ❌ Propose a rubric upgrade (even if you notice a clear anomaly while scoring, only flag it in the console, don't touch the rubric)

## Key Rules

1. **Scoring goes through the sub-agent.** The main Claude no longer scores inline. See the isolation protocol in [cheat-score-blind/SKILL.md](../cheat-score-blind/SKILL.md)
2. **Integer scores.** No 4.5, 3.7
3. **Blind-first.** The sub-agent sees only the script + rubric, so it's blind by nature—that's its entire reason to exist
4. **The reason is a diagnostic tool.** Each dimension's 1–30 char reason is not decoration—at retro time it's used to find which dimension was judged wrong
5. **Writes no files.** This is the core difference between score and predict. Score is exploration, predict is commitment
6. **Doesn't compute a candidate composite.** The composite field in candidates.md is written by cheat-trends/cheat-recommend—score only serves "a concrete, already-written draft"

## Refusals

- "Score it and also predict while you're at it" → refuse. Use `/cheat-predict` instead. Reason: predict must go through the blind check + write an immutable log; score skips those
- "After scoring, write the scores into the observations section of rubric_notes.md" → refuse. The observation lifecycle requires an observation to have an "actuals vs prediction" comparison; a score alone is not an observation
- "Just tell me whether it'll go viral" → refuse. Giving a concrete composite + bucket verdict requires the predict flow; score only outputs the mechanical calculation under the current rubric
- "Skip the blind sub-agent and let the main Claude score directly" → cheat-score **does not accept** this escape hatch (unlike cheat-predict, which has `--skip-blind`). Score is a lightweight exploration with no reason to give up isolation. If the Task tool truly is unavailable → tell the user to configure it and try again

## Integration

- It's the exploration step before `cheat-predict`: the user can score different draft versions repeatedly, settle on one, then predict
- score doesn't update `.cheat-state.json`—this is a side-effect-free operation
- If the user scores the same draft ≥3 times in a row → gently prompt in the console "repeated scoring introduces decision fatigue; you can probably decide now"
