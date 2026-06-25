# Scoring calibration notes

> **This file is the carrier of pattern-first's scoring-rule evolution.** After each retro comparing actual plays vs predicted scores, write the judgment basis and laws explicitly here; before scoring next time, `/cheat-score` `/cheat-predict` read this file first.
>
> **Core principle**: laws must be traceable to specific samples. Don't write empty words like "emotional resonance is important"; write "piece XX's ER=5 was validated / refuted, because the top 3 comments were all the YY pattern".
>
> Full lifecycle protocol: [shared-references/observation-lifecycle.md](../pattern-first/shared-references/observation-lifecycle.md).
> Upgrade flow: [shared-references/bump-validation-protocol.md](../pattern-first/shared-references/bump-validation-protocol.md).

---

## Rubric version log

_Only a structural change bumps the version number; pure observation accumulation doesn't. After a version bump, the samples in the calibration pool must be re-scored with the new formula. Write a structured evidence memo per upgrade (see each version section below)._

**Current version**: `v0`

**Version quick-reference**:

| Version | Effective date | Change type | Driving sample count | Driving article_ids |
|---|---|---|---|---|
| v0 | [YOUR-INIT-DATE] | initial placeholder (cold-start) | 0 (prior) | — |

**Upgrade decision principles**:
- Pure weight fine-tune (e.g. SR×1.5 → ×1.8) → don't bump, trigger a composite recompute
- Dimension-definition refinement (e.g. the SR=5 threshold gets stricter) → don't bump, but annotate the new threshold at retro
- Adding/removing a dimension, or a subversive definition rewrite → bump the major version number

**Migration trigger**: if an old-version-scored article enters the top during candidate filtering → re-read and re-score it on the spot; don't do a full re-score. **The calibration pool (with actuals) must be fully re-scored at each upgrade.**

---

## Current scoring dimensions (0-5)

> **Example: the table below is the tested v2 formula of the "video analysis" project (a Chinese opinion-video creator, 25+ published samples).
> Cold-start users should start equal-weight—see [opinion-video-zero.md](../pattern-first/starter-rubrics/opinion-video-zero.md).
> After calibrating 5 pieces, decide whether to replace this table with your own fitted version.**

| Dimension | Weight | Meaning | Typical signal |
|---|---|---|---|
| emotional_resonance (ER) | 1.5 | emotional impact | comments "tearing up / broke me / me too" |
| social_resonance (SR) | 1.5 | social-issue resonance | social-phenomenon keywords appear in comments |
| hook_potential (HP) | 1.5 | how gripping the opening is | completion rate / first-3s retention |
| quotable_lines (QL) | 1.0 | punchline density | comments quote the original text |
| narrativity (NA) | 1.0 | storytelling | share / save rate |
| audience_breadth (AB) | 1.0 | audience breadth | non-follower proportion |
| satire_depth (SAT) | 1.0 | satire / irony depth | comments "savage / sharp / on point" |

**Composite formula**:

```
composite = (ER×1.5 + SR×1.5 + HP×1.5 + QL + NA + AB + SAT) / 8.5 × 2.0
```

> The cold-start user's placeholder formula (equal-weight):
> ```
> composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
> ```

---

## Observation Log

> **Template** (append one entry per retro):
>
> ```
> ### YYYY-MM-DD [title short-name] (id) — [one-sentence qualitative, e.g. "validates ER dominance"]
> - Prediction: composite=X.XX, bucket=Y
> - Actuals: plays / likes / comments / shares (with T+Nd annotation)
> - Top comment keywords: [brief excerpt + like counts]
> - Judgment: which dimension was validated / refuted? Why?
> - Rubric adjustment: [if any, write "when scoring XX-type articles next time, change YY"]
> - See: [predictions/<file>.md]
> ```
>
> Deletion rules: see [shared-references/observation-lifecycle.md](../pattern-first/shared-references/observation-lifecycle.md): absorbed into a dimension → delete; refuted → delete. git history is the archive.

### Example entry (from the video-analysis project, for reference only; your project's real entries start accumulating after retros)

#### 2026-04-24 stop expecting (ab61ed09) — validates an emotion-oriented viral hit [T+7d data]
- Prediction: composite=8.24 (v2: ER5/HP5/QL5/NA3/AB5/SR2/SAT4), bucket=300k-1M
- Actuals: T+7d 711k (central 500k, **+42%**), share rate **2.53%**
- Top comment keywords: "she's different" / "he's different" appears 12+ times throughout (highest 2266 likes)
- Judgment: ER=5 dominance validated by strong evidence (vs the same-composite "who asked you" at 117k, a **6.07x traffic ratio**)
- Rubric adjustment: candidate for the next bump to raise ER from ×1.5 to ×2.0
- See: [predictions/2026-04-24_ab61ed09_stop-expecting.md]

> The above is an example. In cold-start, delete it and start accumulating real entries from your first retro.

---

