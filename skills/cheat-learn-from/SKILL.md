---
name: cheat-learn-from
description: Import script + data from a benchmark account → extract patterns + derive base rubric signals → write to benchmark.md / script_patterns.md / rubric_notes.md. **This is the tool's earliest signal source**—cold-start users with no history of their own rely entirely on the benchmark; users with history are also advised to import at least 1 benchmark for a sanity check. Triggers: "learn this account" / "break down these benchmark videos" / "learn from" / "import benchmark account" / "find benchmark".
argument-hint: <account-name> [— way: a (default) | b] [— append | --replace]
allowed-tools: Bash(*), Read, Write, Edit, Glob, WebFetch, Skill
---

# /cheat-learn-from — benchmark account import

The tool's most important early signal source is the **benchmark account**—right after init you have no data, and the equal-weight v0 rubric is astrology. But if you can find an account you want to become like, and import 5-10 of its high/medium/low samples, the tool has an anchor.

Later, when your own calibration_samples ≥ 10, the benchmark's influence naturally weakens—your real data becomes the primary signal source. But benchmark.md is **not deleted**; it's still the reference frame for cheat-seed brainstorming.

## Overview

```
[user: learn this account / start cheat-learn-from]
  ↓
[Phase 0: check benchmark status]
  ↓
[Phase 1: choose input method (Way a default)]
  ↓
[Phase 2: collect material]
  Way a: user pastes N script texts + data
  Way b: use whisper to transcribe videos in the samples/ directory
  ↓
[Phase 3: ask each sample's "impression judgment" (high/medium/low + why)]
  ↓
[Phase 4: Claude extracts patterns + derives rubric signals]
  ↓
[Phase 5: user review → revise → write to disk]
  ↓
[Phase 6: write benchmark.md / script_patterns.md / rubric_notes.md]
  ↓
[Phase 7: update state.benchmark_status]
```

## Constants

