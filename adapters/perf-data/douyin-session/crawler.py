"""Douyin Creator Center + front-end comment scraping.

After logging in once, the cookie persists in .auth/ and is reused directly afterward.
A single fetch shares one Chromium session, more stable than one process per step.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from playwright.async_api import BrowserContext, Page, Response, async_playwright
from paths import auth_dir, debug_dir

CREATOR_HOME = "https://creator.douyin.com/creator-micro/home"
CREATOR_CONTENT = "https://creator.douyin.com/creator-micro/content/manage"


class Session:
    """A single browser session, running multi-step fetches in sequence."""

    def __init__(self, ctx: BrowserContext, pw: Any) -> None:
        self.ctx = ctx
        self.pw = pw

    @classmethod
    async def open(cls, headless: bool = False) -> Session:
        pw = await async_playwright().start()
        auth_path = auth_dir()
        auth_path.mkdir(exist_ok=True)
        ctx = await pw.chromium.launch_persistent_context(
            user_data_dir=str(auth_path),
            headless=headless,
            viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        return cls(ctx, pw)

    async def close(self) -> None:
        try:
            await self.ctx.close()
        finally:
            await self.pw.stop()


async def ensure_login(timeout_s: int = 300) -> bool:
    """QR-code login; auto-closes once a sessionid is detected."""
    sess = await Session.open()
    try:
        page = await sess.ctx.new_page()
        await page.goto(CREATOR_HOME)
        print(f"[login] Scan the QR in the popped-up Chromium window. Waiting up to {timeout_s} seconds...")
        for i in range(timeout_s):
            try:
                cookies = await sess.ctx.cookies("https://creator.douyin.com")
                has_session = any(c["name"] in ("sessionid", "sessionid_ss") for c in cookies)
                if has_session and "login" not in page.url:
                    print(f"[login] ✓ login state detected (took {i}s)")
                    await asyncio.sleep(1)
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
        print("[login] timed out without detecting a login state.")
        return False
    finally:
        await sess.close()


async def fetch_recent_videos(sess: Session, limit: int = 50) -> list[dict]:
    """Pull the recent video list from Creator Center."""
    captured: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        if any(k in resp.url for k in (
            "/janus/douyin/creator/pc/work_list",
            "/aweme/v1/creator/item/list",
        )):
            try:
                data = await resp.json()
                captured.append({"url": resp.url, "data": data})
                if len(captured) == 1 and isinstance(data, dict):
                    print(f"[diag] video endpoint keys: {list(data.keys())[:8]}")
            except Exception:
                pass

    page.on("response", on_response)
    try:
        await page.goto(CREATOR_CONTENT, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(8)
        # paginate to load more
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 1200)")
            await asyncio.sleep(1.5)
        videos = _parse_video_list(captured, limit)
        if not videos:
            debug_path = debug_dir()
            debug_path.mkdir(parents=True, exist_ok=True)
            (debug_path / "creator_urls.txt").write_text("\n".join(all_urls), encoding="utf-8")
            print(f"[diag] video list empty, {len(all_urls)} requests dumped.")
        return videos
    finally:
        await page.close()


def _parse_video_list(captured: list[dict], limit: int) -> list[dict]:
    videos: list[dict] = []
    for item in captured:
        data = item["data"]
        candidates: list = []
        if isinstance(data, dict):
            for key in ("aweme_list", "item_list", "items", "list"):
                if key in data and isinstance(data[key], list):
                    candidates = data[key]
                    break
            if not candidates and isinstance(data.get("data"), dict):
                for key in ("aweme_list", "item_list", "items", "list"):
                    if key in data["data"] and isinstance(data["data"][key], list):
                        candidates = data["data"][key]
                        break
        for v in candidates:
            videos.append(_normalize_video(v))
    # dedup (by aweme_id)
    seen = set()
    dedup = []
    for v in videos:
        if v["aweme_id"] in seen:
            continue
        seen.add(v["aweme_id"])
        dedup.append(v)
    return dedup[:limit]


def _normalize_video(v: dict) -> dict:
    aweme_id = v.get("aweme_id") or v.get("item_id") or v.get("id") or ""
    stats = v.get("statistics") or v.get("stats") or {}
    video_info = v.get("video") or {}
    return {
        "aweme_id": str(aweme_id),
        "desc": v.get("desc") or v.get("title") or "",
        "create_time": v.get("create_time") or v.get("createTime") or 0,
        "duration_ms": video_info.get("duration") or v.get("duration") or 0,
        "play_count": stats.get("play_count") or v.get("play_count") or 0,
        "digg_count": stats.get("digg_count") or v.get("digg_count") or 0,
        "comment_count": stats.get("comment_count") or v.get("comment_count") or 0,
        "share_count": stats.get("share_count") or v.get("share_count") or 0,
        "collect_count": stats.get("collect_count") or v.get("collect_count") or 0,
        "raw": v,
    }


async def fetch_video_detail(sess: Session, aweme_id: str) -> dict:
    """Video data-analytics page (completion, follow-conversion, etc.)."""
    captured: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        if any(k in resp.url for k in (
            "data_center", "data_external", "aweme_statistic",
            "item_detail", "statistics", "/data/",
        )):
            try:
                data = await resp.json()
                captured.append({"url": resp.url, "data": data})
            except Exception:
                pass

    page.on("response", on_response)
    try:
        url = f"https://creator.douyin.com/creator-micro/data/following/media?item_id={aweme_id}"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(6)
        if not captured:
            debug_path = debug_dir()
            debug_path.mkdir(parents=True, exist_ok=True)
            (debug_path / "detail_urls.txt").write_text("\n".join(all_urls), encoding="utf-8")
            print("[diag] detailed-data endpoint not intercepted, URL list dumped.")
        return {"captured": captured}
    finally:
        await page.close()


async def fetch_comments_creator(sess: Session, aweme_id: str, max_pages: int = 60) -> list[dict]:
    """Use the Creator Center 'comment management' page. Works once you're logged into Creator Center, more stable than the front end."""
    captured: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        # the Creator Center comment endpoint path varies, match loosely
        if "comment" in resp.url and "creator" in resp.url:
            try:
                data = await resp.json()
                captured.append({"url": resp.url, "data": data})
            except Exception:
                pass
        elif "/aweme/v1/web/comment/list/" in resp.url:
            try:
                data = await resp.json()
                captured.append({"url": resp.url, "data": data})
            except Exception:
                pass

    page.on("response", on_response)
    try:
        # multiple candidate pages, use whichever works
        urls_to_try = [
            f"https://creator.douyin.com/creator-micro/content/comment-manage?item_id={aweme_id}",
            f"https://creator.douyin.com/creator-micro/content/comment-manage",
        ]
        for u in urls_to_try:
            try:
                await page.goto(u, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(4)
                break
            except Exception as e:
                print(f"[warning] {u} failed to load: {e}")

        # if the comment-management page has an item_id filter, it should already show only this video's comments
        # scroll to load pages
        for i in range(max_pages):
            await page.evaluate("window.scrollBy(0, 1500)")
            await asyncio.sleep(1.5)

        debug_path = debug_dir()
        debug_path.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(debug_path / "creator_comment_page.png"))
        (debug_path / "creator_comment_urls.txt").write_text("\n".join(all_urls), encoding="utf-8")

        # parse: extract any structure in data that might contain comments
        comments: list[dict] = []
        for item in captured:
            data = item["data"]
            for key in ("comments", "comment_list", "data"):
                if isinstance(data, dict) and key in data:
                    val = data[key]
                    if isinstance(val, list):
                        for c in val:
                            if isinstance(c, dict) and ("text" in c or "content" in c):
                                comments.append(_normalize_comment_creator(c, aweme_id))
        # dedup
        seen = set()
        dedup = []
        for c in comments:
            if c["cid"] in seen or c.get("aweme_id") and str(c["aweme_id"]) != str(aweme_id):
                continue
            seen.add(c["cid"])
            dedup.append(c)
        dedup.sort(key=lambda x: x["digg_count"], reverse=True)
        print(f"       creator page: {len(dedup)} comments total")
        return dedup
    finally:
        await page.close()


