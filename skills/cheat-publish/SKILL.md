---
name: cheat-publish
description: Register that a piece has been published—write the URL/platform ID/publish time into the corresponding prediction file's header and the state file. This is a lightweight action—it only updates metadata, **touching not a single character of the prediction section**. Triggers: "shipped" / "I shipped" / "the link is X" / "just published [url]" / "publish registered".
argument-hint: <prediction-file-or-url> [— platform: youtube|bilibili|douyin|...]
allowed-tools: Bash(*), Read, Edit, Glob
---

# /cheat-publish — publish registration

Adds the piece's publish metadata (URL, publish time, platform) to the prediction file header and the state file. **Editing the prediction section is forbidden**—the hook will block it.

## Overview

```
[user: shipped https://...]
  ↓
[Phase 0: find the corresponding prediction file]   ← via in_progress_session or matching
  ↓
[Phase 1: parse URL → platform/publish time]
  ↓
[Phase 2: update the prediction file header (metadata section only)]
  ↓
[Phase 3: update .cheat-state.json, clear in_progress_session]
```

## Constants

- **AUTO_DETECT_PLATFORM = true** — auto-detect the platform from the URL pattern
- **VERIFY_BLIND = true** — remind the user: from this moment on, seeing any subsequent data breaks the integrity of the blind declaration

## Inputs

| Required | Source |
|---|---|
| `<prediction-file>` or URL | user argument; if missing, use `in_progress_session.file` from `.cheat-state.json` |
| `.cheat-state.json` | user project root |

## Workflow

### Phase 0: find the corresponding prediction file

By priority:
1. The user argument explicitly gave a prediction file path → use it
2. The user argument gave only a URL → read `in_progress_session.file` from `.cheat-state.json`
3. Neither → list the files in `predictions/*.md` whose header lacks `published_at`, and let the user choose

**Warning path**: if `in_progress_session.file` is more than 14 days apart from the time the user's URL implies → prompt "this prediction was written a long time ago; confirm it's this one?"

### Phase 1: parse the platform

When `AUTO_DETECT_PLATFORM=true`, by URL pattern:

| URL pattern | Platform |
|---|---|
| `youtube.com/*` `youtu.be/*` | youtube |
| `bilibili.com/*` `b23.tv/*` | bilibili |
| `douyin.com/*` `iesdouyin.com/*` `v.douyin.com/*` | douyin |
| `xiaohongshu.com/*` `xhslink.com/*` | xhs |
| `mp.weixin.qq.com/*` | wechat |
| `substack.com/*` `*.substack.com/*` | substack |
| `medium.com/*` `*.medium.com/*` | medium |
| `twitter.com/*` `x.com/*` | twitter |
| other | unknown — ask the user |

Getting the publish time:
- Don't force auto-fetch—most platforms require a login state
- Ask the user: "What's the publish time? (default: now)" → accept ISO 8601 or natural language ("today 14:30" / "20 minutes ago")
- Parse failure → use now()

### Phase 2: update the prediction file header

**Never** touch the `## Prediction` section or anything after it. Only modify the metadata block at the very top of the file.

Read the file, locate the metadata block (all lines before the first `##`). Check whether these fields already exist—if so, warn "already registered" and ask whether to overwrite; if not, append:

```markdown
**Published at**: 2026-05-04T14:32:00+08:00
**Platform**: douyin
**URL**: https://v.douyin.com/abc123
**Video Folder**: videos/2026-05-04_a3f2c1d4_stop-expecting/
**Aweme ID**: 7234567890123456789  (platform-specific ID needed by douyin / video account etc.)
```

**About platform-specific IDs**:
- Douyin: extract `aweme_id` after resolving the short link (v.douyin.com → after redirect contains a modal_id or item_id param)
- Bilibili: the BV number
- Xiaohongshu: note_id
- YouTube: the video_id after the v= param

If the user gives a sharing short link (not immediately resolvable) → mark `Aweme ID: pending`, to be resolved by the adapter at the next `/cheat-retro`.

