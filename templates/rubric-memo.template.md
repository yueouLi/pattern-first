# Rubric Memo — bump upgrade archive

> ⚠️ **This file is a Channel A internal reference. Channel B (the cheat-score-blind sub-agent) **never reads** this file**—the blind sub-agent's hard refusal list explicitly includes this file's path.
>
> This accumulates the full Memo of every rubric bump: triggering observations, evidence data tables (with real sample names + actuals), diagnosis, cross-model audit conclusions, known limitations.

---

## What this file is for

When cheat-bump Phase 5 lands, it writes the upgrade Memo **here**, **not** into `rubric_notes.md`.

Historically cheat-bump wrote the full Memo (with video names + actuals + derived evidence) into `rubric_notes.md`. But `rubric_notes.md` is the blind sub-agent's whitelist file—the sub-agent leaked actuals data through it, and the blind scoring that should have been isolated became "post-hoc explanation having seen the actuals".

The fix:

| File | Content | blind whitelist |
|---|---|---|
| `rubric_notes.md` | formula / dimension definitions (**generic language**, no video names / actuals) / Bucket section / top metadata | ✅ YES |
| `rubric-memo.md` (this file) | the full upgrade Memo (**with** real video names + real play counts + derived evidence) | ❌ NO (hard-forbidden to read) |

---

## Write rules (cheat-bump Phase 5)

- **Append mode**: a new bump's Memo is **appended to the end of the file**, old Memos untouched. Reading in reverse-chronological order shows the full rubric evolution
- **Each Memo section must contain 6 components** (per the [bump-validation-protocol.md](../shared-references/bump-validation-protocol.md) Step 5 template):
  1. Triggering observation (which observations accumulated to ≥3 same-direction deviations)
  2. Evidence data (the calibration-pool re-score table + ranking comparison—**with real video names + actuals**)
  3. Diagnosis (which rubric hypothesis was refuted)
  4. New formula (the changed weights / dimensions)
  5. Cross-model audit conclusion citation (channel C verdict + reason excerpt)
  6. Known limitations (what this bump didn't solve)

- The **derived-evidence section** is also written **here**: a named anchor like "Derived evidence: 'video X' CC=1 → actual 137k" is **absolutely not allowed** in `rubric_notes.md`, all accumulated into this file

---

## Who reads this file

| Skill | Read? | What for |
|---|---|---|
| `cheat-bump` Phase 5 | ✅ write | append a new Memo |
| `cheat-retro` | ✅ read | look back at historical Memos at retro time to find the rubric evolution trajectory |
| `cheat-status` | ✅ read | show "what evidence the last bump used" on the dashboard |
| **`cheat-score-blind`** | ❌ **hard-forbidden** | refusal_code: `blocked_rubric_memo` |
| `cheat-score` / `cheat-predict` main-Claude self-estimate part | doesn't read proactively | the main conversation is already contaminated; reading the Memo again is just redundant |

---

## Memo section format (cheat-bump writes in this format)

Append one section per bump, format:

```markdown
---

## v<N> → v<N+1> Memo (bumped at <ISO 8601>)

### Triggering observation
(List the ≥3 same-direction-deviation observation IDs accumulated to this bump + a one-sentence summary. Cite rubric_notes.md observation IDs)

### Evidence data
**Calibration-pool re-score table**:

| Sample | composite (vN) | composite (vN+1) | rank (vN+1) | actual | rank (actual) | delta |
|---|---|---|---|---|---|---|
| "real video name 1" | 9.41 | 9.55 | 1 | 1.248M | 1 | 0 |
| "real video name 2" | 8.24 | 9.11 | 2 | 711k | 2 | 0 |
| ... | ... | ... | ... | ... | ... | ... |

**Derived evidence** (if any):
- "video name X" CC=1 → actual Y validates the "high-abstraction-density → low reach" hypothesis
- ...

### Diagnosis
(Which hypothesis of rubric vN was refuted by data; why vN+1's formula explains the deviation)

### New formula
Old: `(ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0`
New: `(ER×2.0 + HP×1.5 + MS×1.5 + QL + SR + TS + SAT) / 9.0 × 2.0`

Changes: remove NA / AB; add MS / TS; ER weight 1.5 → 2.0

### Cross-model audit (channel C)
- Audit model: qwen-max-2025-XX
- Verdict: PASS
- Reason excerpt: "..."
- Key risk: "..."

### Known limitations
(What this bump didn't solve; directions still to watch at the next bump)

```

---

## Example: v0 → v1 (first bump)

(When cheat-init creates this file it's empty; the first Memo section is appended here at the first bump)

<!-- subsequent bumps append here -->
