---
name: cheat-init
description: The first-time onboarding and scaffolding creator for pattern-first. Unified flow—all users go through the same 5-phase loop; the only difference is that someone "who has published videos" gets one extra step at init: fetching existing videos to build historical context (used later by cheat-seed for more tailored topics and a more accurate baseline). Triggers: "init" / "first use" / "I'm a new user" / "setup pattern-first". **Must run on the user's first session; other sub-skills auto-route here when .cheat-state.json doesn't exist.**
argument-hint: [— form: opinion-video|long-essay|short-text|podcast]
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-init — first-time onboarding

Take the user from zero to running their first prediction, in ≤ 5 minutes (no prior history) or ≤ 10 minutes (has published, importing history).

## Overview

```
[user says "init" for the first time]
  ↓
[Phase 0: detect current state]
  ↓
[Phase 1: first-screen copy — applicability + expectation management]
  ↓
[Phase 2: 6 questions (Q1-Q5 all asked; Q2 decides whether to go the user-history import path)]
  ↓
[Phase 2.5: benchmark account — strongly recommended (cold-start must ask, published users optional)]
  ↓
[Phase 3: create scaffolding (incl. scripts/ + videos/ + samples/ empty dirs + template files incl. benchmark.md)]
  ↓
[Phase 3.5: user-history import flow (only Q2=has published + user agrees)]
  ↓
[Phase 4: test whether the hook works]
  ↓
[Phase 5: give the "what to say next" checklist]
```

## Constants

- **DEFAULT_RETRO_WINDOW_DAYS = 3**
- **INSTALL_HOOKS = ask** — ask by default; user chooses `auto` to install directly; `skip` to not install
- **TREND_DEFAULT_SOURCES = ["manual-paste"]**

## Inputs

None. All info is collected from the 6 conversation questions.

## Workflow

### Phase 0: detect current state

1. Read the user's current working directory (**the user's content project, not pattern-first itself**)
2. Check whether `.cheat-state.json` already exists:
   - exists → prompt "the project seems already initialized (state file exists). Re-initializing will overwrite the existing config—confirm?" Only continue after the user explicitly confirms
   - doesn't exist → proceed to Phase 1
3. Check whether core files like `rubric_notes.md` / `predictions/` already exist—exist but state file doesn't → it's a "half-initialized" state, prompt the user and ask "infer state from the existing files or reset?"

### Phase 1: state expectations plainly first-screen (incl. applicability check)

Output to the user (verbatim, don't soften):

```
🎯 Pattern First — initialization

Your next piece is already rewriting the you of 3 months from now.
The pattern objectively exists; the difference is whether you **see** it or not.
This lets you see it.

Over the next 5-10 minutes I'll ask 5-6 questions to figure out what you make, what you have, and how you'll use it.
Two things up front:

1. **Early predictions will be inaccurate**—the first 5 pieces are at roughly ±50% precision, a mathematical fact.
   The tool marks the confidence level with 🔴🟠🟡🟢🔵, hides no numbers—
   you judge for yourself whether to trust each one.

2. **Strongly recommend importing a benchmark account**—5-10 benchmark videos and the tool has an anchor immediately.
   Otherwise the first batch of predictions is basically astrology. Q5 will ask again.

Ready to start?
```

If the user answers "continue" or a similar affirmative → Phase 2.
No longer refusing to continue based on content_form—any format is allowed, just with the `rubric_form_mismatch` field marked true, and cheat-status will keep prompting the user "your format needs a bump to adjust weights".

### Phase 2: 6 questions (one at a time, **don't** batch-ask)

**Q1: content form**

> "Which is your content closest to?
> a) **Opinion video** (commentary / current-affairs / argumentation / issue discussion / personal opinion) — directly matches the built-in rubric
> b) **Long-form essay** (WeChat official account / Substack / Medium) — can bootstrap from the opinion-video rubric, adjust weights at bump
> c) **Short-form / thread** (X / Weibo / Jike) — same as above
> d) **Podcast / long-form video** (long YouTube / podcast) — same as above
> e) **Tutorial / tool teaching / Builder** (teaching others how to use tool X / how to build project Y) — same as above
> f) **Other** (gaming / food / makeup / news / story) — the workflow is universal, but the rubric dimensions need adjusting
>      (the ER / SR / HP set may not predict well for your format; you need to derive dimensions that fit)
> g) **Mixed**"

