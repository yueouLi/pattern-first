# [piece title] — prediction log

> **This template is auto-filled by `/cheat-predict`.**
> All predictions use the unified format (7 components + a retro section)—the same for the first 5 pieces and the mature period, the only difference is the confidence level in the header.
>
> Full spec: see [shared-references/prediction-anatomy.md](../pattern-first/shared-references/prediction-anatomy.md).
>
> The example data in the template is from the video-analysis project's "stop expecting" ([predictions/2026-04-24_ab61ed09_stop-expecting.md]).

---

**Article ID**: `<12-char hash>`  ← e.g. ab61ed09f0a1 (sha256 of `scripts/<id>.md`'s first-written content, first 12)
**Title**: `<full title>`
**Rubric Version**: **`<v0/v1/v2/...>`**
**Prediction date**: `<YYYY-MM-DD>` (based on the final draft)
**Script Path**: `scripts/<YYYY-MM-DD>_<id>_<short>.md`
**Script Hash**: `sha256:<12-char>` (hash the script content at predict time; hash again at cheat-shoot, on a mismatch add an integrity warning in the retro section)
**Target Duration (s)**: `<state.typical_duration_seconds>`  ← e.g. 240 (3-5min)
**Actual Script Length**: `<script.md actual word count>`  ← e.g. 980 chars
**Calibration Samples (at predict time)**: `<state.calibration_samples>`  ← e.g. 3
**Confidence**: `<emoji + label>`  ← e.g. 🟡 fairly low (central ±40%, usable as one reference). Derived from calibration_samples, see state-management.md
**Scored By**: `claude` | `claude+user_override`  ← Claude self-scored; if the user challenged and changed fields at the review stage, mark `+user_override`
**User Override**: `<if any, list which fields were changed + original and new value>` | `none`
  ← e.g. `AB: claude=4 → user=3 (user thinks 'solo-company topic isn't that universal')` `central: claude=600k → user=400k`
  ← at retro time this field helps diagnose: which dimension the user's intuition systematically deviates from Claude, validated by actuals → the rubric may be missing something
**Data status at predict time**: **blind** (haven't seen any `<platform>` actual play data)

---

## Input snapshot

**Scores (vN)**: `<dim1=X / dim2=X / ...>` → composite=**`<X.XX>`**

> Example: ER5 / HP5 / QL5 / NA3 / AB5 / SR2 / SAT4 → composite=**8.24**

**User rewrite highlights vs Claude's draft** (if any):
- **Opening**: [what the user cut / added]
- **Cut**: [specific paragraph / concept name / build-up]
- **Kept**: [key punchline / acknowledgments / body structure]
- **Rhythm**: about N% [tighter / looser] than the draft

> If the user wrote from scratch without cheat-seed, write "user-original draft, no Claude-draft comparison".

---

## Prediction

> ⚠️ **This section is immutable**—`hooks/prediction-immutability.sh` intercepts Edits to this section.
> Once written, unchangeable. To redo, create `<this filename>_redo.md`, keep the original.

**Bucket**: `<X-Y>`  ← e.g. `300k-1M`

**Internal probability distribution**:
- `<50k` → X%
- `50k-300k` → X%
- **`<headline bucket>` → X%** (central ~X)
- `>1M` → X%
- `>1.5M` → X%

> Must sum to 100%.
> When confidence is low (few calibration_samples), it **should be flatter** (e.g. 30/30/20/15/5), not sharper (e.g. 5/40/45/8/2)—honestly reflecting the uncertainty.

**One-sentence reason**:
> [core driving factor + strongest counterexample constraint + central prediction]

---

## Reasoning factors

| Factor | Direction | Confidence | Note |
|---|---|---|---|
| `<dim or feature>` | strong + / medium + / weak ? / strong - | high / medium / low | [≤30-char reason] |

> Three confidence tiers: high (strong evidence + multiple anchors), medium (has a reason but few samples), low (by intuition). At retro time if a "low-confidence" factor is validated → strong intuition; a "high-confidence" factor refuted → the rubric has a bug.

---

## Anchor comparison

| Comparison sample | composite | actuals | similarities/differences |
|---|---|---|---|
| `<sample name>` | `<X.XX>` | `<Y>` | [key differing dimension] |

> **When the pool is insufficient** (< 2 samples within composite ±0.5):
> Write "the calibration pool has only N samples, no near-composite samples. **Anchor comparison N/A**—note this prediction's confidence is 🟡 fairly low / 🔴 very low, the bucket central is for reference only."
> **Don't delete this section**—telling the reader why anchors are missing is more honest than silently skipping.

---

## Counterfactual scenarios (for retro)

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

> Which bucket it actually lands in → tells you which rubric hypothesis was tested. **Can't be omitted.**

---

## Critical calibration hypothesis

[Treat this prediction as an experiment, explicitly write "if X happens, it proves Y"]

[Find a comparison sample (preferably the previous prediction)]

Two pieces with [the same composite / a near composite], difference:
- This piece: [key dimension comparison]
- Comparison: [key dimension comparison]

**I bet**: [this piece vs comparison = X times / higher by N]

If it's reversed → [what rubric hypothesis is refuted]
If the gap < N → [the rubric is basically OK / within noise]

> **When the pool has only 0-1 pieces**: write "no comparison sample—but still writing down my core bet for this one (even without an anchor):" then write 1-2 things to test this time.

---

## Retro

> ⚠️ **The section below is appended by `/cheat-retro` after T+`RETRO_WINDOW_DAYS` days.**
> The hook allows appending this section; it doesn't allow editing any character of the prediction section.

(to be filled—run `/cheat-retro <corresponding video folder>` after T+RETRO_WINDOW_DAYS days)