def _normalize_comment_creator(c: dict, default_aweme_id: str) -> dict:
    """Creator Center comment fields (not exactly the same as the front end)."""
    user = c.get("user") or c.get("user_info") or {}
    return {
        "cid": str(c.get("cid") or c.get("comment_id") or c.get("id") or ""),
        "aweme_id": str(c.get("aweme_id") or c.get("item_id") or default_aweme_id),
        "text": c.get("text") or c.get("content") or "",
        "digg_count": c.get("digg_count") or c.get("like_count") or 0,
        "reply_comment_total": c.get("reply_comment_total") or c.get("reply_count") or 0,
        "create_time": c.get("create_time") or 0,
        "user_name": user.get("nickname") or user.get("name") or c.get("user_name") or "",
        "ip_label": c.get("ip_label") or c.get("ip_location") or "",
    }


async def fetch_comments(sess: Session, aweme_id: str, max_pages: int = 60) -> list[dict]:
    """Front-end video page → click the comment icon → scroll to load → intercept comment/list XHR."""
    all_comments: list[dict] = []
    all_urls: list[str] = []

    page = await sess.ctx.new_page()

    async def on_response(resp: Response) -> None:
        all_urls.append(resp.url)
        if "/aweme/v1/web/comment/list/" in resp.url:
            try:
                data = await resp.json()
                for c in data.get("comments") or []:
                    all_comments.append(_normalize_comment(c))
            except Exception:
                pass

    page.on("response", on_response)
    try:
        url = f"https://www.douyin.com/video/{aweme_id}"
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[warning] video page load error: {e}")
        await asyncio.sleep(6)

        # click "video-comment-more" to expand comments (this is the "expand comment section" button)
        for sel in ['[data-e2e="video-comment-more"]', '[data-e2e="feed-comment-icon"]']:
            try:
                await page.locator(sel).first.click(force=True, timeout=3000)
                print(f"       clicked {sel}")
                break
            except Exception:
                pass
        await asyncio.sleep(4)

        debug_path = debug_dir()
        debug_path.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(debug_path / "comment_page.png"))

        # strategy: scrollIntoView on the last comment to trigger the IntersectionObserver lazy-load
        last_count = 0
        stagnant = 0
        i = 0
        for i in range(max_pages):
            await page.evaluate(
                """() => {
                    const items = document.querySelectorAll(
                        '[data-e2e="comment-item"], [data-e2e^="comment-item"], .comment-item'
                    );
                    if (items.length > 0) {
                        items[items.length - 1].scrollIntoView({block: 'end', behavior: 'instant'});
                    } else {
                        // the comment container hasn't rendered items yet, scroll the page
                        window.scrollBy(0, 1500);
                    }
                }"""
            )
            await asyncio.sleep(2.2)
            cur = len({c["cid"] for c in all_comments})
            if cur == last_count:
                stagnant += 1
                if stagnant >= 6:
                    break
            else:
                stagnant = 0
                last_count = cur
        print(f"       exited after {i+1} scrolls, accumulated {last_count} comments")

        # dedup + sort
        seen = set()
        dedup = []
        for c in all_comments:
            if c["cid"] in seen:
                continue
            seen.add(c["cid"])
            dedup.append(c)
        dedup.sort(key=lambda x: x["digg_count"], reverse=True)

        (debug_path / "comment_urls.txt").write_text("\n".join(all_urls), encoding="utf-8")
        return dedup
    finally:
        await page.close()


