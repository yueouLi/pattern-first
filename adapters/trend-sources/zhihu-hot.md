# Adapter: zhihu-hot (Zhihu hot list)

Called by these skills: `cheat-seed` Phase 2a, `cheat-trends`.

> **Current status**: schema only. The actual fetch implementation belongs to batch 3. During the stub period /cheat-seed fetches directly via Claude's `WebFetch` (see "transition implementation" below).

---

## Use cases

- **One of `cheat-seed`'s default sources**—the first topic seed for cold-start users
- **An optional source for `cheat-trends`**—daily candidate-pool replenishment

Best fit: argumentation / issue-discussion / knowledge opinion videos. Zhihu topics are on average more "discussable" than Weibo's—a single title contains a question and a stance, saving half the brainstorm work.

## Dependencies

- Public endpoint, **no login needed**
- Endpoint: `https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true` (JSON)
- Alternative: `https://www.zhihu.com/billboard` (HTML, usable as a fallback)

## Fetch interface

```
fetch(limit: int = 50) -> List[Candidate]
```

Returns a list of items conforming to [shared-references/candidate-schema.md](../../shared-references/candidate-schema.md).

Field mapping:
- `id`: `sha256("trend|" + normalized_title)[:12]`
- `title`: the Zhihu question title
- `source`: `"trend:zhihu-hot"`
- `snapshot_text`: the question title + a 200-char summary of the top-voted answer (optional—use just the title if it can't be fetched)
- `snapshot_at`: fetch time ISO 8601
- `url`: the Zhihu question URL (e.g. `https://www.zhihu.com/question/<id>`)
- Other fields: null

## Failure modes

| Symptom | Handling |
|---|---|
| API endpoint change | switch to the `/billboard` HTML fallback |
| API returns login-required (403) | return an empty list + report |
| network unreachable | return an empty list + report |

**Graceful degradation**: a failure doesn't throw—the caller has other sources to fall back to.

## Stability level

★★★★—the Zhihu API is more stable than Weibo's; the JSON endpoint changes less frequently than Weibo's HTML.

Suggested throttle: `/cheat-seed` defaults to ≤ 3 fetches per user per day.

## Transition implementation (stub)

Before a dedicated adapter is written in batch 3, `/cheat-seed` uses `WebFetch`:

```
WebFetch("https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total?limit=50&desktop=true",
         "parse each item of the data array in the JSON, extract target.title_area.text and target.url, up to 50")
```

If the returned structure fails to parse → switch to the `/billboard` HTML fallback.

## Content characteristics (affecting brainstorm quality)

Zhihu hot-list titles are usually **complete interrogative sentences** ("how to view X", "why Y", "what's the essence of X"), more suitable for direct conversion into opinion-video topics than Weibo hot-search keywords.

But note:
- Some titles are too specific ("company X's layoff event") → Claude needs to do a "case → universal" abstraction lift when brainstorming
- Some titles are too "Zhihu-toned" (academic, long complex sentences) → Claude needs to do a "Zhihu phrasing → short-video hook" translation when brainstorming

## Risk notes

- The Zhihu hot list occasionally has politically-sensitive issues—the "red line" filter at /cheat-seed Phase 1 Q3 is necessary
- Some hot-list topics are already densely covered by Zhihu big-Vs, making differentiation hard for a video—when rough-scoring, suggest prompting the user "this topic is saturated, you need a differentiated angle"

## Related adapters

- [weibo-hot.md](weibo-hot.md) — broader but more fragmented issues, better fit for current-affairs commentary
- bilibili-popular.md (TBD) — a direct reference for video content
- thirdparty-paid.md (TBD) — a paid, stable data source