**Video folder handling**: by the cheat-publish step, the corresponding `videos/<id>/` directory **should already have been created by cheat-shoot** (containing script.md).

- If the video folder doesn't exist → warn "did you skip cheat-shoot? Recommend running cheat-shoot first to register the filmed script into the video folder before publishing", and **ask the user whether to skip registration and publish directly**:
  - Yes → auto-create a video folder (fallback), but don't ask about script consistency, mark `ad_hoc_publish: true`
  - No → have the user run cheat-shoot first and come back to publish

Use the Edit tool (not Write which rewrites the whole file).

**Expected hook behavior**: because we only touch the metadata section (before `## Prediction`), the immutability hook should let it through. If the hook falsely blocks → report a bug, **don't bypass the hook**.

### Phase 3: update the state file

```json
{
  "in_progress_session": null,
  "last_published_at": "<ISO timestamp>",
  "last_published_file": "predictions/<filename>",
  "last_published_video_folder": "videos/<...>/",
  "last_published_platform_id": "<aweme_id or BV number etc.>",
  "pending_retros": [
    "predictions/<filename>"
  ],
  "shoots": [
    // remove the item whose video_folder matches this publish; buffer -1
  ]
}
```

**`shoots` queue handling** (key to buffer tracking):
1. Read state.shoots[]
2. Find the item where `video_folder == this publish's video_folder` → remove it
3. If not found → warn "this video isn't in the buffer queue. Did you publish directly without going through /cheat-shoot?"—doesn't block, but reminds the user to go through /cheat-shoot next time so buffer tracking stays accurate

`last_published_platform_id` is the input when cheat-retro calls the adapter—e.g. douyin-session needs the aweme_id to fetch data directly.

`pending_retros` is the pending-retro list—`cheat-status` uses this list + RETRO_WINDOW_DAYS to show "which ones to retro today".

### Phase 4: reminder + next step + buffer status

```
✅ Registration complete: predictions/2026-05-04_a3f2c1d4e5b6_stop-expecting.md
   - Published at: 2026-05-04 14:32
   - Platform: douyin
   - URL: https://v.douyin.com/abc123

📦 Buffer: N pieces (color + meaning)
   At your cadence (X) = N×X days of buffer
   [if the color changed, prompt "now go shoot / pause shooting"]

⚠️  From this moment on, any play/like/comment data you see about this piece
    breaks the integrity of the blind declaration. If you see it by accident, tell me—
    I'll append an integrity warning to the file.

📅 Scheduled retro: T+3d, around 2026-05-07
   When the time comes, say: "retro predictions/2026-05-04_..."
```

The buffer color is derived from [shared-references/cadence-protocol.md](../../shared-references/cadence-protocol.md). If this publish drops the buffer into red (gap risk) → highlight a warning "must shoot ≥1 more piece today".

## Key Rules

1. **Don't touch the prediction section.** Even to fix a typo, editing the prediction section is not allowed at publish time
2. **Don't fetch data.** publish is a registration action, not data collection (that's cheat-retro's job)
3. **State field names are fixed.** `pending_retros` / `last_published_at` are contracts other sub-skills depend on (especially cheat-status / cheat-retro)
4. **Don't hard-error on unknown platform.** Can't identify → ask the user, allow `platform: other` as a fallback
5. **Re-registration requires explicit consent.** published_at already exists → ask "overwrite?", never silently overwrite

## Refusals

- "Just fix the prediction section while you're at it" → refuse. Use the `_redo.md` path
- "I'll add the URL later, just record the publish time first" → allowed: the URL field can be appended later; published_at + platform are required
- "Skip the metadata update, just clear in_progress_session" → refuse. The metadata is key context at retro time (especially platform, which decides which adapter to use for data collection)

## Integration

- Upstream: `/cheat-predict` (writes the prediction file and sets in_progress_session)
- Downstream: T+RETRO_WINDOW_DAYS later → `/cheat-retro`
- `cheat-status` uses the `pending_retros` field to compute "which ones to retro today"
- The platform field is used by `cheat-retro` to route to the corresponding perf-data adapter (manual-paste / youtube-data-api / etc.)
