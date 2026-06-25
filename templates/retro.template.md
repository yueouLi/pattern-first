# Retro section template

> **This template is auto-appended by `/cheat-retro` to the corresponding prediction file's `## Retro` section.**
> Not a standalone file—just a format reference for the lower half of the prediction file.
>
> Example data is from the video-analysis project's "stop expecting" retro (the retro section of [predictions/2026-04-24_ab61ed09_stop-expecting.md]).
>
> Full spec: see the "retro section" part of [shared-references/prediction-anatomy.md](../pattern-first/shared-references/prediction-anatomy.md).

---

## Retro

**Retro date**: `<YYYY-MM-DD>` (publish T+`<N>`d)
**Fetch time**: `<YYYY-MM-DD HH:MM>`
**Data source**: `manual paste` / `adapter:<platform>`

### Actuals

- Plays: **`<X>`** (lands in the \``<bucket>`\` bucket [high / low / central], **`<+X% / -X%>`** relative to the central `<X>`)
- Likes: `<X>` (like rate `<X.XX%>`)
- Comments: `<N>` (comment rate `<X.XXX%>`)
- Saves: `<N>`
- Shares: **`<X>`** (share rate **`<X.XX%>`**, [strong / medium / weak])

> **Example** (stop expecting, T+7d):
> - Plays: **711k** (high within the `300k-1M` bucket, **+42%** relative to the central 500k)
> - Likes: 24k (like rate 3.38%)
> - Comments: 899 (comment rate 0.126%, **the highest among same-period videos**)
> - Saves: 5251
> - Shares: **18k** (share rate **2.53%**, strong)

> **The key derived ratios must be computed**: like rate, comment rate, share rate—signals the raw play count can't expose.
> E.g. the video-analysis project found "share rate" is the strongest external proxy for the TS (Topic Shareability) dimension: job-hunting 0.96% vs stop-expecting 2.53%—same composite but a 2.6x difference in share rate.

### Top comment keywords

> Cluster the N pasted comments into 3-5 categories (high-like memes / concept references / off-topic noise / share-exposing hints / @-friend propagation, etc.),
> list a representative comment + like count + proportion for each category.

- **"[key meme / sentence pattern]"**: [like count] topping / frequently appearing with N variants ([brief pattern description])
- **"[secondary meme]"**: [like count] [secondary pattern description]
- **withdrawal / resonance / parody type**: [like count] [representative comment]
- **extended quoting**: [other derivative patterns]
- **@-friend propagation / self-deprecating complicity**: [whether the comments are doing this]

> **Example**:
> - **"she's different" / "he's different" meme burst**: 2266 likes topping the chart, appearing at least 12 times throughout (193, 5, 5, 5, 3, 4, 4, 2, 2, 2, 2, 1... repeated variants); the audience **proactively applied the sentence pattern to self-deprecate**—this is a key-level meme
> - **"Joker / clown / simp" secondary meme**: 412 likes "Schrödinger's Joker/Crush superposition", 74 likes "I want to spin in circles myself"
> - **the withdrawal method seriously re-translated**: 27 likes "1. think less 2. don't believe in the beautiful 3. reconstruct the filter"—the audience proactively RTF'd it
> - **@-friend propagation**: lots of @-chains—the comments are a social arena, the audience uses the video as a "rant about a friend / self-deprecating complicity" tool

### Which predictions were validated ✅ / refuted ❌

**Validated ✅**:
- [whether the critical calibration hypothesis held] [comparison with specific numbers]
- [which factors in the reasoning table were validated]
- [which bucket in the counterfactual scenarios was hit]

**Refuted ❌**:
- [if the central deviation exceeds ±25%, state it explicitly]
- [whether the Y of "if X means Y" in the counterfactual actually happened]
- ["high-confidence" items in the reasoning table that were refuted → rubric bug signal]

> **Example**:
> **Validated ✅**:
> - The critical calibration hypothesis **fully held**: this piece 711k / "who asked you" 117k = **6.07x**, far exceeding my bet of 1.5-2x
> - ER=5 dominating emotional propagation → **strong evidence for H1**
> - HP=5 verified: share rate 2.53%, the punchline "intermittent hope" frequently quoted
>
> **Refuted ❌**:
> - The central 500k was exceeded by +42%: underestimated the second-creation virality of the "she's different" meme
> - The counterfactual reasoning "must pair with a strong social issue to break 300k" is **completely wrong**—SR=2 easily broke 700k too
> - My bet on SR ("H2 SR should go up") was **reverse-refuted**: SR **contributes almost nothing** in emotion-oriented scenarios

> **Key discipline**: each validation / refutation must cite specific data ("share rate 2.53%"), no vague wording like "basically matches".

### New observations to write into rubric_notes.md

1. **[one-sentence law title]**: [specific evidence, citing a specific data point]
2. **[second law]**: [as above]
3. **[candidate-dimension naming suggestion]**: [if you observe a dimension the rubric doesn't capture, propose a candidate dimension name + a draft scoring definition]

> **Example**:
> 1. **ER's real weight in emotion-oriented scenarios should be ≥ ×2.0**: the 6x traffic ratio vs "who asked you" is v2 rubric's strongest counterfactual evidence
> 2. **Issue share impulse (TS) is a hidden dimension**: joker / "she's different" / filter reconstruction provide a **safe self-deprecating identity**, sharing doesn't expose one's situation, a TS=5 sample
> 3. **HP × ER resonance effect**: ER=5 + HP=5 + a reusable meme sentence = viral-level; can't be missing any one
> 4. **"second-creation sentence pattern" dimension candidate (Memetic Shareability, MS)**: can the audience make new sentences with the author's pattern? stop-expecting = Y (infinite "she's different" variants), who-asked-you = N (no-need information supply only quotable)

> Each observation must be traceable to a specific data point (don't write "emotion is important"—write "ER5/SR2 vs ER3/SR4 at the same composite, traffic differs 6x").
> These observations are auto-written by `/cheat-retro` into the "Observation Log" section of `rubric_notes.md`.

### Bump trigger assessment

- Deviation direction: [high / low / on-target]
- Accumulated same-direction deviation: [N times (including this one)]
- Whether it triggers a bump proposal: [yes / no]

> If accumulated same-direction deviation ≥3, `/cheat-retro` outputs a "suggest running /cheat-bump" prompt at the end.
> The actual bump is done via `/cheat-bump`; this section is just the trigger record.
