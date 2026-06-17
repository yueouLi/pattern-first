# Candidate Schema

Referenced by these sub-skills: `cheat-trends`, `cheat-recommend`, `cheat-init`, all `adapters/`.

Any "to be decided whether to make" content material—whether from a hand-pasted list / RSS / Notion / platform trend fetch—must be normalized into this schema before entering the candidate pool. This is the output contract of `adapters/`.

The field design references the `articles` table schema of the creator's project (a private project; the tool's methodology is abstracted from it).

---

## Required fields

| Field | Type | Note |
|---|---|---|
| `id` | string (12 chars) | stable hash: `sha256(source + normalized_title + url_path)[:12]`. The same material fetched at different times → same id |
| `title` | string | the candidate's human-readable title |
| `source` | string | source identifier, format `<adapter-type>:<source-name>`, e.g. `trend:hackernews`, `pool:notion-mybook`, `paste:manual` |
| `snapshot_text` | string | the candidate's full text or summary—**this is the input for scoring**, not the url. The adapter is responsible for expanding the url into readable text |
| `snapshot_at` | ISO 8601 | the time this item was fetched/entered |

---

## Optional fields

| Field | Type | Note |
|---|---|---|
| `url` | string | the original link (for traceability) |
| `tier` | enum | `tier1` / `tier2` / `tier3` / `skip` / `risky` / `done`. Rough classification, for filtering |
| `read_status` | enum | `unread` / `skimmed` / `deep_read` / `done`. Processing status |
| `category` | string | custom classification tag (e.g. "social", "family", "academic") |
| `composite_score` | float | the composite obtained by scoring with the current rubric (if scored) |
| `dimension_scores` | object | each dimension's integer score, keys aligned with the current rubric's dimensions (e.g. `{"ER": 5, "HP": 4, ...}`) |
| `scored_under_rubric_version` | string | the rubric version used when scoring |
| `predicted_bucket` | string | the rough-predicted bucket (e.g. `300k-1M`), **note: not a formal prediction**—a rough estimate at the topic stage, completely independent from the immutable prediction in `predictions/*.md` |
| `predicted_reason` | string | a one-sentence reason |
| `note` | string | free-text note, e.g. "wait for a moment to publish", "to re-read", "risky issue" |
| `rejected_at` / `rejected_reason` | ISO 8601 / string | recorded when the user actively skips this candidate |

---

## JSON examples

### Markdown-list adapter output

```json
{
  "id": "a3f2c1d4e5b6",
  "title": "why we all hate reaching out to friends first",
  "source": "pool:markdown-list",
  "snapshot_text": "[the full text the user copied from candidates.md]",
  "snapshot_at": "2026-05-04T08:30:00+08:00",
  "url": null,
  "tier": "tier1",
  "read_status": "skimmed",
  "category": "social",
  "composite_score": 7.4,
  "dimension_scores": {"ER": 4, "HP": 4, "QL": 5, "NA": 3, "AB": 5, "SR": 3, "SAT": 3},
  "scored_under_rubric_version": "v0",
  "predicted_bucket": "50k-300k",
  "predicted_reason": "ER=4+QL=5 strong punchline feel, AB=5 universal, but SR=3 issue not strong enough",
  "note": ""
}
```

### Trend adapter output (HN)

```json
{
  "id": "8c4d92e1f0b3",
  "title": "Show HN: I built a tool that predicts whether your video will go viral",
  "source": "trend:hackernews",
  "snapshot_text": "[the article's full text + a summary of the top 5 comments]",
  "snapshot_at": "2026-05-04T09:15:00+08:00",
  "url": "https://news.ycombinator.com/item?id=12345678",
  "tier": null,
  "read_status": "unread",
  "category": "tech-meta",
  "composite_score": null,
  "dimension_scores": null,
  "scored_under_rubric_version": null
}
```

Before scoring, all score fields are null—as expected. After `cheat-trends` fetches them, it calls `cheat-score` to compute a composite for each.

---

## Markdown representation (the user-visible storage format)

The candidate pool's default storage is `candidates.md` (human-readable), not JSON. Each item is an H3 entry:

```markdown
### [tier1] why we all hate reaching out to friends first
- **id**: a3f2c1d4e5b6
- **source**: pool:markdown-list
- **snapshot_at**: 2026-05-04
- **category**: social
- **composite (v0)**: 7.4 — ER=4 HP=4 QL=5 NA=3 AB=5 SR=3 SAT=3
- **predicted bucket**: 50k-300k
- **note**:

> [snapshot_text section, if any]
```

After upgrading to SQLite (see the upgrade trigger in `cheat-status`), the same fields are stored in the `articles` table, and the markdown view is auto-rendered from the DB.

---

## The key rule of ID stability

**The same material fetched by different adapters at different times → must compute the same id.** This is the basis of dedup.

Algorithm:
```python
import hashlib

def candidate_id(source: str, title: str, url: str = None) -> str:
    normalized_title = title.strip().lower().replace(" ", "")
    url_path = url.split("?")[0].rstrip("/") if url else ""
    raw = f"{source.split(':')[0]}|{normalized_title}|{url_path}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
```

Notes:
- `source` takes the adapter type before the colon (`trend:hackernews` → `trend`), not the specific source name—the same title fetched by both HN and Reddit should be judged the same candidate (to avoid duplicate scoring)
- the title is lowercased + whitespace-stripped—to avoid "Hello World" and "hello world" being computed as different ids
- the url drops the query string—`?utm_source=xxx` doesn't affect the content

---

## Dedup protocol

`cheat-trends` / `cheat-recommend` must execute before writing into `candidates.md`:

1. Compute the new item's id
2. Check whether `candidates.md` already contains this id → skip
3. Check whether `predictions/*.md` contains this id (already published) → skip
4. Check whether `.cheat-cache/trends-history.jsonl` contains this id with `rejected_at != null` → skip (the user already actively rejected it)
5. If it passes, write it

`.cheat-cache/trends-history.jsonl` is the dedup cache of fetch history, one JSON record per line, append-only. Candidates the user rejected are kept here for 6 months; after that they're allowed to reappear (the material may be evaluated differently under a new rubric).

---

## tier semantics

| Tier | Meaning | Corresponding action |
|---|---|---|
| `tier1` | strong candidate, should recommend | enters the `cheat-recommend` ranking pool |
| `tier2` | medium, backup | enters the ranking pool but with low weight |
| `tier3` | weak candidate, kept but not used | doesn't enter the recommend pool, kept as long tail |
| `skip` | user actively skipped | no longer appears |
| `risky` | issue-sensitive / platform-control risk | extra annotation when recommending, requires user confirmation |
| `done` | published | removed from the candidate pool, taken over by the prediction file |

**During cold-start all items default to `unread`/`null tier`**—until the user or `cheat-score` gives a composite, they can't be rough-classified. **Unscored items should not appear in `cheat-recommend` output**—to avoid recommending unread material.

---

## Adapter implementation contract

Any adapter under `adapters/` must:

1. Implement the `fetch() → List[Candidate]` interface (pseudo-signature, actually a protocol described in markdown docs)
2. Output items conforming to this schema
3. Be responsible for expanding the url / short summary into a readable `snapshot_text`—**adapters don't output "bare urls"**
4. Degrade gracefully: if config is missing (API key, cookie), return an empty list + write the reason to stderr/log, **don't throw**

See `adapters/HOWTO.md` (to be written in batch 3).