- **MIN_SAMPLES = 3** — minimum 3 samples (fewer can't extract a pattern)
- **RECOMMENDED_SAMPLES = 5-10** — recommended range, balancing signal vs user effort
- **MAX_SAMPLES_PER_RUN = 15** — single-import cap—more than this and Claude's context is insufficient + the user is tired
- **DEFAULT_WAY = a** — Way a is simple + accurate, the default

## Inputs

| Required | Source |
|---|---|
| `<account-name>` | user argument; if missing, ask |
| `.cheat-state.json` | state file |
| Way a: the script texts + data the user pastes | conversation |
| Way b: video files like `samples/<account-name>/*.mp4` | downloaded in advance by the user |

## Workflow

### Phase 0: check benchmark status

Read the `benchmark_status` in `.cheat-state.json`:

| Status | Handling |
|---|---|
| `none` | first import—continue to Phase 1 |
| `pending` | the user previously agreed to find one later—continue to Phase 1 |
| `imported` (benchmark already exists) | ask "you already have benchmark [current name], N samples. What do you want to do? a) append new videos to the current benchmark  b) replace with a new benchmark  c) just look, don't change" |

Argument parsing:
- `--append` → append to the existing benchmark
- `--replace <new-name>` → replace with a new benchmark (the old one archived to benchmark.archived/)
- no flag + benchmark already exists → go through the question above

### Phase 1: choose input method (**two independent dimensions**)

Each sample = **script** + **data**. How you get each is independent—you can mix and match.

#### Phase 1a: script source (how to get the script)

```
How to get the script?

a) **Paste text (simplest, recommended)**
   - You've organized it / extracted it with a tool—paste it directly into the conversation
   - Tool recommendations (ordered by convenience):

     Douyin / Xiaohongshu:
     - WeChat mini-program "Qingdou" — paste the video link → auto-extract the script + comments. Fastest
     - Similar tools: "video parsing assistant" / "short-video script extraction" mini-programs
     - Usually have a free quota, heavy use is paid

     Bilibili / YouTube:
     - The video page has a "show subtitles/transcript" button (if the creator enabled it)
     - Third-party: DownSub / SaveSubs / yt-dlp --write-auto-sub

     WeChat official account / Substack:
     - Just copy the webpage text

b) **whisper transcribe the video file**
   - You've downloaded the video to samples/<account-name>/<video>/source.mp4
   - Needs whisper-cpp + ffmpeg installed (see adapters/script-extraction/whisper/README.md)
   - Transcription may have typos / missing words / inaccurate punctuation—less accurate than a

c) **Skip the script, use metadata + impression only**
   - You can't get the script and don't want to bother with a tool
   - Consequence: patterns can't be extracted deeply (only title / data / your impression), but the rubric signal is still ok
   - Suitable for "set it up quickly first, fill in later"

Reply a / b / c.
```

#### Phase 1b: data source (how to get plays/likes/comments)

```
How to get the data (plays / likes / comments / shares)?

a) **Fill in numbers manually (simplest)**
   - Check the account backend or video page, tell me the numbers
   - No tools needed

b) **Adapter auto-fetch (if configured)**
   - You've installed a perf-data adapter (e.g. douyin-session)
   - Give me the video URL, the tool fetches the data + top comments itself
   - Comment data is more complete (manual fill only tells me numbers, the adapter can get the actual comment text)

Reply a / b.
```

**The most common combinations**:
- Zero-dependency path: 1a + 1b (paste text + fill manually)—5 minutes done
- Comment-quality priority: 1a + 2b (paste text + adapter fetch)—use this if you've installed an adapter
- Can't-get-script fallback: 1b + 1b (whisper + manual fill)

### Phase 2: collect material

Take the path corresponding to the Phase 1a + 1b combination.

**General discipline**: each sample must have at minimum (script or transcript or an N/A marker) + data (4 basics: plays/likes/comments/shares).

#### Path A: paste text (Phase 1a=a)

```
Good. Let's go one at a time. Minimum 3, recommended 5-10.

Paste the whole first script below (paragraph form, not subtitle format):
```

Receive the script → compute video_id (sha256(script_content)[:12]) → proceed to Phase 2 data collection.

#### Path B: whisper transcription (Phase 1a=b)

```
First confirm whisper is installed:

[run `command -v whisper-cpp` or `command -v whisper` to detect]

If not installed:
  ❌ whisper isn't installed. Pick one:
  - brew install whisper-cpp (recommended—fast)
  - pip install openai-whisper (Python, slower)
  - switch back to Path A and paste text yourself (a mini-program like Qingdou recommended)

Once installed: put the video file at samples/<account-name>/<video-name>/source.mp4
(one subdirectory per video)

Once placed, tell me "placed N", and I'll transcribe.
```

After the user places them:
1. Glob `samples/<account-name>/*/source.*` to find video files
2. For each video, run `bash adapters/script-extraction/whisper/run.sh <video> samples/<account-name>/<id>/`
3. Report failed ones but continue with the others
4. Proceed to Phase 2 data collection

#### Path C: skip the script (Phase 1a=c)

Proceed directly to Phase 2 data collection—tell the user "without a script, the patterns I can extract are limited to title-level / your impression; the rubric signal is extracted normally".

#### Phase 2 data collection (Phase 1b=a manual / b adapter)

**If Phase 1b=a (manual fill)**:

```
First sample's data: tell me
- title
- play count
- likes
- comment count (not the comment content, the number)
- shares / reposts

Any format, as long as it's recognizable. For example:
  "Title: how to stop expecting
   Plays: 710k / likes 24k / comments 899 / shares 18k"

If you can also paste the top 5-10 comments (with like counts) it's even better—pattern extraction can dig to the meme layer.
```

**If Phase 1b=b (adapter)**:

```
You said you've installed an adapter (e.g. douyin-session). Give me each video's URL,
and I'll run the adapter to auto-fetch data + top comments.

First URL:
```

Receive the URL → call the corresponding adapter → write data + comments to samples/<account-name>/<id>/meta.md.

**General**: keep asking for the 2nd / 3rd / ... sample; when the user says "enough" or MAX_SAMPLES_PER_RUN is reached, proceed to Phase 3.

### Phase 3: ask the "impression judgment"

For each sample (whether Way a or b), after collecting the data **additionally ask for the impression**:

```
After reading / listening to this video, your impression—does it count for this account as:
  a) high-performing sample (a flagship / what you want to become)
  b) medium-performing sample (ordinary level / neither here nor there)
  c) low-performing sample (not representative of this account / not what you want to become)

Why? (one sentence—this judgment tells me more about the style you want to do than the data does)
```

Record (impression_label, impression_reason) in memory.

> Note: the impression **can** conflict with the data—e.g. one with high data but the user feels "not a flagship". This conflict is itself a useful signal, record it.

### Phase 4: Claude extracts patterns + derives rubric signals

Read all (script, data, impression) → analyze:

#### 4a. Script patterns

Extract per the cheat-sheet framework of script_patterns.md:
- opening hook: distribution across 3 types (scene immersion / IS parody / data reversal)
- body structure: how many sections / how it's cut
- sentence form / length / rhythm: short or long sentences, any signature sentence patterns
- emotional markers / dual voice
- acknowledgments section / ending
- high-frequency vocabulary / vocabulary style

Output N concrete patterns (each citing a specific sample as evidence).

#### 4b. Rubric signals (**qualitative only, no numeric weights**)

Score the 7 dimensions for each sample (using generic dimensions), then look at:
- which dimensions are commonly high in high-performing samples (per user impression)?
- which dimensions are commonly low in low-performing samples?
- which dimensions show no difference between high/low samples (meaning they're not key dimensions)?

Output **qualitative directions** (not numeric weights):
- "ER looks important" (3/3 high samples ER ≥4)
- "SR looks insignificant" (no difference in SR distribution between high/low samples)
- "high-MS samples show clear meme bursts in the comments"

### Phase 5: user review

Show all results to the user at once:

```
From the N benchmark videos you gave, I extracted:

📝 N script patterns:
  1. **[Pattern 1 name]**: [one-sentence description] → evidence: [sample X / Y]
  2. ...

🎯 Rubric qualitative signals:
  - Dimensions that look important: ER / QL / MS (each supported by N high samples)
  - Dimensions that look insignificant: SR / NA
  - Initial suggestion: your benchmark account is [emotion+punchline-driven] / [data-driven] / [analogy-teaching] / ...
  - **No numeric weights given**—fitting 5-10 samples easily overfits; use as a tier-2 signal first

🎨 Topic-direction sense:
  - Approximate topic distribution: [topic A 40% / topic B 30% / ...]
  - Tone: [one sentence]

Reply "ok" and I write to disk,
or point out which patterns / signals you disagree with ("Pattern X seems off" / "Rubric signal Y is wrong").
```

User feedback loop:
- "ok" → Phase 6 write to disk
- user challenges → Claude revises → re-display → until confirmed

### Phase 6: write to disk

#### 6a. benchmark.md

Per the [templates/benchmark.template.md] format, write to `<user-channel>/benchmark.md`:
- account info (account name, URL, tone, follower scale—user-provided)
- the imported samples table
- base rubric derivation (qualitative only)
- topic-direction sense

If `--append` → append new rows to the existing benchmark.md samples table + re-extract patterns; don't rewrite the whole file.
If `--replace` → move the existing benchmark.md to `benchmark.archived/<old-account>_<date>.md`, write the new one.

#### 6b. samples/<account-name>/

Create a subdirectory for each sample:
```
samples/<account-name>/<video-id>/
├── source.mp4 (only with Way b, not with Way a)
├── transcript.md (written from the pasted text / transcribed by whisper)
└── meta.md (title / data / impression / impression reason)
```

#### 6c. script_patterns.md

Add a new section in `<user-channel>/script_patterns.md`:

```markdown
## Borrowed from benchmark [account-name] (imported on YYYY-MM-DD, N samples)

> These patterns come from the benchmark account—**Imported, untested on my channel**.
> After live verification (run ≥2 times + retro confirms it works), remove this marker and promote to a formal pattern.

### Pattern A: [one-line name]
**From**: [sample X]
**Description**: [detailed]

### Pattern B: ...
```

#### 6d. rubric_notes.md

Add / update the "benchmark-derived initial signals" section in `<user-channel>/rubric_notes.md`:

```markdown
## Benchmark-derived initial signals

> From the benchmark account [account-name] in benchmark.md (N=N samples, imported on YYYY-MM-DD).
> **Qualitative direction only, not adopted as numeric weights**—fitting 5-10 samples easily overfits.
> **Decide later** whether to adjust weights when you formally bump after your own N≥5 calibration samples.

- Dimensions that look important: ER / QL / ...
- Dimensions that look insignificant: SR / NA / ...
- Claude's initial suggestion: [one-sentence qualitative]
```

### Phase 7: update the state file

```json
{
  "benchmark_status": "imported",
  "benchmark_name": "<account-name>",
  "benchmark_sample_count": <N>
}
```

## Key Rules

1. **Way a default**—simple + accurate. Way b is only the fallback for "can't find the script, only have the video"
2. **Must ask the impression**—extracting patterns from the transcript alone easily catches the surface; adding the user's impression digs deeper
3. **Rubric signals qualitative only**—no numeric weights directly. Fitting 5-10 samples overfits
4. **Patterns marked untested by default**—to avoid polluting the user's own pattern library
5. **Don't fetch videos directly**—downloading is the user's job, to avoid TOS + anti-scraping
6. **Re-runnable**—`--append` adds new videos, `--replace` swaps accounts
7. **MIN_SAMPLES = 3**: fewer than 3 can't extract a pattern, refuse to continue

## Refusals

- "Skip the impression judgment, just extract" → refuse. The impression is a key input
- "I can only give 1 sample" → refuse. Minimum 3
- "Just give me numeric weights" → refuse. Phase 4 only gives qualitative signals
- "Can you not write a transcript file, just extract in memory" → no. Persisting the transcript is the basis for the later cheat-retro Phase 4b diff
- "Download the benchmark videos for me" → refuse. Guide the user to download themselves with yt-dlp / BBDown, etc.

## Integration

- Upstream: `/cheat-init` Phase 2.5 **strongly recommends** running `/cheat-learn-from` for cold-start users; **optional** for calibration users
- Upstream: `/cheat-status` keeps reminding when `benchmark_status=pending` + >24h since init
- Downstream: `/cheat-seed` reads benchmark.md when brainstorming → knows the user's benchmark direction
- Downstream: `script_patterns.md` gets a new section; cheat-seed picks a structure per the patterns when writing a draft
- Downstream: `rubric_notes.md` gets a benchmark-derived-signals section, used as one reference at cheat-bump time
- N≥10 prompt: `cheat-status` prompts when the user's calibration_samples ≥10 "you have enough of your own data, the benchmark's influence fades out (kept as a sanity check)"

## When the benchmark fades out

Not a hard sample count, but **Claude judges "whether the user's data signal has exceeded the benchmark"**:

- **Default reference**: calibration_samples ≥ 10 → benchmark influence fades out
- **Can go earlier**: N=5 but ≥3 of the user's (score, actuals) pairs are inconsistent with the benchmark pattern—meaning your account has walked off the benchmark's path
- **Can go later**: N=15 but the user's samples are all very similar (all the same kind of content), the benchmark still has signal value

The judgment conditions + defaults are implemented in cheat-status trigger #19 / cheat-seed Phase 0.

**After fading out**:
- cheat-seed brainstorm still reads benchmark.md, but at a **lower priority than the user's own predictions/**
- the benchmark-signals section of rubric_notes marks `**Status: superseded by user data**`, not deleted but no longer dominant
- benchmark.md is **not deleted**—kept as a sanity check (to see whether your account really deviates too far from the benchmark's direction)

**Anytime the user wants**: run `/cheat-learn-from --replace none` to fully remove the benchmark influence

## Difference from other skills

| Skill | Use |
|---|---|
| `/cheat-learn-from` | import patterns / rubric signals **from a benchmark account** (one-time / occasional append) |
| `/cheat-seed` | brainstorm topics + write a draft (reads benchmark.md for reference) |
| `/cheat-trends` | fetch today's trends (unrelated to the benchmark) |
| `/cheat-bump` | upgrade the rubric (uses the user's own real data after N≥5, not the benchmark signals directly) |
