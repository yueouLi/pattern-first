# adapters/trend-sources/trendradar-mcp — general social trends (MCP)

**Who it suits**: opinion video / current-affairs commentary / culture verticals / food / career / social issues—**any non-AI vertical** content.

---

## What it is

[TrendRadar](https://github.com/sansan0/TrendRadar) is a 57k-star Chinese trend-aggregation monitor (uses the newsnow API to pull multi-platform: Weibo / Zhihu / Douyin / Bilibili / Toutiao, etc.). It ships its own standalone MCP server `trendradar-mcp`, exposing 25+ tools.

cheat-on-content treats it as one of the trend-sources adapters—once the user configures the MCP server, cheat-seed / cheat-trends can call it naturally.

- **Multi-platform coverage**: Weibo / Zhihu / Douyin / Bilibili / Toutiao / 36kr / etc.
- **AI-enhanced tools**: `analyze_topic_trend` gives a surge/decay verdict; `compare_periods` gives week-over-week; `analyze_sentiment` gives sentiment
- **License**: TrendRadar itself is GPL-3.0, but we **only call their server via the MCP protocol**, which doesn't constitute linking—no GPL contagion

## Install

Refer to the [MCP config docs](https://github.com/sansan0/TrendRadar) in the TrendRadar repo. After install, the user's Claude Code `.claude/settings.json` contains the `mcp__trendradar__*` series of tools.

cheat-on-content doesn't bundle TrendRadar—the user installs it themselves and manages the server resources.

## Key tools cheat-seed / cheat-trends call

| MCP tool | Use | Where it's called |
|---|---|---|
| `mcp__trendradar__get_latest_news` | get the latest hot list (most direct) | cheat-seed Mode C primary / cheat-trends primary |
| `mcp__trendradar__get_trending_topics` | auto-extract topic stats | cheat-seed Mode C backup |
| `mcp__trendradar__analyze_topic_trend` | single-topic trend analysis (surge/decay) | cheat-seed Mode A gray-scenario enrich (the user mentioned a concrete topic and agreed to pull data) |
| `mcp__trendradar__compare_periods` | week-over-week / month-over-month | a weak signal of "whether the user's field is changing" at cheat-bump time (rarely used) |
| `mcp__trendradar__search_news` | keyword search | cheat-seed Mode A when the user mentions a keyword |

## Output-format contract

TrendRadar MCP returns JSON / markdown. After cheat-seed receives it:

1. Parse the items (title / source / hot_score / snapshot_at / url)
2. Compute the stable id per [candidate-schema.md](../../shared-references/candidate-schema.md) (`sha256(source + normalized_title + url_path)[:12]`)
3. Dedup (per cheat-trends' dedup protocol)
4. Rough-filter with the current rubric
5. Write into `candidates.md`

## Failure modes

| Symptom | Handling |
|---|---|
| MCP server not installed / not started | cheat-seed auto-degrades to the next enabled source (e.g. aihot or manual-paste), doesn't throw |
| MCP call timeout | times out after 30 seconds, prompts the user "trendradar is slow, wait or switch sources" |
| the newsnow upstream API changed | the TrendRadar maintainer fixes it; the user upgrades along |

## Stability

★★★★—depends on the TrendRadar project's activity (57k stars, active) + the newsnow upstream's stability.

---

## Relationship with other adapters

- **vs aihot.md**: complementary, no overlap. trendradar is general social, aihot is the AI vertical. When both are enabled, route by `content_form` (see [data-source-routing.md](../../shared-references/data-source-routing.md))
- **vs manual-paste**: the eternal fallback. When both APIs fail, use manual-paste

## A note to the TrendRadar team

If you're a TrendRadar maintainer seeing this adapter doc—thank you for building multi-platform aggregation as an MCP server. cheat-on-content is the "content-production-side downstream" of your project—users use TrendRadar to know what's happening, and use cheat-on-content to turn that into a calibrated content-prediction loop. Complementary, not a replacement.

Cross-links welcome: [github.com/XBuilderLAB/cheat-on-content](https://github.com/XBuilderLAB/cheat-on-content).
