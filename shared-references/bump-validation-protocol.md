# Rubric Bump Validation Protocol

Referenced by these sub-skills: `cheat-bump`, the main SKILL.md.

This is the full spec of project principle #2—**bump = full re-score**. Any structural change to the rubric must go through this entire protocol.

---

## Definition of "upgrade"

Any of the following changes triggers the full bump flow:

- Formula coefficient change (ER×1.5 → ×2.0)
- Dimension addition/removal (remove NA, add MS)
- A subversive rewrite of a dimension definition ("QL=number of punchlines" → "QL=reusable sentence patterns")
- Normalization-constant change (divisor from 8.5 → 9.0)

The following changes **don't** trigger a bump, but are annotated in `rubric_notes.md`:
- A marginal refinement of a dimension definition (the QL=5 threshold refined from "≥3 sentences" to "≥3 sentences distributed across different sections")
- A note that a single dimension's threshold got stricter (doesn't change the formula, only the judgment habit when scoring)
- An anchor-sample update (use a new sample as the 5-point benchmark)

---

## When you **can** propose an upgrade (**Claude-judgment-led; below are reference trigger scenarios**)

Any one being true allows a proposal—but **ultimately Claude judges the observation's maturity + signal strength**; below is only a default heuristic:

1. A cross-sample observation shows a **clear support pattern traceable to a specific data point** (default reference ≥3 samples, but Claude can propose based on 1-2 **especially strong** samples—e.g. an anomalous signal like a 6x traffic ratio / a single meme with ≥2000 likes)
2. The current rubric is **systematically biased in the same direction** in recent retros (default reference ≥3 same-direction, but Claude can propose based on 1-2 **extreme deviations**—e.g. a 10x deviation like central 500k vs actual 50k)
3. A candidate dimension shows independent predictive power (reference sample count: ≥3 is stable, but 1-2 strong evidences count too)
4. The calibration pool crosses a watershed (5 / 10 / 20 / 50) triggering a routine review

**When Claude proposes a bump it must explicitly mark**: whether this proposal is default-aligned (meets the routine threshold above) or judgment-driven (based on a strong signal but few samples). Give the user a basis to scrutinize.

---

## When proposing an upgrade is **forbidden**

The following are **hard constraints**—Claude can't break them:

- Currently in an in-progress prediction (state file `in_progress_session != null`)—flow discipline
- No new calibration sample since the last bump—at least 1 new sample is required before bumping again (to avoid circularly validating yourself)

The following are **soft suggestions**—Claude should usually avoid them, but can break with a strong reason and an explicit annotation:

- Generally don't bump when the calibration pool < 5 samples (unless a strong counterexample appears)
- Generally don't bump when < 3 new calibration samples since the last bump (unless the new samples contain a strong counterexample)

**When Claude softly violates, it must:**
1. Explicitly state in the proposal "I know the default suggestion is to wait for N≥5 / wait for ≥3 new samples, but the reason this time is [X strong signal]"
2. Still go through the full 5-step validation flow (including the cross-model audit)
3. If the cross-model audit REJECTs → the bump is rejected, **no "I feel the signal is strong" bypass allowed**

---

## Full upgrade flow (5 mandatory steps, no skipping)

### Step 1: write out the new formula's full equation

You can't just say "raise ER's weight"; you must write the entire equation in full, all coefficients and the normalization constant.

Example (compliant):
```
v2.0  composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
v2.1  composite = (ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0
```

Example (non-compliant):
- "Raise ER's weight to 2.0" ← didn't say whether other weights change
- "Add the MS dimension" ← didn't say the weight and normalization constant

### Step 2: full re-score on the calibration pool, **locally**

Calibration pool definition: all files in `predictions/*.md` with a complete retro section (containing `actual_*` data).

Recompute composite for each with the new formula. **Don't re-score the individual dimension scores**—the dimension scores stay (v2's ER=5 is also ER=5 in v2.1), only recompute the composite.

Exception: if the new formula adds a dimension (e.g. adds MS), then for each old sample you must **back-fill the MS score**. This step makes the upgrade cost rise linearly with sample count, an intentional "upgrade damping".

### Step 3: compute ranking consistency

The new composite ranking vs each sample's actuals bucket ranking must satisfy:
- consistent on ≥`THRESHOLD` proportion of samples (default 4/5 = 80%)
- can't flip the order of any pair the old formula got right (pairwise no-regression)

The ranking-consistency algorithm:
1. Rank all calibration samples by the new composite
2. Rank all samples by actual_plays
3. Compute the Spearman rank correlation; also check whether the relative order of each pair (i, j) is flipped
4. Output the comparison table: each sample's [new rank, actual rank, delta]

