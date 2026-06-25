---
name: cheat-seed
description: Discuss topics with the user in conversation—**one at a time by default**; the user proactively gives a topic or experience, and the AI digs into the user's input, distills an angle, and writes one draft. It's not the AI chasing the user with three open questions, nor dumping 5 candidates at once. Triggers: "find a topic" / "I want to make one about X" / "I have an idea" / "seed". Optional batch mode: `/cheat-seed --batch 5` runs the old brainstorm-5-candidates + write-5-drafts flow.
argument-hint: [— batch: N] [— sources: <comma-separated>]
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-seed — topic conversation (default) / batch brainstorm (optional)

The core of cheat-seed is to **discuss topics with the user**, not to mechanically brainstorm. Good content comes from the user's real experience + observation + emotion—things the AI can't possibly brainstorm out of thin air. The AI's role is to **listen to the user → help distill an angle → write a draft**, not to dump 15 candidates for the user to pick.

**Default mode**: conversational, one at a time.
**Batch mode** (`--batch N`): keeps the old brainstorm-N-candidates + write-N-drafts flow, for users with "no idea at all + want to batch-initialize".

## Three Modes (auto-detected)

```
Mode A — user proactively gives a topic (**most common**):
  User: "/cheat-seed" + directly says "I want to make one about X"
       or: "/cheat-seed I got criticized by my boss in a meeting recently..."
  ↓
  AI **digs into** X / this thing—what moment triggered it? What's the part that makes you [feel / annoyed / find interesting] most?
  ↓
  Converge to a concrete angle → propose → user agrees → write 1 draft → done
  ↓
  Ask "next one?" or the user says "that's it for today"

Mode B — user gives a direction but not specific:
  User: "I want to make something about [career / relationships / AI / ...]"
  ↓
  AI: "[scope] is too broad. What specific thing you recently encountered made you want to do this direction?"
  ↓
  Converge to Mode A's concrete experience

Mode C — user has no idea at all (rare):
  User: "I don't know what to make" / "think of a topic for me"
  ↓
  AI: "OK, entering brainstorm mode—first fetch trends + your prior interest directions, give you 1 suggestion"
  ↓
  Run trend-sources to fetch trends + read candidates.md / predictions/ to see the user's history
  ↓
  Propose 1 angle (not 5) → user agrees → write a draft

Batch Mode — user explicitly wants batch (`/cheat-seed --batch 5`):
  Per the old brainstorm flow: 3 questions → 15 candidates → user picks → write 5 drafts.
  For users who "want to settle the next 2 weeks of topics in one go today".
```

**Key correction** (the difference from the old version):
- The AI **doesn't proactively ask open questions**—it waits for the user's input then digs in
- One topic at a time, not 5
- Default conversational + one at a time, batch is the escape hatch

## Constants

- **DEFAULT_TREND_SOURCES = ["manual-paste"]** — used only in Mode C / the Mode A gray scenario / Batch. The user can add aihot / trendradar-mcp in state
- **TREND_TOOL_ROUTING** — route the data source by `content_form`, see [shared-references/data-source-routing.md](../../shared-references/data-source-routing.md)
- **MODE_B_MAX_REPROBE_TURNS = 2** — the Mode B "why" counter-question is at most 2 rounds; beyond that switch to Mode C
- **MAX_DEEP_DIVE_TURNS = 4** — the Mode A convergence stage is at most 4 counter-questions, to avoid over-interrogation by the AI
- **WITH_DRAFT = yes** — by default write a draft immediately after confirming the angle; the user can say "wait, I'll write it myself" to skip
- **DRAFT_LENGTH** — derived from `state.typical_duration_seconds`: 30s→100-200 chars / 90s→250-500 chars / 240s→600-1000 chars / 450s→1100-2000 chars / 900s→2200+ chars
- **HUMANIZE_DRAFT = on** (default) / off — after writing the draft, run it through the `humanizer` skill to remove AI-writing tells (em-dash overuse / rule of three / inflated vocabulary / vague attribution etc.). When off, output the raw AI draft directly. **Only humanize the body, don't touch the header's "must rewrite" warning**

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | read calibration_samples / typical_duration / cadence |
| `rubric_notes.md` | read the current rubric (for rough scoring) |
| `script_patterns.md` | read existing patterns (pick a structure per the cheat sheet when writing a draft) |
| `predictions/*.md` (if any) | published history, as context when brainstorming |

