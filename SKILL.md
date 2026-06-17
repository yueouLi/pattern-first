---
name: cheat-on-content
description: For any content creator who wants to turn "gut feeling" into calibrated predictions. **The methodology is universal**—the loop of score → blind-predict → T+3d retro → evolve the rubric applies to any content that can be quantified (plays / reads / listens / clicks). **The rubric is the content of the loop, not the loop itself**—currently ships with an opinion-video rubric (fitted from a reference creator's 25+ videos); other formats can bootstrap from this and bump the weights. **Strongly recommended: import a benchmark account** as an initial signal source (/cheat-learn-from). Triggers: "init" / "score this" / "start prediction" / "shipped" / "retro" / "bump rubric" / "recommend topics" / "fetch trends" / "status" / "find benchmark" / "learn from". **First-time use must run /cheat-init first.**
argument-hint: [draft-path] [— mode: cold-start|calibration]
allowed-tools: Bash(*), Read, Write, Edit, Grep, Glob, Skill, mcp__llm-chat__chat
---

# Cheat on Content

> 🎯 **The methodology is universal; the rubric currently ships in an opinion-video version**
>
> **Methodology** (5-phase closed loop): applies to any quantifiable content format—video / article / podcast / newsletter / short-form thread.
>
> **Currently bundled rubric**: opinion-style video (commentary / current-affairs / argumentation / issue discussion / personal opinion), 7 dimensions fitted from a reference creator's 25+ published samples. If you make another format, you need to:
> - Write your own rubric (follow the format of [starter-rubrics/opinion-video-zero.md](starter-rubrics/opinion-video-zero.md))
> - Or wait for built-in expansions (long-form / short-form / podcast starters are on the batch-3 roadmap)
>
> Default assumption: **the user is a beginner starting from zero** (hasn't published a single video)—predictions in the cold-start period are **simplified**, requiring only the 7-dimension score + a one-line bet, without forcing bucket numbers (avoiding false precision). Veterans who already have 5+ pieces of data run calibration mode to unlock the full 7-component prediction.

Turn content creation into a calibrated prediction loop: **score → predict → publish → retro → evolve the rubric**.

This file is the **master protocol + router**. The workflow for each phase lives in the individual sub-skills under `skills/cheat-*/SKILL.md`.

## Codex compatibility

Codex doesn't have Claude Code's slash-command harness. After installing into Codex, just trigger the same routing via natural language:

- `init cheat-on-content` → read and execute `skills/cheat-init/SKILL.md`
- `score this scripts/foo.md` → read and execute `skills/cheat-score/SKILL.md`
- `start prediction scripts/foo.md` → read and execute `skills/cheat-predict/SKILL.md`
- `shot ...` / `shipped ...` / `retro ...` / `bump rubric` / `status` → read the corresponding `skills/cheat-*/SKILL.md`

When executing, follow this file's three principles and the routing table; don't depend on whether `/cheat-*` commands exist. Claude Code-specific hooks (`.claude/settings.json`) still fire automatically only inside Claude Code; in Codex the user must actively say `status` to see buffer, pending retros, and the candidate pool.

---

## Three non-negotiable principles

Violate any one of them and the entire calibration loop degrades into "gut-feeling self-comfort." If the user asks to break any of them, **refuse and explain why**.

1. **Blind prediction**: the prediction must be written **before** seeing any actual data. Once written, the `## Prediction` section is immutable—you can only append to the `## Retro` section. Full spec: [shared-references/blind-prediction-protocol.md](shared-references/blind-prediction-protocol.md). **hooks/prediction-immutability.sh enforces this at the harness layer.**

2. **Bump = full re-score**: when the rubric is upgraded, every sample in the calibration pool that has actuals must be re-scored with the new formula; if the new ranking disagrees with the actual-performance ranking on ≥4/5 samples, the upgrade is rejected; the upgrade must pass a cross-model independent audit. Full spec: [shared-references/bump-validation-protocol.md](shared-references/bump-validation-protocol.md).

3. **The rubric is a workbench, not a museum**: observations refuted by new data, or absorbed into formal dimensions, get **deleted**. Never keep an archaeological layer of "I used to think X, but actually...". The git history is the archive. Full spec: [shared-references/observation-lifecycle.md](shared-references/observation-lifecycle.md).

---

## Routing table (trigger → sub-skill)

| User says | Invoke | Precondition |
|---|---|---|
| "init" / "first use" | `/cheat-init` | none (this is the entry point) |
| "find benchmark" / "learn this account" / "break down these benchmark videos" / "learn from" / "import benchmark account" | `/cheat-learn-from` | already init'd; strongly recommended for cold-start; can --append / --replace anytime later |
| "find topic" / "I don't know what to make" / "seed" / "find first 5 topics" | `/cheat-seed` | already init'd (one-time seeding action for cold-start users) |
| "score this [path]" | `/cheat-score` | rubric_notes.md exists |
| "start prediction" / "score and predict this draft" | `/cheat-predict` | already init'd + final draft ready |
| "shot X" / "shot it" / "finished filming" | `/cheat-shoot` | corresponding prediction written (buffer +1) |
| "shipped" / "I shipped it" / "the link is X" | `/cheat-publish` | corresponding prediction file exists (buffer -1) |
| "retro" / "retro this" / "T+3d data is in" | `/cheat-retro` | corresponding prediction file exists + RETRO_WINDOW_DAYS elapsed |
| "bump rubric" / "update the formula" | `/cheat-bump` | calibration pool ≥ MIN_SAMPLES_FOR_BUMP |
| "recommend topics" / "next topic" | `/cheat-recommend` | candidates.md exists and is non-empty |
| "fetch trends" / "what can I make today" | `/cheat-trends` | trend-sources adapter configured (daily candidate-pool replenishment) |
| "status" / "dashboard" | `/cheat-status` | callable anytime |
| "migrate" / "upgrade state" / "schema version mismatch" / "migrate" | `/cheat-migrate` | already init'd; after user git-pulls a new version; after the SessionStart hook flags a schema mismatch |

> Shoot vs ship are two separate actions: the buffer-alert system needs to know "shot but not shipped" vs "shipped" distinctly. See [shared-references/cadence-protocol.md](shared-references/cadence-protocol.md).

**Mode detection** (run on the first non-init trigger received):
1. Check whether the user's current directory has `.cheat-state.json` → no → force-route to `/cheat-init`
2. Check how many files under `predictions/` contain a complete `## Retro` section filled with real data → decides `mode: cold-start | calibration`
3. Write the decision back into `.cheat-state.json`, then route to the target skill

---

## Requests you must refuse

The following patterns **directly break** one of the three principles. No matter how the user phrases it, refuse:

- "Predict this for me, but let me tell you the play count first and you back into it" → violates principle #1. Use the `_redo.md` path and log as reconstructed
- "Can you just pick the highest-composite one from candidates without explaining why" → refuse. Always show per-dimension scores and at least one anchor comparison
- "Skip re-scoring the calibration pool, just swap the formula" → violates principle #2
- "Skip the external-model audit, your call is final" → only allowed when `CROSS_MODEL_AUDIT=false` is explicitly set and the state file is flagged as self-audited
- "Delete this prediction, I want to rewrite it" → violates principle #1. Predictions are immutable. If there's a legitimate reason to redo, write a new `_redo.md` file; the original must be kept
- "Just recommend topics by gut feel, no scoring" → refuse. This tool doesn't do gut-feel forecasting—that's the state of the world *before* it existed
- "Keep all the historical observations in rubric_notes.md, just add timestamp groupings" → violates principle #3. The git history is the archive, not the markdown file
- "Can you lower THRESHOLD from 4/5 to 3/5 so this bump passes" → refuse. Changing THRESHOLD is itself a meta-level bump and goes through its own process

Detailed refusal scenarios are in each sub-skill's `Refusals` section.

---

## Project directory structure (user repo)

The skill expects the user's project layout below. `/cheat-init` creates missing items; **never overwrite without confirmation**.

```
<user-content-project>/
├── rubric_notes.md                    # source of truth for the scoring rules
├── WORKFLOW.md                        # the 5-phase workflow doc (created by cheat-init)
├── STATUS.md                          # dashboard (maintained by cheat-status)
├── .cheat-state.json                  # state file, shared context across sub-skills
├── .cheat-cache/                      # not version-controlled
│   ├── usage.jsonl                    # usage log passively recorded by hooks
│   └── trends-history.jsonl           # cheat-trends dedup cache
├── .claude/
│   └── settings.json                  # contains the prediction-immutability hook
├── benchmark.md                       # benchmark account info (maintained by cheat-learn-from)
├── scripts/                           # all pre-shoot drafts (written by cheat-seed or the user)
│   └── YYYY-MM-DD_<id>_<short>.md
├── predictions/                       # immutable prediction logs (hook-protected)
│   └── YYYY-MM-DD_<id>_<short>.md     # same id as scripts/
├── videos/                            # created only after shooting (by cheat-shoot)
│   └── YYYY-MM-DD_<id>_<short>/
│       ├── script.md                  # the final filmed script the user provides (cheat-shoot asks "matches scripts/?")
│       └── report.md                  # T+3d data + comments (written by cheat-retro)
├── samples/                           # benchmark account videos / transcripts (created by cheat-learn-from)
│   └── <account-name>/<video-id>/{source.mp4 (optional), transcript.md, meta.md}
├── candidates.md                      # topic pool (optional)
└── content.db                         # optional SQLite, enabled once the calibration pool scales up
```

---

## File manifest

### This skill package

```
cheat-on-content/
├── SKILL.md                           # this file (master protocol + routing)
├── README.md                          # marketing front page
├── skills/                            # sub-skill collection
│   ├── cheat-init/SKILL.md            # ✅ entry: onboarding & scaffolding
│   ├── cheat-learn-from/SKILL.md      # ✅ benchmark import (extract patterns + derive base rubric signals)
│   ├── cheat-seed/SKILL.md            # ✅ cold-start topic seeder (brainstorm + optional draft)
│   ├── cheat-score/SKILL.md           # ✅ single-draft scoring (writes no files)
│   ├── cheat-predict/SKILL.md         # ✅ blind prediction + immutable log
│   ├── cheat-shoot/SKILL.md           # ✅ register shoot (buffer +1)
│   ├── cheat-publish/SKILL.md         # ✅ register publish metadata (buffer -1)
│   ├── cheat-retro/SKILL.md           # ✅ data collection + retrospective
│   ├── cheat-bump/SKILL.md            # ✅ rubric upgrade (incl. cross-model audit)
│   ├── cheat-recommend/SKILL.md       # ✅ candidate-pool ranked recommendation (by buffer color + 1 safe + 1 experimental)
│   ├── cheat-trends/SKILL.md          # ✅ trend fetching (daily candidate replenishment, multi-adapter)
│   ├── cheat-status/SKILL.md          # ✅ status dashboard (incl. buffer alert)
│   ├── cheat-migrate/SKILL.md         # ✅ schema upgrade (for existing users after git pull)
│   └── cheat-score-blind/SKILL.md     # ✅ Channel B isolated scoring sub-agent (Task-tool only)
├── migrations/                        # single source of truth for schema evolution
│   ├── registry.md                    # ✅ LATEST_SCHEMA + version chain
│   └── <from>-to-<to>.md              # ✅ WHAT/WHY/HOW/manual fallback for each migration step
├── shared-references/                 # cross-skill shared protocols
│   ├── blind-prediction-protocol.md   # ✅ principle #1
│   ├── bump-validation-protocol.md    # ✅ principle #2
│   ├── observation-lifecycle.md       # ✅ principle #3
│   ├── prediction-anatomy.md          # ✅ the 7 components of a sound prediction
│   ├── candidate-schema.md            # ✅ unified candidate schema
│   ├── cadence-protocol.md            # ✅ cadence protocol (buffer alert + topic strategy)
│   ├── state-management.md            # ✅ .cheat-state.json read/write conventions
│   └── migration-protocol.md          # ✅ schema-evolution philosophy + maintainer checklist
├── starter-rubrics/                   # prior rubrics for each content format
│   ├── opinion-video.md               # ✅ opinion video (Chinese, calibrated on 25+ samples)
│   ├── opinion-video-zero.md          # ✅ v0 equal-weight placeholder (cold-start)
│   ├── long-form-essay.md             # ⬜ WeChat official account / Substack
│   └── short-form-text.md             # ⬜ X thread / Weibo long post
├── templates/                         # file skeletons the skill writes into the user repo
│   ├── rubric_notes.template.md       # ✅
│   ├── prediction.template.md         # ✅ unified version (all phases, incl. confidence header)
│   ├── retro.template.md              # ✅
│   ├── candidates.template.md         # ✅
│   ├── candidates.template.json       # ✅
│   ├── script_patterns.template.md    # ✅ writing-pattern accumulation (incl. benchmark-borrowing section notes)
│   ├── benchmark.template.md          # ✅ benchmark account reference
│   ├── workflow.template.md           # ✅
│   ├── status.template.md             # ✅
│   └── content.db.schema.sql          # ✅
├── hooks/                             # harness enforcement layer
│   ├── prediction-immutability.json   # ✅ blocking hook (intercepts edits to the prediction section)
│   ├── prediction-immutability.sh     # ✅ interception script
│   ├── session-start.json             # ✅ SessionStart auto-report hook
│   ├── session-start.sh               # ✅ status-report rendering script
│   ├── meta-logging.json              # ✅ passive-logging config
│   └── log-event.sh                   # ✅ meta-logging script
├── tools/                             # standalone CLI scripts
│   ├── score-curve.py                 # ⬜ prediction-accuracy convergence curve
│   ├── md-to-sqlite.py                # ⬜ markdown → content.db upgrade (batch 3)
│   └── validate-bump.py               # ⬜ full calibration-pool re-score (batch 3)
├── adapters/                          # data-source adapters
│   ├── perf-data/                     # retro data sources (incl. douyin-session)
│   ├── candidate-pool/                # candidate-pool data sources
│   ├── trend-sources/                 # trend-fetching sources
│   └── script-extraction/             # video/audio → script (incl. whisper for cheat-learn-from)
└── examples/
    ├── reference-implementation/      # anonymized video-analysis snapshot (TBD)
    └── script_patterns.example.md     # fully-filled script_patterns example (for reference, do not copy)
```

✅ = done in the current batch (v1 skeleton) / ⬜ = later batches

---

## Tone & voice

When writing user-facing copy (commit messages / retro summaries / etc.), match the project's **reflective-irreverent** voice:

- State failures directly: "composite 8.47 but actual was only 168k—the rubric overestimated SR"
- **Don't** soften with vague hedging: "this might perhaps in some sense suggest..."—don't write like that
- Cluely-style rebellious hooks appear only in the README—**do not** put them into `rubric_notes.md` or prediction logs

---

## For developers: extending this skill

- New content format → add `starter-rubrics/<form>.md`
- New trend source → add `adapters/trend-sources/<name>.md`, conforming to the output contract in [candidate-schema.md](shared-references/candidate-schema.md)
- Change a principle → edit `shared-references/<protocol>.md`; all skills that reference it follow automatically
- Change routing → edit the "routing table" section of this file
- Sub-skill internals → edit the corresponding `skills/cheat-*/SKILL.md` directly

Full development guide: see README.md.