## Major Cross-Video Observations (≥2-sample support but need more verification)

> Single-sample observations go in the "Observation Log" section first, not here. Only the same pattern at ≥2 samples is promoted here.

(none yet—auto-accumulates after you start recording)

---

## Law Accumulation Zone (high-confidence, must-read before scoring)

> Each law needs ≥2-sample support + has passed the upgrade validation flow (i.e. absorbed into a dimension or explicitly confirmed).

(none yet—will have content after 1-2 upgrades)

---

## Benchmark-derived initial signals

> Derived from [benchmark.md](benchmark.md) (if any), indicating **which dimensions look important** in the benchmark account's high/medium/low samples.
>
> **Qualitative direction only, not adopted as numeric weights directly**—fitting 5-10 samples easily overfits.
> Decide whether to adjust weights later when you formally bump after your own N≥5 calibration samples.
>
> Initially empty—filled here after `/cheat-learn-from` finishes.

(to be filled by cheat-learn-from)

---

## Hypotheses to Verify

> Single-sample observations + a strong signal but not yet reproduced are parked here.

- [ ] [example] analogy-type articles > direct-statement articles (check after the next analogy piece is published)
- [ ] [example] during festivals like Spring Festival / Qingming, family-type articles get a temporary AB +1 (no samples)

---

## Rejected-upgrade log

> Bumps that were proposed but didn't pass validation are recorded here—to avoid re-proposing the same failed plan half a year later.

(none yet)

---

## Bucket scheme (**current: ratio**)

> ⚠️ **Bucket boundaries are an attribute of the user's account, not a universal constant**—absolute-number buckets ("50k is the bottom") only hold for veterans with a follower base; for a 0-follower newcomer they make every video land in "bottom 99%" and the bucket loses ranking meaning.
>
> The tool switches among three bucket schemes by calibration stage. The currently-active scheme is decided by the `bucket_scheme` field of `.cheat-state.json`.

### Stage 1: cold-start, ratio bucket (current stage)

`bucket_scheme = "ratio"`

**Piece 1**: use the platform generic default (actual play count)

| Bucket | Range (actual plays) | Meaning | Prior probability |
|---|---|---|---|
| bottom | < 100 | nearly buried by the algorithm | 30% |
| baseline | 100 - 1,000 | a small recommendation supported by completion rate | 40% |
| hit | 1,000 - 10,000 | the signal of a first breakout | 20% |
| small breakout | 10,000 - 100,000 | an extremely rare "zero-follower first viral" | 8% |
| big breakout | > 100,000 | anomalous algorithmic over-weighting | 2% |

**From piece 2 on**: `baseline = the previous piece's actual plays` (or the median of the recent 3)

| Bucket | Multiple range | Meaning |
|---|---|---|
| regression | < 0.3 × baseline | clearly worse than the previous |
| flat | 0.3 - 1 × baseline | same tier as the previous |
| hit | 1 - 3 × baseline | moderate breakout |
| small breakout | 3 - 10 × baseline | significant breakout |
| big breakout | > 10 × baseline | magnitude jump |

See the "ratio-bucket scheme" section of [starter-rubrics/opinion-video-zero.md](../pattern-first/starter-rubrics/opinion-video-zero.md).

### Stage 2: after N=5, switch to fixed absolute buckets (with ratio backup)

`bucket_scheme = "absolute_with_ratio"`

After running 5 pieces, `/cheat-bump --bucket-only` auto-derives:
- `baseline = the median of the 5 pieces' actual plays`
- boundaries = baseline × {0.3 / 1 / 3 / 10 / 30}

`/cheat-bump --bucket-only` replaces this section's table when it lands.

### Stage 3: after N≥10, switch to percentile buckets (recommended long-term scheme)

`bucket_scheme = "percentile"`

Boundaries = the percentiles of your historical samples:
- bottom = bottom 30%
- baseline = 30-60%
- hit = 60-85%
- small breakout = 85-95%
- big breakout = top 5%

`/cheat-status` proactively suggests switching at N=10. This scheme is always self-consistent—no matter how big the account, the semantics of "top 5%" stay stable.

---

> **The reference creator's absolute buckets** (fitted on 25+ videos, **only applicable to a mature creator with a follower base**—don't copy before you're calibrated):
>
> | Bucket | Range (plays) | Prior probability |
> |---|---|---|
> | bottom | <50k | 5% |
> | baseline | 50k-300k | 35% |
> | hit | 300k-1M | 45% |
> | breakout | 1M-1.5M | 12% |
> | phenomenal | >1.5M | 3% |

---

## Default retro window

`RETRO_WINDOW_DAYS = 3`

Why 3 days: algorithmic-distribution decisions are basically done within 72 hours; waiting longer only introduces noise without adding signal.

If your platform is special—remember to write the override reason here, e.g.:
> WeChat official account RETRO_WINDOW_DAYS = 7 (published within 24h of the push, the long tail is slower)
