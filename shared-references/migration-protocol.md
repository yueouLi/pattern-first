# Migration Protocol (schema-evolution philosophy)

Referenced by the `cheat-migrate` skill / `cheat-init` / the SessionStart hook / maintainers. Specifies how to safely evolve the `.cheat-state.json` schema without disrupting existing users.

---

## Core principles

1. **Every release must let an existing user's old state work**—via a migrate upgrade, or via `state.get(field, default)` compatibility
2. **MINOR change = add a field / soften an enum**; old state works even without running migrate (missing fields use a default value), and running it makes the state complete
3. **MAJOR change = delete a field / rename / change semantics**; old state **must** run migrate, otherwise a skill reading an inconsistent field will error
4. **No version-skipping allowed**; a multi-version upgrade must apply each step in order. Each step is idempotent
5. **Failure stops in place**; no rollback, let the user fix at the breakpoint and continue
6. **schema_version is monotonically increasing**; no downgrade allowed (to downgrade, cp a historical git snapshot)

---

## When it counts as MINOR vs MAJOR

### MINOR scope (old state runs without migrate)

- Adding a field (with a well-defined default value; old skills not reading it don't error)
- Softening enum values (e.g. adding a third `"adaptive"` to `"strict" / "lenient"`, old values still legal)
- Adding a new optional value to a field (e.g. a list field gains a new element)
- Changing a default value (doesn't change semantics)

### MAJOR scope (must run migrate)

- **Deleting a field**—old skills still write it, new skills don't read it, ambiguity results
- **Renaming a field**—old/new skills can't see what the other wrote
- **Changing a field's semantics** (e.g. `mode` from an enum to an integer; `baseline_plays` from int to list)
- **Changing enum values** (e.g. `"opinion-video"` to `"opinion_video"`, old value no longer legal)
- **Splitting a field / merging fields**

> For gray areas, **conservatively judge as MAJOR**—writing one extra migration file is better than letting the user's state error.

---

## Maintainer checklist: the 4 things to do when bumping the schema

Each time you prepare a release, if you changed the state schema:

### 1. Change the hardcoded schema_version cheat-init writes for new state

```diff
- "schema_version": "1.1",
+ "schema_version": "1.2",
```

Location: the state-write section of `skills/cheat-init/SKILL.md` Phase 3.

### 2. Change the LATEST_SCHEMA marker in migrations/registry.md

```diff
- LATEST_SCHEMA = "1.1"
+ LATEST_SCHEMA = "1.2"
```

And append a new row to the "version chain" table:

```
| 1.1 | 1.2 | NO/YES | [1.1-to-1.2.md](1.1-to-1.2.md) | one-sentence description |
```

### 3. Write migrations/<old>-to-<new>.md

4 required sections (refer to the `1.0-to-1.1.md` template):
- WHAT changed
- WHY
- HOW (Claude steps for /cheat-migrate)
- Manual fallback

> Can't write the 4 sections = the change is too complex and not thought through = you shouldn't release this schema bump.

### 4. Mark the version number + link in CHANGELOG.md

```markdown
## [0.2.0] — YYYY-MM-DD

### BREAKING / MINOR

- schema_version 1.1 → 1.2: <one-sentence description>. Migration guide: [migrations/1.1-to-1.2.md](migrations/1.1-to-1.2.md)
- ...
```

Use `### MINOR` for MINOR, `### BREAKING` for MAJOR—make it prominent.

---

## How a skill reads state (defensive programming)

When a skill reads state it **must** use the `state.get(field, default)` pattern:

```python
# good
target_cadence = state.get("target_publish_cadence_days", None)
benchmark_status = state.get("benchmark_status", "none")
shoots = state.get("shoots", [])

# bad (old state without this field raises KeyError)
target_cadence = state["target_publish_cadence_days"]
```

Reasons:
- On a MINOR upgrade, old state is missing the new field—the `get` pattern lets the skill auto-use the default
- The user hand-edited state and deleted a field—same as above
- Reduces the hard "must migrate before running" dependency inside skills

**Exception**: core identifier fields are allowed direct indexing (e.g. `state["schema_version"]`, `state["rubric_version"]`)—their absence means the state file is fundamentally invalid and should error explicitly.

---

## The SessionStart hook's role

The hook detects at each session start:

```bash
state_schema=$(jq -r '.schema_version // "unknown"' "$STATE_FILE")
if [[ "$state_schema" != "$LATEST_SCHEMA" ]]; then
  echo "⚠️ schema version mismatch: state=$state_schema, skill expects=$LATEST_SCHEMA"
  echo "   Suggest running /cheat-migrate to upgrade (non-blocking, work continues)"
fi
```

**Non-blocking**: the user can choose "keep working first, run migrate later". On a MINOR mismatch most features still run; on a MAJOR mismatch some skills may error—then running migrate is still in time.

---

## For developers: practices to avoid frequent schema bumps

Not every change needs a schema bump. Here's the philosophy:

- **Prefer MINOR**: add a field where you can, delete fields rarely. Deleting fields annoys existing users
- **Batch bumps**: accumulating 3-5 MINORs to release together is friendlier than bumping on every small change
- **Defer bumps**: if a MINOR field is unused by 90% of users, **don't** rush to bump the schema—let that field silently work via `state.get(field, default)`, and bump along the way at the next release
- **Avoid MAJOR**: never go MAJOR when MINOR solves it. E.g. rather than renaming a field, keep the old field + add a new one (mark the old deprecated, delete only at the next MAJOR release)

---

## Backup retention policy

`/cheat-migrate` backs up to `.cheat-state.json.backup-<timestamp>` before writing.

How long to keep backups:
- When the user runs `/cheat-status`, if there's a backup + state has run stably for N days → prompt "you can clean up N old backups"
- `/cheat-init` re-init cleans up all old backups (since re-initializing, old backups have little meaning)
- The user manually running `rm .cheat-state.json.backup-*` is always OK

Not version-controlled: `.cheat-state.json.backup-*` should be in `.gitignore` (already covered by the `.cheat-state.json` wildcard rule).
