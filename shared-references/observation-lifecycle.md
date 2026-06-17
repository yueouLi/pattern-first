# Observation Lifecycle Protocol

Referenced by these sub-skills: `cheat-retro`, `cheat-bump`, the main SKILL.md.

This is the full spec of project principle #3—**the rubric is a workbench, not a museum**. Any addition or deletion of observation entries in `rubric_notes.md` must follow this protocol.

---

## Three life stages

Every observation is in one of these states:

```
[new]  →  [Observation Log]  →  [Cross-Video Observation]  →  [Law Accumulation] / [absorbed into a dimension] / [refuted]
                                              ↘
                                               [Hypotheses to Verify] (parked)
```

| Stage | Location in rubric_notes.md | Trigger |
|---|---|---|
| **Observation Log** | the `## Observation Log` section | written after a single retro. One entry per video retro |
| **Cross-Video Observation** | the `## Major Cross-Video Observations` section | the same pattern appears in ≥2 samples |
| **Law Accumulation** | the `## Law Accumulation Zone (high-confidence)` section | already has ≥2-sample support and **passed the upgrade validation flow** (i.e. absorbed into a dimension or explicitly confirmed) |
| **Hypotheses to Verify** | the `## Hypotheses to Verify` section | a single-sample observation parked, awaiting more samples |

---

## Thresholds for promoting to the next stage (**Claude-judgment-led; below are reference defaults**)

| From → To | Default reference threshold | Claude judges signal strength (can softly violate) |
|---|---|---|
| Observation Log → Cross-Video Observation | same pattern ≥2 samples | 1 sample + strong meme evidence of ≥2000 likes in comments can also promote |
| Cross-Video Observation → Hypotheses to Verify | single sample + strong signal but not yet reproduced | — |
| Cross-Video Observation → Law Accumulation | ≥2 samples + no formula change needed | 1 sample + a strong counterexample (≥3x deviation) can also promote (mark `**Single-sample, high-confidence**`) |
| Cross-Video Observation → dimension (no longer exists separately) | ≥3 samples + absorbed via the bump flow | same as cheat-bump's READINESS_HEURISTIC |
| any → delete | refuted by new data / absorbed into a dimension / accumulated as a law | `cheat-bump` cleanup pass, or a standalone operation |

**Core principle**: sample count is a **proxy indicator of signal strength**, not the signal itself. 3 clear samples traceable to specific data points > 10 scattered, low-confidence samples.

**Discipline on Claude's soft violations**:
- Annotate `**Promoted with N samples (default expects M)**: <why it still holds>`, for the user to scrutinize
- Don't soft-violate in a chain—if Claude has soft-violated 2+ times in the last 3 promotions, cheat-status prompts "your observation-promotion judgment may be too aggressive, suggest reviewing back to the default threshold"

### Sample size → allowed actions (refined grading)

What changes you can make is decided by the **total sample count** of the calibration pool—a crude big move needs more evidence:

| Calibration pool size | Allowed actions | Note |
|---|---|---|
| **1** | record a "single observation" | a single point can't trigger any rule change, only serve as a seed |
| **2-4** | distill a "candidate law" + promote to the "Cross-Video Observation" section | still can't change the formula |
| **5-9** | revise a dimension definition (**qualitative change**—e.g. state the SR=5 threshold more strictly) | don't touch weight numbers, only change the judgment habit. **The first formal bump is also in this tier** (the rubric shape first takes form) |
| **10-19** | fine-tune weights ±0.2 (**quantitative change**) | e.g. ER ×1.5 → ×1.7; adding / removing a dimension is still a "qualitative big move" needing more samples |
| **20+** | reverse-derive weights via regression (**data-driven**) | Spearman correlation, etc., usable as a bump basis |

**Key discipline**:
- Don't use regression at N=5—fitting a 7-dim formula to 5 points will definitely overfit
- Don't still adjust weights by intuition at N=20—you already have a data signal
- The bump protocol's (`bump-validation-protocol.md`) `MIN_SAMPLES_FOR_BUMP=5` is the minimum threshold for **the shape first taking form**, not the threshold for "starting data-driven"—the latter requires N≥20

---

## Deletion rules (the easiest part to get wrong)

**Two kinds of entries must be deleted, can't be kept**:

### Type A: observations absorbed into a dimension

Example: at the v2.1 upgrade, "observation E (the second-creation volume of the acknowledgments section is the strongest external evidence of ER=5)" was absorbed into the new dimension **MS (Memetic Shareability)**.

→ After the upgrade lands, **delete** the "observation E" log entry. The dimension MS itself is the new home.

**Reason**: keeping the observation = the same concept appears twice in the file (once as a dimension, once as an observation). The reader gets confused: is this history or a still-active rule?

### Type B: observations refuted by new data

Example: observation X proposed "long videos have a low ceiling", later 4 long-video samples all broke 500k → refuted.

→ **Delete** this observation.

**Reason**: keeping it = letting the future you or another reader score by a wrong rule.

---

## Entries that must be kept

The following entries are **not deleted**, kept in place or migrated to the appropriate section:

- **Unresolved observations** (neither absorbed nor refuted) → migrate to the new version's "Hypotheses to Verify" section across upgrades
- **Historical calibration events** (e.g. "the v1 → v2 upgrade was because the housing-price piece's 2.59M was severely underestimated") → kept in the "upgrade Memo" section of the version log, **not** kept in the observation section
- **Laws still in effect in this version** (already accumulated into the "Law Accumulation Zone") → kept

---

## Disallowed anti-patterns (**must refuse**)

The following are all "museum impulses"—treating rubric_notes.md as a historical archive:

