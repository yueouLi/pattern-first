---
name: cheat-trends
description: Fetch today's hot topics from configured trend sources (HN / Reddit / YouTube trending / Bilibili popular / etc.), dedupe + rough-score + write into candidates.md. **Most people have no candidate pool—this is the key that makes the "I have no material" problem disappear at step two of onboarding.** Triggers: "fetch trends" / "what can I make today" / "trending now" / "find a topic".
argument-hint: [— sources: <comma-separated>] [— max-per: 20]
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-trends — trend fetching

Multi-adapter pattern: read the output of each `trend-sources` adapter → dedupe → rough-score → write into `candidates.md`.

## Overview

```
[user: fetch trends]
  ↓
[Phase 0: read .cheat-state.json to get enabled adapters]
  ↓
[Phase 1: call fetch on each adapter]
  ↓
[Phase 2: normalize to candidate-schema]
  ↓
[Phase 3: dedupe (vs candidates / predictions / trends-history)]
  ↓
[Phase 4: rough-score each new item (using cheat-score inline logic)]
  ↓
[Phase 5: sort + ask the user which to add to candidates.md]
  ↓
[Phase 6: write + update the trends-history.jsonl cache]
```

## Constants

- **TREND_SOURCES = ["manual-paste"]** — the list of enabled adapters (default only manual-paste, the most stable)
- **LOOKBACK_HOURS = 24** — fetch trends from the last N hours
- **MAX_PER_SOURCE = 20** — at most N items per adapter
- **DEDUPE = true** — dedup switch
- **AUTO_SCORE = true** — auto-call cheat-score to rough-score after fetching
- **MIN_COMPOSITE_TO_SUGGEST = 6.0** — don't recommend the user add items below this score to the candidate pool (still written to trends-history to avoid re-recommending next time)

> 💡 Override at call time: `/cheat-trends — sources: manual-paste,hackernews,bilibili-popular — max-per: 10`

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | default sources |
| `adapters/trend-sources/<name>.md` | the implementation description of each adapter |
| `candidates.md` | dedup reference |
| `predictions/*.md` | dedup reference (don't re-recommend what's already published) |
| `.cheat-cache/trends-history.jsonl` | historical-fetch dedup cache |

## Workflow

### Phase 0: read enabled adapters

```python
# pseudocode
state = read('.cheat-state.json')
enabled_adapters = args.sources or state.get('enabled_trend_sources', ['manual-paste'])
```

If enabled_adapters is empty → output guidance:

```
You currently have no trend sources enabled.

Fastest setup:
- One-off run: /cheat-trends — sources: manual-paste,hackernews
- Permanently enable: edit the enabled_trend_sources array in .cheat-state.json

Available adapters (see adapters/trend-sources/):
- manual-paste (default, always works)
- hackernews (HN Algolia API, no key needed)
- reddit-rising (public .json endpoint)
- youtube-trending (needs a YouTube Data API key)
- bilibili-popular (public endpoint, occasionally changes)
- xhs-explore / douyin-hot (fragile, need a cookie)
- thirdparty-paid (Newrank / Feigua, you wire up the API yourself)
```

### Phase 1-2: call fetch + normalize on each adapter

For each adapter, read the fetch interface described in its `adapters/trend-sources/<name>.md` (actually a Bash call to underlying Python / shell / WebFetch):

| Adapter | Implementation |
|---|---|
| `manual-paste` | ask the user: "paste your candidate URL/title list for today (one per line)" → parse each line, WebFetch URLs to expand a snippet |
| `hackernews` | WebFetch the HN Algolia API: `https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage={N}` → extract title/url/snippet |
| `reddit-rising` | WebFetch Reddit JSON: `https://www.reddit.com/r/<subreddit>/rising.json?limit={N}` |
| `youtube-trending` | needs an API key configured in `.env` or .cheat-state.json, call YouTube Data API v3 `videos?chart=mostPopular` |
| `bilibili-popular` | WebFetch the Bilibili popular endpoint |
| `xhs-explore` / `douyin-hot` | need the user to provide a cookie path, call the endpoint described by the corresponding platform-stub; missing cookie → skip that adapter |
| `thirdparty-paid` | schema only—read `adapters/trend-sources/thirdparty-paid.md`, have the user wire it up |

Each adapter outputs items conforming to [candidate-schema.md](../../shared-references/candidate-schema.md).

**Graceful degradation**: a single adapter failing (missing API key / endpoint 503 / expired cookie) → skip that adapter, **don't throw**, and explain in the summary:
```
✅ hackernews: pulled 18 items
⚠️  youtube-trending: skipped (missing API key—see adapters/trend-sources/youtube-trending.md to configure)
✅ bilibili-popular: pulled 15 items
❌ douyin-hot: skipped (cookie file doesn't exist)
```

