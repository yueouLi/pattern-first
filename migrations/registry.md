# Migrations Registry

The single source of truth for cheat-on-content's schema-version evolution. `/cheat-migrate` reads this file to decide which migrations to run.

---

## Current schema_version

**`1.4`**—written into new state files by `cheat-init` Phase 3.

The `LATEST_SCHEMA` marker below is referenced by the `cheat-migrate` skill and the SessionStart hook:

```
LATEST_SCHEMA = "1.4"
```

> Maintainer note: when bumping this value you **must** add a corresponding migration file + append a row to the "version chain" below.

---

## Version chain

In chronological order, each row represents a schema upgrade. `/cheat-migrate` uses this table to compute which steps to run in order, from the user's current version to LATEST_SCHEMA.

| from | to | breaking? | migration file | description |
|---|---|---|---|---|
| (none) | 1.0 | — | (built-in) | the first v1 schema |
| 1.0 | 1.1 | NO | [1.0-to-1.1.md](1.0-to-1.1.md) | remove the three enum fields `mode` / `prediction_complexity` / `bucket_scheme`; add `target_publish_cadence_days` / `baseline_plays` / `benchmark_*` / `shoots` etc. |
| 1.1 | 1.2 | NO | [1.1-to-1.2.md](1.1-to-1.2.md) | the `shoots[]` item gains 5 fields (`scripts_path` / `script_consistency` / `script_diff_pct` / `v2_prediction_written` / `script_hash_at_shoot`)—for the "post-shoot script change triggers a v2 prediction re-judgment" workflow |
| 1.2 | 1.3 | NO | [1.2-to-1.3.md](1.2-to-1.3.md) | add `last_prediction_self_scored: bool` + `last_self_scored_at` fields—for the channel-B isolated scoring introduced by the cheat-score-blind sub-agent. `true` means the last prediction went through `--skip-blind`, and cheat-status keeps nagging |
| 1.3 | 1.4 | **BREAKING for blind channel** | [1.3-to-1.4.md](1.3-to-1.4.md) | rubric file split: `rubric_notes.md` → `rubric_notes.md` (blind whitelist, generic language) + `rubric-memo.md` (blind hard-forbidden to read, with real video names/actuals). State fields unchanged; existing users must run migrate to split the existing rubric_notes.md. Without it → the blind sub-agent still flags non_blind_warning |

---

## Migration-file naming convention

- Filename: `<from>-to-<to>.md` (e.g. `1.1-to-1.2.md`)
- Each must contain 4 sections:
  1. **WHAT changed**—field-level diff (added / removed / renamed)
  2. **WHY**—why the change
  3. **HOW (Claude steps)**—the natural-language steps Claude executes in order when running `/cheat-migrate`
  4. **Manual fallback**—the minimal instructions to hand-edit `.cheat-state.json` if the user doesn't want to run the skill

---

## Philosophy (see [shared-references/migration-protocol.md](../shared-references/migration-protocol.md))

- **MINOR bump** (e.g. 1.1 → 1.2): only add fields or soften enum values. Old state reads the default via `state.get(field, default)`, **can run without migrate**—but running it makes the state file complete
- **MAJOR bump** (e.g. 1.x → 2.0): delete a field / rename a field / change a field's semantics. Old state **must** run migrate, otherwise a skill reads an inconsistent field
- **No version-skipping allowed**: a 1.0 user upgrading to 1.3 must run 1.0→1.1, 1.1→1.2, 1.2→1.3 in order. Each step idempotent
- **Failure stops in place**: migrating fails at step N → state.schema_version is still N-1 (not the target version). After fixing, a re-run continues from the breakpoint

---

## For developers: adding a migration

When bumping the schema (in order):

1. Decide clearly whether it's MINOR or MAJOR (refer to the philosophy section above)
2. Change the hardcoded `schema_version` in `cheat-init/SKILL.md` to the new value
3. Change the `LATEST_SCHEMA = "X.Y"` marker in this file
4. Append a row to this file's "version chain" table
5. Create `migrations/<old>-to-<new>.md`, fill all 4 sections
6. Mark `BREAKING` (major) or `MINOR` in CHANGELOG.md, add a migration-file link
7. Run it through: call `/cheat-migrate` on a fixture old state, verify the upgrade to the new version with all state fields present

If you can't be bothered to write the standard 4-section migration file, **defer** the schema bump to the next sizeable change—don't bump the schema first and backfill the docs.