| Anti-pattern | Why not |
|---|---|
| `~~ER weight 1.5~~` `**changed to 2.0**` (old value with strikethrough) | use git history to see the old value, don't pile it in the file |
| "I used to think SR was important, but actually..." | such archaeological entries leave the reader not knowing what the current rule is |
| "NA was key in the v1 era, after v2 found it wasn't" | same as above. Delete the NA-related entries, keep a version memo explaining why NA was cut |
| "Keep this observation as a counterexample" | the place for a counterexample is the "refuted hypotheses" subsection of the version memo, not the observation section |
| "Delete it at the next bump, leave it for now" | refuse. Delete it cleanly in the same operation that lands the bump |

git history is the real archive. `rubric_notes.md` is a snapshot of the currently-active rules—opening it, the reader should see **how to score today**, not the evolution history of the past few months.

---

## Blind channel leak guard (**any skill writing rubric_notes.md must follow**)

`rubric_notes.md` is the **whitelist** of the cheat-score-blind sub-agent (channel B)—when the sub-agent reads this file to score a script, the file content can't contain **the actuals of published pieces**, otherwise the sub-agent's "blindness" is broken.

**Patterns forbidden from being written into rubric_notes.md**:

| Pattern | Example | Replacement location |
|---|---|---|
| Real video title + actuals | "'stop-expecting' plays 711k" | rubric-memo.md |
| Derived evidence with a named anchor | "Derived evidence: 'she's different' MS=5 → actual 1.248M" | rubric-memo.md |
| Calibration-pool re-score table | the sample comparison table at bump time | rubric-memo.md |
| Cross-model audit citation with numbers | "audit: 'boss nonsense' rank consistent ✓" | rubric-memo.md |
| Numbers containing `\d+w` / `\d+万` / `\d+M` / `\d+k` (**except bucket boundaries**) | "actual 137k" | rubric-memo.md |

**Allowed patterns** (generic language):

- Formula: `(ER×2.0 + HP×1.5 + ...) / N × M`
- Dimension definition: `ER (Emotional Resonance): 0=no emotion / 3=medium resonance / 5=extreme resonance`
- Derived evidence **abstracted**: `Derived evidence: high-abstraction-density sample → CC=1 → low reach`
- Bucket boundaries (numbers belong to the rule, not actuals): `50k-300k / 300k-1M / 1M-1.5M / >1.5M`
- Observation ID + one sentence: `Observation E: opening 5 sec contains a question → ER+` (no sample name / no actuals)

**Mandatory self-check at the end of cheat-bump Phase 5**: after writing rubric_notes.md, run `grep -E '[0-9]+\s*[wWmMkK万]|plays|actual|实绩'` → on a hit → abort + roll back. This is a hard constraint.

Historical background: when PR #11 introduced cheat-score-blind it missed this—cheat-bump wrote the Memo into rubric_notes.md, and the sub-agent read the actuals through the whitelist. PR #12 fixed it (split files) + added this section's constraint to prevent recurrence.

---

## Mandatory timing of the cleanup pass

`cleanup pass` = clearing out all observations meeting the "deletable" condition at once.

Mandatory triggers:
- **The last step of landing a bump** (see `bump-validation-protocol.md` Step 5)
- The user explicitly triggers a "settlement" operation (rare)

Not mandatory but suggested:
- Every 5 samples added to the calibration pool, proactively review the "Observation Log" section to see which can be promoted / deleted
- When the `cheat-status` dashboard detects `rubric_notes.md` exceeding 500 lines, suggest a settlement

---

## Line budget

The reference (target) size of a healthy `rubric_notes.md`:

| Calibration pool size | Healthy lines | Alert lines |
|---|---|---|
| 0-5 pieces | 100-200 | >300 |
| 5-20 pieces | 200-400 | >500 |
| 20-50 pieces | 300-500 | >700 |
| 50+ pieces | 400-600 | >800 |

Lines over the alert → must run a cleanup pass. This isn't for looks, it's so the **reader can read the core rules within 60 seconds before scoring**.

---

## Alignment with the "Observation Log" template

The standard template for each observation-log entry (`rubric_notes.template.md` uses this too):

```markdown
### YYYY-MM-DD [title short-name] (id) — [one-sentence qualitative, e.g. "validates ER dominance"]
- Prediction: composite=X.XX, bucket=Y
- Actuals: plays / likes / comments / shares (with T+Nd annotation)
- Top comment keywords: [brief excerpt + like counts]
- Judgment: which dimension was validated / refuted? Why?
- Rubric adjustment: [if any, write "when scoring XX-type articles next time, change YY"]
- See: [predictions/<file>.md]
```

The template for a cross-video observation:

```markdown
### Observation X — [one-sentence law]
**Evidence**:
- Sample 1 (composite, actuals): core data
- Sample 2 (composite, actuals): core data
- Sample 3 (composite, actuals): core data

**Hypothesis**: [if the law holds, what rubric adjustment it implies]

Sample count: N, [exceeded / to be filled].
```

---

## Interface with the bump protocol

`cheat-bump` at Step 5 (cleanup pass) must process the observation sections in this order:

1. List all `## Observation Log` section entries
2. Ask 3 questions about each:
   - Was it absorbed into a formal dimension by this bump? → delete
   - Was it refuted by this bump's new data? → delete
   - Is it still unresolved? → migrate to the "Hypotheses to Verify" section
3. List all `## Major Cross-Video Observations` section entries
4. Ask the same 3 questions about each
5. Migrate laws that are "validated but don't need a formula change" → to the "Law Accumulation Zone"
6. Finally **re-read** the full `rubric_notes.md`, ensuring a reader can understand the current scoring rules within 60 seconds of opening it
