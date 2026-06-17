# Benchmark account: [BENCHMARK-NAME]

> **This file is created and maintained by `/cheat-learn-from`.**
>
> Early on, the tool derives **a lot** of its rubric / pattern / topic direction from here—this is your anchor when you just init'd and don't have your own history yet.
>
> Once you accumulate N≥10 calibration samples, the benchmark's influence **naturally weakens**—your real data becomes the primary signal. But the benchmark isn't deleted, it's kept as a sanity check (to see whether your account really deviates from the benchmark's direction).
>
> Anytime you can:
> - **append** benchmark videos: `/cheat-learn-from --append <new-videos>`
> - **replace** the benchmark account: `/cheat-learn-from --replace <new-account>`

---

## Account info

- **Name**: [benchmark account name]
- **Platform**: [Douyin / Bilibili / YouTube / WeChat official account / ...]
- **URL**: [account homepage]
- **Follower scale**: [user-provided, for reference—e.g. "10k / 100k / 1M"]
- **Style / tone**: [user description—e.g. "knowledge / academic parody" / "personal ranting" / "tech tutorial"]
- **Import date**: [YYYY-MM-DD]
- **Sample count**: N

---

## Imported samples

| # | Video title | Plays | Likes | Comments | Shares | Your impression | transcript |
|---|---|---|---|---|---|---|---|
| 1 | [example] how to stop expecting | 710k | 24k | 899 | 18k | high | samples/[BENCHMARK-NAME]/ab61ed09/transcript.md |
| 2 | [example] boss nonsense | 390k | 12k | 567 | 7.9k | medium | samples/[BENCHMARK-NAME]/5fe5d869/transcript.md |
| 3 | [example] who asked you | 110k | 3.8k | 198 | 2.7k | low | samples/[BENCHMARK-NAME]/8b5627e6/transcript.md |

> **Impression record**: high / medium / low is your **subjective** judgment after watching the video of "does it count as a flagship for this account"—not data-driven, an intuitive judgment. This judgment tells Claude more about the style you want to do than the data does.

---

## Base rubric derivation (one-time at init, **qualitative direction only**)

> Based on observing N benchmark samples, Claude summarizes which dimensions look correlated with "high performance" and which don't.
> **No numeric weights directly**—fitting 5-10 samples easily overfits. Give the direction, the user decides whether to adjust weights in rubric_notes.md.

### Dimensions common to high-performing samples (look important)

- [example] **ER (Emotional Resonance) high**: 3/3 high-performing samples have a strong emotional anchor
- [example] **QL (Quotable Lines) high**: 3/3 high-performing samples have ≥2 standalone-spreadable punchlines
- [example] **MS (Memetic Shareability) high**: 3/3 high-performing samples show reused sentence patterns in the comments

### Dimensions common to low-performing samples (look unimportant)

- [example] **SR (Social Resonance) insignificant**: even SR=4 in low-performing samples didn't help
- [example] **NA (Narrativity) insignificant**: no clear difference in NA distribution between high/low samples

### Claude's initial suggestion

- [example] your benchmark account looks **emotion-resonance + punchline** driven
- Suggest initial rubric weights ×1.5 on ER / QL / MS (if enabled)
- **But please wait until you run 5+ calibration pieces of your own before formally bumping**—5 benchmark samples aren't enough to conclude

See the "benchmark-derived initial signals" section of [rubric_notes.md](rubric_notes.md).

---

## Base patterns derivation

See the "Borrowed from benchmark [BENCHMARK-NAME]" section of [script_patterns.md](script_patterns.md).

Each pattern is marked **Imported, untested on my channel**—your channel may not apply; remove the marker after live verification (run ≥2 times + retro confirms it works).

---

## Topic-direction sense

> cheat-seed brainstorm reads here—gives suggestions based on the benchmark account's topic distribution.

[example] topic types the benchmark account often makes:
- crush / emotional withdrawal (~40%)
- academic-issue parody (~30%)
- workplace observation (~20%)
- social-issue commentary (~10%)

> You don't have to do exactly the same topics—this is just a reference frame.
> cheat-seed Mode A/B/C still prioritizes what you actually want to make.

---

## Maintenance history

| Date | Operation | Details |
|---|---|---|
| YYYY-MM-DD | first import | N=3 samples, method [way a paste text / way b whisper] |

---

## When it fades out later

- When `state.calibration_samples >= 10`, cheat-status prompts "you have enough of your own data, the benchmark is mainly a sanity check now, no longer dominant"
- But benchmark.md is **not deleted**—it's still the reference frame for cheat-seed brainstorm
- If the benchmark account's style itself changed / you no longer want to benchmark it → run `/cheat-learn-from --replace <none>` to remove (history kept in the file, but cheat-seed no longer reads it)
