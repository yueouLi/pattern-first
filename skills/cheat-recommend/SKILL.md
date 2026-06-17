---
name: cheat-recommend
description: Recommend the top N topics from candidates.md, sorted by the current rubric, each with composite + a one-line rationale + anchor comparison. **When candidates doesn't exist, give guidance rather than an error.** Triggers: "recommend topics" / "next topic" / "what should I make next" / "pick a topic".
argument-hint: [— top: N] [— filter: tier1|all|safe|risky]
allowed-tools: Read, Glob, Grep
---

# /cheat-recommend — candidate-pool ranked recommendation

Read candidates.md → sort by composite → output the top N recommendations, each with scoring detail + anchor comparison + recommendation rationale.

## Overview

```
[user: recommend topics]
  ↓
[Phase 0: check candidates.md existence]   ← if missing, guide, don't error
  ↓
[Phase 1: parse the candidates list]
  ↓
[Phase 2: filter (tier / safety / already published)]
  ↓
[Phase 3: sort by composite + find anchors]
  ↓
[Phase 4: output top N + each one's rationale + anchor comparison]
```

## Constants

- **TOP_N = 5** — recommend top 5 by default
- **STRATEGY = stable+experimental** — when recommending ≥2, follow the "1 safe-score + 1 experimental" strategy of [cadence-protocol.md](../../shared-references/cadence-protocol.md); when recommending 1, only the top safe-score
- **POOL_PATH = candidates.md** — candidate-pool path
- **EXCLUDE_PUBLISHED = true** — exclude already-published ones (dedup against `predictions/*.md`)
- **EXCLUDE_REJECTED = true** — exclude ones the user actively skipped (`tier=skip`)
- **REQUIRE_SCORED = true** — only recommend already-scored ones—avoid recommending material that hasn't been read
- **DUPLICATE_CATEGORY_LOOKBACK** — derived from `state.target_publish_cadence_days`: don't recommend a candidate of the same category already published within max(3, cadence_days × 3) days (avoid aesthetic fatigue)

> 💡 Override at call time: `/cheat-recommend — top: 3 — filter: safe`

## Inputs

| Required | Source |
|---|---|
| `candidates.md` | user project root |
| `predictions/*.md` | for dedup |
| `.cheat-state.json` | current rubric_version |

## Workflow

### Phase 0: candidate-pool existence check

Read `candidates.md`:

| State | Handling |
|---|---|
| File doesn't exist | **don't error**. Output guidance: see "no-candidate-pool guidance" below |
| File exists but empty (< 1 entry) | same as above |
| File exists and non-empty | proceed to Phase 1 |

