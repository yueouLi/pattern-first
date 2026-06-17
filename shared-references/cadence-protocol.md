# Cadence Protocol

Referenced by these sub-skills: `cheat-status`, `cheat-recommend`, `cheat-shoot`, `cheat-publish`, the SessionStart hook.

Codifies "what to do on which day"—to avoid the user driving every step. Lets Claude answer at session open "should I shoot / publish / retro now".

---

## Three cadence layers

### Daily (every day / each session open)

1. The SessionStart hook auto-renders a 4-6 line report:
   - 📦 Buffer status (color + count)
   - ⏰ Pending retros due
   - 🎯 Candidate pool top 3 (rough rank)
   - 📅 Last trend-fetch time
   - ⚠️ Key to-do
2. Don't proactively start any action—wait for the user to decide

### Event-level (T+`RETRO_WINDOW_DAYS` days due)

- Anything published-not-retro'd + time reached → highlighted at the top of SessionStart
- User gives data (paste / URL) → `/cheat-retro` auto-runs

### Weekly (the user-decided "batch-processing day")

- Fetch trends (`/cheat-trends`) to refresh the candidate pool
- Check the rubric-bump trigger conditions
- Check whether STATUS.md / rubric_notes.md needs a cleanup

---

## Buffer alert rules

**Buffer = the length of the `state.shoots` array** = the number of videos shot but not published.

`/cheat-shoot` adds a video to `state.shoots`, `/cheat-publish` removes it—the two events being separate keeps buffer tracking accurate.

### Color thresholds (derived from `target_publish_cadence_days`)

`buffer_days = buffer_count × target_publish_cadence_days`

| buffer_days | Color | Meaning | Action |
|---|---|---|---|
| < 1 | 🔴 **red** | alert—the next publish day may have a gap | **must shoot today**, and only the safe-score (top 1, no risk) |
| 1-2 | 🟠 orange | low | should shoot 1-2 |
| 3-5 | 🟢 green | normal | steady rhythm, can shoot or rest |
| > 5 | 🔵 blue | backed up | **pause shooting**, focus on shipping inventory + retro |

**Examples**:
- User cadence = 1 (daily), buffer count = 0 → buffer_days = 0 → 🔴
- User cadence = 7 (weekly), buffer count = 1 → buffer_days = 7 → 🔵 (one piece lasts seven days)
- User cadence = 1, buffer count = 4 → buffer_days = 4 → 🟢

### Flexible cadence (target_publish_cadence_days = null)

The user chose "flexible/irregular" at cheat-init → buffer monitoring is **off**. The SessionStart report only shows "shot not published: N", no color, no alert.

---

## Topic strategy (when `/cheat-recommend` recommends ≥ 2)

When recommending 2 at a time, follow the **1 safe-score + 1 experimental** principle:

### Item 1 (safe-score)

- Ranked top 1-3
- Category **not duplicating** the recent N published (N = max(3, target_publish_cadence_days × 3), to avoid aesthetic fatigue)
- High composite + safe issue (not risky)

### Item 2 (experimental)

- A candidate-pool sample that can verify a **hypothesis to verify** (e.g. an A/B comparison for a new dimension)
- Or verify a **new pattern** (Pattern N of [script_patterns.md](script_patterns.md))
- The composite isn't necessarily top, but it has "information value"—after the retro it can advance the rubric / pattern library

### Buffer-color override of recommendations

| Buffer color | Recommendation-strategy override |
|---|---|
| 🔴 red | **only the top 1 safe-score**—no experimental. "Just getting one shot today is enough" |
| 🟠 orange | 1 safe + 1 experimental, but suggest prioritizing the safe-score |
| 🟢 green | standard 1+1 |
| 🔵 blue | **pause recommendations**—reply "your buffer is backed up, ship inventory first + retro" |

**Key constraints** (followed at any color):
- ≤ 2 consecutive of the same category
- An already-published candidate (marked done) isn't recommended
- A candidate the user actively skipped (marked skip) isn't recommended within 6 months

---

## Cadence meta-rules

By priority (high → low):

