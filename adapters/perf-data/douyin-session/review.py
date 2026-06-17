"""Run once after publishing a video: fetch comments/data → generate NotebookLM-friendly md.

Usage:
    python review.py                          # interactively pick a video
    python review.py login                    # login only (first time)
    python review.py video <aweme_id> [script.txt]   # specify a video directly
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import crawler
import renderer
from paths import videos_dir


def _prompt(msg: str) -> str:
    try:
        return input(msg).strip()
    except EOFError:
        return ""


def _pick_video(videos: list[dict]) -> dict | None:
    if not videos:
        print("No video list fetched. Confirm Creator Center is logged in, or the page structure changed and the crawler needs updating.")
        return None
    print("\nRecent videos:")
    for i, v in enumerate(videos):
        t = renderer._fmt_time(v.get("create_time", 0))
        desc = (v.get("desc") or "").replace("\n", " ")[:40]
        print(f"  [{i}] {t} | plays {renderer._fmt_num(v.get('play_count'))} | {desc}")
    choice = _prompt("\nPick an index (Enter to cancel): ")
    if not choice.isdigit():
        return None
    idx = int(choice)
    if 0 <= idx < len(videos):
        return videos[idx]
    return None


def _resolve_script(raw: str) -> str:
    """Allow dragging a file into the terminal; handle macOS escaped spaces."""
    p = raw.strip().strip("'").strip('"').replace("\\ ", " ")
    if not p:
        return ""
    path = Path(p).expanduser()
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")
    print(f"[warning] file not found {path}, leaving the script empty.")
    return ""


async def run() -> None:
    """Interactive: list the recent 10, the user picks one, then drags in the script, then fetch.

    Note: opens Chromium twice (once to pick the video, once to fetch everything).
    """
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    print("[pick video] opening Creator Center to pull the list...")
    sess = await crawler.Session.open()
    try:
        videos = await crawler.fetch_recent_videos(sess, limit=10)
    finally:
        await sess.close()
    video = _pick_video(videos)
    if not video:
        print("Cancelled.")
        return

    script_raw = _prompt("Drag in the script txt (or Enter to skip): ")
    script_path: str | None = None
    if script_raw.strip():
        p = Path(script_raw.strip().strip("'").strip('"').replace("\\ ", " ")).expanduser()
        if p.is_file():
            script_path = str(p)
        else:
            print(f"[warning] not found {p}, leaving the script empty.")

    await run_with_id(video["aweme_id"], script_path)


async def run_with_id(aweme_id: str, script_path: str | None) -> None:
    active_videos_dir = videos_dir()
    active_videos_dir.mkdir(parents=True, exist_ok=True)

    script = ""
    if script_path:
        p = Path(script_path).expanduser()
        if p.is_file():
            script = p.read_text(encoding="utf-8", errors="ignore")
            print(f"Script: {p.name} ({len(script)} chars)")
        else:
            print(f"[warning] script not found {p}")

    print(f"[fetch] video {aweme_id}")
    result = await crawler.fetch_all(aweme_id)
    video = result["video"]
    detail = result["detail"]
    comments = result["comments"]

    out_dir = renderer.output_dir_for(video, active_videos_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if script:
        (out_dir / "script.txt").write_text(script, encoding="utf-8")
    md = renderer.render_report(video, script, comments, detail.get("captured"))
    report = out_dir / "report.md"
    report.write_text(md, encoding="utf-8")
    print(f"\n✓ {report}")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        asyncio.run(crawler.ensure_login())
        return
    if len(sys.argv) > 1 and sys.argv[1] == "video":
        aweme_id = sys.argv[2]
        script_path = sys.argv[3] if len(sys.argv) > 3 else None
        asyncio.run(run_with_id(aweme_id, script_path))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        async def _list() -> None:
            sess = await crawler.Session.open()
            try:
                videos = await crawler.fetch_recent_videos(sess, limit=20)
            finally:
                await sess.close()
            for i, v in enumerate(videos):
                t = renderer._fmt_time(v.get("create_time", 0))
                desc = (v.get("desc") or "").replace("\n", " ")[:50]
                print(f"[{i}] {v['aweme_id']}  {t}  plays{renderer._fmt_num(v.get('play_count'))}  {desc}")
        asyncio.run(_list())
        return
    asyncio.run(run())


if __name__ == "__main__":
    main()
