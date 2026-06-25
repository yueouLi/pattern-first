# Workflow quick-reference (pattern-first)

> This is the quick-reference doc `/cheat-init` creates at your project root. The full spec is in pattern-first's `SKILL.md` and `shared-references/`.
> This file is for when you "forget what to say next"—you don't need to read it cover to cover.

---

## The flow in one breath

```
find a topic
  ├─ no prior history → /cheat-seed brainstorm (interests × trends)
  └─ has history       → /cheat-seed brainstorm (interests × trends × what you've done before)
                    (both run cheat-seed; the difference is the published one gets extra history context at brainstorm)
  ↓
cheat-seed writes 5 drafts to → scripts/<date>_<id>_<short>.md
  ↓
user rewrites scripts/<date>_<id>_<short>.md (overwrite the same file)
  ↓
/cheat-score scripts/<date>_<id>_<short>.md → see the rubric score (exploration)
  ↓
/cheat-predict scripts/<date>_<id>_<short>.md → write immutable prediction v1 to predictions/
  ↓
after filming → /cheat-shoot scripts/<date>_<id>_<short>.md
   ├─ create the videos/<date>_<id>_<short>/ directory
   ├─ ask the user: "does the script you actually used while filming match scripts/<id>.md?"
   │   ├─ matches → cp → videos/<id>/script.md, keep v1 prediction
   │   ├─ changed → ask for the final draft → compute diff
   │   │   ├─ diff ≥30% → auto /cheat-predict — mode: v2 → append `## Prediction v2` section to predictions/<id>.md
   │   │   └─ diff <30% → ask whether v2, default keep v1
   │   └─ heavily changed → use the _redo flow (new scripts/<id>_redo.md + re-run cheat-predict)
   └─ buffer +1
  ↓
publish → /cheat-publish + URL → buffer -1
  ↓
T+3 days → /cheat-retro videos/<date>_<id>_<short>/
   ├─ fetch data / user pastes → write videos/<id>/report.md
   ├─ append the ## Retro section to predictions/<id>.md
   ├─ diff scripts/<id>.md vs videos/<id>/script.md → learn the user's script-change pattern
   └─ write new observations into rubric_notes.md / script_patterns.md
  ↓
accumulated ≥3 same-direction deviations → /cheat-bump (upgrade the rubric)
```

---

## The five stages' trigger words

### ① Topic stage

| What you want | Trigger |
|---|---|
| see recommendations after candidates.md is ranked | "recommend topics" / "what should I make next" |
| fetch today's trends to expand candidates | "fetch trends" / "what can I make today" |
| see the current status | "status" |

> Having no candidates.md in cold-start is the default state—don't think the tool is broken because of this.

### ② Score + predict

| What you want | Trigger | Writes a file? |
|---|---|---|
| see a draft's rubric score (exploration) | "score this path/to/draft.md" | no |
| write a formal immutable prediction log for the final draft | "start prediction" or "start prediction for this draft path/to/draft.md" | yes (`predictions/...md`) |

> **The core difference between score and predict**:
> - score is exploration, side-effect-free, can be run repeatedly
> - predict is a commitment; once written, the `## Prediction v1` (or `## Prediction v2`) section is hook-locked

