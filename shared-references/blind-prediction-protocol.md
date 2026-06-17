# Blind Prediction Protocol

Referenced by these sub-skills: `cheat-predict`, `cheat-retro`, the main SKILL.md.

This is the full spec of project principle #1. Any sub-skill must execute this protocol before writing a prediction.

---

## Core definition

**Blind prediction**: a prediction completed **before** the predictor (human or model) has seen any real post-publish performance data about the piece.

Once a prediction is written into the `## Prediction` section of `predictions/*.md`, that section is **immutable**—you can only append a `## Retro` section at the end of the file, not modify any character of the prediction section.

---

## The "has seen data" boundary (key, often violated)

Any of the following being true → no longer blind, **writing a prediction is forbidden**:

| Information | Breaks blind? | Exception |
|---|---|---|
| The piece's play count / read count on any platform | ✗ breaks | none |
| The piece's like / comment / share counts | ✗ breaks | none |
| The piece's specific comment content | ✗ breaks | none |
| The piece's algorithmic recommendation slot / trending-chart position | ✗ breaks | none |
| Post-publish screenshots / backend data of the piece | ✗ breaks | none |
| The performance of **others'** pieces published in the same period | ○ doesn't break | — |
| The performance of **historically similar-topic** pieces | ○ doesn't break (this is exactly what anchor comparison does) | — |
| The piece's **pre-publish** script content | ○ doesn't break | this is the prediction's input |
| The user's verbal "I feel this one's ok" | △ caution | the user's subjective feeling isn't "data", but note the user bias in the prediction |

**Judgment shortcut**: if a piece of information **can only be obtained after the piece is published**, it counts as "data".

---

## Situations the predictor must proactively declare

Before starting `cheat-predict`, the sub-skill must self-check and **proactively declare** to the user:

1. **The piece has been published more than RETRO_WINDOW_DAYS days** (default 3 days) → must refuse to write a "prediction", instead log it as `**Reconstructed retrospective**`, clearly marked non-prediction
2. **The piece is published but < RETRO_WINDOW_DAYS days, and the user hasn't revealed any data** → allow a blind prediction, but mark the file header `published_before_prediction: true` + `blind_status: confirmed_no_data_seen`
3. **The user has already pasted any subsequent data in the conversation** → handle as #1, log as reconstructed

`BLIND_CHECK=strict` (default): any of the above breaking conditions hitting → **refuse to execute**.
`BLIND_CHECK=lenient`: warn only + force the annotation, allow continuing—only for offline testing or academic drills, **not recommended for real calibration**.

---

## The engineering boundary of immutability

The non-modifiability of the `## Prediction` section is a **UX promise**, enforced at the hook layer:

- `hooks/prediction-immutability.sh` checks files under `predictions/` on PreToolUse(Edit|Write)
- any diff between `## Prediction` and the next level-2 heading → exit 1, block
- appending to the `## Retro` section → let through

**Forbidden "bypass" patterns** (sub-skills must refuse):
- "Rewrite the prediction section a bit more accurately" → refuse. If there's a legitimate reason to redo, create a new file `<original filename>_redo.md`, keep the original
- "My probability distribution is off by 0.5%, let me fix it" → refuse. Append to the retro section `Correction: original distribution X% should be Y%, typo found on <date>`
- "I didn't consider SR=4 earlier, re-score it" → refuse. Same path as above

The only scenario where editing the prediction section is allowed: a **pure markdown formatting error** (wrong heading level, broken list bullet), and the user explicitly states it's a formatting fix. Even then the hook still blocks, and the user must explicitly bypass (manually set the environment variable `CHEAT_BYPASS_IMMUTABILITY=1` once)—the bypass should leave a trace in git history.

---

## Filename convention (**consistent in three places**)

One content, three files, **named with the same `<date>_<id>_<short>`**:

