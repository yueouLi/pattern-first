"""Render the fetched data into NotebookLM-friendly Markdown."""
from __future__ import annotations

import datetime as dt
from pathlib import Path


def _fmt_time(ts: int) -> str:
    if not ts:
        return "unknown"
    return dt.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _fmt_num(n: int | None) -> str:
    if n is None:
        return "-"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def _fmt_duration(ms: int) -> str:
    if not ms:
        return "-"
    s = ms // 1000
    return f"{s//60}:{s%60:02d}" if s >= 60 else f"{s}s"


def render_report(
    video: dict,
    script: str,
    comments: list[dict],
    detail_captured: list[dict] | None = None,
) -> str:
    lines: list[str] = []
    desc = video.get("desc") or "(untitled)"
    aweme_id = video["aweme_id"]

    lines.append(f"# {desc}")
    lines.append("")
    lines.append(f"- Video ID: `{aweme_id}`")
    lines.append(f"- Published: {_fmt_time(video.get('create_time', 0))}")
    lines.append(f"- Duration: {_fmt_duration(video.get('duration_ms', 0))}")
    lines.append(f"- Link: https://www.douyin.com/video/{aweme_id}")
    lines.append(f"- Fetched at: {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("## Playback data")
    lines.append("")
    lines.append(f"- Plays: {_fmt_num(video.get('play_count'))}")
    lines.append(f"- Likes: {_fmt_num(video.get('digg_count'))}")
    lines.append(f"- Comments: {_fmt_num(video.get('comment_count'))}")
    lines.append(f"- Saves: {_fmt_num(video.get('collect_count'))}")
    lines.append(f"- Shares: {_fmt_num(video.get('share_count'))}")
    lines.append("")

    if detail_captured:
        lines.append("### Detailed metrics (from Creator Center)")
        lines.append("")
        lines.append("```json")
        import json
        for item in detail_captured[:3]:
            lines.append(json.dumps(item["data"], ensure_ascii=False, indent=2)[:2000])
        lines.append("```")
        lines.append("")

    lines.append("## Original script")
    lines.append("")
    lines.append(script.strip() if script.strip() else "(not provided)")
    lines.append("")

    lines.append(f"## Comments (descending by likes, {len(comments)} total)")
    lines.append("")
    if not comments:
        lines.append("(no comments fetched—the comment section may be collapsed or the account isn't logged in)")
    else:
        for c in comments:
            text = c["text"].replace("\n", " ").strip()
            reply = f" 💬{c['reply_comment_total']}" if c.get("reply_comment_total") else ""
            lines.append(f"- [👍{c['digg_count']}{reply}] {text}")
    lines.append("")

    return "\n".join(lines)


def slugify(text: str, max_len: int = 30) -> str:
    """Generate a folder-friendly short title."""
    bad = '<>:"/\\|?*\n\r\t'
    out = "".join("_" if ch in bad else ch for ch in text).strip()
    return out[:max_len] or "untitled"


def output_dir_for(video: dict, root: Path) -> Path:
    date = _fmt_time(video.get("create_time", 0))[:10].replace("unknown", "nodate")
    slug = slugify(video.get("desc") or video["aweme_id"])
    return root / f"{date}_{slug}"