### Phase 3: dedupe

Per the "dedup protocol" in [candidate-schema.md](../../shared-references/candidate-schema.md):

1. Compute an id for each item (`sha256(source_type + normalized_title + url_path)[:12]`)
2. Check whether `candidates.md` already contains this id → skip
3. Check whether `predictions/*.md` already contains this id → skip
4. Check whether `.cheat-cache/trends-history.jsonl` already contains this id with `rejected_at != null` → skip

Write the dedup stats into the summary report.

### Phase 4: rough-score

When `AUTO_SCORE=true`, for each new item:
1. Use the item's `snapshot_text` as input
2. Score the 7 dimensions per the current rubric (**don't** call the `/cheat-score` sub-skill through IO; reuse the scoring logic inline)
3. Compute the composite
4. Give a one-sentence rationale

**Note**: rough-scoring ≠ a formal prediction. A prediction must be based on the final draft (revised by the user); the scoring here is just a rough filter for "is it worth developing into a full draft".

When `AUTO_SCORE=false`, items are written into candidates.md with composite=null, requiring a later manual `/cheat-score`.

### Phase 5: sort + ask

Sort descending by composite, filter out those with composite < `MIN_COMPOSITE_TO_SUGGEST`:

```
🔥 Trend fetch complete. Per-source pull stats:
- manual-paste: 5 items (user input)
- hackernews: 18 items
- bilibili-popular: 15 items
skipped douyin-hot (missing cookie)

27 new items left after dedup.
After rough-scoring, 12 have composite ≥ 6.0:

| # | Title | source | composite | bucket | rationale |
|---|---|---|---|---|---|
| 1 | why we all hate reaching out to friends first | hackernews | 8.4 | 300k-1M | ER+QL both 5, AB universal |
| 2 | the thousand variants of "she's different" | bilibili-popular | 8.1 | 300k-1M | high MS candidate dimension |
| 3 | ...... |

Which to add to candidates.md?
- add all → reply "all"
- pick a few → reply "1, 3, 5"
- none → reply "none" (these will be recorded in trends-history to avoid re-recommending)
```

### Phase 6: write to disk

After the user responds:
1. Selected items → append to `candidates.md` in the "Markdown representation" format of [candidate-schema.md](../../shared-references/candidate-schema.md)
2. All fetched items (selected or not) → append to `.cheat-cache/trends-history.jsonl`:
   ```jsonl
   {"id": "...", "title": "...", "source": "...", "snapshot_at": "...", "rejected_at": null|"<ISO>", "fetched_at": "<ISO>"}
   ```

### Phase 7: state update

```json
{
  "last_trends_run_at": "<ISO>",
  "last_trends_added_count": 5
}
```

## Key Rules

1. **Don't throw.** A single adapter failing → skip + report. All adapters failing → error "all sources failed" with troubleshooting guidance
2. **manual-paste is always there.** Even if every other adapter breaks, manual-paste mode must run—it's the fallback
3. **Dedup is a hard constraint.** The same id is not re-recommended; ones the user rejected aren't re-recommended within 6 months
4. **Rough-scoring must be honestly annotated.** Mark `composite (rough, snapshot-based)` on the candidates.md entry to avoid confusion with the prediction's fine score
5. **Doesn't go directly into predictions/.** trends only produces candidates; predict is a separate action

## Refusals

- "Just scrape the Douyin hot feed directly, no cookie" → refuse. Douyin's anti-scraping is extremely strict; without a cookie it will fail; route to the douyin-session adapter config doc
- "Skip dedup, write everything fetched in" → refuse. It pollutes the candidate pool and breaks the sort at the next recommend
- "Skip rough-scoring, just write raw titles" → allowed (`AUTO_SCORE=false`), but remind the user a later `/cheat-score` is needed to enter the recommend pool

## Integration

- Upstream: the user configures the `enabled_trend_sources` array in `.cheat-state.json`
- Downstream: `/cheat-recommend` reads and sorts `candidates.md` directly—right after trends writes, recommend sees it
- With `/cheat-init`: users who chose "no candidate pool" at onboarding Q4 are routed here
- With `/cheat-status`: the status dashboard shows "last trend fetch: X days ago / candidate pool to clean: Y items"

## Adapter implementation notes

Each `adapters/trend-sources/<name>.md` must document the following:
1. **Dependencies**: API key / cookie / package
2. **Fetch interface**: how it's called (python script path / shell command / API endpoint)
3. **Output schema**: must conform to candidate-schema.md
4. **Failure modes**: common errors + graceful-degradation behavior
5. **Stability level**: ★ 1–5 stars

See [adapters/HOWTO.md](../../adapters/HOWTO.md) (to be implemented in batch 3).