**No-candidate-pool guidance** (key: don't let the user get discouraged the first time they hit cheat-recommend):

```
You currently have no candidate pool (candidates.md doesn't exist or is empty).

Most people have no candidate pool—that's normal. Four ways to build one, pick one:

1. 🌱 [recommended] run /cheat-seed
   A one-time seeding action: 3 questions (interests / tone / red lines) → pull public trends + Claude brainstorm
   → output 15 candidates for you to pick 5 → by default also write 5 drafts. 5 minutes done.

   - No prior history: pure brainstorm (interests × trends)
   - Has prior history (imported at init): the brainstorm recommends based on "what you've done before"

   Say: "find a topic" or "seed"

2. 🔥 [daily replenishment] use /cheat-trends to fetch 20 scored candidates
   Say: "fetch trends" — pull N items each from weibo-hot / zhihu-hot / Bilibili popular / HN / your configured sources
   Suitable for users who've already run /cheat-seed and want to top up the pool daily

3. ✍️  Build manually: paste candidate titles into candidates.md, one per line
   I'll auto rough-score each one

4. 📋 Import from Notion / RSS: run /cheat-init --mode add-pool to configure an adapter

You can also skip the candidate pool and just give me a concrete draft and say "start prediction".

> The difference between /cheat-seed vs /cheat-trends:
> - seed is a seeding action (includes brainstorm + optional draft), suitable for "I'm starting from zero with no topic"
> - trends is daily multi-adapter fetching (no brainstorm, no draft writing), suitable for "daily replenishment of the pool"
```

After the guidance → exit, don't continue to later phases.

### Phase 1: parse candidates

Parse each H3 entry per the "Markdown representation" format of [candidate-schema.md](../../shared-references/candidate-schema.md):

```markdown
### [tier1] Title
- **id**: a3f2c1d4e5b6
- **composite (v2)**: 8.47 — ER=4 HP=4 QL=5 NA=3 AB=5 SR=3 SAT=3
- **predicted bucket**: 50k-300k
...
```

Extract each one's `id` / `title` / `tier` / `composite` / `dimension_scores` / `note`.

Fault tolerance: `candidates.md` format was hand-edited by the user → ask the user for the schema, **don't silently ignore unrecognized entries**.

### Phase 2: filter

```
1. EXCLUDE_PUBLISHED=true → scan the headers of predictions/*.md, extract all ids; filter them out of the pool
2. EXCLUDE_REJECTED=true → filter tier=skip
3. REQUIRE_SCORED=true → filter composite=null (unscored ones not recommended)
4. filter argument:
   - tier1: keep only tier=tier1
   - all: no filter (tier1+2+3)
   - safe: exclude tier=risky
   - risky: show only tier=risky (for "I just want to publish a risky issue today")
```

### Phase 2.5: Buffer-color override (**highest priority**)

Read `state.shoots` + `state.target_publish_cadence_days` to compute the buffer color ([cadence-protocol.md](../../shared-references/cadence-protocol.md)):

| Buffer color | Recommendation-strategy override |
|---|---|
| 🔴 red | **only the top 1 safe-score**—no experimental. Reply: "buffer is at 0/1 piece, high gap risk for the next publish day, must shoot ≥1 safe-score today. Below is the top 1 safe-score (no experimental)" |
| 🟠 orange | standard 1 safe + 1 experimental, but prompt "suggest prioritizing the safe-score" |
| 🟢 green | standard 1+1 (default) |
| 🔵 blue | **refuse to recommend**. Reply: "your buffer is at N pieces; cadence-protocol says pause shooting when backed up. Ship inventory first + retro. To override manually, say 'I insist on shooting'" |
| flexible mode (`target_publish_cadence_days=null`) | don't apply the buffer override, standard strategy |

### Phase 3: sort + pick 1 safe + 1 experimental (per STRATEGY)

#### Item 1 (safe-score)

1. Sort descending by `composite`
2. Filter out `tier=risky` (a safe-score needs a safe issue)
3. Filter out duplicates whose `category` was published/recommended within the last `DUPLICATE_CATEGORY_LOOKBACK` days (avoid aesthetic fatigue)
4. Take the top 1

#### Item 2 (experimental)

1. In candidates.md, find:
   - the one whose dimension combination **differs most** from recently-published samples (adds calibration information), or
   - the one with a clear pattern/dimension hypothesis (e.g. "an A/B comparison for MS=5"), or
   - tier=risky but the user actively wants to try (override with `--filter risky`)
2. The composite isn't necessarily top—but it has "information value"
3. If there's no suitable experimental candidate in the pool → reply: "there's no obvious experimental sample in the pool, here are 2 safe-scores for you"

#### The remaining (TOP_N - 2) items

Fill up descending by composite, marked "(backup)".

#### Anchors

For each item, find 1–2 **published** pieces with a close composite as anchors (read from `predictions/*.md`). Prioritize **same-duration** anchors (per `state.typical_duration_seconds` ±20%).

### Phase 4: output

```
🎯 Candidate-pool recommendations (rubric: v2 / buffer: 🟢 green / cadence: every other day)

📌 Item 1 — **safe-score** (recommend shooting immediately):
  **[tier1] [👍 9.18] the high-density system of "for your own good"**
   - dimensions: ER=5 HP=5 QL=4 NA=4 AB=5 SR=5 SAT=4
   - rough-predicted bucket: 300k-1M (central ~600k)
   - rationale: ER+SR both 5 top-tier, "high-density family issue" universal and safe to share
   - anchor: hamster (composite 9.41, actual 1.24M) — same "theoretical framework + concrete sample" route
   - risk: heavy issue, not suitable for 2 such pieces in a row

🧪 Item 2 — **experimental** (verify a specific hypothesis):
  **[tier1] [👍 8.71] the length of "haha"**
   - dimensions: ER=3 HP=5 QL=5 NA=4 AB=5 SR=4 SAT=5
   - rough-predicted bucket: 300k-1M (central ~550k)
   - **test goal**: v2.1 candidate dimensions MS+TS both 5 vs "who asked you" with same ER/HP/QL/SR but MS+TS low at 3
   - information value: shooting this gives strong evidence for / weak refutation of promoting v2.1
   - anchor: "who asked you" (composite 8.24, actual 117k)

(backup top 3):
  3. ……
  4. ……
  5. ……

Next step:
- Pick the safe-score + experimental, shoot 1 of each → rewrite the script → "start prediction"
- Shooting only 1 → pick the safe-score (the redder the buffer, the more you should pick safe)
- Want to fetch more candidates → say "fetch trends"
- Not satisfied → say "change filter to all" to see other tiers or "regen"
```

If the buffer color is 🔴:
```
🔴 buffer alert: your buffer is at 0/1 piece, **the next publish day may have a gap**.
   Per the cadence protocol, only the top 1 safe-score (no experimental):

  **[tier1] [👍 9.18] the high-density system of "for your own good"**
   - ...(same safe-score format as above)

You must shoot this today. Pick 5 candidates → "fetch trends".
```

If the buffer color is 🔵:
```
🔵 buffer backed up: your buffer is at N pieces, **pausing recommendations**.
   Per the cadence protocol, ship inventory first + retro.
   - shot not published: N pieces (earliest shot X days ago)
   - pending retros: N pieces
   Say "shipped ..." to dequeue, or "retro" to handle pending items.
   If you insist on shooting new, reply "I insist on shooting" and I'll recommend the top 1 safe-score.
```

Each item must have: dimension scores (so the user can challenge the score) + an anchor (so the user can calibrate the composite's credibility) + a rationale (so the user understands the recommendation logic). **Outputting only a composite ranking without explanation is not allowed**—that's a black box.

## Key Rules

1. **Don't error, give guidance.** A missing candidate pool is the default state, not an error
2. **Don't recommend unscored ones.** REQUIRE_SCORED=true is an honesty threshold—recommending unread material is astrology
3. **Must carry an anchor.** composite 8.47 means different things on different accounts; the anchor grounds the abstract number to a real sample
4. **Must carry a rationale.** One sentence—why is this one stronger than the second?
5. **Dedup published.** Don't recommend already-published ones (the user can explicitly override)

## Refusals

- "Just give me the highest composite, no need to explain" → refuse. Showing the scores + anchor is the only chance to spot a "misjudgment"
- "Re-score every entry in candidates.md" → route to `/cheat-score` for individual ones; batch re-scoring is part of `/cheat-bump`, not in recommend's scope
- "Sort by predicted bucket, not by composite" → ask the reason. The bucket is the discretization of the composite; sorting by composite = sorting by bucket, the difference is the within-bucket order—if the user truly wants to sort by "bet expected value", you need to multiply by average plays, which is a separate scoring dimension

## Integration

- Upstream: `/cheat-trends` pulls external trends into candidates.md → recommend sees them automatically
- Downstream: after the user picks one and writes a draft → `/cheat-predict` (the candidate's rough composite doesn't enter the prediction; the prediction re-scores)
- Coordinates with `/cheat-status`: status shows "the candidate pool has N tier1 unpublished", recommend provides the concrete recommendations
