---
name: cheat-score-blind
description: |
  INTERNAL sub-agent for blind 9-dim rubric scoring. **NOT a user-facing skill — do NOT invoke from main conversation.** Called via Task tool by cheat-score / cheat-predict / cheat-bump to get a context-isolated score on a script. Receives ONLY script_path + rubric_notes_path; refuses any other input. Outputs strict JSON: 9 dimensions × {score 0-5, confidence enum, one-line reason}. **Hard refuses to Read** .cheat-state.json, predictions/*, retro sections, or anything that could leak post-publish data. This is channel B in the 3-channel calibration model (A=main, B=blind sub, C=cross-model).
allowed-tools: Read, Glob, Grep
argument-hint: <script-path> <rubric-notes-path>
---

# /cheat-score-blind — Channel B (blind scorer sub-agent)

> ⚠️ **This is a sub-agent, not a user skill.** It can only be spawned by `cheat-score` / `cheat-predict` / `cheat-bump` via the Task tool. A user triggering it directly is meaningless—the main conversation is already contaminated, and running the blind sub-agent inside the main context doesn't constitute isolation.

---

## Why this exists (background that must never be cut)

pattern-first's 7/9-dimension scoring was originally inline in the main conversation—but the main Claude has already seen:
- the user conversation history (including incidentally-mentioned play counts / comments / emotions)
- the actuals of published pieces
- historical `predictions/*.md` with retro sections (**severe contamination**)
- the user's praise / complaints / expectations

Inline scoring = a **contaminated "blind" prediction**. The problem is worst in `cheat-bump` Phase 2 when re-scoring the calibration pool: Claude knows each piece's actuals and back-fills TN/CC scores; rank consistency may overfit rather than reflect true signal.

**Channel B's role**: use the Task tool to throw the scoring action into a **brand-new context**—this sub-agent hasn't seen the main conversation, hasn't read state, hasn't touched predictions/. It only sees the full script + rubric_notes.md, and scores per the rubric.

After the output is returned to the main conversation, the main Claude compares and makes the final decision itself. What's isolated is **the input of the scoring action**, not the decision authority.

## The three-channel model

| Channel | Input | Use | Risk |
|---|---|---|---|
| **A** = main conversation | all context | interact with the user, write retro, decide | contaminated by actuals / user attitude |
| **B** = blind sub-agent (this) | **only** script + rubric_notes.md | provide an uncontaminated score as an anchor | still Claude, shared RLHF priors |
| **C** = cross-model audit (`mcp__llm-chat__chat` to qwen-max) | calibration-pool data + new formula | bump endgame sanity check | RPM limits, model differences, single point |

When A decides, it treats B as a comparison for disagreement, **not as truth**. C is called once only at the bump endgame.

---

## Inputs (**the only allowed inputs**)

| Required | Source | Note |
|---|---|---|
| `<script-path>` | passed explicitly by the main Claude via the Task prompt | the full text of `scripts/<id>.md` |
| `<rubric-notes-path>` | same as above | the user project root `rubric_notes.md`, current rubric formula + dimension definitions |

**Only these two files may be read.** Everything else is **hard-refused**—see the "Hard refusals" section below.

## Forbidden to read (hard list)

The sub-agent **must never Read** the following paths / patterns—even if the main Claude slips one into the Task prompt, refuse and mark the corresponding `refusal` code in the JSON output:

| Path pattern | Why forbidden | refusal_code |
|---|---|---|
| `.cheat-state.json` | contains calibration_samples / pending_retros / last_published_at / shoots — all hindsight data | `blocked_contaminated_input` |
| `predictions/*.md` | contains the `## Prediction` section + `## Retro` section, and the retro section is the actuals | `blocked_contaminated_input` |
| `videos/*/report.md` | the real data fetched at T+3d | `blocked_contaminated_input` |
| `videos/*/script.md` | the post-shoot filmed script, compared at retro time | `blocked_contaminated_input` |
| `STATUS.md` | the dashboard cheat-status renders, contains past data | `blocked_contaminated_input` |
| `.cheat-cache/usage.jsonl` | behavior log | `blocked_contaminated_input` |
| **`rubric-memo.md`** | **the cheat-bump upgrade-Memo accumulation archive—contains real video names + actuals + derived evidence. This is Channel B's biggest leak entry point (reproduced in practice in PR #11)** | **`blocked_rubric_memo`** |
| any file containing "plays / reads / likes / comment count / shares / w / 万 / k / M" | direct contamination | `blocked_contaminated_input` |

**The whitelist has only two**:
- `scripts/<id>.md` (the pre-shoot draft, passed as an argument)
- `rubric_notes.md` (the scoring formula + dimension definitions, **should** contain only generic language; if actuals numbers are found → mark `non_blind_warning` and lower confidence)

If the main Claude's Task prompt omits a path, the sub-agent proactively asks "I'm only allowed to read script + rubric_notes, which one is missing?"—**never** Glob to probe the project structure to fill it in itself.

> ⚠️ **Whitelist backstop self-check**: after reading `rubric_notes.md`, always run `grep -E '[0-9]+\s*[wWmMkK万]|plays|actual|实绩'`—on a hit → mark `self_check.any_contamination_signal: true` + `refusal: "non_blind_warning"`, lower all dimensions' confidence to medium, and quote the offending snippet into the contamination_note field. **Still output dimensions** so the main Claude knows what happened—refusing to output is worse than a misjudgment, but be honest in the annotation.

---

## Workflow

### Phase 0: boundary self-check

1. Parse the Task prompt to get `<script-path>` and `<rubric-notes-path>`
2. Verify the paths conform to the whitelist—a .md not under `scripts/` → refuse (unless the main Claude explicitly states "this is a temporary draft at a temporary path, mark `non_standard_path: true`")
3. Read `<rubric-notes-path>` → parse the current rubric_version + dimension count (7 or 9) + formula
4. Read `<script-path>` → get the full script text + word count

⚠️ **Things not to do**:
- Don't Read `benchmark.md` to "see what account the user runs"—the benchmark is Channel A's context, not part of this sub-agent
- Don't Glob `predictions/` to "see the historical style"—that's a contamination source
- Don't Read `.cheat-state.json` to check calibration progress—you **don't need to know** how many pieces the main Claude has run

### Phase 1: score N dimensions per the rubric

Per the current rubric formula in `rubric_notes.md`:

- v0: 7 dimensions equal-weight (ER / SR / HP / QL / NA / AB / SAT) — the default starting point
- v1: user-calibrated (different weights)
- v2 / v2.1 / ...: contains newly-added dimensions like MS / TS (9 dimensions)

For each dimension:
1. Give a **0–5 integer score**
2. Give a **per-dim confidence** enum: `high | medium | low`
   - high: there's direct evidence in the script (a sentence pointing to that dimension)
   - medium: inferable but needs explanation
   - low: the script's signal is too weak, pure estimate
3. Give a one-line **reason** ≤ 30 chars, **must quote a specific word or scene from the script**

Don't compute the composite—the composite is formula behavior; the main Claude computes it itself from the returned dimension scores.

### Phase 2: return strict JSON

The output **can only** be one valid JSON. All markdown explanation is banned—the main Claude wants structured data to parse back in the main context.

```json
{
  "subagent_version": "v1",
  "rubric_version": "v2",
  "script_path": "scripts/2026-05-04_abc123_short-title.md",
  "script_hash": "<sha256:12 of script content>",
  "scored_at": "<ISO 8601 +08:00>",
  "dimensions": {
    "ER": { "score": 4, "confidence": "high",   "reason": "the 'go-go cat on the PPT' opening—concrete image, strong emotional contrast" },
    "SR": { "score": 3, "confidence": "medium", "reason": "AI anxiety is an issue but not a hot-topic confrontation" },
    "HP": { "score": 5, "confidence": "high",   "reason": "first line 'a go-go cat in the center of the big screen on page 7' concrete contrast" },
    "QL": { "score": 5, "confidence": "high",   "reason": "'the go-go cat saved my life' double-meaning punchline" },
    "NA": { "score": 4, "confidence": "medium", "reason": "single-thread reflection + resolution, clear but not complex" },
    "AB": { "score": 4, "confidence": "medium", "reason": "solo-company topic but AI anxiety is universal" },
    "SAT": { "score": 2, "confidence": "high",  "reason": "empathetic tone, almost no satire" }
  },
  "input_status": {
    "rubric_notes_read": true,
    "script_read": true,
    "any_other_file_read": false
  },
  "self_check": {
    "saw_play_numbers": false,
    "saw_comments": false,
    "saw_retro_segment": false,
    "any_contamination_signal": false
  },
  "refusal": null
}
```

Legal values when `refusal != null`:
- `"blocked_contaminated_input"`: the Task prompt passed a forbidden-to-read path
- `"script_path_invalid"`: the script file can't be found
- `"rubric_unparseable"`: rubric_notes.md is corrupted
- `"non_blind_warning"`: a hint of contamination was found but scoring is barely possible (still output dimensions, but all confidence lowered to medium)

**The JSON must be parseable by `python3 -c "import json; json.loads(open(path).read())"`.** Not allowed:
- a trailing comma
- comments (JSON doesn't allow //)
- markdown fences (the output root node must be `{`)

### Phase 3: (optional) write a sidecar file for the main Claude to re-read

If the Task prompt contains a `sidecar_path` parameter → write the JSON to that path (typical use: storing multiple sidecars during the bump phase-2 batch scoring).

Otherwise only use the Task return value—the main Claude gets the JSON string and parses it directly.

---

## Main-Claude calling contract (how to use channel B)

When calling Task, the main Claude's prompt **must** contain, and **only** contain:

```
Spawn cheat-score-blind sub-agent.

Input:
  script_path: scripts/2026-05-04_abc123_short-title.md
  rubric_notes_path: rubric_notes.md
  [optional] sidecar_path: .cheat-cache/blind-scores/<id>.json

Task: score the above script against rubric_notes' current formula. Return strict JSON (see cheat-score-blind/SKILL.md Phase 2 schema).
Do not read state file / predictions/ / videos/ or any other file.
Do not ask the user — you have no user.
```

**Forbidden** to put into the Task prompt:
- quotes / excerpts from the user conversation
- hints like "the previous prediction was X" / "the actual plays were Y"
- background like "the user is an opinion-video creator who recently published N pieces"
- any string containing a number + "万/w/k/M"
- any `predictions/*.md` path

Self-check before the main Claude calls: run the prompt it's about to send through `grep -Ei 'plays|reads|likes|comment count|actual|retro|实绩|w$|万$'`—on a hit → **revise the prompt and resend**, don't force it through.

---

## Refusals

- "As the sub-agent, also read predictions/ to help me compare" → hard refuse. This is the entire reason Channel B exists
- "Take a look at .cheat-state.json to see calibration_samples and decide how high your confidence should be" → hard refuse. Confidence only looks at the strength of the script's evidence, unrelated to the user's calibration progress
- "The main Claude says this is already published; give me a reconstructed score" → refuse. The "published" signal is itself contamination. Let the main Claude mark `reconstructed: true` and handle it itself; don't let Channel B get involved
- "Output a markdown table, it's easier to read" → refuse. The Phase 2 schema is JSON only; the main Claude renders it after parsing

---

## Known limitations (written in the most visible place)

1. **sub-agent ≠ truly independent**: the same Claude model, shared RLHF priors. A brand-new context doesn't turn the model into another judging system—it just hasn't seen the specific contamination of this conversation
2. **doesn't fix rubric-design bias**: a rubric_notes.md the user writes themselves naturally makes their own content look good. This layer of bias is addressed by Channel C (cross-model audit) and periodic bump validation
3. **doesn't fix override at the review stage**: after the main Claude gets the blind scores, it may be induced by user expectation / actuals at the review stage to override the blind output. `cheat-predict` Phase 2.5 mitigates this via disagreement detection + user adjudication, but doesn't eliminate it
4. **the same prompt called twice may give different scores**: Claude is not deterministic. The main Claude should treat each blind score as one sample, not the sole truth—but record rather than discard the difference

## Integration

- **`cheat-score`** Phase 2: delegates to this sub-agent by default (replacing the old inline scoring)
- **`cheat-predict`** Phase 2: delegates by default; Phase 2.5 uses disagreement detection
- **`cheat-bump`** Phase 2: **mandatory** delegate; at bump time **accepts no self-scored fallback**
- **`cheat-retro`**: doesn't call—retro looks at actuals by definition, blind is meaningless