> **v2 re-judgment trigger**: when cheat-shoot detects the line-diff between the filmed script and the original scripts is ≥30%, it auto-calls cheat-predict to write the `## Prediction v2` section (append, doesn't overwrite v1). See the v1/v2 section convention in [shared-references/prediction-anatomy.md](../shared-references/prediction-anatomy.md).

### ③ Publish registration

Right after publishing:

```
"shipped https://..."
```

Or:

```
"shipped predictions/2026-05-04_xxx.md the link is https://..."
```

Updates the prediction file header's `published_at` / `Platform` / `URL`, and adds the file to the `pending_retros` queue.

### ④ Retro

After T+3 days (default):

```
"retro predictions/2026-05-04_xxx.md"
```

Or simply:

```
"retro"
```

The latter takes the earliest one from `pending_retros`.

> The retro needs you to provide data. The default is manual paste—paste "plays / likes / comments / shares" and the top 20 comments into the conversation.
> With an adapter configured, you can let cheat-retro auto-fetch.

### ⑤ Rubric upgrade (rare)

**Only proposed when conditions are met**:
- calibration pool ≥ 5 pieces
- ≥ 3 new calibrations since the last bump
- ≥ 3 consecutive same-direction deviations detected

If met, run:

```
"upgrade rubric --propose 'ER weight 1.5→2.0, add the MS dimension'"
```

A bump is a high-risk operation—it runs 5-step validation (including a cross-model independent audit). See `pattern-first/shared-references/bump-validation-protocol.md`.

---

## The three non-negotiable principles

> Violate any one of these → the entire calibration loop degrades into astrology.

1. **Blind prediction**: the prediction section is written before seeing any data, and is unchangeable once written. Enforced by the hook at the harness layer.
2. **Bump = full re-score**: a bump must re-score the entire calibration pool + a cross-model independent audit.
3. **The rubric is a workbench, not a museum**: delete observations absorbed / refuted. git history is the archive.

---

## Default config

The default values for a project created by `/cheat-init`:

| Setting | Default | When to change |
|---|---|---|
| `RETRO_WINDOW_DAYS` | 3 | change to 7 for long-form / slow platforms |
| `BLIND_CHECK` | strict | temporarily change to lenient for drills / tests |
| `MIN_SAMPLES_FOR_BUMP` | 5 | don't lower |
| `CROSS_MODEL_AUDIT` | true (if mcp__llm-chat__chat is configured) | false only when offline |
| `TREND_SOURCES` | ["manual-paste"] | add new sources via the `enabled_trend_sources` field |
| `POOL_PATH` | candidates.md | change the field when using Notion |

---

## Dashboard (the status command)

Say "status" anytime to output:
- current mode / rubric version / calibration sample count
- to-do (pending retros + same-direction-deviation warning + stale in-progress)
- candidate-pool size + days since the last trend fetch
- health (rubric_notes.md line count / whether hooks are installed / whether cross-model audit is configured)
- recommended next steps (by recommended priority)

---

## File structure (your project root)

```
<your-content-project>/
├── rubric_notes.md          # source of truth for the scoring rules
├── script_patterns.md       # writing-pattern accumulation
├── WORKFLOW.md              # this file
├── STATUS.md                # dashboard (maintained by cheat-status)
├── candidates.md            # candidate pool (optional; written by cheat-seed / cheat-trends)
├── .cheat-state.json        # state file (git tracked)
├── .cheat-cache/            # local cache (gitignored)
│   ├── usage.jsonl
│   └── trends-history.jsonl
├── .cheat-secrets.json      # API key / cookie (gitignored)
├── .cheat-hooks/            # copies of the hook scripts
│   ├── prediction-immutability.sh
│   ├── session-start.sh
│   └── log-event.sh
├── .claude/settings.json    # contains the pattern-first hooks
│
├── scripts/                 # **all pre-shoot drafts**
│   └── YYYY-MM-DD_<id>_<short>.md   # written by cheat-seed or the user
│
├── predictions/             # **immutable prediction logs** (hook-protected)
│   └── YYYY-MM-DD_<id>_<short>.md   # written by cheat-predict
│
└── videos/                  # **created only after shooting** (by cheat-shoot)
    └── YYYY-MM-DD_<id>_<short>/
        ├── script.md        # the final filmed script you provide
        └── report.md        # T+3d data (written by cheat-retro)
```

### The relationship of the three directories

| Directory | Stage | Content | Who writes |
|---|---|---|---|
| `scripts/` | pre-shoot draft | Claude AI draft or user-original | cheat-seed writes the first version; the user's rewrite is also in the same file |
| `predictions/` | prediction locked | the 7-component immutable log | written by cheat-predict |
| `videos/<id>/` | post-shoot artifacts | the final filmed script + T+3d data | cheat-shoot creates the dir; cheat-retro writes report.md |

The three use the same `<date>_<id>_<short>` naming; `<id>` is the first-12 sha256 of `scripts/<id>.md`'s first-written content, **unchanged on draft rewrite**.

`/cheat-init` auto-creates the above skeleton (doesn't overwrite existing).

---

## Stuck?

- See the "requests you must refuse" section of `pattern-first/SKILL.md`—what you want to do may be exactly what's designed to be refused
- See the corresponding sub-skill's `pattern-first/skills/cheat-X/SKILL.md`
- Run "status" to see cheat-status's "recommended next steps"
