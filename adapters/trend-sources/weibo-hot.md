# Adapter: weibo-hot (Weibo hot search)

Called by these skills: `cheat-seed` Phase 2a, `cheat-trends`.

> **Current status**: schema only. The actual fetch implementation belongs to batch 3. During the stub period /cheat-seed fetches + parses directly via Claude's `WebFetch` (see "transition implementation" below).

---

## Use cases

- **One of `cheat-seed`'s default sources**—the first topic seed for cold-start users
- **An optional source for `cheat-trends`**—daily candidate-pool replenishment

Best fit: current-affairs commentary, social issues, hot-topic interpretation opinion videos.

## Dependencies

- Public endpoint, **no cookie needed**
- Endpoint: `https://s.weibo.com/top/summary?cate=realtimehot` (HTML page)
- Alternative: `https://weibo.com/ajax/side/hotSearch` (JSON, returns 401 at some times, unstable)

## Fetch interface

```
fetch(limit: int = 50) -> List[Candidate]
```

Returns a list of items conforming to [shared-references/candidate-schema.md](../../shared-references/candidate-schema.md).

Field mapping:
- `id`: `sha256("trend|" + normalized_title)[:12]`
- `title`: the hot-search term
- `source`: `"trend:weibo-hot"`
- `snapshot_text`: the hot-search term + (if any) the official tag + a brief summary (auto-fetch 1-2 sentences from the hot-search detail page)
- `snapshot_at`: fetch time ISO 8601
- `url`: `https://s.weibo.com/weibo?q=<encoded_keyword>`
- Other fields: null (no scoring at the fetch stage; handled by the caller's cheat-score)

## Failure modes

| Symptom | Handling |
|---|---|
| HTML structure change causes parse failure | return an empty list + write to stderr "weibo HTML structure changed, see adapters/trend-sources/weibo-hot.md to fix it yourself" |
| endpoint 503 / rate limit | return an empty list + report |
| network unreachable | return an empty list + report |

**Graceful degradation**: a single failure doesn't throw—the caller (cheat-seed / cheat-trends) falls back to other sources.

## Stability level

★★★—public endpoint, but Weibo occasionally adjusts the page structure + has anti-scraping (high-frequency fetching from the same IP in a short time gets rate-limited).

Suggested throttle: `/cheat-seed` defaults to ≤ 3 fetches per user per day—the cold-start stage doesn't need higher frequency.

## Transition implementation (stub)

Before a dedicated adapter implementation is written in batch 3, when `/cheat-seed` calls this source it directly uses Claude's `WebFetch` tool to fetch `https://s.weibo.com/top/summary?cate=realtimehot` and extract the top 50 hot-search titles from the HTML. Handled specifically by cheat-seed's Phase 2a:

```
WebFetch("https://s.weibo.com/top/summary?cate=realtimehot",
         "extract the top 50 hot-search titles, one per line, descending by heat")
```

If the WebFetch content yields ≥10 recognizable hot searches → treat as success; otherwise treat as failure, skip this source.

## Risk notes

- Weibo hot search content **often contains politically-sensitive / entertainment-gossip** issues—the "red line" filter at /cheat-seed Phase 1 Q3 is crucial
- Some hot-search terms are too short (5-10 chars) and lack context—Claude needs to expand them when brainstorming
- A hot search's "heat" score and "how suitable it is for an opinion video" are **not positively correlated**—don't feed the heat directly as a composite input when rough-scoring

## Related adapters

- [zhihu-hot.md](zhihu-hot.md) — higher issue depth, better fit for argumentation
- bilibili-popular.md (TBD) — younger-skewing issues
- thirdparty-paid.md (TBD) — Newrank / Feigua, paid but stable