Record to `content_form` + `rubric_form_mismatch`.

**Q1 → `content_form` enum mapping** (**must store the enum value, not the letter**):

| User answer | `content_form` value to write |
|---|---|
| a | `"opinion-video"` |
| b | `"long-essay"` |
| c | `"short-text"` |
| d | `"podcast"` |
| e | `"tutorial-builder"` |
| f | `"other"` |
| g | `"mixed"` |

`rubric_form_mismatch` derivation:
- choose a → `false`
- choose b/c/d/e/f/g → `true`, cheat-status keeps prompting "your format may need a bump to adjust weights"
- **No more "severe mismatch" tier**—all formats can run the workflow, just some rubrics need a more aggressive bump

**Q1.5: typical duration** (only when Q1=a/d/f)

> "Your video's typical duration?
> a) 30s-1min  b) 1-3min  c) 3-5min (recommended starting point)
> d) 5-10min   e) 10min+"

Record to `typical_duration_seconds` (30 / 90 / 240 / 450 / 900).

**Q1.6: publish frequency**

> "How often do you plan to publish?
> a) daily   b) every other day   c) weekly   d) flexible / irregular (turn off buffer monitoring)"

Record to `target_publish_cadence_days` (1 / 2 / 7 / null).

**Q2: Has this channel published videos?**

> "a) Haven't published — I'll help you brainstorm 5 candidates from interests + trends + write 5 first drafts
>  b) Have published — whether 1 or 100, I'll fetch your history so later brainstorms fit what you've done"

If a → state writes `calibration_samples: 0`, **skip Phase 3.5**, go straight to Phase 4.
If b → proceed to **Q2.1**.

**Q2.1: platform + fetch plan** (only Q2=b)

> "Which platform is your content mainly on?
> a) Douyin — install the douyin-session adapter (Playwright + QR-code login to Douyin Creator Center)
> b) YouTube — install the youtube-data-api adapter (needs an API key)
> c) Bilibili — bilibili-stat adapter
> d) Other / multi-platform — use manual paste mode"

If a/b/c → ask Q2.2; if d → jump to Q2.3 manual.

**Q2.2: adapter install timing** (only Q2.1=a/b/c)

> "Install the adapter now for auto-fetch, or tell me manually first?
> - Install now — I'll guide you through Playwright + QR scan → fetch the recent N pieces of data
> - Install later — manual mode first, state marks 'pending_adapter_setup',
>            cheat-status keeps prompting to install"

If "install now" → go through the adapter install guide (see each adapter's README) → verify fetch works → Q2.3.
If "later" → jump to Q2.3 manual.

**Q2.3: fetch scope / history scale**

If the adapter is installed and verified:
> "How many of your recent pieces can I fetch as a baseline?
> (10-25 recommended; more samples = more accurate baseline. Up to your account's actual count)"
→ user gives a number N, Phase 3.5 fetches N

If manual mode:
> "Roughly how many have you published? A range is fine (e.g. '5-10' / '20+'),
>  this is only used to mark a calibration_samples estimate, no need to be exact."
→ user gives an estimate, Phase 3.5 skips fetching, calibration_samples writes the estimate

**Q3: data collection method**

> "How will you get data for the T+3 day retro?
>
> a) Manual paste — fallback. **You must paste the top 20+ comments (with like counts)**, not just the play count.
>    Comments are the real signal—a meme burst like 'she's different' can only be seen from comments;
>    the play count never tells you what content actually hit the audience.
> b) **[recommended default]** adapter auto-fetch — comments + data both required.
>    If you haven't installed an adapter now, that's fine, state marks 'pending_adapter_setup',
>    just install it before the first publish (cheat-status keeps reminding).
>    Install guide in adapters/perf-data/<platform>/README.md."

**Q3 → `data_collection` enum mapping**:

| User answer | `data_collection` value to write |
|---|---|
| a | `"manual"` |
| b (default) | `"adapter"` |

Default to b—unless the user explicitly says "a, I want it manual".

**Q4: candidate topics**

