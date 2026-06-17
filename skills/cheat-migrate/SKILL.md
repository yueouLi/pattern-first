---
name: cheat-migrate
description: Upgrade an existing user's .cheat-state.json to the current schema_version. Read migrations/registry.md to compute the migration chain, apply each migration file in order. Idempotent: running twice gives the same result. On failure, stops at the intermediate version without advancing. Triggers: "migrate" / "upgrade state" / "my state is an old version" / "schema version mismatch".
argument-hint: [— from: <version>] [— to: <version>] [— dry-run]
allowed-tools: Bash(*), Read, Write, Edit, Skill
---

# /cheat-migrate — schema version migration

Upgrade the user's `.cheat-state.json` from an old `schema_version` to the `LATEST_SCHEMA` that cheat-on-content currently expects.

---

## Overview

```
[user: migrate / or runs it after the SessionStart prompt]
  ↓
[Phase 0: read .cheat-state.json + migrations/registry.md → determine the migration chain]
  ↓
[Phase 1: dry-run (default) shows the migration plan, wait for user confirmation]
  ↓
[Phase 2: back up .cheat-state.json → .cheat-state.json.backup-<timestamp>]
  ↓
[Phase 3: apply the HOW section of each step's migration file in order]
  ↓
[Phase 4: verify the upgraded state file parses + schema_version is updated]
  ↓
[Phase 5: report + prompt to clean up the backup if needed]
```

---

## Constants

- **REGISTRY_PATH = `${SKILL_DIR}/../../migrations/registry.md`** — single source of truth for the version chain
- **MIGRATIONS_DIR = `${SKILL_DIR}/../../migrations/`** — migration files directory
- **DRY_RUN_BY_DEFAULT = true** — the first run shows the plan, doesn't directly modify the file
- **BACKUP_BEFORE_WRITE = true** — must back up before writing; the backup file is kept until the next successful init / manual cleanup by the user
- **STOP_ON_STEP_FAILURE = true** — any step failing → stop at the intermediate version, don't advance, don't roll back

> 💡 Override at call time: `/cheat-migrate — dry-run: false` to execute directly / `/cheat-migrate — to: 1.2` to upgrade only to the specified version

---

## Inputs

| Required | Source |
|---|---|
| `.cheat-state.json` | user project root |
| `migrations/registry.md` | LATEST_SCHEMA + version chain |
| `migrations/<from>-to-<to>.md` | the specific migration instructions for each step |

---

## Workflow

### Phase 0: determine the migration chain