## Workflow

### Phase 0: prerequisite checks + load all context (**core: 3 context sources**)

1. Read `.cheat-state.json` → if it doesn't exist, prompt to run `/cheat-init` first
2. Read `rubric_notes.md` for the current formula (for rough scoring)
3. Read `script_patterns.md`—pick a structure per the cheat sheet when writing a draft
4. **Read existing prediction files** (including reconstructed ones imported at init) as **context source A** (the user's own history):
   - 0 → A is empty
   - ≥1 → A has content, extract (title / 7 dims / actuals)
5. **Read `benchmark.md`** (if it exists) as **context source B** (the benchmark account):
   - `state.benchmark_status = imported` → B has content, extract the benchmark account's sample topic distribution, tone, Patterns
   - `state.benchmark_status = none / pending` → B is empty
6. Check the user's argument—whether it contains a concrete topic / experience, to decide Mode A/B/C/Batch

**Context priority when brainstorming** (**Claude judges**—below are reference defaults):

- **A dominant** (the user's own data): when Claude judges the user's data can drive the direction (reference default: `calibration_samples ≥ 10`, but Claude can go earlier—e.g. N=5 but ≥3 strong samples clearly inconsistent with the benchmark)
- **B dominant** (benchmark): when user data is scarce + the benchmark has content
- **B absent** (benchmark empty) + user data scarce: rely purely on user input + fetching trends; clearly tell the user "no benchmark and not enough of your own data, recommend running /cheat-learn-from then coming back to brainstorm"

The judgment basis is **not a hard sample count**, but:
- whether the user's recent N samples' actuals **are consistent with the benchmark's high-performing sample types**—consistent means the benchmark still has reference value; inconsistent means the user has walked their own path
- the **diversity** of the user's samples—3 pieces all the same kind isn't mature; 3 pieces covering different categories is more credible than 10 of the same kind

### Phase 1: Mode routing

Read the user input, identify:

**Contains concrete nouns + emotion / experience words** ("I had a meeting yesterday..." / "I saw X and it made me..." / "I feel about Y...") → **Mode A** (dig in; if the topic is current-affairs, Phase 2A.5 asks whether to pull external data)

**Contains direction words but no concrete content** ("want to do career" / "AI direction" / "relationships") → **Mode B** (single question "why do you want to do this"—the user-introspection window, **calling no trend tools**)

**Explicitly says no idea** ("don't know what to make" / "think of something" / "just give me anything") → **Mode C** (call trend tools per [data-source-routing.md](../../shared-references/data-source-routing.md) + user picks + return to introspection; if none works, the three-option "talk about experience" fallback)

**Explicit `--batch N`** (user proactively batch) → **Batch Mode**

**Pure `/cheat-seed` with no extra content** → **ask the entry question**:

```
What do you want to do today?

- Have a topic / experience in mind → just tell me ("I want to make one about X" / "Recently I X...")
- Know the rough direction → tell me ("want to do career" / "AI direction") → I'll ask you a single "why"
- No idea at all → say "help me think" → I'll pull today's trends from [aihot / trendradar] for you to look at
- Settle a batch → say "batch <N>"

(I won't chase you with a pile of open questions—give me one sentence and I start)
```

Note this is the **only open-ended question**—asked only when the user **purely triggers** `/cheat-seed`. If the user already gave content in the trigger ("/cheat-seed I want to make..." or "find a topic, I had a meeting recently..."), go straight to Mode A/B/C without asking this.

### Phase 2A: Mode A deep dive (user gave a concrete topic / experience)

**Core principle**: **dig into** the content the user gave, **don't switch to another topic**.

**Counter-question types (pick by scenario)**:

- triggering moment: "you mentioned X, what specific moment first made you want to make it?" / "what made you feel this was worth a video?"
- emotional anchor: "what detail in this makes you most [angry / find absurd / find interesting]?"
- angle choice: "do you want to say [angle a: critique the phenomenon] or [angle b: self-reflection] or [angle c: generalize to the universal]?"
- audience imagination: "who in your mind are you talking to? How will they think / share after watching?"
- objection probe: "if someone rebuts with [opposing view X], how would you respond?"—forces the user to clarify their stance first

**Counter-question discipline**:
- Ask only **1** question at a time (don't pack 3 in a row)
- At most `MAX_DEEP_DIVE_TURNS` rounds (default 4)—beyond that proactively converge: "OK I think that's enough, let me propose an angle to try"
- If the user's answer contains emoji / is short / impatient → converge immediately, don't push

**Convergence output**:

```
I think this angle works:

[one-sentence thesis: within 50 chars]

Approach:
- Use [Pattern X structure] (from script_patterns.md)
- Hook: [concrete scene / sentence]
- Body: [what the 3 observations are]
- Ending: [MVP sentence direction]

Rough score (v0 equal-weight 7 dims): ER=X HP=X QL=X NA=X AB=X SR=X SAT=X → composite ≈ X.X
Confidence: 🔴 very low (you've only calibrated 0/N pieces)

Want me to write a draft first? (yes / change angle / I'll write it myself)
```

User replies yes → Phase 4 write the draft.
User says "change angle" → back to Phase 2A to dig more.
User says "I'll write it myself" → add the candidate to candidates.md marked tier1, end.

### Phase 2B: Mode B — single "why" question, trigger user introspection

The user gave a direction but not specific ("want to do career" / "AI direction" / "relationships"). **This stage calls no trend tools**—it's the window for user introspection; external info contaminates it.

Ask only one question, **straight to the point**:

```
Why do you want to make this topic?
```

Don't ask "three examples a/b/c"—that's dumping options for the user to pick, breaking introspection. Let the user organize their own words.

**Route by the user's answer**:

| User answer | Category | Action |
|---|---|---|
| Contains a concrete experience / personal sticking point ("I often work overtime myself" / "I saw X and it made me...") | **real motivation** | switch to Mode A deep dive (Phase 2A) |
| Abstract hype attribution ("this topic is hot lately" / "everyone's doing it" / "heard it grows followers") | **empty motivation** | counter-ask "so what angle on this topic do you feel most strongly about?"—force out a personal stake; still empty → switch to Mode C |
| "I don't know either" / "a friend said it makes money" / vague hedging | **truly no idea** | switch directly to Mode C |

**Counter-question discipline**: at most 2 rounds. If the 2nd round still can't surface a real motivation → switch directly to Mode C, **don't dig endlessly**.

> Design intent: Mode B is a "filter", not a "factory". A user comes here to either reveal a real motivation (→ enter Mode A) or reveal they actually have no idea (→ enter Mode C). Both are better than forcing a topic out within Mode B.

### Phase 2C: Mode C — external material + user picks + return to introspection

The user has no idea at all (says so explicitly / switched over from Mode B). **This is the only entry point that calls trend tools by default.**

Per the routing rules of [shared-references/data-source-routing.md](../../shared-references/data-source-routing.md):

1. **Pull external material** (pick a trend source by `content_form`):
   - `tutorial-builder` / AI-type → call the aihot skill
   - `opinion-video` / `long-essay` / `podcast` / `other` → call trendradar-mcp (if enabled)
   - `mixed` → call both
   - none available → use manual-paste (ask the user: "anything you saw today worth making? Paste a few URLs/titles")

2. **Talk-about-experience fallback** (the user refuses to look at external material / isn't interested in any of it):

   ```
   None of the external material resonated, so back to you. Three openings, pick one to start:

   a) A specific thing you actually encountered recently? ("Last week I saw my colleague X...")
   b) Something you recently read / saw that made you want to rant? ("There's an answer on Zhihu...")
   c) An unsolved puzzle you've long mulled over? ("I've never figured out why X...")

   Pick any one and start talking.
   ```

3. **After pulling external material**, rough-filter with the rubric + filter by content_form, keep the 5 most fitting:

   ```
   These 5 today fit your format:
   1. [Title A] (source: trendradar / Weibo hot search / hot_score: 8.5)
   2. [Title B] (source: aihot / model category / curated)
   3. ...

   Which resonates most? If none, reply 'none' and I'll ask in a different direction.
   ```

4. **User picks one → return to introspection**:

   ```
   OK [Title X]. Why do you feel most strongly about this one?
   Is it [angle1] or [angle2] or something else?
   ```

   → user answers → switch to Mode A deep dive.

5. **User replies 'none'** → switch back to the "talk-about-experience fallback" of Mode C step 2.

**Key**: trends aren't "dump 5 candidates for the user to pick", they're "give material + force-ask the user's personal stake"—the AI doesn't decide for the user which one is most worth making.

### Phase 2A.5: Mode A gray scenario — the user talked about a current-affairs topic

Mode A digs into the user's experience by default. But if **what the user talked about is itself a current-affairs topic** (product name + time word / person name + event word), per the "current-affairs determination" rule of [data-source-routing.md](../../shared-references/data-source-routing.md), **ask** the user whether to pull external data for reference:

```
💡 [topic] is current-affairs—I can pull today's opinion climate (sentiment across platforms + main angles) as reference.

Want to see it? Reply 'show' and I'll fetch; reply 'no need' and I'll dig into your angle directly.
```

User replies "show" → call the corresponding trend source → inline the data into the deep-dive context;
User replies "no need" → standard Mode A deep dive, don't touch external data.

**Never call proactively**—the user's angle takes priority over external data, to avoid external info **skewing** the user's perspective.

### Phase 2D: Batch Mode (user explicitly `--batch N`)

**Keeps the old brainstorm flow**:

1. Ask 3 checklist questions (interests / tone / red lines)—only Batch mode asks these
2. Fetch trends + Claude brainstorms 15 candidates
3. User picks N
4. Write N drafts to scripts/—**each goes through Phase 4's paragraph-form format + Phase 4.5 self-check** (line-format + humanizer), not skipped just because it's a batch

See the commit history (the old cheat-seed's Phase 1-3). This is an escape hatch, not the default.

### Phase 3: compute candidate ID + write to the candidate pool

Regardless of Mode A/B/C path, after confirming the angle:

1. Compute the candidate id: `sha256("seed-" + thesis + trigger time)[:12]`
2. Write one entry to `candidates.md` (per the [candidate-schema.md](../../shared-references/candidate-schema.md) format)
3. Mark `tier=tier1` + `read_status=deep_read` (already discussed, not a skim)

### Phase 4: write the draft

`WITH_DRAFT=yes` → write in turn to `scripts/<YYYY-MM-DD>_<id>_<short-title>.md`:

**Must read** `script_patterns.md` before writing the draft—pick a structure fitting the user's topic per the "structure-selection cheat sheet". If the file is still at the abstract-skeleton stage (the user hasn't filled in many patterns), use the generic framework of the corresponding starter rubric.

**Word count**: derived per `DRAFT_LENGTH` (based on `typical_duration_seconds`).

#### ⚠️ The body must be paragraph form, not subtitle format (**the most common generation drift**)

The model's training prior defaults to writing a "video script" in teleprompter/subtitle short-line format. **This is wrong**—a cheat-seed draft is prose for the user to **rewrite**, not filming subtitles. Subtitles are auto-broken by the editor after shooting, not the form at writing time.

When generating the body, keep your eyes on this comparison:

```
❌ Subtitle format (don't write like this):
Have you noticed
all the reviewers are saying the same thing
your research is too old-fashioned
but look closely
they're all citing reactions from 5 years ago

✅ Paragraph form (must write like this):
Have you noticed all the reviewers are saying the same thing—your research is too old-fashioned. But look closely: they're all citing reactions from 5 years ago. AI isn't new; what's new is that everyone collectively woke up this time.
```

Rules:
- **Each paragraph 100-300 chars**, naturally connected by commas / periods / dashes, **don't hard-break at sentence boundaries**
- A blank line between paragraphs (break only at a natural topic switch)
- A draft body is usually 3-6 paragraphs, **shouldn't have dozens of single-sentence lines**

#### Format:

```markdown
# [thesis title]

> ⚠️ **Draft by Claude — you must rewrite before filming**
>
> This is scaffolding, not a finished product. Your tone / rhythm / personal experience can't be AI-generated.
> Rewrite flow:
> 1. **Rewrite directly in this file** (same path: scripts/<...>.md)
>    - add your tone, personal experience, real punchlines
>    - cut the build-up, cut the model's abbreviations, cut the academic packaging
> 2. After rewriting, run `/cheat-predict scripts/<this file>.md`
> 3. After filming, run `/cheat-shoot scripts/<this file>.md`

**Article ID**: <12-char hash>
**Tone**: [derived from the discussion, not a checklist Q]
**Target duration**: <state.typical_duration_seconds converted> minutes
**Target word count**: <derived from duration>
**Structure selection**: [explicitly marked per the cheat sheet of script_patterns.md, e.g. "metaphor-first" / "data-reversal opening"]
**Patterns used**: [number + brief note]
**Discussion seed**: [one-sentence recap of the core from the deep dive]

---

[draft body — **paragraph form**, 3-6 paragraphs, each 100-300 chars, not single-sentence fragments]
```

`WITH_DRAFT=no` (user says "I'll write it myself") → skip Phase 4 + Phase 4.5.

### Phase 4.5: draft self-check pass (formatting + de-AI-ify)

After the draft is written and **before showing it to the user**, run two self-check steps. **Fixed order: 4.5a fix formatting first, then 4.5b de-AI-ify**—the humanizer processes prose, and feeding it subtitle-format fragments causes chaos.

**Why it's safe** (doesn't contaminate calibration): a cheat-seed draft is not the thing being predicted/published—after the user rewrites it, cheat-predict scores the **user's final draft**. These two steps just give the user a cleaner starting point.

#### Phase 4.5a: line-format self-check (subtitle format → paragraph form)

Phase 4's prose instruction + the ❌/✅ comparison already suppress the prior at generation, but generation can still drift. This step is the **deterministic backstop**:

```bash
# Only look at the body section (after the --- divider)
body=$(awk '/^---$/{f=1;next} f' scripts/<id>.md)
line_count=$(printf '%s\n' "$body" | grep -c .)        # non-empty line count
char_count=$(printf '%s' "$body" | wc -m | tr -d ' ')
avg_chars_per_line=$(( char_count / (line_count > 0 ? line_count : 1) ))
```

Determination: **`avg_chars_per_line < 15` AND `line_count >= 8`** → judged subtitle format → **auto-reflow**:
- merge sentence-boundary hard breaks back into natural paragraphs
- split into 3-6 paragraphs by topic switch, each 100-300 chars
- replace the body section with Edit (don't touch the header)
- mark a line in the Phase 5 output: "📐 detected subtitle format, reflowed to paragraph form"

No hit → skip, the body is already paragraph form.

#### Phase 4.5b: humanizer de-AI-ify

`HUMANIZE_DRAFT=on` (default)—run it through the `humanizer` skill. The first draft Claude writes itself naturally carries AI tells (em-dash overuse / rule of three / "inflated" vocabulary / vague attribution / shallow -ing analysis); this step clears them.

Steps:

1. Check whether the `humanizer` skill is available (`~/.claude/skills/humanizer/` exists):
   - unavailable → skip 4.5b, add a line in the Phase 5 output "(humanizer not installed, the draft is the raw AI version—`git clone https://github.com/blader/humanizer` to ~/.claude/skills/ to enable auto de-AI-ify)"
2. Available → call `humanizer` via the Skill tool, **passing only the draft body** (after the `---` divider, the paragraph form already reflowed by 4.5a), **never the header**:
   - the header's `⚠️ Draft by Claude — you must rewrite before filming` warning is an **intentional scaffolding marker**, not prose to humanize
   - **voice calibration**: if the user has historical scripts (`videos/*/script.md`) or filled in `script_patterns.md`, pass the most recent 1-2 as voice reference samples for the humanizer—lean toward "**this user's voice**", not "generic human voice"
3. The humanizer returns the de-AI-ified body → use Edit to replace the draft file's body section (don't touch the header)
4. Record the "which tells were fixed" reported by the humanizer (e.g. `em-dash overuse ×3 / rule of three ×2 / inflated vocabulary: "profound" "fundamentally"`), shown in the Phase 5 output

**Discipline**:
- The humanizer is for **de-AI-ifying**, not for **rewriting on the user's behalf**. It makes the draft less machine-written, but it's **still not the user's voice**—the header's "must rewrite" warning still holds, and the Phase 5 output must reiterate it
- If the humanizer rewrites a sentence in a way that deviates from the `structure selection` / patterns used → the pattern wins, roll back that sentence (the pattern was decided with the user; the humanizer shouldn't override it)
- The humanizer is **not responsible for formatting**—the line-break issue was fixed in 4.5a, and what the humanizer receives is already paragraph form

### Phase 5: output "next step" + ask whether to continue

```
✅ Draft written: scripts/2026-05-04_<id>_<short>.md
📐 Format self-check: passed (paragraph form)  ← or "detected subtitle format, reflowed to paragraph form"
🧹 Ran through humanizer: fixed em-dash overuse ×3 / rule of three ×2 / inflated vocabulary 2 places
   (the draft is less "machine-flavored" now—but this is still scaffolding, not your voice)

Next you can:
- Rewrite this draft (edit the file directly)—add your tone, experience, real punchlines
- After rewriting, run "score this scripts/<...>.md" to see the 7-dim scores
- Decide to film → "start prediction scripts/<...>.md"

What do you want to make next?
(Just tell me a concrete experience / topic, or say "that's it for today" to end)
```

> The humanizer line only appears when `HUMANIZE_DRAFT=on` and the skill is available. When not installed, replace it with a line on how to enable it.

User says "that's it for today" → end cheat-seed.
User gives a new topic → back to Phase 1 to re-route.

## Key Rules

1. **The AI doesn't proactively ask open questions**—asks the entry question only once when the user purely triggers `/cheat-seed`; otherwise **waits for the user's input then digs in**
2. **One topic at a time**—by default Mode A/B/C all give 1 suggestion; only go Batch when the user proactively wants a batch
3. **Counter-question discipline**: ask 1 at a time, at most 4 rounds, converge immediately when the user is impatient
4. **Dig into the topic the user gave**, don't switch to something else—if you say "got criticized by my boss in a meeting", the AI shouldn't ask "so have you felt lately that AI makes everyone..." kind of parallel topic
5. **Writing a draft must read script_patterns.md**—pick a structure per the user's existing patterns
6. **A draft is scaffolding**—the header carries a prominent "must rewrite" warning
7. **The humanizer only de-AI-ifies, doesn't rewrite for the user**—Phase 4.5b makes the draft less machine-flavored, but it's still not the user's voice; the "must rewrite" warning doesn't expire just because it passed the humanizer
8. **The body is paragraph form, not subtitle format**—watch Phase 4's ❌/✅ comparison at generation; Phase 4.5a uses `avg_chars_per_line < 15 AND line count ≥ 8` as the deterministic backstop, reflowing on a hit. Subtitles are auto-broken by the editor after filming, not the form at writing time

## Refusals

- "Skip the deep dive, just write the draft" → ask "do you want to just give a topic for me to write? OK but the draft quality may be poor—I don't know your angle. Give me a one-sentence thesis and I'll write"
- "AI decides the topic for me" → refuse. In the Mode A/B/C paths, the AI always only **presents external material** + **asks the user's angle**, doesn't decide "which one to make" for the user
- "I can't be bothered to answer why in Mode B, just give me 5 candidates" → refuse. Mode B's "why" is a filter—if you can't answer it, you shouldn't use a Mode B direction. Either enter Mode A with a concrete experience, or enter Mode C and I'll help you find material
- "In Mode A, pull trends for me directly without asking" → refuse. A Mode A user already has an angle; pulling external data without permission contaminates their perspective. See [data-source-routing.md](../../shared-references/data-source-routing.md)
- "Write 5 drafts at once" → not in the default flow. The user must explicitly `--batch 5`
- "I can't be bothered to rewrite, just film the AI draft" → warn "a script generated directly by AI films with low ER and will contaminate your calibration data", but if the user insists, allow it (mark `unmodified_ai_draft: true`)

## Integration

- Upstream: at the end of `/cheat-init` Phase 5, when `pool_status=none + calibration_samples=0`, it proactively asks "run /cheat-seed now?"
- Upstream: `/cheat-recommend` mentions `/cheat-seed` in the guidance copy when candidates is empty
- Upstream: `/cheat-status` prompts "you haven't filmed yet—run /cheat-seed?" when `pool_status=none + >24h since init`
- Downstream: the user's candidate → candidates.md (tier1, deep_read)
- Downstream: (default) draft → Phase 4.5 humanizer de-AI-ify → scripts/<id>.md → user rewrites → /cheat-predict
- Optional dependency: the [`humanizer`](https://github.com/blader/humanizer) skill (MIT, external project). When installed at `~/.claude/skills/humanizer/`, Phase 4.5 auto-enables it; when not installed, gracefully skip. **Not bundled into pattern-first**—the user clones it themselves
- Difference from `/cheat-trends`: cheat-seed is **discuss + write a draft** (conversation-heavy); cheat-trends is **multi-adapter fetch + rough score** (fetch-heavy). They serve different purposes and don't replace each other.
