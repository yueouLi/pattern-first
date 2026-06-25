# State Management (state-file read/write conventions)

Referenced by all sub-skills. `.cheat-state.json` is the **single source of truth** for context shared across sub-skills—any runtime state, accumulated metric, or mode marker is read from here and written back here.

---

## File location

```
<user-content-project>/.cheat-state.json
```

**Never** put it in the global `~/.claude/` or in pattern-first's own directory—one user may maintain multiple content projects, each with independent state.

---

## Full schema

```json
{
  "schema_version": "1.4",
  "skill_version": "1.0.0",

  "rubric_version": "v0",
  "content_form": "opinion-video",
  "typical_duration_seconds": 240,
  "target_publish_cadence_days": 2,
  "rubric_form_mismatch": false,
  "benchmark_status": "none",
  "benchmark_name": null,
  "benchmark_sample_count": 0,
  "baseline_plays": null,

  "calibration_samples": 0,
  "calibration_samples_at_last_bump": 0,

  "data_collection": "manual",
  "pool_status": "none",
  "data_layer": "markdown",

  "hooks_installed": false,
  "enabled_trend_sources": ["manual-paste"],
  "enabled_perf_adapters": [],

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

  "initialized_at": "2026-05-04T15:00:00+08:00"
}
```

### Key changes (v1.4)

Compared to v1.3 (**MINOR but BREAKING for blind channel integrity**—existing users must run migrate):

- **rubric file split**: `rubric_notes.md` → `rubric_notes.md` (formula + generic dimension definitions; blind whitelist) + `rubric-memo.md` (upgrade Memo with evidence + derived evidence; blind hard-forbidden to read)
- **state fields unchanged**—only the `schema_version` bump marks that existing users must run the migration to split the existing rubric_notes.md into two files
- Works with the `blocked_rubric_memo` refusal_code of [skills/cheat-score-blind/SKILL.md](../skills/cheat-score-blind/SKILL.md) + the cheat-bump Phase 5 leak-guard self-check
- **Consequence of not running migrate**: the blind sub-agent still reads the actuals in rubric_notes.md, self-reports `non_blind_warning` and lowers all confidence to medium—usable but no longer "truly blind"
- See [migrations/1.3-to-1.4.md](../migrations/1.3-to-1.4.md)

### Key changes (v1.3)

Compared to v1.2 (MINOR, compatible):