1. Read `.cheat-state.json` → parse `current_version = state.schema_version`
2. Read `migrations/registry.md` → parse the `LATEST_SCHEMA` field (line: `LATEST_SCHEMA = "X.Y"`)
3. Parse the `args.to` override (if any); otherwise target = LATEST_SCHEMA
4. Parse the `args.from` override (rare scenario: the user's state file schema field is broken, force-specify the start point)
5. **State judgment**:
   - `current_version == target` → output "✅ state is already {target}, no migration needed" → exit
   - `current_version > target` (e.g. the user ran a dev version then switched back to release) → error "can't downgrade, please adjust manually or re-init"
   - `current_version < target` → continue, look up the migration chain from the registry
6. Compute `chain = [(from, to, file), ...]` from the registry's "version chain" table, threading current → target in order

If a step is missing from the registry (e.g. `current_version` isn't in the table) → error and show "currently known versions: [1.0, 1.1, ...]" for the user to check.

### Phase 1: dry-run

Output the migration plan:

```
📋 Migration plan

Current version: 1.0
Target version: 1.2
Will run 2 steps in order:

  [1/2] 1.0 → 1.1 (MINOR)
       Added fields: typical_duration_seconds, target_publish_cadence_days, ... (12 fields total)
       Removed fields: mode, prediction_complexity, bucket_scheme
       See: migrations/1.0-to-1.1.md

  [2/2] 1.1 → 1.2 (MINOR)
       Added fields: [...]
       See: migrations/1.1-to-1.2.md

⚠️ Backup location: .cheat-state.json.backup-<timestamp>

Continue? Reply yes to execute / no to exit / dry-run-detail to see exactly what each step changes.
```

If `args["dry-run"] == false` or the user replies yes → proceed to Phase 2.

### Phase 2: backup

```bash
cp .cheat-state.json .cheat-state.json.backup-$(date +%s)
```

Output: "📦 Backed up to .cheat-state.json.backup-1714838400"

### Phase 3: apply each step in order

For each (from, to, file) in the chain:

1. Output "→ [N/M] applying {file}..."
2. Read `migrations/<file>` → find the `## HOW (Claude steps for /cheat-migrate)` section
3. **Execute the natural-language steps in the section item by item**—this is key: the migration is run by Claude reading the markdown, not by a python script
4. After each step completes:
   - update the in-memory state.schema_version = to
   - **atomic write** to disk (write .tmp → rename)
5. If a step fails:
   - output "❌ {file} step N failed: {error}"
   - don't advance, don't roll back (state has stopped at the intermediate version from the last successful step)
   - prompt: "stopped at schema_version: {last_success_version}. After fixing, re-running /cheat-migrate will continue from here"
   - exit

### Phase 4: verify

After the upgrade:
1. Read `.cheat-state.json` → parse → should succeed
2. Check `schema_version == target`
3. Check that all "required fields" are non-missing (refer to the full schema in [shared-references/state-management.md](../../shared-references/state-management.md))
4. Failure → error "migration complete but verification failed: {detail}. The state file may be inconsistent—check the backup to restore"

### Phase 5: report

```
✅ Migration complete

  From: 1.0
  To: 1.2
  Steps applied: 2

The state file now contains X fields, all passing verification.

📦 Backup kept: .cheat-state.json.backup-1714838400
   (after confirming everything is fine you can manually rm it; the next successful /cheat-init also cleans up expired backups)

Recommended next steps:
  - run /cheat-status to confirm the dashboard is normal
  - if you need to reinstall hooks, run bash <skill_repo>/install.sh --reinstall-hooks
```

---

## Key Rules

1. **Idempotent**: re-running on an already-upgraded state should immediately exit "no migration needed", **not** re-apply the steps. Achieved by comparing `current_version == target`
2. **No version-skipping**: 1.0 → 1.3 must go in order 1.0→1.1→1.2→1.3, each step independently recoverable. No "merged migration that jumps straight from 1.0 → 1.3" is allowed
3. **No silent compatibility**: unrecognized state file schema_version → explicitly error "unknown version X, most recent known version Y", don't pretend to continue
4. **Failure stops in place**: when step N fails, schema_version stays at the successful version N-1, doesn't roll back to pre-migration. A re-run continues from the breakpoint
5. **Backup is a hard constraint**: there must be a backup before writing. Even if the user runs `--dry-run: false`, the backup action still runs
6. **Doesn't touch predictions / rubric / videos**: only modifies `.cheat-state.json`. Other user data is each skill's responsibility; the migrate skill doesn't touch it
7. **MAJOR vs MINOR transparency**: the dry-run output must mark (MAJOR) / (MINOR). On MAJOR, additionally prompt "old skills reading old fields will have problems; after migrating you can't roll back to the old skill version"

---

## Refusals

- "Skip the dry-run, overwrite my state right now" → **allowed** (`--dry-run: false`), but the backup is still enforced
- "My state is corrupted / the schema_version field is gone, can you guess a version to run" → allowed to specify `--from: 1.0`, but warn "a guess-based migration may cause field misalignment"
- "Downgrade to an older version (current > target)" → refuse. Schema evolution is one-directional. To downgrade, manually cp a historical git snapshot
- "Merge multiple migration steps into one atomic" → refuse. Each step being independently recoverable is the core design
- "Call migrate in the middle of running cheat-bump / cheat-predict" → refuse. Wait for the other skill to finish, to avoid corrupting the in_progress_session state

---

## Integration

- Upstream: the SessionStart hook detects `state.schema_version != LATEST_SCHEMA` → outputs a red warning + suggests running `/cheat-migrate`
- Upstream (manual): after the user git pulls a new version, sees the CHANGELOG marks BREAKING → runs it proactively
- Downstream: after running, all other skills reading state get the latest fields
- With `cheat-init`: init writes new state using LATEST_SCHEMA directly, no need to go through migrate
- With `install.sh --reinstall-hooks`: migration does **not** reinstall hook scripts (hook scripts are skill-package code, not part of the user's state). These two things are decoupled

---

## State field read/write

This skill **writes**:
- `schema_version` (updated after each successful step)

This skill **reads**:
- all existing fields (depending on the HOW steps of the specific migration file)

This skill **never** writes:
- business state like `calibration_samples` / `pending_retros` / `shoots` (those are other skills' responsibility)
- exception: when a migration file explicitly says "need to scan predictions/ to compute baseline_plays when deriving a new field value", that's initializing a new field, not modifying an old one

---

## Examples

### Example 1: user upgrades from v0.1.0 to v0.2.0 (assume 0.2 introduces schema 1.2)

```
User: migrate
Claude: [runs cheat-migrate]
  Phase 0: current=1.1, target=1.2, chain=[(1.1, 1.2)]
  Phase 1: dry-run outputs the plan
  User: yes
  Phase 2: backup
  Phase 3: apply 1.1-to-1.2.md (MINOR: add fields like platform_metrics_url)
  Phase 4: verify OK
  Phase 5: report ✅
```

### Example 2: user skipped multiple versions

```
User: I went from v0.1.0 to v0.5.0, state is still 1.0
Claude: [runs cheat-migrate]
  Phase 0: current=1.0, target=1.4 (LATEST), chain=[(1.0, 1.1), (1.1, 1.2), (1.2, 1.3), (1.3, 1.4)]
  Phase 1: dry-run outputs the 4-step plan
  ...
```

### Example 3: migration fails midway

```
Phase 3:
  → [1/4] apply 1.0-to-1.1.md ✓
  → [2/4] apply 1.1-to-1.2.md ✓
  → [3/4] apply 1.2-to-1.3.md... ❌ failed: user's baseline_plays field contains a non-numeric value, can't convert to int

state has stopped at schema_version: 1.2.
After fixing .cheat-state.json, re-running /cheat-migrate will continue from 1.2 → 1.3.
```
