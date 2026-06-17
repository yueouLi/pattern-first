# Writing-pattern accumulation (**example / reference—not a user template**)

> ⚠️ **This file is a reference sample, not a user template.** The `script_patterns.md` in your project is the **abstract skeleton** copied from `templates/script_patterns.template.md`, initially empty.
>
> This example shows you "what a fully-filled script_patterns.md looks like"—reverse-engineered from a real "Chinese opinion-video creator, 25+ published videos".
>
> **Don't copy it verbatim**—your channel / tone / audience are completely different, and most of the patterns here won't work for you. Slowly accumulating **your** patterns from your own retros is the tool's core value.
>
> To use a pattern from this file → add it manually in your script_patterns.md, marked `**Imported from example, untested on my channel**`—remove the marker after ≥2 retros validate it.
>
> ---
>
> rubric_notes.md teaches Claude **how to score**, script_patterns.md teaches Claude **how to write**. The two are decoupled—a high-scoring draft isn't necessarily well-written (the rubric missed MS / TS), a well-written draft isn't necessarily high-scoring (structural innovation running outside the patterns).
>
> Example data is from the "video analysis" project (Chinese opinion video, reverse-engineered from 25+ published samples).

---

## ⚠️ Patterns are a toolbox, not a mold (core meta principle)

All the patterns below are **one of the paths reverse-engineered from published samples**, not a template that should be applied by default.

**Counterexample**: using "3-section + acknowledgments + interaction hook" every time—the account's ceiling is just "a stably-made medium hit". **A true viral hit comes from structural innovation**—the reference creator's "she's different" meme burst was outside the patterns.

Before writing, **always answer first**: what is this article's strongest attribute? Then decide which pattern to use. See the "structure-selection cheat sheet" below.

---

## Structure-selection cheat sheet (match by article attribute)