- **Added `last_prediction_self_scored: bool`**—`true` only when the last `/cheat-predict` went through the `--skip-blind` flag or the user chose b at Phase 2.5 (trust the main Claude's self-estimate). cheat-status / the SessionStart hook nag based on it: "the last prediction didn't go through the blind sub-agent, N days now"
- **Added `last_self_scored_at: ISO 8601 / null`**—the timestamp when `last_prediction_self_scored` triggered; cleared back to null when going through the sub-agent
- Works with the channel-B isolation protocol of [skills/cheat-score-blind](../skills/cheat-score-blind/SKILL.md)—upgrading contamination tracking from "relying on git history" to "relying on a state field"
- Old state missing these two fields → fall back to `false` / `null`, **MINOR compatible**

### Key changes (v1.2)

Compared to v1.1 (MINOR, compatible):

- **`shoots[]` item schema extended**—added `scripts_path`, `script_consistency`, `script_diff_pct`, `v2_prediction_written`, `script_hash_at_shoot` fields. Semantics in cheat-shoot Phase 4. These fields record "whether a post-shoot script change triggered a v2 prediction re-judgment", and cheat-retro uses them to decide whether to read `## Prediction v1` or `## Prediction v2`
- Old state missing these fields → skills use `state.get(field, default)` (`script_consistency` defaults `"consistent"`, `v2_prediction_written` defaults `false`, `script_diff_pct` defaults `null`). **Not forced to run migrate**—but running it aligns the state fields with the schema doc

### Key changes (v1.1)

Compared to v1.0:

- **Removed `mode`** ("cold-start" / "calibration" binary) → judge state by the `calibration_samples` integer
- **Removed `prediction_complexity`** ("cold-start-simple" / "complete" binary) → all predictions use the unified full 7-component structure, **confidence level derived from calibration_samples**
- **Removed `bucket_scheme`** ("ratio" / "absolute" / "absolute_with_ratio" / "percentile" four tiers) → bucket boundaries are **auto-derived** by a single algorithm: has `baseline_plays` → by multiples; none → platform generic default; samples ≥10 → recompute baseline

Reason: a hard mode switch is the designer's guess, not how the UX should be. A unified flow + progressive confidence annotation better fits the fact that "a channel is a continuously-evolving spectrum, not discrete stages".

---

## Field descriptions (each field's semantics + who writes/reads)

### Metadata

| Field | Type | Writer | Reader | Note |
|---|---|---|---|---|
| `schema_version` | string | cheat-init / cheat-migrate | all skills | "1.1". Bumped on schema upgrade; existing users upgrade via [/cheat-migrate](../skills/cheat-migrate/SKILL.md). See [migration-protocol.md](migration-protocol.md) |
| `skill_version` | string | cheat-init | all skills | the current pattern-first version |
| `initialized_at` | ISO 8601 | cheat-init | cheat-status | first-init time, never changes |

### Mode and config

| Field | Type | Values | Writer | Reader |
|---|---|---|---|---|
| `rubric_version` | string | "v0" / "v1" / "v2" / ... | cheat-init / cheat-bump | cheat-score / cheat-predict / cheat-retro |
| `content_form` | enum | "opinion-video" / "long-essay" / "short-text" / "podcast" / "other" / "mixed" | cheat-init | cheat-predict / cheat-recommend |
| `typical_duration_seconds` | int | the user's typical video duration. Decides the word count of cheat-seed's draft + cheat-predict's same-duration anchor priority | cheat-init | cheat-seed / cheat-predict |
| `target_publish_cadence_days` | int / null | the user's target publish frequency (1=daily / 2=every other day / 7=weekly / null=flexible). Decides the buffer-alert color thresholds | cheat-init | cheat-status / cheat-recommend / cheat-shoot / cheat-publish / SessionStart hook |
| `rubric_form_mismatch` | bool | true means content_form ≠ opinion-video but still bootstrapping with the opinion built-in rubric—prompts the user to adjust weights at bump | cheat-init | cheat-status (keeps prompting) |
| `benchmark_status` | enum | "none" / "imported" / "pending" (user agreed to find one later) | cheat-init / cheat-learn-from | cheat-seed (reads benchmark.md when brainstorming) / cheat-status (keeps reminding when pending) |
| `benchmark_name` | string / null | benchmark account name; null when none | cheat-learn-from | cheat-status / cheat-seed |
| `benchmark_sample_count` | int | number of imported benchmark videos | cheat-learn-from (write / append) | cheat-status (prompts benchmark fade-out when N≥10) |
| `baseline_plays` | int / null | the user's baseline plays; at first init if there's fetched history → median; none → null; later back-filled when the 1st cheat-retro piece has actuals | cheat-init / cheat-retro / cheat-bump (--bucket-only) | cheat-predict (derives bucket boundaries) |
| `data_collection` | enum | "manual" / "adapter" | cheat-init | cheat-retro (decides the DATA_SOURCE default) |
| `pool_status` | enum | "none" / "markdown" / "notion" / "sqlite" | cheat-init / cheat-recommend | cheat-recommend / cheat-status |
| `data_layer` | enum | "markdown" / "sqlite" | cheat-init / md-to-sqlite.py | all skills that read predictions |
| `hooks_installed` | bool | true / false | cheat-init | cheat-status (keeps prompting) |
| `enabled_trend_sources` | array of string | list of trend-source adapter names (e.g. `["weibo-hot", "zhihu-hot"]`) | cheat-init / user manual | cheat-trends |
| `enabled_perf_adapters` | array of string | list of perf-data adapter names (e.g. `["douyin-session"]`). Empty → cheat-retro uses manual paste | cheat-init / user after manual config | cheat-retro |

### Accumulated counts

| Field | Type | Writer | Use |
|---|---|---|---|
| `calibration_samples` | int | cheat-retro (+1 per retro) | cheat-status progress bar / cheat-bump threshold |
| `calibration_samples_at_last_bump` | int | cheat-bump | "how many new samples since the last bump" |

### Timestamps (last_X_at)

| Field | Type | Writer |
|---|---|---|
| `last_bump_at` | ISO 8601 / null | cheat-bump |
| `last_bump_self_audited` | bool | cheat-bump (true when CROSS_MODEL_AUDIT=false) |
| `last_published_at` | ISO 8601 / null | cheat-publish |
| `last_published_file` | string / null | cheat-publish |
| `last_retro_at` | ISO 8601 / null | cheat-retro |
| `last_trends_run_at` | ISO 8601 / null | cheat-trends |
| `last_trends_added_count` | int | cheat-trends |
| `last_prediction_self_scored` | bool | cheat-predict (true with `--skip-blind` or Phase 2.5 choosing b; cleared back to false on the next sub-agent run) |
| `last_self_scored_at` | ISO 8601 / null | cheat-predict (synced with `last_prediction_self_scored`) |

### List queues

| Field | Type | Writer | Reader | Protocol |
|---|---|---|---|---|
| `consecutive_directional_errors` | array of "high"/"low" | cheat-retro (push) / cheat-bump (clear) | cheat-status / cheat-retro self-check | the deviation direction of recent N retros; 3 consecutive same-direction triggers a bump proposal |
| `pending_retros` | array of file path | cheat-publish (push) / cheat-retro (remove) | cheat-status | the prediction file paths awaiting retro |
| `shoots` | array of {video_folder, prediction_file, shot_at, ad_hoc} | cheat-shoot (push) / cheat-publish (remove) | cheat-status / cheat-recommend / SessionStart hook | the shot-not-published queue. `len(shoots) = buffer count`, `buffer_days = buffer × target_publish_cadence_days` decides the color |

### Session state

| Field | Type | Writer | Reader | Protocol |
|---|---|---|---|---|
| `in_progress_session` | object / null | cheat-predict (create) / cheat-publish (clear) | cheat-publish / cheat-status | see "in_progress_session sub-structure" below |

#### `in_progress_session` sub-structure

```json
{
  "type": "prediction",
  "file": "predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md",
  "started_at": "2026-05-04T14:00:00+08:00",
  "rubric_version": "v2"
}
```

`type`: currently only `"prediction"`. In the future may add `"bump"` to indicate a long bump flow in progress.

---

## Read/write protocol

### Read (any skill)

```python
# pseudocode
import json, os

state_path = os.path.join(os.getcwd(), ".cheat-state.json")
if not os.path.exists(state_path):
    # doesn't exist = user hasn't initialized, route to /cheat-init
    raise NeedsInitError()

with open(state_path) as f:
    state = json.load(f)

# check schema_version compatibility
LATEST_SCHEMA = "1.1"  # see migrations/registry.md
if state.get("schema_version") != LATEST_SCHEMA:
    # don't raise directly — prompt the user to run /cheat-migrate (non-blocking)
    log_warning(f"schema version mismatch: state={state.get('schema_version')}, expected={LATEST_SCHEMA}. Suggest running /cheat-migrate")
    # MINOR mismatch usually still continues; on MAJOR, reading some fields may KeyError → use .get(field, default) as backstop
```

**Key discipline**:
- After reading, don't immediately worry about missing fields—use `state.get(field, default)` for tolerance. When a new skill version introduces a new field, an old state file lacks it, and should default gracefully rather than crash
- **Never** mutate state in memory then forget to write back—downstream skills read the disk version

### Write (any skill)

```python
# pseudocode — read-modify-write pattern
state = read_state()
state["calibration_samples"] += 1
state["last_retro_at"] = now_iso()
write_state(state)

def write_state(state):
    state_path = os.path.join(os.getcwd(), ".cheat-state.json")
    tmp_path = state_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, state_path)  # atomic rename
```

**Key discipline**:
- **Atomic write**: write to .tmp → rename. Avoids a half-written corrupted state file
- **Always indent=2**: human-readable, for the user to hand-edit + git diff
- **ensure_ascii=False**: keep non-ASCII characters un-escaped (no \uXXXX)
- **Finish writing before continuing**: avoid downstream skills reading the old value

### Concurrency model

Expected scenario: **single user + single Claude Code session**. No locking.

If two sessions operate the same project in parallel (rare and not recommended): a write-over may occur. **When needed in the future** a file lock (`fcntl.flock`) can be added; not added now, to avoid introducing complexity.

---

## Field-write responsibility table (to prevent "who should write this field" ambiguity)

| Field | Sole writer | When written |
|---|---|---|
| `rubric_version` | cheat-init / cheat-bump | init writes the initial value; bump on version upgrade |
| `baseline_plays` | cheat-init / cheat-retro / cheat-bump (--bucket-only) | at init if an adapter fetched history → median; no history → null; the 1st retro with actuals → backfill; bump --bucket-only → recompute |
| `calibration_samples` | cheat-retro | +1 each time a retro successfully writes to disk |
| `pending_retros` | cheat-publish (push) / cheat-retro (remove) | publish pushes this one; retro completion removes it |
| `consecutive_directional_errors` | cheat-retro (push) / cheat-bump (clear) | push when retro determines the deviation direction; clear when bump lands |
| `in_progress_session` | cheat-predict (create) / cheat-publish (clear) | created when predict finishes writing the file; cleared at publish registration |
| `last_bump_at` | cheat-bump | when the bump lands |

**Never allow** multiple skills to write the same field—it breaks the state semantics. If a new field is needed in the future, first decide "who is the sole writer".

---

## Handling a corrupted / inconsistent state file

| Symptom | Handling |
|---|---|
| File doesn't exist | prompt "not initialized, run /cheat-init", **don't** auto-create |
| JSON parse failure | prompt "state file corrupted: path/to/.cheat-state.json", suggest manual fix or backup + re-init |
| Unrecognized schema_version | prompt the version number + suggest running [/cheat-migrate](../skills/cheat-migrate/SKILL.md). The SessionStart hook auto-detects and prompts |
| `pending_retros` contains deleted files | cheat-status silently removes them on detection, no error |
| `in_progress_session` file no longer exists | cheat-status detects it → asks the user whether to clean up |
| `calibration_samples` inconsistent with the actual retro count in `predictions/` | cheat-status reports the discrepancy. A temporary hand-edit of state suffices; a persistent inconsistency is a bug and should add a reconciliation step to cheat-migrate in the next minor version |

---

## Relationship with git

`.cheat-state.json` **should** be tracked in git:
- ✅ it's a snapshot of project config + accumulated metrics
- ✅ git history provides the full trajectory of state evolution
- ✅ multi-device sync relies on git push/pull
- ❌ does **not** contain sensitive info (cookie / API key should go in `.env` or `.cheat-secrets.json`, separately gitignored)

The `.cheat-cache/` directory **should not** be tracked in git:
- contains `usage.jsonl` (the local log of the meta-logging hook)
- contains `trends-history.jsonl` (the dedup cache of trend fetching)
- may also contain adapter debug files (e.g. `douyin-session-debug/`)
- these are device-local state, syncing across devices is meaningless

`/cheat-init` should auto-append (not overwrite) to the `.gitignore` at the user project root:

```
.cheat-cache/
.cheat-secrets.json
```

---

## Upgrade path

The full philosophy and maintainer checklist: see [migration-protocol.md](migration-protocol.md). Short version:

On a future schema change:
1. Bump `schema_version` (e.g. "1.1" → "1.2")
2. Write `migrations/<old>-to-<new>.md` (4 sections: WHAT/WHY/HOW/Manual fallback)
3. Change the `LATEST_SCHEMA` marker + version chain in `migrations/registry.md`
4. The SessionStart hook prompts the user to run `/cheat-migrate` when it detects an inconsistency
5. **Never** let a skill silently support an old schema's deleted/renamed field—that turns "which field means what under which version" into a mystery

Adding a field (MINOR, non-breaking):
- Read with `state.get(field, default)`
- An old state file automatically gets the default
- **Still need to bump schema_version + write the migrations file**—to ensure eventual state-file consistency; but the user can defer running migrate

Delete / rename / change semantics (MAJOR, breaking):
- Must bump schema_version + write the migration file
- Mark `BREAKING` in the CHANGELOG

---

## The boundary of users hand-editing the state file

Fields allowed to be hand-edited:
- `enabled_trend_sources` (array, decides which sources cheat-trends uses)
- `data_collection` (switch manual ↔ adapter)

Fields **not** recommended to hand-edit (breaks invariants):
- `calibration_samples` / `pending_retros` / `consecutive_directional_errors` (should be updated via the retro flow)
- `rubric_version` (should be updated via the bump flow)
- `in_progress_session` (should be updated via the predict/publish flow)

If the user really wants to reset: recommend **deleting the entire .cheat-state.json + re-running /cheat-init**—safer than hand-editing single fields.

---

## Confidence label derivation table (**single source of truth**)

Used jointly by cheat-predict / cheat-status / cheat-recommend / the SessionStart hook. Derived from `calibration_samples`, all skills use the same logic:

| `calibration_samples` | confidence emoji + label | numeric meaning | how the user should use it |
|---|---|---|---|
| 0 | 🔴 very low | "astrology-level, pure discipline training" | don't decide whether to publish based on composite; writing a prediction is to **collect data**, not to **make a decision** |
| 1-2 | 🟠 low | "central ±50%, directional sense beats absolute numbers" | trust "A beats B in traffic" direction, not the specific number |
| 3-5 | 🟡 fairly low | "central ±40%, usable as one reference" | the bucket ranking is usable, the central point estimate is still a guess |
| 6-10 | 🟢 medium | "central ±25%, can participate in decisions" | usable as one basis for "whether to publish" |
| 11-20 | 🟢 fairly high | "central ±15%, rubric shape stable" | the central estimate is trustworthy |
| 21+ | 🔵 high | "central ±10%, can data-drive a bump" | entering the data-driven stage—bump with regression rather than intuition |

> The ±X% above are **empirical values** (based on the reference creator's real calibration curve), not a mathematically strict guarantee. A new account's real ±X% has to wait until you've produced your own score-curve.png to verify.

**Don't use this table to gate any feature**—all skills run the same flow at all calibration_samples values, just **showing** the current confidence level in the output. This is the core principle of the new design.
