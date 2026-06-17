# Starter Rubric: opinion-style video — v0 cold-start placeholder

**This is the placeholder rubric for a new creator with no data at all.** It will be wrong. **The first 5 predictions are at roughly ±50% precision—a mathematical fact of cold-start, not a rubric failure.**

After running 5 pieces (each completing the `/cheat-predict` → publish → `/cheat-retro` loop), you'll have your first personal calibration data and can propose the first `/cheat-bump` upgrade to v1 (or adopt the v2 of [opinion-video.md](opinion-video.md) as a starting point and recalibrate the weights).

---

## v0 composite formula (**equal-weight placeholder**)

```
composite = (ER + HP + QL + NA + AB + SR + SAT) / 7 × 2.0
```

Each dimension is a 0-5 integer. The composite ranges 0-10.

**Why equal-weight instead of v2's differentiated weights**:
- You have **no data** to support any specific weight
- Starting with v2's weights would make you think those weights are universal—they aren't, they're fitted to the reference creator's account
- Equal weighting lets you give "neutral attention" to each dimension before the data comes out
- After the 5th piece, your retro data tells you which dimensions actually predicted propagation for your account

---

## The 7 dimensions

### ER — Emotional Resonance
*Can the script produce a **specific, nameable** emotion in the first 30 seconds?*

- **0** — pure information transfer; no emotional hook
- **3** — general resonance
- **5** — sharp, specific, self-recognition one is somewhat unwilling to admit

### HP — Hook Potential
*Can the first 3 seconds force the viewer to watch for 30 seconds?*

- **0** — generic opening ("hi everyone...")
- **3** — a concrete promise or counterintuitive assertion
- **5** — a concrete, vivid scene the viewer can't stop processing

### QL — Quotable Lines
*Are there at least 2-3 lines that can be screenshotted and spread as standalone text?*

- **0** — all narration
- **3** — one memorable line at the end
- **5** — multiple standalone-usable lines, distributed across different parts of the script

### NA — Narrativity
*Is there a recognizable arc, or flat narration?*

- **0** — list-style
- **3** — a loose main thread
- **5** — a tight three-act structure

### AB — Audience Breadth
*How broad is the potential audience for this issue?*

- **0** — extremely niche
- **3** — medium
- **5** — universal

### SR — Social Resonance
*Does the script touch a current social pattern?*

- **0** — purely personal / interpersonal
- **3** — touches a recognized phenomenon but with no new angle
- **5** — names a structural pattern the audience recognizes but has no language for

### SAT — Satire Depth
*Does the script use multi-layer irony / parody format?*

- **0** — sincere and direct
- **3** — one layer of irony
- **5** — nested or self-referential irony

If your channel takes the sincere route, give SAT a 3 as a placeholder.

---

## Bucket prediction: unified format at all stages + progressive confidence annotation

> Poor early prediction precision is a mathematical fact—**not solved by omitting the bucket**, but by **the header's confidence level + a flatter probability distribution** to honestly express uncertainty. See [shared-references/prediction-anatomy.md](../shared-references/prediction-anatomy.md) and the [confidence table in state-management.md](../shared-references/state-management.md).
>
> When calibration_samples is few, the probability distribution **should be flatter** (e.g. 30/30/20/15/5 rather than 5/40/45/8/2)—**this is the way to honestly express uncertainty**, not to skip the bucket.

## Ratio-bucket scheme (applies at all stages)

> ⚠️ **A new creator's bucket can't use absolute numbers**—the reference creator's "50k is the bottom" is a "phenomenal viral hit" for a 0-follower newcomer.
> If you copy absolute-number buckets, every video lands in "bottom 99%", and the bucket loses any ranking meaning.
>
> The **ratio bucket** uses "the multiple relative to your own previous piece" to bucket. Always applicable, no matter how big your account.

### Piece 1: use the platform generic default (you don't have a "previous piece" yet)

Typical distribution for a 0-follower newcomer's 1st video on Douyin / Bilibili / TikTok / YouTube:

| Bucket | Range (**actual play count**) | Meaning | Prior probability |
|---|---|---|---|
| bottom | < 100 | nearly buried by the algorithm | 30% |
| baseline | 100 - 1,000 | a small recommendation supported by completion rate | 40% |
| hit | 1,000 - 10,000 | the signal of a first breakout | 20% |
| small breakout | 10,000 - 100,000 | an extremely rare "zero-follower first viral" | 8% |
| big breakout | > 100,000 | anomalous algorithmic over-weighting | 2% |

