# Changelog

All notable changes to cheat-on-content will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning follows [SemVer](https://semver.org/).

---

## [Unreleased]

### Fixed — cheat-seed wrote drafts in subtitle format (one sentence per line)

**Problem**: Users reported that the draft body cheat-seed wrote was in "one sentence per line" subtitle format rather than paragraph form. The root cause wasn't missing documentation—the "no subtitle format" instruction existed in 4 files, but **all as prose instructions**. At the moment of generating the draft, the model's "video script = teleprompter short lines" training prior overrode the single line of prose buried in Phase 4.

**Fix** (two-pronged):
- **A — suppress the prior at generation time**: the Phase 4 draft template block now adds a **concrete side-by-side comparison** of ❌ subtitle format / ✅ paragraph form, placed right next to the body placeholder—so at the moment of generation the eyes are on the example and the prior is anchored down
- **B — deterministic backstop after writing**: added a Phase 4.5a line-format self-check—compute the body's `avg_chars_per_line`; `< 15 chars AND line count ≥ 8` → judged subtitle format → auto-reflow into a 3–6 paragraph version. Doesn't rely on the model's self-awareness, relies on `awk`
- Phase 4.5 order fixed: **4.5a fix formatting first, then 4.5b humanizer** (the humanizer processes prose; feeding it broken lines causes chaos)
- The N drafts in batch mode also go through the Phase 4 format + Phase 4.5 self-check

### Added — cheat-seed Phase 4.5: humanizer self-check pass (de-AI-ify)

**Problem**: The cheat-seed first draft Claude writes naturally carries AI-writing tells—em-dash overuse, rule of three, inflated vocabulary, vague attribution, shallow -ing analysis. The starting point users got was heavily "machine-flavored."

**Change**: after the draft is written and before showing it to the user, add Phase 4.5—run it through the [`humanizer`](https://github.com/blader/humanizer) skill (MIT, external project, 18k stars) to strip AI tells.
- Only humanize the **body**, don't touch the "must rewrite" warning in the header (that's an intentional scaffolding marker)
- **voice calibration**: when historical scripts / `script_patterns.md` exist, pass them as reference samples—lean toward "the user's voice," not "generic human voice"
- Report which tells were fixed, shown in the Phase 5 output
- `HUMANIZE_DRAFT = on` by default; gracefully skip + hint how to enable when humanizer isn't installed
- **Doesn't contaminate calibration**: a cheat-seed draft is not the thing being predicted/published—cheat-predict scores the user's final draft; humanizing the first draft just gives a cleaner starting point
- **Doesn't rewrite for the user**: humanizer de-AI-ifying ≠ becoming the user's voice; the "must rewrite" warning still holds

humanizer is **not bundled** into cheat-on-content—the user `git clone`s it themselves to `~/.claude/skills/humanizer/`.

### Fixed — douyin-session runtime path privacy hole (@level5Ninja [#16](https://github.com/XBuilderLAB/cheat-on-content/pull/16))

**Problem**: the douyin-session adapter wrote `.auth/` (**containing the Douyin login cookie**), debug screenshots, and reports into the **skill source directory** rather than the user's content project—with a symlink install, the user's session credentials would land inside the cheat-on-content repo, at risk of being committed. The meta-logging hook also stored the first 120 chars of every user prompt into `usage.jsonl`, over-collecting.

**Fix**:
- Added `adapters/perf-data/douyin-session/paths.py` — a runtime path helper (`runtime_project_root` / `auth_dir` / `debug_dir` / `videos_dir`), using the `CHEAT_PROJECT_ROOT` env var + cwd fallback
- `.auth/` → user content project root; debug artifacts → `.cheat-cache/douyin-session-debug/`; report/script → user project `videos/` (no longer scattered in the skill source tree)
- `run.sh` exports `CHEAT_PROJECT_ROOT`
- the meta-logging hook no longer stores a prompt summary—now records only `prompt_present` (bool) + `prompt_chars` (length)
- docs (adapter README + state-management.md) synced

### Fixed — cheat-shoot DIFF_METRIC false-triggers v2 in colloquial scenarios (**BREAKING for v2-trigger-logic**)

**Problem**: cheat-shoot Phase 3b used line-level unified diff to compute `diff_pct = (added + removed) * 100 / orig_lines`. But in **the creator's real scenario**—the draft is markdown long sentences (~50 chars per line), the filmed script is whisper-transcribed colloquial short fragments (~5–10 chars per line)—the same content inflates diff_pct to 100–200%, triggering a v2 re-judgment that shouldn't happen.

**Reproduced in practice** (use clone PR pre-fix):
- draft markdown 63 lines / ~380 chars
- filmed transcription 100 lines / same ~380 chars
- content almost fully preserved (reviewer's original sentences verbatim + the "reaction 5 years ago" concept + all the punchlines from the level-up section)
- only addition: 1 brand-anchor sentence "fully embrace AI"
- **line-level diff_pct = 198%** ⚠️ v2 falsely triggered
- true semantic content diff ≈ 15–25%

**Fix**: split the metric.
- **DIFF_METRIC=char_levenshtein_normalized** (new default) — [tools/diff_pct.py](tools/diff_pct.py) first normalizes (strip markdown headers / dividers / list markers / decorative punctuation / collapse all whitespace), then computes char-level Levenshtein / max(len_a, len_b)
- backend priority: `rapidfuzz` (C-backed, ~ms scale; needs `pip install rapidfuzz`) → `difflib.SequenceMatcher` (stdlib, always available, ~10ms scale)
- **V2_TRIGGER_THRESHOLD = 0.30** unchanged (the threshold is empirically reasonable)
- legacy line-level kept as the ultimate fallback (downgrades only when both python3 + tools/diff_pct.py are unreachable)

**Tests**: 3 fixtures × 2 backends = 6 cases, all pass:

| Case | Content | Expected range | difflib | rapidfuzz |
|---|---|---|---|---|
| 1 | markdown long sentences vs transcribed short fragments (same content) | < 30 | 7 | 12 |
| 2 | completely different topic | ≥ 60 | 88 | 97 |
| 3 | add 20% outro/CTA | 10–30 | 14 | 25 |

Run `bash tools/diff_pct_test.sh` to reproduce.

**Known limitations**:
- historical v2 prediction files keep the line-level numbers as an audit trail—we don't re-run past predictions
- normalize is heuristic (Chinese punctuation)—may need regex tuning for other languages / atypical markdown

### Fixed — `rubric_notes.md` actuals-leak hole (**BREAKING for blind channel integrity**)

**Problem**: the cheat-score-blind sub-agent introduced in PR #11 promised to read only the two files `scripts/<id>.md` + `rubric_notes.md`. But cheat-bump Phase 5 wrote the upgrade Memo (containing real video names + actuals + derived evidence) into `rubric_notes.md`—the sub-agent read actuals through the whitelist that it shouldn't have seen, and blind scoring became "post-hoc rationalization having seen the actuals." Reproduced in practice: out of 5 published videos, the sub-agent auto-flagged 2 with `any_contamination_signal: true` (refusal=`non_blind_warning`, all dimensions' confidence dropped to medium).

**Fix** (split files):
- **Added `rubric-memo.md`**—the upgrade-Memo accumulation archive. cheat-bump Phase 5 writes **here**, **not** rubric_notes.md. Append mode accumulates multiple bumps
- **`rubric_notes.md` strictly narrowed**—holds only the formula + generic language dimension definitions + bucket boundaries + top-of-file metadata pointing to rubric-memo.md. **Never** contains real video names / actuals / derived evidence with named anchors
- **`cheat-score-blind` hard-forbidden from reading `rubric-memo.md`**—refusal_code `blocked_rubric_memo`; plus a whitelist-file **backstop self-check** (grep hits an actuals pattern → flag `non_blind_warning`)
- **`cheat-bump` Phase 5 leak guard**—grep self-check after writing rubric_notes.md; hits a forbidden pattern → abort + roll back
- **`shared-references/observation-lifecycle.md` adds a constraint**—any skill writing rubric_notes.md must not include actuals patterns (preventing future recurrence)

**Existing users must run**: any v0.x project whose existing `rubric_notes.md` contains a bump Memo **must** run `/cheat-migrate` after git pull to split rubric_notes.md into two files. Without it → the blind sub-agent still leaks. See [migrations/1.3-to-1.4.md](migrations/1.3-to-1.4.md).

### Changed — schema 1.3 → 1.4 (MINOR but BREAKING for blind channel)

- state fields **unchanged**—the `schema_version` bump only marks "existing users must run the file-layer split migration"
- [migrations/1.3-to-1.4.md](migrations/1.3-to-1.4.md) 7-step standard flow (backup → scan → extract → write rubric-memo.md → clean rubric_notes.md → self-check → bump schema)
- cheat-init, SessionStart hook LATEST_SCHEMA, registry.md synced in all three places

### Added — Blind scoring sub-agent (channel B isolation)

**Problem**: cheat-on-content's 7/9-dimension scoring was originally done inline in the main conversation—but the main Claude has already seen the user's conversation, the actuals, and the retro-section history; scoring was contaminated. It's especially severe in `/cheat-bump` Phase 2 when re-scoring the calibration pool—rank consistency may overfit rather than reflect true signal.

**Change**: introduced [skills/cheat-score-blind](skills/cheat-score-blind/SKILL.md) as a **channel B** isolated scoring sub-agent. The three-channel model:
- **A** = main conversation: decisions / writing retros / interacting with the user
- **B** = blind sub-agent (new): receives only `script_path` + `rubric_notes_path`, hard-refuses to read state file / predictions/ / videos/, outputs strict JSON 9-dimension scores + per-dim confidence
- **C** = cross-model audit (qwen-max via `mcp__llm-chat__chat`, existing): the bump endgame sanity check

Concrete landing:
- **`cheat-score` Step 3** changed to Task-tool delegate to cheat-score-blind (no more inline scoring; cheat-score has no `--skip-blind` because it's a lightweight exploration)
- **`cheat-predict` Phase 2** delegates by default; new **Phase 2.5** does disagreement detection—blind vs main-Claude self-estimate |delta| ≥ 2 pops user adjudication (choose a/b/c); header adds `BlindScored By` + `BlindScore Disagreement` fields (**all dimensions recorded**, even delta=0, as retro-analysis material)
- **`cheat-predict --skip-blind`** flag is the escape hatch: triggers `state.last_prediction_self_scored=true` + `last_self_scored_at` timestamp; cheat-status / SessionStart hook keep nagging until the next normal call clears it
- **`cheat-bump` Phase 2** **mandates** the sub-agent, **accepts no fallback**—Task tool unavailable → abort bump, no "self-audit"; each prediction's `Re-scored under vN` line additionally marks `blind: true`
- **SessionStart hook** detects `last_prediction_self_scored && days_since >= 7` and outputs a red warning
- **install.sh / uninstall.sh** add `cheat-score-blind` to the SKILLS array (14 sub-skills)

### Changed — schema 1.2 → 1.3 (MINOR)

- added `last_prediction_self_scored: bool` (default false) + `last_self_scored_at: ISO 8601 / null`
- [migrations/1.2-to-1.3.md](migrations/1.2-to-1.3.md) contains the 4-section standard format (WHAT/WHY/HOW/Manual fallback)
- old state runs `/cheat-migrate` to upgrade; compatible even without it (skills use `state.get(field, default)` as backstop)

### Known limitations (written into cheat-score-blind/SKILL.md)

1. **sub-agent ≠ truly independent** — same Claude model, shared RLHF priors; a new context is not another judging system
2. **doesn't fix rubric-design bias** — a rubric the user writes themselves naturally makes their own content look good. This layer of bias is addressed by the channel C cross-model audit and periodic bump validation
3. **doesn't fix override at the review stage** — after the main Claude gets the blind scores, it may be induced by actuals to override in Phase 2.5. Disagreement detection + user adjudication mitigate but don't eliminate it

### Changed — README / cheat-init voice reshaped (recursive fatalism)

- **README tagline changed to the recursive-fatalism version**: "You're reading this. The skill predicted it. ... You pausing to wonder 'is this real'—that's in its prediction too." Replacing the original "publishing by feel is a guess, this lets you calculate" frame
- **Added 🌀 Origin section**: the essence of the creator's own video script (the awakening from first-order to second-order fatalism) as a mid-README narrative hook
- **closing tagline adds a callback**: "You reading this line—that's predicted too"—a head-to-tail echo that locks the reader into the prediction loop
- **cheat-init Phase 1 first screen synced**: changed from "making content is fundamentally cheating" to "your next piece is already rewriting the you of 3 months from now. The pattern objectively exists; the difference is whether you see it or not. This lets you see it."
- **GitHub repo description** synced to the recursive version

### Changed — multilingual README split

- `README.md` is now **English by default**—the first screen for international users
- `docs/README_CN.md` is Simplified Chinese (original README content + fatalism reshape)
- both get a language switcher at the top (QuantDinger style)
- logo path + internal links adjusted to relative paths

### Added — Star History chart

Both READMEs add a [star-history.com](https://star-history.com) chart at the end for community visualization of project momentum.

### Changed — de-emphasize Claude Code

The README install section changed from the dual "### Claude Code" + "### Codex" headings to "default + supported agents list"—packaging the skill as a cross-agent workflow rather than Claude Code-exclusive. The daily-use section similarly switched to the generic "skill-compatible agent."

### Added — Terminal-style logo SVG

- `docs/logo.svg` (1.9KB native SVG, no image-asset dependency)
- terminal window + traffic lights + `$ fatesnail` command line + 5-phase loop + `// cheat on content` comment
- centered in the README hero

### Added — cheat-seed Mode refactor + dual trend-tool integration

**Problem**: the original Mode B gave "three kinds of examples a/b/c" to get the user to tell their experience—but the same script treated **users with a direction but abstract** ("I want to do career topics") and **users with no idea at all** ("help me think") the same; the former actually has real motivation and doesn't need AI to enumerate, and what the latter needs is external material, not a prompt.

**Change**:

- **Mode B changed to a single question "why do you want to make this topic?"** — a user-introspection window, **calling no trend tools**. 3 kinds of answer: contains a concrete experience → switch to Mode A; empty motivation → counter-question up to 2 rounds; truly no idea → switch to Mode C
- **Mode C integrates external material**: route trend tools by `content_form`—AI-type formats call [aihot](adapters/trend-sources/aihot.md), culture/society formats call [trendradar-mcp](adapters/trend-sources/trendradar-mcp.md), hybrids call both; after the user picks one, **return to introspection** and ask "why do you feel most strongly about this one," then switch to Mode A to dig deeper
- **Mode A gray scenario** (user gave a current-affairs topic): Phase 2A.5 asks "want to pull external data for reference"—**doesn't call proactively**, avoiding external info skewing the user's angle
- **the three experience options moved to the Mode C backstop**: presented only when the user refuses external material or isn't interested in any external option

### Added — two first-class trend sources

- **[aihot](adapters/trend-sources/aihot.md)** (Claude skill): the Chinese AI-industry daily picks from [aihot.virxact.com](https://aihot.virxact.com), 5 categories (models/products/industry/papers/tips). No auth, curl a public API, rate limit 600/min
- **[trendradar-mcp](adapters/trend-sources/trendradar-mcp.md)** (MCP server): [TrendRadar](https://github.com/sansan0/TrendRadar) (57k stars, GPL-3.0—calling via MCP doesn't constitute linking). 25+ MCP tools—besides `get_latest_news` there's `analyze_topic_trend` (surge/decay detection), `compare_periods` (week-over-week), `analyze_sentiment`

### Added — `shared-references/data-source-routing.md`

The trigger and routing protocol for trend tools—single source of truth recording: "when to call" (the trigger matrix for 5 entry points) + "which to call" (the content_form → adapter routing table) + "what to do when not calling" (the failure-downgrade chain) + token-cost awareness.

### Philosophy unchanged

> Trend tools are a "pre-stocked material library," not the "main menu"—AI provides material, the user decides the angle.

cheat-seed's core thesis "good content comes from the user's real experience; AI doesn't brainstorm out of thin air" is fully preserved. The new design only keeps the "no idea at all" cold-cold-start path from deadlocking.

### Added — v2 prediction re-judgment system (post-shoot script-change scenario)

- **append-only v2 prediction**: cheat-shoot detects line-level diff ≥ 30% (`V2_TRIGGER_THRESHOLD`) between the filmed script and `scripts/<id>.md` → auto-calls `/cheat-predict — mode: v2 — prediction-file: <path>` → appends a `## Prediction v2 (replaces v1)` section before `## Retro` in the original prediction file. **The v1 section is never modified** (physically enforced by the hook); only v2 enters cheat-retro's deviation calculation
- **immutability hook awk upgrade**: changed from a single `## Prediction` to recognizing multiple `## Prediction vN` sections (v1 / v2 / any vN locked together), while remaining compatible with v0.1.0's legacy bare heading. End-to-end 5-scenario verification passed (editing v1 / editing v2 / editing legacy all BLOCK; appending a new section, editing `## Retro` all ALLOW)
- **cheat-predict adds Phase 0.7 mode detection**: detects the target prediction file already contains a `## Prediction...` section → auto-switch to v2 mode (Edit appends at the `## Retro` boundary, doesn't Write-overwrite)
- **cheat-retro upgrade**: recognizes multiple `## Prediction vN`, takes the last section as the calibration basis; the prediction-section hash check is extended to "the merged hash of all v? sections," and any edit triggers an error rollback
- **prediction header new field `Prediction Basis`**: `pre_shoot` (v1 default) / `post_shoot_pre_publish` (v2). score-curve and cheat-bump use this to separate the two data lines and avoid mixing samples
- **shoots[] item schema extended**: added `scripts_path` / `script_consistency` / `script_diff_pct` / `v2_prediction_written` / `script_hash_at_shoot` (see [migrations/1.1-to-1.2.md](migrations/1.1-to-1.2.md))

### Changed — schema 1.1 → 1.2 (MINOR)

- bump the `LATEST_SCHEMA` marker + version chain in [migrations/registry.md](migrations/registry.md)
- cheat-init writes `"schema_version": "1.2"` for new state
- SessionStart hook `LATEST_SCHEMA="1.2"` — existing user git pulls + runs a session → hook flags schema mismatch → user runs `/cheat-migrate` to upgrade in 5 seconds. MINOR-compatible, not forced (skills use `state.get(field, default)` as backstop)

### Why now

The user's real workflow: finish a draft → **often ad-lib the script while filming** → the draft and the actually-aired version diverge. The original strict blind prediction ("predict before shooting, only register after") meant "the draft that was predicted" and "the draft that actually aired" weren't the same one—calibration distortion.

The v2 system makes "post-shoot script change" a first-class citizen: v1 stays as the archive, v2 re-judges based on the actual filmed script, and diff(v1, v2) itself becomes strong evidence for rubric upgrades (the user rewrote the script to be higher ER → the tool learns this user's ER threshold is inconsistent with the current formula). The blind-prediction principle is preserved: v2 is still completed before publishing, with no play data to "cheat" with.

### Added — Codex install compatibility (@songth1ef [#6](https://github.com/XBuilderLAB/cheat-on-content/pull/6))

- **`install.sh --codex`**: installs the root router skill `cheat-on-content` and 13 sub-skills into `~/.codex/skills/`
- **`install.sh --all`**: installs both the Claude Code and Codex skills
- **`uninstall.sh --codex` / `--all`**: symmetric uninstall of Codex or the dual install
- **Codex routing note**: Codex triggers the same flow via natural language, not relying on Claude Code's `/cheat-*` slash-command harness

### Added — Migration system (so long-term iteration doesn't break existing users)

- **`/cheat-migrate` skill**: upgrades an existing user's `.cheat-state.json` from the old `schema_version` to the current `LATEST_SCHEMA`. Idempotent, no version-skipping, stops at the breakpoint on failure
- **`migrations/` directory**: single source of truth for version evolution
  - `registry.md`: the `LATEST_SCHEMA` marker + full version chain
  - `<from>-to-<to>.md`: 4 sections per migration step (WHAT changed / WHY / HOW Claude steps / Manual fallback)
- **`shared-references/migration-protocol.md`**: evolution philosophy + maintainer checklist (the 4 things a schema bump must do)
- **SessionStart hook enhancement**: detects `state.schema_version != LATEST_SCHEMA` → outputs a non-blocking warning suggesting `/cheat-migrate`
- **`install.sh --reinstall-hooks <project>`**: after git pull, rewrites the scripts in the user project's `.cheat-hooks/` (doesn't touch state / rubric / predictions)
- **state-management.md upgrade**: all schema-upgrade docs point to cheat-migrate; clarifies the MINOR / MAJOR boundary

### Why now

The state of v0.1.0 users is schema 1.1. If later we change field semantics, delete fields, rename, etc. → without a migration system, existing users would get stuck after git pull. This system makes "long-term iteration that doesn't break existing users" the norm.

### Fixed

- **cheat-init `content_form` stored as a letter bug**: the Phase 3 state JSON template used the abstract placeholder `<Q1>`, causing Claude to literally write `"a"` into the state file instead of the enum `"opinion-video"`. Fix: Q1/Q3/Q4/Q5 each get an explicit letter→enum mapping table + a bold warning in the Phase 3 template. Also filled in the 7 missing `last_*` init fields (previously relying on the `state.get(field, default)` backstop) + `enabled_perf_adapters` derivation + forcing `initialized_at` to use the local `+08:00` timezone instead of UTC `Z`

### Changed — README rewrite (positioning adjustment after the v0.1.0 ship)

- title: English `Cheat on Content`, subtitle reworded (it was a Chinese tagline at the time)
- tagline faces the "cheating" frame head-on: "Making content is fundamentally cheating—whoever sees through the pattern first takes the traffic"
- added the "but can't ChatGPT / Doubao / DeepSeek do this too?" section—core positioning as "your own ops expert + auto-evolving"
- removed the early-product warning section (the badge + this CHANGELOG already convey it; repeating is a lack of confidence)
- cut the ARIS attribution (kept the multi-adapter design idea, removed the external credit)
- README total length 330 lines → 90 lines
- cheat-init Phase 1 first-screen copy rewritten in sync: removed methodology philosophy, 2 caveats (early-stage inaccuracy + strongly recommend importing a benchmark)

### Remaining items

- Step B: soften more hardcoded rules
- complete reference-implementation anonymized snapshot

---

## [0.1.0] — 2026-05-05

> ⚠️ **Early-stage product (v0.x)—the state schema may still break**
>
> Before v1.0, each upgrade may change the field structure of `.cheat-state.json`. **Back up your entire `<your-channel>/` directory before upgrading.** Major breaking changes will be marked `BREAKING` in this CHANGELOG, with manual migration steps given where possible.

### Added

- **Methodology + 12 sub-skills**: the full closed loop init → learn-from → seed → score → predict → shoot → publish → retro → bump, plus status / recommend / trends helpers
- **3 non-negotiable principles**: blind prediction + bump=full re-score + the rubric is a workbench not a museum (see `shared-references/`)
- **`/cheat-learn-from` benchmark import**: 5–10 benchmark samples derive base rubric signals + script patterns. Two input methods (paste text, default / whisper transcription) + two data methods (manual fill / adapter auto-fetch)
- **Buffer alert system** (cadence-protocol): derives color thresholds from publish frequency, alerts on a publishing gap
- **Unified prediction format + confidence levels**: same 7-component prediction at all phases, header shows 🔴/🟠/🟡/🟢/🔵 confidence level
- **prediction-immutability hook**: harness-layer enforcement of principle #1 (end-to-end verification 5/5 pass)
- **SessionStart auto-report hook**: auto-renders a status report at each session start
- **Cross-model bump audit** (mcp__llm-chat__chat): calls an external LLM for independent judgment during a rubric upgrade
- **douyin-session adapter** (Playwright): auto-fetches Douyin video + comment data
- **whisper adapter**: transcribes a video file into a transcript
- **9 templates** + **2 starter rubrics** (opinion-video v2 calibrated / opinion-video-zero v0 equal-weight)
- **score-curve.py**: prediction-accuracy convergence-curve diagnostic tool

### Soft rules (Claude-judgment-led, not hard thresholds)

The rules below **have default reference values** but Claude can softly violate them based on strong signals:

- bump trigger sample count (default ≥5, can make an exception based on a strong counterexample)
- same-direction-deviation trigger (default ≥3 consecutive, can make an exception based on 1 extreme deviation)
- benchmark-influence fade-out (default calibration_samples ≥10, can make an exception based on "user-data vs benchmark divergence")
- observation-promotion threshold (default ≥2 samples, can make an exception based on a strong signal)

On a soft violation, Claude must explicitly mark it `judgment-driven` for the user to scrutinize.

### Hard constraints (cannot be softly violated)

- bump validation `THRESHOLD = 4/5` (statistical rigidity)
- prediction immutability hook (binary)
- `RETRO_WINDOW_DAYS = 3` default (user-configurable 1/7)
- must have ≥3 benchmark samples to extract patterns
- must have ≥20 top comments to complete a manual-paste retro

### Known limitations

- **v0.x has no automatic migration**: if the state schema changes on upgrade, existing users must manually wipe + re-init
- **adapter fragility**: the Douyin / Xiaohongshu adapters rely on anti-scraping bypasses and may break when the platform changes, requiring ongoing maintenance
- **whisper Chinese accuracy**: the medium model is good enough; long-form accuracy is mediocre, manual review recommended for important scripts

---

## Upgrade guide (pre-v1.0)

After each git pull:

1. **Symlink-mode install (recommended)**: takes effect directly, no reinstall needed
2. **Copy-mode install**: re-run `bash install.sh --copy`
3. **If the CHANGELOG marks `BREAKING`**: follow the manual migration steps. When there are no steps, a wipe + re-init is recommended