def _normalize_comment(c: dict) -> dict:
    user = c.get("user") or {}
    return {
        "cid": c.get("cid") or "",
        "text": c.get("text") or "",
        "digg_count": c.get("digg_count") or 0,
        "reply_comment_total": c.get("reply_comment_total") or 0,
        "create_time": c.get("create_time") or 0,
        "user_name": user.get("nickname") or "",
        "ip_label": c.get("ip_label") or "",
    }


async def fetch_all(aweme_id: str) -> dict:
    """One session runs the video list + detailed data + comments."""
    sess = await Session.open()
    try:
        print("  → opening Creator Center, pulling the video list")
        videos = await fetch_recent_videos(sess, limit=50)
        video = next((v for v in videos if v["aweme_id"] == aweme_id), None)
        if not video:
            print(f"       didn't find {aweme_id} in the recent {len(videos)}, continuing with minimal metadata.")
            video = _normalize_video({"aweme_id": aweme_id})
        else:
            print(f"       ✓ {video.get('desc', '')[:40]}")

        print("  → opening the data-analytics page")
        detail = await fetch_video_detail(sess, aweme_id)

        print("  → opening the front-end video page to fetch comments")
        comments = await fetch_comments(sess, aweme_id, max_pages=60)
        print(f"       final {len(comments)} comments")

        return {"video": video, "detail": detail, "comments": comments}
    finally:
        await sess.close()


if __name__ == "__main__":
    asyncio.run(ensure_login())