| Article attribute | Suitable structure | Published samples (you fill) | Status |
|---|---|---|---|
| **Strong metaphor** (a concrete vehicle can analogize anything) | **metaphor-first**—open with a scene-immersion metaphor → body translates → meta-parody acknowledgments | e.g. hamster ✓ | example |
| **Strong time dimension** (a day's cycle / phased evolution) | **timeline narrative**—open with time-point switches → name the concept → interweave data | (to be filled) | example |
| **Strong satire/parody (SAT=5)** | **stand-up style**—open with a single-event bit → punchline → expand | (to be filled) | example |
| **Strong data contrast** (cold-data violence) | **data-reversal opening**—a specific number → counterintuitive comparison → data-driven narrative | e.g. housing price ✓ / boss nonsense ✓ | example |
| **Multiple real events / cases** | **case-driven**—open with a landmark event → abstract naming → three-section breakdown | (to be filled) | example |
| **Multiple parallel concepts** | **3-section assembly line**—IS parody → 3 named sections → acknowledgments | (to be filled) | example |
| **Strong scene immersion** (scrolling chat logs late at night / the comment-section scene) | **second-person immersion** → reversal → data → three sections | e.g. stop expecting ✓ | example |
| **Strong reusable sentence pattern (high MS)** | **template core**—the sentence pattern runs through the whole script → an interaction hook activates the template | e.g. stop-expecting "she's different" ✓ | example |

### Usage

Before writing, ask yourself:
1. What is this article's strongest attribute?
2. Which structure in the table corresponds?
3. If the attributes are diverse, which structure lets the strongest attribute reach its maximum?

---

## Core pattern library

### Pattern 1: opening hook, pick one of three (first 3 seconds)

**Never** use "in recent years / hi everyone / today let's talk about". Three validated patterns:

**A. Second-person scene immersion → reversal** (applies: the original has a concrete metaphor / experimental subject / case)
> You run into an X on the street / impulsively pay for Y / but this thing and Z / are essentially the same thing

**B. Parody-of-the-original-style impact statement** (applies: read the original's IS directly when it's already sharp)
> This study only affects people who are still X at 3 a.m.

**C. Throw data directly / a reversal observation** (applies: the original has a strong data point)
> The author scraped X / computed several numbers / average Y / but Z is only W

---

### Pattern 2: compress the body to "strictly 3 observations"

Well-performing scripts all follow the three-section pattern of `the author proposed X observations/concepts/metrics`:

| Video example | The three observations |
|---|---|
| hamster | resource misallocation / obligation-ification of giving / stigmatization of nature |
| stop expecting | QOI (proportion of time thinking about it daily) / WIC (the "what-if" coefficient) / intermittent reinforcement |
| boss nonsense | semantic black hole / TOP10 ranking (opening #1 + ending #10) / the universal formula |

**Strictly 3**—not 4, not 5. When the original has 4-7 concepts, cut to 3—pick the most nameable + most reusable.

**Special handling of the TOP10 list**: keep the head + tail + "the rest you can go look up yourself"—don't lay out all 10.

---

### Pattern 3: stripping / keeping the academic packaging

| Must keep | Must strip |
|---|---|
| self-coined concept names (QOI / WIC / semantic black hole) → an MS source | model names (abbreviations longer than 3 chars) |
| key precise numbers (83.6% / 7.4 items) | sample-size build-up ("312 participants...") |
| the acknowledgments section (if it's itself the MVP) | literature review ("Vlahovic 2012... König 2019...") |
| reversal data points ("system-crash probability up 412%") | limitations discussion |
| punchline sections of the author's original words | experiment-procedure details (unless they're the hook) |

**Judgment principle**: can the audience **restate/reuse** this thing in the comments? Yes → keep; no → cut.

---

### Pattern 4: "I" expression nodes (emotional markers)

In well-performing scripts "I" appears 0-2 times, **always at an emotional climax**—a "time to resonate" cue for the audience.

**Pattern**: each time "I" appears, it must be immediately followed by a high-intensity information point. **Don't say an empty "I think".**

---

### Pattern 5: dual-voice structure (author + user narration)

Each script is **not a user monologue**, but a dual voice of `the author says... the user annotates...`:

- The author's words introduce the **framework** ("the author proposes...")
- The user's words do the **grounded translation** ("the working-person's version" / "meaning" / "in other words" / "in plain words")
- The user's words do the **emotional marking** ("what broke me most" / "the most reversal-y part of the piece" / "even scarier")

**Never** let a section go more than 4 lines without a user grounding word.

---

### Pattern 6: the acknowledgments section isn't mandatory

Judgment principle: only fully quote the acknowledgments section when it **is itself the MVP line** (i.e. can stand alone as a meme). Otherwise replace its function with the closing core punchline.

The acknowledgments section is the core propagation vehicle of some of the reference creator's videos, but other videos broke 300k+ without one. **The MVP line is the killer move.**

---

### Pattern 7: standardized ending structure

```
[reflective MVP section (author's original words or user's distillation)]
[optional: the user's personalized interpretation]
[outro: "no commentary can replace the original / class dismissed"]
```

`No commentary can replace the original / class dismissed` is a fixed outro (the reference creator's signature). **You should build your own signature outro**—the audience recognizes it and it forms a brand.

---

### Pattern 8: sentence length / paragraph rhythm (**the most overlooked**)

**Write drafts in paragraph form** (each paragraph 100-300 chars, commas, periods, natural sentences), **don't write line-by-line subtitle format**—that's the subtitle the editor auto-breaks after the user films, **not the form at writing time**.

- **Writing form (draft-v0.md / script.md)**: full paragraphs
- **Subtitle form (after the video is filmed)**: the editor auto-breaks into 5-15 chars / line
- cheat-seed **only outputs paragraph form** when writing a draft

**Sentence rhythm within a paragraph**:
- **Short sentences predominate**—avoid compound sentences, avoid literary connectors
- Use periods + commas normally, don't fear punctuation
- **Use more tone particles** (e.g. sentence-end softeners, related to your account's style)

**Counterexample** (thesis-style):
> Within the asynchronous social matrix, the monosyllabic onomatopoeia "ha" and its multi-order repetition sequences have evolved into a key social-lubrication protocol.

**Should be written like this** (short-sentence paragraph):
> Have you ever thought about how many "ha"s to type when chatting. "haha" won't do, "hahaha" works, "hahahaha" risks sounding fake, eight "ha"s risks sounding passive-aggressive.

---

### Pattern 9: vocabulary-style cheat sheet

**High-frequency words** (validated effective for the reference creator):
- grounded translation: the working-person's version / meaning / in other words / in plain words / simply put
- reversal markers: but / even scarier / even funnier / the most reversal-y part of the piece
- emotional markers: broke me / scalp tingling / made me re-read it several times / it really is
- rhythm words: ah / just / you see

**Avoid**:
- thesis-style connectors: "secondly" / "this study" / "in summary" / "therefore"
- adjective pile-up: "extremely precise" "very profound"—just give the noun directly
- long, drawn-out modifiers: "a kind of phenomenon based on..."

**You should build your own vocabulary style**—the above is the reference creator's; your channel's tone may be completely different.

---

### Pattern 10: duration target

Well-performing video durations (the reference creator, 3-5min range):
- 1:57 (390k) — the shortest
- 2:11 (110k)
- 2:52 (710k)
- 3:00 (1.24M)

**Don't exceed 3:30** (under the NA=4 weight of the v2 starting point). **Your account may differ**—adjust per the typical_duration_seconds configured at cheat-init.

---

## User script-change history observations (**continuously appended, cheat-retro suggests additions after retros**)

> Each time a retro finds "the user changed X and a clear Y traffic impact appeared", cheat-retro suggests appending a row here.

| Video | What the user cut | What the user added | Traffic impact |
|---|---|---|---|
| example: stop expecting | the EWDM model name + the 312-person sample build-up | — | T+7d 711k (high) |
| example: boss nonsense | the middle 8 of the TOP10 + the acknowledgments section | — | T+4d 396k (high) |

**Conclusion** (the reference creator): the user **systematically cuts** list-style enumeration + academic build-up + model abbreviations. Next time writing the first draft, **don't stuff these in for the user to cut**—cut them directly.

**Your channel's conclusion** (to be filled, after a few retros):
- ……

---

## Newly discovered Patterns (numbering continues)

> When cheat-retro finds a new phenomenon during a retro (a script change brought a clear traffic change, a new pattern appeared in the comments), it suggests appending a new pattern.

### Pattern 11 (example): comment-section interaction hook (from the reference creator's "length of haha")

**Phenomenon**: the "tell me X in the comments" prompt at the end of the video can:
1. **Directly trigger MS (Memetic Shareability)**—explicitly invoke audience-generated content
2. **Lower the comment threshold**—the audience has a concrete answer framework
3. **Generate visible group behavior**—the comment section's collective performance is itself a secondary propagation vehicle

**Trigger condition**: only use when the script has a **reusable concrete dimension**—the audience must know what to fill into the comments.

---

### Pattern 12 (example): opening softening (for heavy issues)

**Phenomenon**: heavy issues like family, childhood trauma, intimate relationships—a direct assertion triggers the audience's "offended" reaction. Add "I think" as a buffer:

| Issue type | The opening should | The emotional words should |
|---|---|---|
| family / trauma / gender | soften with "I think" | be softened ("broke me" → "deeply moved") |
| entertainment / tech / academic-circle in-jokes | direct assertion | be moderately strong |

---

## Maintenance suggestions

- **Keep < 500 lines**—append new patterns after each retro, but also periodically delete refuted old patterns (same lifecycle protocol as rubric_notes.md—see [observation-lifecycle.md](../cheat-on-content/shared-references/observation-lifecycle.md))
- **After the 5th retro**: completely rewrite all the "example"-marked patterns above into your account's tested ones—the examples just show you the format, not the truth
- **A new pattern must have ≥1-sample support**—a single-point observation goes in the bottom "to be verified" section first, ≥2 to be promoted
- Each pattern **must be traceable to a specific video** + data (don't write "the opening hook is important", write "the reference creator's stop-expecting used an IS parody opening, T+7d 710k")
