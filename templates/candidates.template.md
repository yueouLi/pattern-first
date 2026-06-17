# Candidate topic pool

> **This file is written by `/cheat-trends` with trend-fetch results, and read and ranked by `/cheat-recommend`.
> Can also be hand-edited—just paste candidate titles as H3 entries.**
>
> Full schema spec: [shared-references/candidate-schema.md](../cheat-on-content/shared-references/candidate-schema.md).

---

## Usage notes (read on first seeing this file)

Each candidate is an H3 entry (`### [tier] title`) with metadata bullets below. The minimal version only needs a title line—`/cheat-recommend` auto-calls `/cheat-score` to rough-score unscored entries.

### Field meaning quick-reference

- **id**: 12-char hash, for cross-file dedup. Leave blank on a hand-added entry, `/cheat-trends` auto-computes
- **source**: source identifier, format `<adapter-type>:<source-name>`
- **snapshot_at**: fetch / entry time (ISO 8601 or YYYY-MM-DD)
- **tier**: rough classification `tier1` / `tier2` / `tier3` / `skip` / `risky` / `done`
- **read_status**: `unread` / `skimmed` / `deep_read` / `done`
- **composite (vN)**: the composite under the current rubric (rough score, **not a prediction**)
- **predicted bucket**: the rough-predicted bucket (rough, only for ranking)
- **note**: notes (e.g. "wait for a moment to publish", "to re-read", "risky issue")

### The minimal format for a hand-added entry

```markdown
### title
- snapshot_at: 2026-05-04
```

The rest of the fields are filled by `/cheat-recommend` on the next call (auto-calling `/cheat-score`).

---

## Candidates

> Delete all the example entries below, start accumulating from your real candidates.
> The examples show real samples (anonymized) from the "video analysis" project's current candidate pool.

### [tier1] the high-density family system of "for your own good"

- **id**: e7c2f1a4d3b6
- **source**: pool:manual
- **snapshot_at**: 2026-05-01
- **tier**: tier1
- **read_status**: deep_read
- **composite (v2)**: 9.18 — ER=5 HP=5 QL=4 NA=4 AB=5 SR=5 SAT=4
- **predicted bucket**: 300k-1M (central ~600k)
- **note**: heavy issue, not suitable for 2 such pieces in a row

> "For your own good" is Chinese families' highest-tier rhetoric of controlling their children, backed by a whole cognitive system of "I understand your needs better than you do".
> [snapshot_text section—close-reading notes after deep_read, optional]

---

### [tier1] the length of "haha"

- **id**: 229f5798b1d8
- **source**: pool:manual
- **snapshot_at**: 2026-05-03
- **tier**: tier1
- **read_status**: deep_read
- **composite (v2)**: 8.71 — ER=3 HP=5 QL=5 NA=4 AB=5 SR=4 SAT=5
- **note**: v2.1 candidate dimensions MS+TS both 5—the key A/B verification sample for the v2.1 upgrade

> A study of the nonlinear relationship between "haha" length and willingness to communicate in social media.
> Forms a perfect A/B comparison with "who asked you"—same ER/HP/QL/SR/SAT, the only difference is MS and TS each +3.

---

### [tier2] Freud's philosophy of sexual repression

- **id**: 8c4d92e1f0b3
- **source**: trend:manual-paste
- **snapshot_at**: 2026-04-28
- **tier**: tier1
- **read_status**: skimmed
- **composite (v2)**: 9.53 — ER=4 HP=5 QL=5 NA=4 AB=5 SR=5 SAT=5
- **predicted bucket**: 300k-1M (central ~700k)
- **note**: **risky** (sexual topic), need to assess the account's risk tolerance

> Freud's core theory was rejected by 21st-century psychology, but his description of "repression → symptom" still has explanatory power in intimate-relationship practice.

---

### [skip] [example - a skipped candidate]

- **id**: a1b2c3d4e5f6
- **source**: trend:hackernews
- **snapshot_at**: 2026-05-02
- **tier**: skip
- **rejected_at**: 2026-05-02
- **rejected_reason**: doesn't fit this account's issues (pure tech news)

---

### [done] [example - a published candidate]

- **id**: ab61ed09f0a1
- **source**: pool:manual
- **snapshot_at**: 2026-04-22
- **tier**: done
- **read_status**: done
- **composite (v2)**: 8.24
- **published_at**: 2026-04-24
- **predictions_file**: predictions/2026-04-24_ab61ed09_stop-expecting.md

> A done-tier entry **doesn't appear in `/cheat-recommend`'s output**—already published, not re-recommended.

---

## Maintenance suggestions

- **Keep < 100 active** (tier1+tier2+tier3, excluding skip/done). Beyond that the ranking is unstable
- **Periodically clean up skip**: skips older than 6 months can be auto-removed from `.cheat-cache/trends-history.jsonl` (they reappear when `/cheat-trends` re-fetches them)
- **Use the risky tag seriously**: `/cheat-recommend` highlights risky items for a second confirmation; don't mark everything "a bit controversial" as risky, you'll get numb