### Step 4: cross-model independent audit (**mandatory**, unless escape hatch)

When `CROSS_MODEL_AUDIT=true` (default):
1. Call `mcp__llm-chat__chat`, packaging the following to the external LLM:
   - the old formula + the new formula
   - for all calibration-pool samples: dimension scores, composite (new + old), actual_plays, actual_likes, actual_comments, actual_shares
   - the Step 3 ranking-comparison table
2. The external LLM independently judges two things:
   - is the ranking consistency really ≥ THRESHOLD?
   - does the new formula have stronger explanatory power than the old one?
3. The external LLM must output **PASS** / **REJECT** + a ≥100-char reason
4. Only when **both** the local verdict and the external verdict pass can you proceed to Step 5

`CROSS_MODEL_AUDIT=false`: skip the external audit—**only for offline/no-network use**. The state file marks `last_bump_self_audited: true`, and `cheat-status` keeps prompting the user to configure the external audit.

### Step 5: post-upgrade settlement (cleanup pass)

Landing a bump must be done all at once:

1. Update `**Current version**` at the top of `rubric_notes.md` and add a row to the **version quick-reference table**
2. Write the full memo in the "vN → vN+1 upgrade Memo" section (triggering observation + evidence data + diagnosis + new formula + known limitations)
3. Delete all "observation log" entries that drove this upgrade and were absorbed into a formal dimension
4. Delete "observation log" entries refuted during the upgrade
5. Still-unresolved "observation log" entries → move to the new version's "hypotheses to verify" section (kept)
6. Append a line at the **bottom** of every calibration sample's prediction file: `**Re-scored under <new-version> on YYYY-MM-DD**: composite=X.XX → Y.YY` (don't touch the prediction section, don't touch the retro section, only append this line)

Settlement is not optional. rubric_notes.md is a workbench, not a museum—see `observation-lifecycle.md`.

> Note: per the file-split isolation (schema 1.4), the full Memo with real video names + actuals (step 2's "memo") goes into `rubric-memo.md`, while `rubric_notes.md` keeps only generic language. See cheat-bump Phase 5.

---

## Handling after a bump is rejected

Any step failing → the bump is rejected; handle per the following:

| Failure location | Handling |
|---|---|
| Step 3 local ranking inconsistent | The candidate formula returns to the "to verify" zone. **Not allowed** to silently loosen THRESHOLD (e.g. from 4/5 to 3/5)—that's honest self-deception. THRESHOLD is a protocol rigidity, different from the sample-count threshold of "when you can propose a bump" (the latter can be softly violated) |
| Step 4 external audit REJECT | Record the external LLM's reason in full in the "rejected-upgrade log" section of `rubric_notes.md` |
| Step 4 external audit conflicts with the local verdict (one PASS one REJECT) | Treat as REJECT. A conflict means at least one side's reading of the data is unstable, shouldn't upgrade |
| Step 5 settlement can't be completed (e.g. an observation can neither be deleted nor kept) | The bump rolls back to step 0. Note: this means the new formula still has an uncaptured "unresolved observation", the plan is immature |

---

## Upgrade damping (why this protocol is intentionally hard)

Each additional sample in the calibration pool raises the bump cost linearly:
- Pool of 3-5 → near-zero cost
- Pool of 20-30 → noticeable cost
- Pool of 50+ → painful

This is **intentional design**. Frequent bumps = the rubric chasing noise. A stable rubric's signature is: **bumps get rarer, bumps get bigger**—a single bump explains multiple accumulated observations, rather than one-observation-one-upgrade.

Reference the video-analysis project: v1 → v2 took about 4 weeks (from first publish to the first bump), and v2 → v2.1 has been a candidate for 4 weeks still not promoted (waiting for 6-sample joint validation). This is a healthy cadence.

---

## Anti-patterns (requests that must be refused)

- "Skip re-scoring the calibration pool, just swap the formula" → refuse. Step 2 can't be skipped
- "The external LLM audit is too much hassle, skip it" → only allowed when `CROSS_MODEL_AUDIT=false` is explicitly set
- "I'm only adjusting one weight this time, that's not an upgrade right" → any coefficient change counts. Step 1 must write the full equation
- "It's just for my own use, no need for the whole flow" → refuse. The value of this flow is when you **look back in the future**—you'll later want to ask "why wasn't v2.3 adopted", and there must be a complete memo
- "Can you change THRESHOLD from 4/5 to 3/5 so this passes" → refuse. Changing THRESHOLD is itself a meta-level bump, requiring its own process