> "Do you have a candidate-topic list now? (e.g. maintained in external markdown / Notion)
> a) No (default) — I'll help you brainstorm in a bit, or use /cheat-trends daily to fetch
> b) Yes, a markdown list
> c) Yes, Notion / other"

**Q4 → `pool_status` enum mapping**:

| User answer | `pool_status` value to write |
|---|---|
| a (default) | `"none"` |
| b | `"markdown"` |
| c | `"notion"` |

**Q5: install a few hooks (installed by default, no decision needed from you)**

> "Q5: I'll install a few hooks while I'm at it, reply 'yes' or 'enter' to install:
>
> 1. **Prediction lock** — after we finish a prediction together, the file is locked. Neither you nor I can edit the prediction section.
>    The retro can only append to the lower half of the same file, not contaminating the upper-half judgment.
>    (Without this lock, seeing the data later and wanting to "fix the prediction" is nearly inevitable—you or I will do it)
>
> 2. **SessionStart auto-report** — at the top of every new session, show buffer / pending retros / top candidates
>
> 3. **Silent usage log** — asynchronously records usage frequency, non-blocking, for future diagnostics
>
> All three together. **You can also not install** (reply 'no') but you lose the prediction lock and calibration value drops.
>
> Reply yes / no."

**Q5 → `hooks_installed` mapping**:

| User answer | `hooks_installed` value to write |
|---|---|
| yes / enter / default | `true` (bool, **not the string `"yes"`**) |
| no | `false` |

Default yes—unless the user explicitly says no.

### Phase 2.5: benchmark account (**ask all users**, cold-start strongly recommended)

> The tool's most important early signal source is the **benchmark account**—right after init you have no data, and the equal-weight v0 rubric is astrology.
> But if you can find an account you want to become like, and import 5-10 of its high / medium / low samples, the tool has an anchor.

Ask:

```
🎯 Benchmark account

Can you find a benchmark account? At least 3 videos from that account.

  - You **have never published** (Q2=a/b) → **strongly recommended**—the rubric has no anchor and relies entirely on the benchmark.
    Without one, you use the generic v0 equal-weight rubric, and the first 5 predictions are worse and stay worse longer
  - You **have history** (Q2=c) → **optional**—you can calibrate from your own history alone;
    but importing at least 1 benchmark for a sanity check is recommended (to see whether your account really deviates from the benchmark's direction)

a) Find one now → immediately enter /cheat-learn-from (5-15 minutes, depending on material readiness)
b) Find one later → state marks `benchmark_status: pending`, cheat-status keeps reminding
c) Don't → state marks `benchmark_status: none`, start with the generic v0

Reply a / b / c.
```

Behavior:
- choose a → after Phase 3 finishes creating the scaffolding, **auto-dispatch to /cheat-learn-from** (don't make the user run it manually—it's already in the init flow). After finishing, return to init Phase 4
- choose b → state marks `benchmark_status: pending` + `benchmark_name: null`
- choose c → state marks `benchmark_status: none`

Record to `benchmark_status` / `benchmark_name` (if a is chosen, written inside cheat-learn-from).

### Phase 3: create scaffolding (explain each item)

Create in order and **explain each item's purpose**:

1. **`.cheat-state.json`**
   ```
   "Creating .cheat-state.json — the place sub-skills share context.
    All the answers collected this init are written here."
   ```
   Write (**all `<...>` placeholders must be replaced with the concrete enum value per the Q mapping tables above, never store the letter directly**):
   ```json
   {
     "schema_version": "1.4",
     "skill_version": "1.0.0",
     "rubric_version": "v0",
     "content_form": "<look up Q1 mapping, write the enum string like \"opinion-video\">",
     "typical_duration_seconds": <Q1.5 derived: 30/90/240/450/900>,
     "target_publish_cadence_days": <Q1.6 derived: 1/2/7/null>,
     "rubric_form_mismatch": <Q1=a→false; else→true>,
     "benchmark_status": "<Phase 2.5 derived: a→\"imported\"/b→\"pending\"/c→\"none\">",
     "benchmark_name": <string name if imported, else null>,
     "benchmark_sample_count": <number if imported, else 0>,
     "baseline_plays": null,
     "calibration_samples": <Q2=a→0; Q2=b→Phase 3.5 import backfill or Q2.3 estimate>,
     "data_collection": "<look up Q3 mapping, write \"manual\" or \"adapter\">",
     "pool_status": "<look up Q4 mapping, write \"none\"/\"markdown\"/\"notion\">",
     "data_layer": "markdown",
     "hooks_installed": <look up Q5 mapping, write bool true/false>,
     "enabled_trend_sources": ["manual-paste"],
     "enabled_perf_adapters": <Q2.1=a→[\"douyin-session\"]; b→[\"youtube-data-api\"]; c→[\"bilibili-stat\"]; else→[]>,
     "last_bump_at": null,
     "last_bump_self_audited": false,
     "last_published_at": null,
     "last_published_file": null,
     "last_retro_at": null,
     "last_trends_run_at": null,
     "last_trends_added_count": 0,
     "last_prediction_self_scored": false,
     "last_self_scored_at": null,
     "consecutive_directional_errors": [],
     "pending_retros": [],
     "shoots": [],
     "in_progress_session": null,
     "initialized_at": "<local ISO 8601 with timezone, e.g. \"2026-05-05T20:11:13+08:00\", **don't use the UTC Z suffix**>"
   }
   ```