> For WeChat official account / Substack, replace "plays" with "reads", similar magnitude (50-500 reads for a 0-follower account's first post is the norm).

**When predicting piece 1**: choose a bucket + write a probability distribution. **It will very likely land in "baseline"**—a mathematical fact, not your failure.

### From piece 2 on: use the ratio bucket

Let `baseline = the actual plays of the previous piece` (or the median of the recent 3, if available).

| Bucket | Multiple range | Meaning |
|---|---|---|
| regression | < 0.3 × baseline | clearly worse than the previous |
| flat | 0.3 - 1 × baseline | same tier as the previous |
| hit | 1 - 3 × baseline | moderate breakout |
| small breakout | 3 - 10 × baseline | significant breakout |
| big breakout | > 10 × baseline | magnitude jump |

**Benefits of the ratio bucket**:
- 100 → 1000 plays (10x) and 50k → 500k plays (10x) **are the same kind of achievement**—the ratio bucket marks both "big breakout"
- As your account grows from 0 to 100k followers, the bucket boundaries auto-rise
- No need for "should I over-praise this number today"—the multiple is absolute

**Example**:
- Piece 1: 480 plays (lands "baseline") → baseline = 480
- Piece 2 predicted bucket = "hit" (500-1500), actual 1200 → hit
- Piece 3 baseline rolling update = (480 + 1200) / 2 = 840

### After piece 5: suggest fixing absolute buckets + ratio buckets coexisting

After running 5 pieces, your baseline is stable from 5 data points. `/cheat-status` proactively prompts:

> You've calibrated 5 pieces, you can fix absolute bucket boundaries based on the actual distribution.
> Run `/cheat-bump --bucket-only` to auto-derive.

After fixing, absolute buckets are for "long-term trend identification" (is this better than last month's?), ratio buckets for "recent fluctuation" (is this better than the previous?).

### After N≥10: can switch to percentile buckets

When the calibration pool ≥ 10, switch bucket boundaries to percentiles: your top 20% of videos are "viral hits", 10-20% is "hit", 30-70% is "baseline". This scheme is always self-consistent—no matter how big the account, the semantics of "top 20%" stay stable.

---

**Important warning**:
- The placeholder probabilities above are "the prior when you know nothing"—your real distribution emerges after the 5th piece
- In pieces 1-5, your judgment of your own bucket boundaries **will fluctuate greatly**—this is the normal cold-start state
- After the 5th piece you **must** run `/cheat-bump --bucket-only` to recalibrate

---

## Cold-start strategy (**must read, the most overlooked section**)

A cold-start "prediction" isn't a prediction—it's **data collection**. Understanding this is the watershed for whether the tool is useful to you.

### What your predictions do in the first 5 pieces, three things

1. **Build discipline**: write a blind judgment before seeing any data. This is the spine—not the number itself
2. **Record 7-dim scores**: after the retro each sample becomes a (score, actuals) pair; at piece 5 these pairs are the input for the rubric's first upgrade
3. **Record anchor hypotheses**: write hypotheses like "I bet ER=5 gets more traffic than ER=3"; retro validation → evidence for a rubric upgrade

**What you shouldn't do**: decide whether to publish a draft based on the cold-start composite. **±50% precision—the decision is meaningless.** For ones already decided to publish, run the full loop; for ones you're hesitating on, go by your own feeling.

### Sampling strategy for the first 5: **actively choose the most diverse drafts**

If your first 5 are all the same `ER=5 / SR=2 / HP=5` template, at retro time **you can't** tell which dimension actually predicted traffic—multicollinearity.

**Counterintuitive but correct**: in cold-start, actively choose samples with the most diverse dimension combinations:
- 1 piece ER-dominant (emotion-oriented, low SR)
- 1 piece SR-dominant (social-issue-oriented, low ER)
- 1 piece SAT-dominant (satirical)
- 1 piece QL-dominant (punchline-dense)
- 1 piece all-medium (all 3-4)

If you only have "safe same-template drafts", pick the most diverse 5. **Chase "all viral hits" in the stable period; in cold-start chase "maximum information".**

### When to start trusting predictions

| Calibration samples | What you can trust |
|---|---|
| N=0-2 | Trust nothing. The bucket is a placeholder |
| N=3-5 | Trust the "which dimension may matter" direction; not the specific composite number |
| N=5-10 | Trust the bucket ranking; not the central point estimate |
| N=10-20 | The central is trustworthy ±30%; usable as one decision reference |
| N≥20 | The rubric truly becomes a "cheat device"—but you've also developed your own content intuition |

**Cold-start's real gift isn't prediction precision—it's the retro habit it forces you to build.** By the time this habit persists to N=20, your content intuition itself is much stronger.

---

## Cold-start retro discipline (**stricter than the stable period**)

Each of the first 5 must complete the full loop. **Skipping the retro on any one → the whole calibration fails.**

The minimum info to fill each retro:
- Actual plays / reads
- Actual likes (to see the like rate)
- Actual comment count (to see interaction)
- Top 3 comments + like counts (to see the audience's real reception point)
- My v0 prediction vs actual: which dimension was validated / refuted

After 5 pieces you'll see at least one pattern—e.g. "my ER is always overestimated" or "my SR dimension predicts nothing at all"—this pattern is the evidence for your first bump.

---

## Upgrade options from piece 6

After running 5 calibration pieces, you have 3 paths:

### Path A: from v0 → v1 (fit weights yourself)
Run `/cheat-bump --propose "<your specific weight adjustment>"`. The system forces a full re-score + cross-model audit.

### Path B: directly adopt v2 as a starting point
Copy the v2 formula of [opinion-video.md](opinion-video.md) into your `rubric_notes.md`, **then run `/cheat-bump`**—the bump flow uses your 5 pieces of data to verify whether v2 is really better on your account.

### Path C: keep v0 equal-weight, run more samples
If 5 pieces don't show a clear pattern, run 5 more. An equal-weight v0 is nothing to be ashamed of before 10-15 samples.

---

## What this rubric can't do

- **Can't tell you "whether it'll go viral"**—cold-start prediction confidence is low, the bucket should usually be given 30%-50% rather than ≥80%
- **Can't set bucket boundaries for you**—platform / account differences are too big
- **Can't transfer across accounts**—the same v0 rubric fits a different v1 on a different person's account

---

## The most important sentence

**In the first 5 pieces you aren't making decisions, you're collecting data.**

The biggest temptation in cold-start is "seeing composite 8.4 and thinking this one will go viral". **Don't believe it.** 8.4 is computed relative to an un-calibrated rubric—it means almost nothing for your account. Start trusting numbers after the 5th piece.
