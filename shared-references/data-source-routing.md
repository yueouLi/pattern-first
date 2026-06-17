# Data Source Routing — the trigger and routing protocol for trend tools

Referenced by cheat-seed / cheat-trends. Specifies **when** to call trend tools, **which one** to call, and **what to do when not calling**.

---

## Core philosophy

> **Trend tools are a "pre-stocked material library", not the "main menu".**
>
> - The user is **introspecting** (telling their own experience / thinking about motivation) → **don't call**, avoid contaminating with external info
> - The user is **finding material** (no idea / wants a batch / explicitly fetching trends) → **call**, route the data source by content_form
> - The user is **confirming an angle** (talked about a current-affairs topic) → **don't call proactively**, let the user decide whether to use external data for reference

Design purpose: protect cheat-seed's core thesis—"good content comes from the user's real experience, AI doesn't brainstorm out of thin air"—while not letting the "no idea at all" new creator deadlock.

---

## Trigger matrix (referenced by cheat-seed Phase 1)

| cheat-seed Mode | Call by default? | Trigger condition |
|---|---|---|
| **Mode A** (user gave a concrete experience/topic) | ❌ don't call by default | only when what the user talked about is itself current-affairs (contains a product name/person name/event name + a time word) + the user **actively agrees** |
| **Mode B** (direction not specific, asking "why") | ❌ **never call** | at this stage the user is introspecting, external material is noise |
| **Mode C** (no idea at all) | ✅ call by default | Mode C's core action is to lay out external material |
| `--batch N` | ✅ call by default | batch brainstorm must have an anchor |
| `/cheat-trends` explicit | ✅ call | the main entry, no explanation needed |
| `/cheat-recommend` | ❌ don't call by default | a pool already exists; unless the pool hasn't updated in >7 days → prompt to trends first |

---

## Current-affairs determination (for the Mode A gray scenario)

Let Claude judge, **don't write a regex whitelist**:

| Signal | Meaning |
|---|---|
| Contains a **proper noun** (person name / product name / event name) | strong signal—possibly current-affairs |
| Contains a **time word** ("today" / "just" / "recently" / "just happened") | strong signal |
| Contains a **structure word** ("compare" / "respond" / "event") | weak signal |
| Contains only generic nouns + personal-experience words ("I" / "yesterday" / "my colleague") | counter-signal—it's an evergreen personal experience, **not current-affairs** |

Determination result:
- **strong signal** → ask the user "want to pull this topic's opinion climate for reference"
- **weak signal / ambiguous** → don't ask proactively, go straight into Mode A deep dive
- **counter-signal** → 100% don't call

Consistent with the "soft rules, Claude judges" philosophy of [bump-validation-protocol.md](bump-validation-protocol.md).

---

## Data-source routing (by content_form)

[adapters/trend-sources/](../adapters/trend-sources/) currently has two first-class citizens + one fallback:

| Adapter | Suitable content_form |
|---|---|
| [`aihot`](../adapters/trend-sources/aihot.md) | `tutorial-builder` / AI-industry commentary / AI tutorials / AI product reviews |
| [`trendradar-mcp`](../adapters/trend-sources/trendradar-mcp.md) | `opinion-video` / `long-essay` / `short-text` / `podcast` / `other` (life/career/culture) |
| `manual-paste` | the eternal fallback—the user pastes a URL/title list |

### content_form → primary + secondary call matrix

| content_form | Primary | Secondary | Don't call |
|---|---|---|---|
| `opinion-video` | trendradar-mcp | aihot (only when the topic relates to the AI industry) | — |
| `long-essay` | trendradar-mcp | aihot (as above) | — |
| `short-text` | trendradar-mcp | aihot (as above) | — |
| `podcast` | trendradar-mcp | aihot (as above) | — |
| `tutorial-builder` | **aihot** | trendradar-mcp (only when it involves a generic tool/product launch) | — |
| `mixed` | call both | — | Claude judges which vertical each candidate belongs to |
| `other` (food/makeup/story/...) | trendradar-mcp | — | aihot (unrelated to AI) |

### User-layer override

The `enabled_trend_sources` field of `.cheat-state.json` is the **explicit switch**:

```json
"enabled_trend_sources": ["aihot", "trendradar-mcp", "manual-paste"]
```

Only those in the array get called. Empty array → only manual-paste.

When cheat-trends is called explicitly, it supports override: `/cheat-trends — sources: aihot` (use aihot only this time).

---

## Failure-downgrade chain

```
[cheat-seed Mode C triggers a trend pull]
  ↓
[choose the primary by content_form]
  ↓
  ├─ primary succeeds → get data → enter the flow
  ├─ primary fails (API down / MCP not installed / timeout)
  │   ↓
  │   [choose the secondary by content_form]
  │   ├─ secondary succeeds → get data → tell the user "the primary was unavailable, used the secondary"
  │   └─ secondary also fails → fall back to manual-paste
  │       ↓
  │       [ask the user: "anything you saw today worth making? Paste a few URLs/titles for me"]
  └─ the user currently has no source enabled → prompt how to enable + use manual-paste directly this time
```

**Key discipline**: all failures **don't throw**. cheat-seed always runs—the only difference is whether there's external material.

---

## Token-cost awareness

Trend API calls **have a cost** (aihot is tokens / trendradar-mcp is an MCP call + LLM context). Determination principles:

| Scenario | Call frequency |
|---|---|
| Mode C triggered | at most 1 per session (cache the data in memory after fetching) |
| Mode A gray scenario | only call with the user's agreement, 1 time |
| `--batch N` | 1 call to get enough candidates |
| User keeps saying "another batch" | the second time is allowed, the third time prompt "want to change the query angle" |

Don't repeatedly call the same endpoint in the same session—that's a waste.

---

## Relationship with candidates.md

The data the trend tools pull back **ultimately lands in** the `candidates.md` defined by [candidate-schema.md](candidate-schema.md):

```
[trend tool] → items
  → dedup (vs candidates.md / predictions/ / .cheat-cache/trends-history.jsonl)
  → rough score (cheat-seed inline rubric)
  → write into candidates.md (with a source field indicating which adapter it came from)
```

After cheat-seed Mode C gets the data it **doesn't** go straight into brainstorm; it first enters candidates.md, then lets Claude pick from the pool. This way the data is traceable and reusable by later cheat-recommend.

---

## Extension guide for maintainers

To add a trend source:

1. Write `adapters/trend-sources/<name>.md`, following the format of the existing aihot.md / trendradar-mcp.md
2. Add a row in the "data-source routing" section of this file—clarify the content_form that adapter suits
3. No need to change cheat-seed's internal logic—it auto-enables per `enabled_trend_sources`
4. Mark MINOR in the CHANGELOG

Don't hardcode "aihot"/"trendradar-mcp" into cheat-seed's SKILL.md—keep the adapter model extensible.
