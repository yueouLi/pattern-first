---
name: cheat-bump
description: Propose and execute a rubric or bucket upgrade. Two modes: **full rubric bump** (the highest-risk action, 5 mandatory steps + cross-model audit) and **--bucket-only lightweight recalibration** (only swap bucket boundaries, don't touch the rubric formula). **Phase 2 mandatorily goes through the cheat-score-blind sub-agent to re-score the calibration pool**—no self-scored fallback accepted. Triggers: "upgrade rubric" / "bump rubric" / "update the formula" / "I want to add a dimension" / "adjust weights" / "recalibrate bucket".
argument-hint: --propose "<...>" | --bucket-only [--scheme ratio|absolute|percentile]
allowed-tools: Bash(*), Read, Write, Edit, Glob, Grep, Skill, Task, mcp__llm-chat__chat
---

# /cheat-bump — rubric / bucket upgrade

Two modes:

| Mode | Trigger | What it does | Validation strength |
|---|---|---|---|
| **full rubric bump** | `--propose "<new formula>"` | change the formula / dimensions / weights | 5 steps + cross-model audit (mandatory) |
| **bucket-only recalibration** | `--bucket-only` | only re-derive the bucket boundaries | data auto-derived, no audit |

A full rubric bump strictly follows the 5 steps of [shared-references/bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md). bucket-only takes the lightweight path—see Phase B below.

## Overview

```
Entry: user triggers /cheat-bump
  ↓
[Phase A0: detect call mode]
  ↓
  ├─ --bucket-only  →  [Phase B: lightweight bucket recalibration]
  └─ --propose      →  [Phase 0~6: full rubric bump]
```

## Phase A0: call-mode routing (do first)

Read the user argument:
- contains `--bucket-only` → take **Phase B** (lightweight recalibration)
- contains `--propose "<...>"` → take **Phase 0~8** (full rubric bump)
- neither → ask the user: "what do you want to do? 1) adjust the rubric formula / add or remove dimensions → --propose; 2) only re-derive the bucket boundaries → --bucket-only"

If the user says "I think ER is too low and want to adjust it" → it's the `--propose` path.
If the user says "my account grew, the buckets are off" → it's the `--bucket-only` path.
**The two paths can't be mixed**—one operation does one thing only.

---

## Full rubric bump flow

```
[user: upgrade rubric --propose "ER×1.5→2.0, cut NA, add MS"]
  ↓
[Phase 0: prerequisite-gate check]
  ↓
[Phase 1: write out the full new-formula equation]
  ↓
[Phase 2: full re-score of the calibration pool]
  ↓
[Phase 3: compute ranking consistency]
  ↓
[Phase 4: cross-model independent audit (mandatory)]
  ↓
[Phase 5: land it + cleanup pass]
  ↓
[Phase 6: append a Re-scored line to the bottom of every calibration sample's prediction file]
```

## Constants

- **READINESS_HEURISTIC** —
  - **Default reference**: calibration pool ≥ 5 samples + at least 1 cross-sample observation with ≥3-sample support
  - **But Claude can propose a bump** (even with few samples) if the observation signal is especially strong:
    - N=3 but a strong counterexample that completely refutes the current rubric hypothesis appears (a ≥3x deviation like composite 8.5 vs actual 50k)
    - 1 piece shows a single-point but extremely strong phenomenon (e.g. a single meme with ≥2000 likes in the comments)
  - **Claude can also refuse a bump** (even with enough samples) if the evidence is weak:
    - N=10 but the observations are all low-confidence scattered patterns with no clear direction
    - the user did a lot of "just glanced at it" non-serious judgment at retro time
  - **Must be stated in the prediction header or cheat-bump output**: whether this proposal is default-aligned or judgment-driven, giving the user a basis to scrutinize
- **THRESHOLD = 0.8** — the consistency threshold between the new ranking and the actuals ranking (4/5). This is **hardcoded**—the statistical rigidity of bump validation
- **CROSS_MODEL_AUDIT = true** — call an external LLM for independent audit. false only for offline
- **REQUIRE_CONFIRM = true** — require the user to explicitly say "yes, bump" before landing

## Inputs

| Required | Source |
|---|---|
| `--propose` text | user argument; if missing, ask |
| `rubric_notes.md` | user project root |
| all of `predictions/*.md` | calibration-pool data |
| `.cheat-state.json` | state |

## Workflow

### Phase 0: prerequisite-gate check

Per the "when forbidden" section of [bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md), check item by item:

| Check | Failure handling |
|---|---|
| Calibration-pool total sample count vs observation strength | **Claude judges**—per READINESS_HEURISTIC: default ≥5 samples but exceptions allowed (strong counterexample / strong meme). If the default isn't met, Claude must **explicitly state** why it still proposes the bump ("although only N=3 samples, piece X shows composite Y vs actual Z, a W-fold deviation"), for the user to scrutinize |
| New calibrations since the last bump vs observation maturity | **Claude judges**—default suggest ≥3 new samples, but if 3 consecutive pieces all point strongly in the same direction → no need to wait longer |
| `in_progress_session == null` | refuse: "you have an in-progress prediction unfinished. Finish that flow or clear state first" |
| The trigger condition holds (systematic deviation / cross-sample new observation / sufficient new-dimension evidence) | warn but don't block—ask the user why bump now |

Pass → proceed to Phase 1.

### Phase 1: write out the full new-formula equation

**You can't just accept the user's short description.** Expand it into the full equation:

```
Current: v2  composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
Proposed: v2.1  composite = (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0

Change summary:
- ER ×1.5 → ×2.0 (up)
- SR ×1.5 → ×1.0 (down)
- Add MS ×1.5 (Memetic Shareability)
- Add TS ×1.0 (Topic Shareability)
- Remove NA (overlaps with HP)
- Remove AB (replaced by TS)
- Normalization constant 8.5 → 9.0
- Total dimension count: 7 → 7 (net change 0)
```

If the user's proposal is vague (e.g. "raise ER's weight a bit") → ask for the exact number, **don't guess yourself**.

### Phase 2: full re-score of the calibration pool (**mandatorily through the blind sub-agent**)

Glob all files in `predictions/*.md` with a complete retro section → the calibration pool.

**A bump is the tool's highest-risk action—all re-scoring must go through the [cheat-score-blind](../cheat-score-blind/SKILL.md) sub-agent.** Inline re-scoring = the main Claude has already seen the actuals, and rank consistency becomes overfit rather than true signal.

#### Mandatory constraints

- **No self-scored fallback accepted**—`/cheat-predict` has a `--skip-blind` flag, but `/cheat-bump` **does not**. If the Task tool is unavailable → **abort bump**, report to the user "resolve the Task tool before bumping"
- **No "I'll just recompute composite without re-scoring dims" accepted**—even if the new formula only adjusts weights without adding dimensions, every prediction's dims must be re-judged against the script by the sub-agent. Reason: the old dim scores may themselves be contaminated; with changed weights you can't guarantee the old dims still hold

#### For each prediction:

1. Parse the prediction file to get the corresponding `scripts/<id>.md` path (from the `Script Path` header field)
2. Verify the script file exists + its hash matches the header `Script Hash`; mismatch → warn (the script was changed) but still spawn the sub-agent
3. **Spawn the cheat-score-blind sub-agent via the Task tool**:
   ```
   Spawn cheat-score-blind sub-agent.

   Input:
     script_path: <the prediction header's Script Path>
     rubric_notes_path: rubric_notes.md
     sidecar_path: .cheat-cache/bump-rescores/<prediction-id>.json

   Task: score the script against rubric_notes' current formula (now the new version vN+1).
   Return strict JSON. Write the sidecar file for the bump main flow to batch-read.

   Do not read state file / predictions/ / videos/ or any other file.
   Do not ask the user — you have no user.
   Do not read this prediction file itself — you only see the script + rubric.
   ```
4. Wait for the sub-agent to finish → read the sidecar JSON → the main flow computes composite with the new formula
5. Write the "re-score table" to `.cheat-cache/bump-rescores.json` (aggregate). **Mark each entry `blind: true`**—at bump phase 5 cleanup, write this field together with the new score onto the prediction file's `Re-scored under v<N+1>` line

#### Honest annotation of remaining contamination

Even going through the sub-agent, **two kinds of residual contamination must be honestly annotated in the bump report**:

| Type | Source | Annotation field |
|---|---|---|
| Model-prior contamination | the sub-agent is still Claude, shared RLHF | `model_prior_warning: true` (default true, can't be turned off) |
| User's own rubric-design bias | rubric_notes.md is written by the user, naturally fits their own content | `rubric_self_designed: true` (default true, can't be turned off) |

These two remind the user that channel C (cross-model audit) is indispensable. The end of the bump report must print: "the rank consistency above is consistency within channel A. **The final decision must wait for the channel C audit to pass.**"

#### Failure modes

| Symptom | Handling |
|---|---|
| A prediction's script file is gone | the sub-agent skips it, the main flow aggregate reports "N excluded due to missing script". If the remaining valid pool < MIN_SAMPLES → abort bump |
| The sub-agent returns `refusal != null` | resend the Task up to 3 times; still fails → mark that one `rescore_failed: true` and exclude it from the pool |
| The Task tool is entirely unavailable | abort bump, prompt the user "the Task tool is a hard dependency of bump. If this is truly an offline environment, run `/cheat-bump --bucket-only` for the lightweight branch" |
| The sub-agent output contains a contamination_signal | mark `suspicious: true` but don't exclude—the end of the bump report lists these suspicious entries for the user to review |

### Phase 3: compute ranking consistency

```
For each sample:
  new_composite_rank: the rank under the new formula
  actual_plays_rank: the rank by actual plays
  delta: |new_rank - actual_rank|

Output the comparison table:
| Sample | composite (v2) | composite (v2.1) | rank (new) | actual | rank (actual) | delta |
|---|---|---|---|---|---|---|
| hamster | 9.41 | 9.55 | 1 | 1.248M | 1 | 0 |
| stop-expecting | 8.24 | 9.11 | 2 | 711k | 2 | 0 |
| boss-nonsense | 7.65 | 8.11 | 4 | 396k | 3 | 1 |
| job-paradox | 8.47 | 7.56 | 5 | 168k | 4 | 1 |
| who-asked-you | 8.24 | 7.00 | 6 | 117k | 5 | 1 |

Ranking consistency: 4/5 within |delta| ≤ 1
Pairwise no-regression: all pairs the old formula got right are not flipped under the new formula ✓
```

Verdict:
- ranking consistency < THRESHOLD (default 0.8) → **local reject**, clearly report failure before Phase 4
- a pairwise regression appears → **local reject**

`THRESHOLD` is hardcoded in the protocol—no temporary lowering allowed (that itself is another meta-decision requiring a bump).

### Phase 4: cross-model independent audit (**mandatory**, unless escape hatch)

`CROSS_MODEL_AUDIT=true` (default):

Call `mcp__llm-chat__chat`:

```
prompt:
You are an independent reviewer. Below is a rubric formula a content creator is preparing to upgrade.
Independently judge two things:
1. Ranking consistency: does the new formula's ranking of the samples actually agree with the actual-performance ranking on ≥80% of samples?
2. Explanatory power: does the new formula explain the calibration pool's actuals distribution better than the old one?

Data:
Old formula: (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
New formula: (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0

Calibration pool:
[the full JSON of the Phase 2 re-score table]

Ranking comparison:
[the full JSON of the Phase 3 table]

Output format:
- Verdict: PASS or REJECT
- Reason: ≥100 chars
- Key risks: [if any, list the new formula's potential problems]
```

On receiving the external LLM's reply → parse the verdict.

Verdict logic:
- local PASS + external PASS → pass, proceed to Phase 5
- local PASS + external REJECT → **treat as REJECT**. A conflict means at least one side's reading is unstable
- local REJECT → already terminated in Phase 3
- mcp__llm-chat__chat unavailable → gracefully degrade to `CROSS_MODEL_AUDIT=false`, the state file marks `last_bump_self_audited: true`

`CROSS_MODEL_AUDIT=false`:
- rely only on the local verdict
- the state file keeps the marker, cheat-status keeps prompting the user "this bump was self-audited, suggest configuring mcp__llm-chat__chat"

### Phase 5: land it + cleanup pass

After passing the audit, **REQUIRE_CONFIRM=true** → ask the user: "the new formula PASSed local and external audit. Final confirmation: execute the bump landing? This will modify rubric_notes.md + rubric-memo.md and delete several absorbed observations. Only execute on answering 'yes, bump'."

After user confirmation:

#### 5a. Update `rubric_notes.md` (**generic language only, no video names / actuals**)

- Update the top metadata:
  - `**Current version**: vN+1`
  - `**Last bumped at**: <ISO 8601>`
  - `**Upgrade memos**: see [rubric-memo.md](rubric-memo.md)` (a pointer, don't copy the Memo content)
- Add a row to the version quick-reference table (only version number + formula signature, **without** evidence samples)
- Update the "current scoring dimensions" section (remove NA / AB, add MS / TS)
- The **derived-evidence section**, if a new dimension needs an anchor explanation → **use generic language**:
  - ✅ allowed: "Derived evidence: high-abstraction-density sample → CC=1 → low reach"
  - ❌ forbidden: "Derived evidence: 'stop-expecting' CC=1 → actual 137k" (video name + actuals number)
  - on a forbidden-pattern hit → extract that section into the "derived evidence" subsection of rubric-memo.md, replace in place with generic language

#### 5b. Write the Memo to `rubric-memo.md` (**append mode, don't overwrite history**)

Per [bump-validation-protocol.md](../../shared-references/bump-validation-protocol.md) Step 5 + the [templates/rubric-memo.template.md](../../templates/rubric-memo.template.md) format, append a Memo section to the end of the file:

- triggering observation (with the real observation ID)
- evidence data (**the calibration-pool re-score table + ranking comparison, with real video names + actuals**)
- derived evidence (**with real sample names + actuals**)
- diagnosis
- new formula
- cross-model audit conclusion citation (with model name + verdict + reason excerpt)
- known limitations

**Never** overwrite existing rubric-memo.md content—bump memos accumulate chronologically.

#### 5c. cleanup pass (per the "mandatory cleanup-pass timing" of [observation-lifecycle.md](../../shared-references/observation-lifecycle.md))

Execute within `rubric_notes.md` (**don't** touch rubric-memo.md):

- observations absorbed into a new dimension → delete (e.g. observation E absorbed into MS → delete observation E)
- observations refuted by new data → delete
- still-unresolved observations → migrate to the new version's "hypotheses to verify" section
- already-verified "laws" → move to the "law accumulation zone"

#### 5d. tidy + self-check

- Re-read the full `rubric_notes.md`, ensure a reader can understand the current rules within 60 seconds—exceeding 600 lines triggers an extra cleanup
- **Self-check leak guard**: run `grep -E '[0-9]+\s*[wWmMkK万]|plays|actual|实绩'` on `rubric_notes.md` → on a hit → **abort bump + roll back**, prompt the user "rubric_notes.md wrote forbidden content (actuals / play counts)". This content should be in rubric-memo.md, not rubric_notes.md

### Phase 6: batch-update the calibration samples

For each calibration sample's prediction file, **append at the bottom** (don't touch the prediction section, don't touch the retro section):

```markdown

---
**Re-scored under v2.1 on 2026-05-04**: composite=8.24 → 9.11 (blind: true)
(full re-computation at rubric bump time, independently scored by the cheat-score-blind sub-agent; see the v2 → v2.1 upgrade Memo in rubric-memo.md)
```

The `blind: true` field is **required**—it tells anyone reading this record in the future "this is channel B isolated scoring, not the main Claude's self-estimate". If a prediction was excluded in Phase 2 due to sub-agent failure → it won't have a Re-scored line (left as-is).

Use the Edit tool, matching the very end of each file.

### Phase 7: update the state file

```json
{
  "rubric_version": "v2.1",
  "last_bump_at": "<ISO timestamp>",
  "last_bump_self_audited": false,
  "consecutive_directional_errors": [],
  "calibration_samples_at_last_bump": <current value>
}
```

Clear `consecutive_directional_errors`—the new rubric re-counts.

### Phase 8: console report

```
✅ Rubric upgraded v2 → v2.1

Changes:
- ER ×1.5 → ×2.0
- SR ×1.5 → ×1.0
- Added MS / TS
- Removed NA / AB

Calibration-pool re-score: 5/5 passed the ranking check (4/5 consistent + 0 pairwise regressions)
Cross-model audit: ✅ PASS
Cleanup pass: deleted observations D and E (absorbed into the QL redefinition and the MS dimension)

From the next prediction on, scoring uses the v2.1 formula.
All historical prediction files have had a Re-scored marker appended.
```

---

## Phase B: bucket-only recalibration (lightweight branch)

`/cheat-bump --bucket-only [--scheme ratio|absolute|percentile]`

**The essential difference from a full bump**: bucket boundaries are not part of the rules, they're a data-derived quantity. Re-deriving them **doesn't need a cross-model audit**—the derivation algorithm is deterministic, with no "judgment" component.

### B1: choose the algorithm (auto-derived by available sample count, **scheme not stored in state**)

| Algorithm | Applies | Boundary derivation |
|---|---|---|
| `ratio` (default N=1-4) | small sample | last piece / median of recent 3 × {0.3 / 1 / 3 / 10 / 30} |
| `absolute` (default N=5-9) | medium sample | calibration-pool median × {0.3 / 1 / 3 / 10 / 30}, fixed boundaries |
| `percentile` (default N≥10) | large sample | calibration-pool actuals percentiles {30 / 60 / 85 / 95 / 100} |

The `--scheme` argument lets the user **explicitly override the default**:
- `--scheme ratio` forces ratio (even if N≥5)
- `--scheme absolute` forces absolute
- `--scheme percentile` forces percentile (requires N≥3, otherwise error)

No `--scheme` specified → auto-derive per the table above.

> The old design had a `bucket_scheme` state field—removed in v1.1. All skills derive the algorithm in real time from calibration_samples, no need to persist "which one is current". This avoids the state-inconsistency problem of "forgot to sync after switching scheme".

### B2: derive new boundaries

Read all samples in `predictions/*.md` with `actual_plays`.

**ratio mode**:
```
baseline = median(actual_plays of the recent 3)
buckets = {
  "regression":    (-inf, baseline * 0.3),
  "flat":          (baseline * 0.3, baseline * 1),
  "hit":           (baseline * 1, baseline * 3),
  "small breakout":(baseline * 3, baseline * 10),
  "big breakout":  (baseline * 10, +inf),
}
```

**absolute mode**:
```
baseline = median(all calibration-pool actual_plays)
buckets = {
  "bottom":     (-inf, baseline * 0.3),
  "baseline":   (baseline * 0.3, baseline * 1),
  "hit":        (baseline * 1, baseline * 3),
  "breakout":   (baseline * 3, baseline * 10),
  "phenomenal": (baseline * 10, +inf),
}
```

**percentile mode**:
```
sorted_plays = sorted(all calibration-pool actual_plays)
buckets = {
  "bottom":     ≤ p30,
  "baseline":   p30 - p60,
  "hit":        p60 - p85,
  "small breakout": p85 - p95,
  "big breakout":   ≥ p95,
}
```

### B3: report changes + user confirmation

```
Current bucket scheme: ratio
proposed scheme: absolute
baseline: 42k median (based on 5 calibration samples)

New boundaries:
- bottom:     < 13k
- baseline:   13k - 42k
- hit:        42k - 126k
- breakout:   126k - 420k
- phenomenal: > 420k

Derivation note:
- 5 actuals: 15k / 38k / 42k / 56k / 180k
- median 42k, new buckets derived by ×{0.3, 1, 3, 10}

Confirm to apply? (yes / no)
```

### B4: land it

After user confirmation:
1. Edit the "Bucket scheme" section of `rubric_notes.md`, replace with the new table
2. Update the `baseline_plays` field in `.cheat-state.json` (the bucket scheme is not persisted—the next cheat-predict derives it in real time)
3. Append a change-log line at the top of the bucket section of `rubric_notes.md`: `v2 buckets recalibrated on YYYY-MM-DD: scheme=absolute, baseline=42k (based on N=10 samples)`
4. **Don't** modify any prediction file—historical predictions' bucket labels stay as-is (the judgment made under the scheme at the time that sample was written)

### B5: impact on future predictions

From the next `/cheat-predict` on, derive by the new buckets. The bucket labels in historical prediction files are **not recomputed**—a bucket is a semantic judgment at prediction time, and rewriting it after the fact breaks blindness.

### What Phase B does not do

- doesn't re-score composite (the formula didn't change)
- doesn't re-audit the observations section (the rubric didn't change)
- doesn't call the cross-model audit (deterministic derivation needs no judgment)
- doesn't require a strict sample-count gate (Claude judges per READINESS_HEURISTIC; ratio mode runs at N=1)

---

## Key Rules

1. **The 5 steps can't be skipped** (full rubric bump only). Refuse any "let's just run a simplified version first" request
2. **THRESHOLD is hardcoded** (full rubric bump only). No dynamic adjustment allowed
3. **Cross-model audit is the default** (full rubric bump only). Disabling the audit requires an explicit marker in the state file
4. **The cleanup pass is part of the bump** (full rubric bump only). Bumping without cleaning the observations section is not allowed
5. **REQUIRE_CONFIRM** (both modes). Before landing, the user must explicitly say "yes, bump" or "yes, recalibrate"
6. **Bucket recalibration doesn't touch historical predictions.** A bucket is a prediction-time semantic; rewriting it after the fact breaks blindness

## Refusals

- "Skip re-scoring the calibration pool, just swap the formula" → refuse. Principle #2
- "Skip the cheat-score-blind sub-agent, the main Claude can just re-score directly" → refuse. bump **does not accept** any self-scored fallback—sub-agent unavailable → abort bump, no "self-audit"
- "Skip the external LLM audit" → only when `CROSS_MODEL_AUDIT=false` is explicitly set
- "Set THRESHOLD to 3/5 this time so it passes" → refuse. Changing THRESHOLD is a meta-level bump
- "Keep all old observations as history" → violates principle #3
- "Bump first, do cleanup next time" → refuse. Cleanup is part of the bump
- "Only recompute composite without re-scoring dims" → refuse. New weights × old dims is still old contamination. Every dim is re-judged against the script by the sub-agent
- "Write the full Memo into the top of rubric_notes.md so it's easy for me to read" → refuse. rubric_notes.md is on the blind sub-agent's whitelist—containing video names / actuals → leaks through the whitelist. The Memo goes in rubric-memo.md (**outside** the whitelist); rubric_notes.md only holds the formula + generic-language dimension definitions + the pointer
- "Keep real video names in the derived-evidence section so the rubric reads more concretely" → refuse. In rubric_notes.md you must use generic language ("high-abstraction-density sample"); derived evidence with video names goes in rubric-memo.md

## Integration

- Upstream: `/cheat-retro` detects ≥3 same-direction deviations → proposes running `/cheat-bump`
- Dependencies: `mcp__llm-chat__chat` (if configured) + the Task tool (to spawn cheat-score-blind)
- Modifies:
  - `rubric_notes.md` (structural update, **never** writes real video names / actuals)
  - `rubric-memo.md` (**new**—append the full Memo, with evidence + derived evidence)
  - all `predictions/*.md` (append a Re-scored line, don't touch the prediction section)
  - `.cheat-state.json`
- Downstream: the next `/cheat-predict` automatically scores by the new rubric_version