2. **`rubric_notes.md`**
   ```
   "Creating rubric_notes.md — the source of truth for your scoring dimensions.
    Using the v0 placeholder rubric—equal-weight 7 dimensions (each dimension equally important).

    Why it's called v0: v0 is the placeholder before calibration. Your account's real weights
    must be reverse-engineered from your data, not preset. After running 5 pieces with data, it
    will auto-propose an upgrade to 'calibrated v1' (your first truly calibrated rubric).

    ⚠️ rubric_notes.md is a whitelist file for the blind sub-agent (channel B)—
    it can only contain generic language (formula / dimension definitions / bucket boundaries), not real video names / actuals.
    The Memo at each bump upgrade (with evidence data + derived evidence) goes into rubric-memo.md (created next step)."
   ```
   - Copy `pattern-first/starter-rubrics/<form>-zero.md` (cold-start) or `<form>.md` (still usable as a reference when you have data)

2.5. **`rubric-memo.md`** (**new**—to support the cheat-score-blind isolation protocol)
   ```
   "Creating rubric-memo.md — the bump-upgrade Memo accumulation archive.
    This is where cheat-bump Phase 5 writes the full Memo (with real video names + actuals + derived evidence).

    Why a separate file: the blind sub-agent's whitelist is rubric_notes.md;
    historically, writing the bump Memo into rubric_notes.md let the blind sub-agent get actuals data
    through the whitelist that it shouldn't see—this file is the isolation fix; the sub-agent is hard-forbidden from reading it.

    It's empty now, waiting to append the first Memo after the first cheat-bump upgrade."
   ```
   - Copy `pattern-first/templates/rubric-memo.template.md` → `<user-repo>/rubric-memo.md`

3. **`script_patterns.md`**
   ```
   "Creating script_patterns.md — your writing-pattern accumulation (decoupled from the rubric).
    rubric_notes.md teaches Claude how to score;
    script_patterns.md teaches Claude how to write."
   ```
   - Copy `pattern-first/templates/script_patterns.template.md`

4. **Four directories**: `scripts/` + `predictions/` + `videos/` + `samples/` (all with `.gitkeep`)
   ```
   "Creating four directories:

    scripts/      — pre-shoot drafts (written by cheat-seed or you)
    predictions/  — immutable prediction logs (hook-protected)
    videos/       — post-shoot working dir (cheat-shoot creates subdirs)
    samples/      — benchmark account videos / transcripts (cheat-learn-from creates subdirs)

    The first three are interlinked by the same <date>_<id>_<short> naming.
    samples/ is grouped by benchmark account name: samples/<account-name>/<video-id>/."
   ```

4.5. **`benchmark.md`** (only when Phase 2.5 chooses a/b)
   ```
   "Copying the benchmark.md placeholder template (actual content filled by cheat-learn-from)—
    this is the central reference for your benchmark account.
    Early on the tool derives a lot of its rubric / pattern / topic direction from here;
    later after N≥10 the influence fades, but it's kept as a sanity check."
   ```
   - Copy `pattern-first/templates/benchmark.template.md` → `<user-repo>/benchmark.md`
   - **Phase 2.5 choosing c doesn't create it** → benchmark.md doesn't exist, state marks `benchmark_status: none`