```
scripts/<date>_<id>_<short>.md        ← pre-shoot draft (written by cheat-seed or the user)
predictions/<date>_<id>_<short>.md    ← immutable prediction (written by cheat-predict)
videos/<date>_<id>_<short>/           ← created only after shooting (by cheat-shoot)
  ├── script.md                       ← the final filmed script the user provides
  └── report.md                       ← T+3d data (written by cheat-retro)
```

- `<date>`: **the date the draft was first written to disk** (i.e. the creation date of `scripts/<id>.md`), not the prediction / shoot / publish date. Reason: keep the ID stable—after a major draft rewrite the hash changes but you still want the file to be traceable
- `<id>`: 12-char sha256 prefix, hashed over the **first-written draft content**. Unchanged after the user edits the draft—for cross-file references
- `<short>`: a 3-8 char short name (Chinese or English) for human recognition

Reconstructed redo: add `_redo` after `<short>`, in all three places:
- `scripts/<date>_<id>_<short>_redo.md`
- `predictions/<date>_<id>_<short>_redo.md`
- `videos/<date>_<id>_<short>_redo/`

The original files are kept (not deleted).

---

## The checklist a sub-skill must do

When `cheat-predict` starts:
1. Read the `BLIND_CHECK` constant
2. Ask the user about the piece's current publish status (not published / published < RETRO_WINDOW_DAYS / published ≥ RETRO_WINDOW_DAYS)
3. Ask whether any subsequent data about the piece was mentioned in the conversation history (if so, self-check the conversation for keywords like "plays/reads/likes/comments")
4. If #2 or #3 hits a breaking condition → handle per the `BLIND_CHECK` mode
5. Only after passing, allow writing `predictions/*.md`

When `cheat-retro` starts:
1. Read the target prediction file
2. **First cache the `## Prediction` section in memory**—any subsequent write to the file must first verify that section is unchanged
3. Fetch data → append the `## Retro` section
4. After writing, **verify again**: the post-write file's `## Prediction` section hash should equal the cache from step 2. Not equal → error and roll back

The main SKILL.md:
- When the user says "rewrite the prediction" / "change the prediction section" / "you predicted wrong before, let me fix it for you", **refuse directly and explain**, guiding them to use the `_redo.md` path

---

## Abnormal-state handling

| Scenario | Handling |
|---|---|
| The prediction file's prediction section was accidentally hand-edited | Don't auto-roll-back (a bigger disruption). The next `cheat-retro` detects the inconsistency → append to the retro section `**Integrity warning**: the prediction section was externally modified at <ISO timestamp>, blindness can't be guaranteed`; the calibration value is downgraded to "reference", not counted in the bump calibration pool |
| The prediction file is lost / deleted | Recover from git log. If unrecoverable → record in `rubric_notes.md` "<id> prediction file lost, the calibration pool is missing this sample" |
| The user was originally cold-start and midway wants to "backfill" the prediction of a published piece | Always log as `**Reconstructed retrospective**`, not counted in the calibration pool—this is a backfill, not a prediction. Can be recorded as an "observation" in `rubric_notes.md` |

---

## Anti-patterns (requests that must be refused)

- "Predict for me, but let me tell you the play count first and you back into it" → refuse. Directly breaks blindness
- "This one was published 5 days ago and the data is out, but pretend you didn't see it, make me a prediction to see if it's accurate" → refuse. Use the `_redo.md` reconstructed path
- "The last prediction was miscalculated, fix the probability distribution for me" → refuse. Explain in the retro section
- "Can you skip the blind check, I have a special reason" → ask the reason; only "formatting fix" is a legitimate bypass reason

---

## Why (why is this so strict)

Blind prediction is the **only signal source** of the entire cheat-on-content calibration loop. Once the prediction section is modified after the fact, all "which dimension was validated / refuted" judgments lose their baseline—you don't know whether you originally predicted right, or fixed it right after the fact.

Calibration value = prediction precision × prediction credibility.
- Prediction precision can be slowly improved via rubric upgrades.
- Prediction credibility, once broken, is unrecoverable—**this is why immutability is enforced at the hook layer, not a gentleman's agreement**.