1. **Buffer over score**: in a red alert, don't gap out by "waiting for a better topic"—shooting a composite-7.5 safe-score is safer than "waiting for tomorrow's 9.0"
2. **Retro over new shoot**: on the day T+RETRO_WINDOW_DAYS is due, **retro first then consider shooting new**—otherwise the data signal is lost and rubric calibration is harmed
3. **Sync over backlog**: when the buffer is full (blue), don't shoot more, ship first—the timeliness of already-shot topics decays
4. **Experimental at most 1/day**: when shooting 2 a day, at least 1 is a safe-score. **Don't go all-experimental**—the experiment failure rate is too high in cold-start and hurts the calibration rhythm

---

## Standardized "today's workflow" templates

### Situation 1: buffer sufficient + not yet T+3d retro

```
SessionStart report → user decides to shoot/not
├─ shoot → "recommend topics" → cheat-recommend recommends 2 →
│       user picks → /cheat-seed writes a draft (cold-start) or user writes their own →
│       user rewrites → script.md → user shoots → "shot videos/<...>/" → cheat-shoot
└─ don't shoot → wait
```

### Situation 2: buffer sufficient + T+3d retro due

```
SessionStart report contains an ⏰ retro reminder → user gives video URL or pastes data →
cheat-retro auto-runs → write the retro section → check the bump trigger conditions
├─ triggered → propose /cheat-bump (not forced, user decides)
└─ not triggered → wait for the next verification sample
```

### Situation 3: buffer red alert

```
🔴 first line of SessionStart is an alert → user decides
├─ shoot → cheat-recommend only recommends the current top 1 safe-score → shoot immediately
└─ accept the gap risk → user's own call, cheat-status keeps prompting
```

### Situation 4: buffer blue backlog

```
🔵 SessionStart report "backed up" → user decides
├─ publish → "shipped https://..." → cheat-publish → buffer -1
├─ retro → see situation 2
└─ shoot new → cheat-recommend refuses: "your buffer is at N, ship ≤3 first then come back"
```

### Situation 5: periodic batch-processing day (user-triggered)

```
user says "fetch trends" → cheat-trends → candidate pool updated
+ user says "see if the rubric should be bumped" → cheat-status checks the accumulated same-direction deviation
+ user says "check the rubric_notes line count" → cheat-status health check
```

---

## Fallback: when the flow deviates

If a day violates the cadence (buffer=0 but the user forcibly doesn't shoot / backlog ≥10 but the user keeps shooting), the SessionStart report **explicitly annotates**:

```
❌ You haven't published new content for N days (last publish: YYYY-MM-DD),
   buffer = 0, your channel is currently in a "de facto gap" state
```

Or:

```
❌ Your buffer is at N but you're still shooting new,
   N of the past N have gone X days unpublished—there's a timeliness-loss risk
```

**Won't auto-attempt to remedy**—only explicitly report, and the user decides how to get back to the cadence.

---

## Sub-skill responsibility table

| Skill | Cadence responsibility |
|---|---|
| `/cheat-init` | ask the cadence; write `target_publish_cadence_days`; install the SessionStart hook |
| `/cheat-shoot` | add the video folder to state.shoots, buffer +1 |
| `/cheat-publish` | remove the corresponding item from state.shoots, buffer -1 |
| `/cheat-status` | compute buffer + color, output the report |
| `/cheat-recommend` | give recommendations per the buffer color + topic strategy |
| `/cheat-retro` | after the retro, update STATUS (auto-triggers /cheat-status) |
| SessionStart hook | call /cheat-status to render the 4-6 line report, write to STATUS.md |

---

## Key difference: cheat-on-content vs the video-analysis project

| Dimension | Video analysis | cheat-on-content |
|---|---|---|
| Cadence source | default daily (hardcoded in CADENCE.md) | user-filled (cheat-init asks, 4 tiers: daily/every-other-day/weekly/flexible) |
| Buffer thresholds | 0/1/2/3-5/6+ (by "piece") | 0/1-2/3-5/>5 (by "buffer_days"—derived from the user's cadence) |
| 2-recommendation strategy | 1 safe + 1 experimental | same |
| SessionStart report | text constraint in CLAUDE.md + Claude self-discipline | hook-enforced + Claude reads the hook output |