5. **`WORKFLOW.md`** + **`STATUS.md`**
   - Copy the corresponding files from templates/

6. **If Q5=yes → install hooks**
   - Read `.claude/settings.json` (if it doesn't exist, create an empty `{}`)
   - Merge in `hooks/prediction-immutability.json`'s `hooks.PreToolUse`
   - Merge in `hooks/session-start.json`'s `hooks.SessionStart`
   - Merge in `hooks/meta-logging.json`'s hooks (if also enabled)
   - Copy `prediction-immutability.sh` + `session-start.sh` + `log-event.sh` to `.cheat-hooks/`, chmod +x
   - The command paths in settings.json use `${CLAUDE_PROJECT_DIR}/.cheat-hooks/`

7. **(Pool option c—Notion)** Only record `pool_status: notion` in the state file, to be handled when cheat-trends is later called

### Phase 3.5: import flow (only Q2=b and the user agrees to fetch)

If Q2.2=install now → go through adapter install + login (see [adapters/perf-data/<platform>/README.md](../../adapters/perf-data/)).

After a successful fetch, for each published video:

1. **Create the video folder**: `videos/<date>_<id>_<short>/`
   - `<date>` = the video's actual publish date
   - `<id>` = 12-char hash, sha256 of (title + platform ID)
   - `<short>` = the first 3-8 chars of the title
2. **Write report.md**: fill in the data fetched from the adapter (plays / likes / comments / shares / top comments)
3. **Ask the user for the original script**: "for video '{title}', did you keep the original script?"
   - yes → user provides → save as `videos/<id>/script.md`
   - no → mark `script_lost` (still create the video folder, just script.md is missing)
4. **Write a reconstructed prediction**: `predictions/<date>_<id>_<short>.md`
   - header marks `**Reconstructed retrospective — NOT a blind prediction**`
   - the 7-dim score is **reverse-scored** based on the script + retro-section actuals—clearly a non-calibration use
   - doesn't count toward calibration_samples (this is imported history, not calibration accumulation)

After import:
- derive `baseline_plays` = the median plays of the fetched videos → write into the state file
- derive the confidence level → used directly when cheat-predict later writes predictions
- output a summary: "imported N pieces of history. The most recent one X plays, median Y, created N video folders + reconstructed predictions"

### Phase 4: test whether the hook works (only when Q5=yes)

Run a fake Edit-interception test:
1. Create a temp file `predictions/_test_hook.md`, containing `## Prediction\n[test]\n## Retro\n`
2. Try to Edit this file's `## Prediction` section
3. The hook should exit 1 and block → report "✅ immutability hook works"
4. Delete the test file
5. SessionStart hook verification: call `bash .cheat-hooks/session-start.sh` once directly → should output a report (even an empty one is fine)

If the hook doesn't work → **don't pretend success**, clearly tell the user: "hook installation failed, possibly the .claude/settings.json config didn't take effect. Recommend checking manually or restarting Claude Code."

### Phase 4.5: if Phase 2.5 chose a → dispatch to /cheat-learn-from

If the user chose a in Phase 2.5 (import a benchmark account now) → **auto-trigger /cheat-learn-from**:

```
✅ Scaffolding + hooks installed.

Now immediately entering /cheat-learn-from to help you import the benchmark account—
you chose "find one now" at init, so we won't make you open another session.

[invoke /cheat-learn-from]
```

After cheat-learn-from finishes, return to init's Phase 5.

If Phase 2.5 chose b/c → skip Phase 4.5, go straight to Phase 5.

### Phase 5: give the "what to say next" checklist

```
✅ Initialization complete (rubric: v0, calibration_samples: <N>, confidence: <emoji level>)

Next time you can just say these:

📝 Finished a draft → "score this scripts/<...>.md"
🎯 Before publishing → "start prediction scripts/<...>.md"
🎬 Finished filming → "shot scripts/<...>.md" → create video folder + buffer +1
🚀 After publishing → "shipped https://..."
📊 T+3 days → "retro videos/<...>/"
📈 Anytime → "status" (see the full dashboard)

<if Q4=no candidate topics:>
🌱 Run /cheat-seed now to find topics?
   - No prior history: pure brainstorm (interests × trends)
   - Has history (already imported): the brainstorm recommends based on what you've done before
   Reply "yes, seed" to run now, "no" to think yourself.

💡 Your confidence is <current level> — it auto-rises as you run more retros.
   Don't skip prediction because confidence is low—the discipline of prediction is itself the tool's core;
   the "value" of early predictions is data collection, not decision-making. After the 5th retro the rubric calibrates for the first time,
   and confidence crosses into 🟡 fairly low; after the 10th, 🟢 medium.
```

## Key Rules

1. **Don't pretend success**: any step failing → clearly tell the user which step errored. Never write "✅ init complete" if it isn't actually complete
2. **Don't batch-ask**: ask the 5 questions one at a time
3. **Don't silently mkdir**: explain the purpose of each file as you create it
4. **Don't push SQLite**: give all users markdown, a single line "we'll suggest upgrading at 30 pieces later" is enough
5. **Unified state fields**: removed enum fields like mode / prediction_complexity / bucket_scheme—use a single calibration_samples integer + confidence derivation
6. **Import failure doesn't block**: Q2=b but adapter install fails / fetch fails → gracefully degrade to "mark the calibration_samples estimate, don't import historical video folders"

## Refusals

- "Skip Q1-Q5, just create all the files for me" → refuse. The answers directly affect default config (content_form, cadence, hooks)
- "I already initialized elsewhere, sync that project's config over" → be cautious. Tell the user to manually cp the existing `.cheat-state.json` and `rubric_notes.md`; don't auto-sync across projects
- "Don't install the hook but keep the immutability promise" → allowed, state marks `hooks_installed: false`, cheat-status keeps prompting "your immutability is a gentleman's agreement"

## Integration

- After writing, the main SKILL.md's routing unlocks all other sub-skills
- `cheat-status` reads the `calibration_samples` field of `.cheat-state.json` to decide which confidence level to show
- If Q2=b went through import → the historical reconstructed predictions go into `predictions/` and `videos/<...>/`, but **don't** count toward calibration_samples (not real calibration samples)
- `/cheat-seed` reads all historical reconstructed predictions in `predictions/` → knows "what the user has done before" when brainstorming

## State field write checklist

| Field | Write timing | Source |
|---|---|---|
| `schema_version` | Phase 3 | hardcoded "1.1" |
| `skill_version` | Phase 3 | hardcoded "1.0.0" |
| `rubric_version` | Phase 3 | "v0" |
| `content_form` | Phase 3 | Q1 → look up the mapping table for the enum value (**not the letter**) |
| `typical_duration_seconds` | Phase 3 | Q1.5 derived |
| `target_publish_cadence_days` | Phase 3 | Q1.6 derived |
| `rubric_form_mismatch` | Phase 3 | Q1≠a → true |
| `benchmark_status` | Phase 3 / 2.5 | derived from the Q2.5 answer |
| `benchmark_name` | Phase 3 / 2.5 | provided by the user at Q2.5 |
| `benchmark_sample_count` | Phase 3 / 2.5 | backfilled after cheat-learn-from import |
| `baseline_plays` | Phase 3.5 (if import succeeds) | median of imported data; else null |
| `calibration_samples` | Phase 3 / Phase 3.5 | Q2=a→0; Q2=b→Q2.3 estimate or import count |
| `data_collection` | Phase 3 | Q3 → look up the mapping table for the enum value |
| `pool_status` | Phase 3 | Q4 → look up the mapping table for the enum value |
| `enabled_perf_adapters` | Phase 3 | Q2.1 derived (if Q2=a then `[]`) |
| `hooks_installed` | Phase 3-4 | Q5 → bool (not a string) |
| `last_bump_at` / `last_published_at` / `last_published_file` / `last_retro_at` / `last_trends_run_at` | Phase 3 | all `null` |
| `last_bump_self_audited` | Phase 3 | `false` |
| `last_trends_added_count` | Phase 3 | `0` |
| `last_prediction_self_scored` | Phase 3 | `false` |
| `last_self_scored_at` | Phase 3 | `null` |
| `initialized_at` | Phase 3 | now() local ISO 8601, with `+08:00` timezone, **not UTC `Z`** |
