# adapters/trend-sources/aihot — AI-industry trends

**Who it suits**: AI tutorials / Builders / tool accounts / AI-industry commentary. **Doesn't suit** ordinary life/career/culture verticals (use trendradar-mcp.md).

---

## What it is

A Claude-skill adapter for [aihot.virxact.com](https://aihot.virxact.com). curl the public REST API directly to get the Chinese AI-industry daily picks + historical archive.

- **5 content categories**: models / products / industry / papers / tips
- **Data freshness**: human-curated daily + real-time incremental; the items endpoint covers the last 7 days
- **No auth**, no API key, no MCP server—just install the skill and use it directly

## Install

```bash
UA='Mozilla/5.0 ... Chrome/124'
curl -fsSL -A "$UA" https://aihot.virxact.com/aihot-skill/install.sh | bash
```

After install, Claude sees this skill at `~/.claude/skills/aihot/SKILL.md` and auto-triggers it when the user asks about AI news.

## How cheat-seed / cheat-trends call it

**Don't curl directly**—just let Claude naturally trigger the aihot skill:

| cheat-seed scenario | Internal instruction to Claude |
|---|---|
| Mode C, content_form involves AI/tutorial/Builder | "call the aihot skill to get today's AI-circle curated items, filter by content_form and give 5" |
| Mode A, user mentions an AI product name ("DeepSeek V5") | "call the aihot skill with the q param to search that keyword's last-7-days activity" |

The aihot skill's SKILL.md already describes the endpoints + routing priority in detail (defaults to curated, not the daily digest)—cheat-seed doesn't need to re-write this logic, **trust the aihot skill's own judgment**.

## Output-format contract

The aihot skill returns markdown by default, grouped into 5 categories (models/products/industry/papers/tips). After cheat-seed receives it:

1. Filter out irrelevant categories by `content_form` (e.g. opinion-video → keep industry + products; tutorial-builder → keep models + tools)
2. Use the current rubric to rough-filter the 5 most suitable
3. Convert to the [candidate-schema.md](../../shared-references/candidate-schema.md) schema and write into `candidates.md`

## Failure modes

| Symptom | Handling |
|---|---|
| 403 Forbidden | the UA isn't a browser format—the aihot skill's own SKILL.md warns about this in its first paragraph; installed correctly, no problem |
| endpoint timeout / 5xx | gracefully degrade to trendradar-mcp or manual-paste; don't throw |
| the user's content_form is entirely unrelated to AI (e.g. food/makeup) | cheat-seed should **not call aihot**—per the routing table of [data-source-routing.md](../../shared-references/data-source-routing.md) |

## Stability

★★★★★—public API, author-maintained, no auth dependency.

---

## Relationship with other adapters

- **vs trendradar-mcp.md**: complementary, no overlap. aihot is the AI vertical, trendradar is general. When both are enabled, route by `content_form`.
- **vs manual-paste**: the eternal fallback. When both aihot/trendradar fail, use manual-paste.
