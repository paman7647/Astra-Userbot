import base64
import io
import logging
import os
import random
import textwrap
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import aiohttp
from PIL import Image, ImageDraw, ImageFont
from utils.bridge_downloader import bridge_downloader
from utils.database import db
from utils.helpers import safe_edit, smart_reply, handle_command_error

from . import *

logger = logging.getLogger("Astra.Memes")

# ── Config ──────────────────────────────────
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)
REDDIT_UA = "AstraUserbot/1.0 (by /u/AstraBot)"
LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

# ── Reddit OAuth2 Token Cache ────────────────
_oauth_token_cache: Dict = {"token": None, "expires_at": 0}

# ── Subreddit Lists ────────────────────────
INDIAN_MEMES = [
    "IndianDankMemes", "SaimanSays", "indiameme", "DHHMemes", "FingMemes",
    "jeeneetards", "MandirGang", "2bharat4you", "teenindia",
    "DesiMemeTemplates", "MechanicalPandey", "Indiancolleges", "IndianMemeTemplates",
]
INDIAN_NSFW_MEMES = ["sunraybee", "okbhaibudbak", "IndianDankTemplates", "IndianDankMemes"]
GLOBAL_MEMES = [
    "dankmemes", "memes", "wholesomememes", "PrequelMemes",
    "terriblefacebookmemes", "funny", "ProgrammerHumor",
]
GLOBAL_NSFW_MEMES = ["HolUp", "cursedimages", "ImFinnaGoToHell", "dankmemes", "memes"]
ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_NSFW_MEMES = list(set(INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES))


# ── Database Helpers ────────────────────────

async def _db_ok() -> bool:
    try:
        return db.sqlite_conn is not None
    except:
        return False


async def cleanup_old_seen(hours: int = 24):
    try:
        if not await _db_ok():
            return
        cutoff = int(time.time()) - (hours * 3600)
        await db.sqlite_conn.execute("DELETE FROM seen_memes WHERE fetched_at < ?", (cutoff,))
        await db.sqlite_conn.commit()
    except Exception:
        pass


async def is_meme_seen(post_id: str) -> bool:
    try:
        if not await _db_ok():
            return False
        cur = await db.sqlite_conn.execute("SELECT 1 FROM seen_memes WHERE post_id = ?", (post_id,))
        return await cur.fetchone() is not None
    except:
        return False


async def mark_meme_seen(post_id: str, subreddit: str):
    try:
        if not await _db_ok():
            return
        await db.sqlite_conn.execute(
            "INSERT OR IGNORE INTO seen_memes (post_id, subreddit, fetched_at) VALUES (?, ?, ?)",
            (post_id, subreddit, int(time.time())),
        )
        await db.sqlite_conn.commit()
    except Exception:
        pass


# ── Helpers ─────────────────────────────────

def _is_video_post(pdata: dict, url: str) -> bool:
    low_url = url.lower()
    return bool(
        pdata.get("is_video")
        or pdata.get("post_hint") == "video"
        or pdata.get("post_hint") == "rich:video"
        or any(ext in low_url for ext in [".mp4", ".gifv", ".mkv", ".webm", ".mov"])
        or "v.redd.it" in low_url
        or "youtube.com" in low_url
        or "youtu.be" in low_url
    )


def get_reddit_headers():
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    ]
    return {"User-Agent": random.choice(browsers), "Accept": "application/json", "Cache-Control": "no-cache"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 1: MEME-API (Primary — fast, reliable)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_meme_api(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    subs = list(subreddits)
    random.shuffle(subs)
    try:
        async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:10]:
                try:
                    url = f"https://meme-api.com/gimme/{sub}/5"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        data = await resp.json()
                        memes = data.get("memes", [])
                        if not memes and data.get("url"):
                            memes = [data]
                        random.shuffle(memes)
                        for meme in memes:
                            pid = meme.get("postLink", "")
                            if await is_meme_seen(pid):
                                continue
                            if not nsfw and meme.get("nsfw"):
                                continue
                            m_url = meme.get("url", "")
                            if not m_url or _is_video_post({}, m_url):
                                continue
                            return {
                                "id": pid, "url": m_url,
                                "title": meme.get("title", "Meme"),
                                "subreddit": meme.get("subreddit", sub),
                                "is_nsfw": meme.get("nsfw", False),
                            }
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"meme-api error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 2: DIRECT REDDIT JSON (Fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_reddit(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ["hot", "new", "top"]
    random.shuffle(sorts)
    try:
        async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:5]:
                for sort in sorts:
                    try:
                        params = f"/{sort}.json?limit=50&raw_json=1"
                        if sort == "top":
                            params += "&t=" + random.choice(["day", "week", "month"])
                        async with session.get(f"https://www.reddit.com/r/{sub}{params}") as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json()
                        posts = data.get("data", {}).get("children", [])
                        if not posts:
                            continue
                        random.shuffle(posts)
                        for post in posts:
                            p = post.get("data", {})
                            if not p or p.get("stickied"):
                                continue
                            pid = p.get("name", "")
                            if not pid or await is_meme_seen(pid):
                                continue
                            if not nsfw and p.get("over_18"):
                                continue
                            url = p.get("url", "")
                            if _is_video_post(p, url) or p.get("is_self") or p.get("is_gallery"):
                                continue
                            low = url.lower()
                            if not any(low.endswith(e) for e in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                                if "i.redd.it" not in low and "imgur.com" not in low:
                                    continue
                                if "imgur.com" in url and "/a/" not in url and "/gallery/" not in url:
                                    url += ".jpg"
                            return {
                                "id": pid, "url": url,
                                "title": p.get("title", ""),
                                "subreddit": p.get("subreddit", sub),
                                "is_nsfw": bool(p.get("over_18")),
                            }
                    except Exception:
                        continue
    except Exception as e:
        logger.debug(f"reddit direct error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 3: REDDIT OAUTH2 (Authenticated)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _get_reddit_creds() -> tuple:
    cid = await db.get("reddit_client_id") or os.getenv("REDDIT_CLIENT_ID", "")
    csec = await db.get("reddit_client_secret") or os.getenv("REDDIT_CLIENT_SECRET", "")
    return cid, csec


async def _get_reddit_oauth_token() -> Optional[str]:
    global _oauth_token_cache
    now = time.time()
    if _oauth_token_cache["token"] and now < _oauth_token_cache["expires_at"] - 60:
        return _oauth_token_cache["token"]
    cid, csec = await _get_reddit_creds()
    if not cid or not csec:
        return None
    try:
        auth = aiohttp.BasicAuth(cid, csec)
        async with aiohttp.ClientSession(headers={"User-Agent": REDDIT_UA}) as session:
            async with session.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth, data={"grant_type": "client_credentials"}, timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    token = d.get("access_token")
                    if token:
                        _oauth_token_cache = {"token": token, "expires_at": now + d.get("expires_in", 3600)}
                        return token
    except Exception as e:
        logger.debug(f"Reddit OAuth error: {e}")
    return None


async def _fetch_via_reddit_oauth(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    token = await _get_reddit_oauth_token()
    if not token:
        return None
    headers = {"Authorization": f"bearer {token}", "User-Agent": REDDIT_UA, "Accept": "application/json"}
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ["hot", "new", "top"]
    random.shuffle(sorts)
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:5]:
                for sort in sorts:
                    try:
                        params = f"/{sort}.json?limit=50&raw_json=1"
                        if sort == "top":
                            params += "&t=" + random.choice(["day", "week", "month"])
                        async with session.get(f"https://oauth.reddit.com/r/{sub}{params}") as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json()
                        posts = data.get("data", {}).get("children", [])
                        if not posts:
                            continue
                        random.shuffle(posts)
                        for post in posts:
                            p = post.get("data", {})
                            if not p or p.get("stickied"):
                                continue
                            pid = p.get("name", "")
                            if not pid or await is_meme_seen(pid):
                                continue
                            if not nsfw and p.get("over_18"):
                                continue
                            url = p.get("url", "")
                            if _is_video_post(p, url) or p.get("is_self") or p.get("is_gallery"):
                                continue
                            low = url.lower()
                            if not any(low.endswith(e) for e in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                                if "i.redd.it" not in low and "imgur.com" not in low:
                                    continue
                                if "imgur.com" in url and "/a/" not in url:
                                    url += ".jpg"
                            return {
                                "id": pid, "url": url,
                                "title": p.get("title", ""),
                                "subreddit": p.get("subreddit", sub),
                                "is_nsfw": bool(p.get("over_18")),
                            }
                    except Exception:
                        continue
    except Exception as e:
        logger.debug(f"reddit oauth error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 4: IMGFLIP (Free image memes)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_imgflip(nsfw: bool = False) -> Optional[Dict]:
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get("https://api.imgflip.com/get_memes") as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                memes = data.get("data", {}).get("memes", [])
                if not memes:
                    return None
                meme = random.choice(memes)
                return {
                    "id": f"imgflip_{meme['id']}", "url": meme["url"],
                    "title": meme["name"], "subreddit": "imgflip", "is_nsfw": False,
                }
    except Exception as e:
        logger.debug(f"ImgFlip error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 5: 9GAG RSS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_9GAG_FEEDS = ["https://9gag.com/hot.rss", "https://9gag.com/trending.rss", "https://9gag.com/fresh.rss"]


async def _fetch_via_9gag(nsfw: bool = False) -> Optional[Dict]:
    import re
    feed_url = random.choice(_9GAG_FEEDS)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS reader)"}
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            async with session.get(feed_url) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
        root = ET.fromstring(text)
        ns = {"media": "http://search.yahoo.com/mrss/"}
        items = root.findall(".//item")
        if not items:
            return None
        random.shuffle(items)
        for item in items:
            img_url = None
            thumb = item.find("media:thumbnail", ns)
            if thumb is not None:
                img_url = thumb.get("url")
            if not img_url:
                enc = item.find("enclosure")
                if enc is not None:
                    img_url = enc.get("url")
            if not img_url:
                desc = item.findtext("description", "")
                match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
                if match:
                    img_url = match.group(1)
            if not img_url or any(ext in img_url.lower() for ext in [".mp4", ".webm"]):
                continue
            title = item.findtext("title", "9gag meme")
            link = item.findtext("link", "")
            post_id = f"9gag_{link.split('/')[-1] if link else random.randint(1000, 9999)}"
            return {
                "id": post_id, "url": img_url,
                "title": title, "subreddit": "9gag", "is_nsfw": False,
            }
    except Exception as e:
        logger.debug(f"9gag error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 6: GIPHY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_giphy(nsfw: bool = False) -> Optional[Dict]:
    api_key = await db.get("giphy_api_key") or os.getenv("GIPHY_API_KEY", "")
    if not api_key:
        return None
    try:
        rating = "r" if nsfw else "g"
        url = f"https://api.giphy.com/v1/gifs/trending?api_key={api_key}&limit=25&rating={rating}"
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                gifs = data.get("data", [])
                if not gifs:
                    return None
                gif = random.choice(gifs)
                gif_url = gif.get("images", {}).get("original", {}).get("url")
                if not gif_url:
                    return None
                return {
                    "id": f"giphy_{gif['id']}", "url": gif_url,
                    "title": gif.get("title") or "Giphy meme",
                    "subreddit": "giphy", "is_nsfw": nsfw,
                }
    except Exception as e:
        logger.debug(f"Giphy error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 7: REDDIT RSS (Free, no auth)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_reddit_rss(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    import re
    subs = list(subreddits)
    random.shuffle(subs)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; RSS reader)", "Accept": "application/rss+xml, application/xml, text/xml"}
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:6]:
                sort = random.choice(["hot", "new", "top"])
                t_param = "&t=week" if sort == "top" else ""
                url = f"https://www.reddit.com/r/{sub}/{sort}.rss?limit=25{t_param}"
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        text = await resp.text()
                    root = ET.fromstring(text)
                    entries = root.findall("atom:entry", ns) or root.findall(".//item")
                    if not entries:
                        continue
                    random.shuffle(entries)
                    for entry in entries:
                        entry_id = entry.findtext("atom:id", "", ns) or entry.findtext("id", "") or entry.findtext("link", "")
                        title = entry.findtext("atom:title", "", ns) or entry.findtext("title", "Meme")
                        content = (entry.findtext("atom:content", "", ns) or entry.findtext("content", "")
                                   or entry.findtext("atom:summary", "", ns) or entry.findtext("description", ""))
                        is_nsfw_post = "[nsfw]" in title.lower() or "nsfw" in content.lower()
                        if not nsfw and is_nsfw_post:
                            continue
                        post_id = f"rss_{entry_id.split('/')[-1] or entry_id[-16:]}"
                        if await is_meme_seen(post_id):
                            continue
                        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
                        img_url = img_match.group(1) if img_match else None
                        if not img_url:
                            link_el = entry.find("atom:link", ns)
                            direct_link = link_el.get("href", "") if link_el is not None else entry.findtext("link", "")
                            if direct_link:
                                low = direct_link.lower()
                                if any(low.endswith(e) for e in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                                    img_url = direct_link
                                elif "i.redd.it" in low or "i.imgur.com" in low:
                                    img_url = direct_link
                        if not img_url or _is_video_post({}, img_url):
                            continue
                        return {
                            "id": post_id, "url": img_url,
                            "title": title, "subreddit": sub, "is_nsfw": is_nsfw_post,
                        }
                except ET.ParseError:
                    continue
                except Exception:
                    continue
    except Exception as e:
        logger.debug(f"Reddit RSS error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 8: REDLIB / LibReddit PROXY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REDLIB_INSTANCES = [
    "https://redlib.kylrth.com", "https://redlib.catsarch.com",
    "https://rl.bloat.cat", "https://redlib.privacydev.net",
    "https://redlib.tux.pizza", "https://reddit.invak.id",
]


async def _fetch_via_redlib(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    subs = list(subreddits)
    random.shuffle(subs)
    instances = list(REDLIB_INSTANCES)
    random.shuffle(instances)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AstraBot)", "Accept": "application/json"}
    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for instance in instances[:3]:
                for sub in subs[:4]:
                    sort = random.choice(["hot", "new", "top"])
                    t_param = "&t=week" if sort == "top" else ""
                    url = f"{instance}/r/{sub}/{sort}.json?limit=50&raw_json=1{t_param}"
                    try:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                continue
                            data = await resp.json(content_type=None)
                        posts = data.get("data", {}).get("children", [])
                        if not posts:
                            continue
                        random.shuffle(posts)
                        for post in posts:
                            p = post.get("data", {})
                            if not p or p.get("stickied"):
                                continue
                            pid = p.get("name", "")
                            if not pid or await is_meme_seen(pid):
                                continue
                            if not nsfw and p.get("over_18"):
                                continue
                            url_post = p.get("url", "")
                            if _is_video_post(p, url_post) or p.get("is_self") or p.get("is_gallery"):
                                continue
                            low = url_post.lower()
                            if not any(low.endswith(e) for e in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                                if "i.redd.it" not in low and "imgur.com" not in low:
                                    continue
                                if "imgur.com" in url_post and "/a/" not in url_post:
                                    url_post += ".jpg"
                            return {
                                "id": pid, "url": url_post,
                                "title": p.get("title", ""),
                                "subreddit": p.get("subreddit", sub),
                                "is_nsfw": bool(p.get("over_18")),
                            }
                    except Exception:
                        continue
    except Exception as e:
        logger.debug(f"Redlib error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIFIED FETCHER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_meme(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    """Multi-source meme fetcher — 8 independent sources (image only).
    Order: meme-api → reddit-rss → redlib-proxy → reddit-oauth → reddit-direct → imgflip → 9gag → giphy
    """
    await cleanup_old_seen(24)

    result = await _fetch_via_meme_api(subreddits, nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_reddit_rss(subreddits, nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_redlib(subreddits, nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_reddit_oauth(subreddits, nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_reddit(subreddits, nsfw=nsfw)
    if result:
        return result

    # Global fallbacks
    result = await _fetch_via_meme_api(ALL_MEMES, nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_imgflip(nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_9gag(nsfw=nsfw)
    if result:
        return result
    result = await _fetch_via_giphy(nsfw=nsfw)
    if result:
        return result

    logger.warning(f"All 8 sources exhausted. nsfw={nsfw}")
    return None


# ── Media Sender ────────────────────────────

async def send_meme_media(client, chat_id, meme_data, reply_to) -> bool:
    url = meme_data.get("url", "")
    subreddit = meme_data.get("subreddit", "meme")
    caption = f"🔥 *{meme_data['title']}*\n\n📍 *Sub:* r/{subreddit}"
    if meme_data.get("is_nsfw"):
        caption = "🔞 " + caption
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return False
                raw = await resp.read()
                content_type = resp.headers.get("Content-Type", "image/jpeg")
    except Exception as e:
        logger.warning(f"Media download error: {e}")
        return False
    b64_data = base64.b64encode(raw).decode("utf-8")
    ext_map = {"image/jpeg": "jpg", "image/png": "png", "image/gif": "gif", "image/webp": "webp"}
    ext = ext_map.get(content_type.split(";")[0].strip(), "jpg")
    media = {"mimetype": content_type, "data": b64_data, "filename": f"meme_{subreddit}.{ext}"}
    await client.send_media(chat_id, media, caption=caption, reply_to=reply_to)
    return True


# ── Generic Handler (DRY) ──────────────────

async def _meme_handler(client, message, subs, label, fallback_subs=None, **kwargs):
    status_msg = await smart_reply(message, f"*{label}*")
    try:
        meme = await fetch_meme(subs, **kwargs)
        if not meme and fallback_subs:
            meme = await fetch_meme(fallback_subs, **kwargs)
        if meme:
            ok = await send_meme_media(client, message.chat_id, meme, message.id)
            if ok:
                await mark_meme_seen(meme["id"], meme["subreddit"])
                await status_msg.delete()
            else:
                await safe_edit(status_msg, f"❌ Media download failed.\n📎 URL: `{meme.get('url', '?')[:80]}`")
        else:
            subs_tried = ", ".join(subs[:3])
            await safe_edit(
                status_msg,
                f"❌ No fresh memes found.\n🔍 Subs: `{subs_tried}`\n💡 Use `.memedebug` to check connectivity.",
            )
    except Exception as e:
        await handle_command_error(client, message, e, context="Meme command failure")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# COMMAND HANDLERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@astra_command(name="imeme", description="Get a spicy Indian meme", category="Fun & Memes", usage=".imeme")
async def imeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳 Fetching Indian meme...")


@astra_command(name="idmdmes", description="Get a NSFW/Edgy Indian meme", category="Fun & Memes", usage=".idmdmes")
async def idmdmes_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞 Fetching edgy Indian meme...", fallback_subs=INDIAN_MEMES, nsfw=True)


@astra_command(name="meme", description="Get a random global meme", category="Fun & Memes", aliases=["m"], usage=".meme", is_public=True)
async def meme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_MEMES, "🌍 Fetching global meme...")


@astra_command(name="dmeme", description="Get a NSFW/Dark global meme", category="Fun & Memes", usage=".dmeme")
async def dmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_NSFW_MEMES, "🔞 Fetching dark meme...", fallback_subs=ALL_MEMES, nsfw=True)


@astra_command(name="idm", description="Get a meme from r/IndianDankMemes", category="Fun & Memes", usage=".idm")
async def idm_handler(client: Client, message: Message):
    await _meme_handler(client, message, ["IndianDankMemes"], "🇮🇳 Fetching IDM meme...", fallback_subs=INDIAN_MEMES)


# ── Meme Maker (PIL) ─────────────────────────

@astra_command(
    name="mm",
    description="Create a meme from an image. Use | to separate top and bottom text.",
    category="Tools & Utilities",
    usage="(reply to image) Top Text | Bottom Text",
    is_public=True,
)
async def meme_maker_handler(client: Client, message: Message):
    """Meme maker plugin using PIL."""
    is_image = message.type == MessageType.IMAGE
    has_quoted_image = message.has_quoted_msg and message.quoted_type == MessageType.IMAGE
    if not is_image and not has_quoted_image:
        return await smart_reply(message, "✨ Reply to an image to make a meme.")

    text = " ".join(extract_args(message))
    if not text:
        return await smart_reply(message, "✨ Provide text for the meme. Example: `.mm Top Text | Bottom Text`")

    top_text, bottom_text = "", ""
    if "|" in text:
        parts = text.split("|")
        top_text = parts[0].strip().upper()
        bottom_text = parts[1].strip().upper()
    else:
        top_text = text.strip().upper()

    status_msg = await smart_reply(message, "✨ **Generating meme...**")

    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download image.")

    img = Image.open(io.BytesIO(media_data)).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    font_path = os.path.join(LOGOS_DIR, "font1.ttf")
    if not os.path.exists(font_path):
        font_path = None

    def get_font(text_line, max_w, max_h):
        size = int(height / 10)
        try:
            font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
            while font_path and font.getlength(text_line) > max_w and size > 12:
                size -= 2
                font = ImageFont.truetype(font_path, size)
            return font
        except:
            return ImageFont.load_default()

    def draw_text(text_val, pos_type):
        if not text_val:
            return
        wrapped = textwrap.wrap(text_val, width=20)
        y_curr = 20 if pos_type == "top" else (height - (len(wrapped) * (height / 10)) - 20)
        for line in wrapped:
            fnt = get_font(line, width * 0.9, height / 10)
            bbox = draw.textbbox((0, 0), line, font=fnt)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (width - w) / 2
            for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                draw.text((x + ox, y_curr + oy), line, font=fnt, fill="black")
            draw.text((x, y_curr), line, font=fnt, fill="white")
            y_curr += h + 10

    draw_text(top_text, "top")
    draw_text(bottom_text, "bottom")

    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90)
    await client.send_media(
        str(message.chat_id),
        {"mimetype": "image/jpeg", "data": base64.b64encode(out.getvalue()).decode(), "filename": "meme.jpg"},
        caption="✨ **Meme Generated By Astra**"
    )
    await status_msg.delete()


# ── Debug & Config ─────────────────────────

@astra_command(name="memedebug", description="Diagnose meme fetching issues", category="System", usage=".memedebug", owner_only=True)
async def memedebug_handler(client: Client, message: Message):
    status_msg = await smart_reply(message, "🔍 *Running Meme Diagnostics...*")
    report = "🛠️ *Astra Meme Diagnostics*\n━━━━━━━━━━━━━━━━━━━━━━\n"

    async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
        try:
            async with session.get("https://meme-api.com/gimme/1") as resp:
                icon = "✅" if resp.status == 200 else "⚠️"
                report += f"{icon} *MemeAPI:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *MemeAPI:* `{str(e)[:40]}`\n"

        try:
            async with session.get("https://www.reddit.com/r/memes/hot.json?limit=1") as resp:
                icon = "✅" if resp.status == 200 else ("🚫" if resp.status == 403 else "⚠️")
                report += f"{icon} *Reddit Direct:* `{resp.status}`"
                if resp.status == 403:
                    report += " _(IP blocked — use OAuth)_"
                report += "\n"
        except Exception as e:
            report += f"❌ *Reddit Direct:* `{str(e)[:40]}`\n"

        token = await _get_reddit_oauth_token()
        if token:
            try:
                oauth_headers = {"Authorization": f"bearer {token}", "User-Agent": REDDIT_UA}
                async with session.get("https://oauth.reddit.com/r/memes/hot.json?limit=1", headers=oauth_headers) as resp:
                    icon = "✅" if resp.status == 200 else "⚠️"
                    report += f"{icon} *Reddit OAuth2:* `{resp.status}`\n"
            except Exception as e:
                report += f"❌ *Reddit OAuth2:* `{str(e)[:40]}`\n"
        else:
            report += "⬜ *Reddit OAuth2:* Not configured\n"

        try:
            async with session.get("https://www.reddit.com/r/memes/hot.rss?limit=1", headers={"Accept": "application/xml"}) as resp:
                icon = "✅" if resp.status == 200 else "⚠️"
                report += f"{icon} *Reddit RSS:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *Reddit RSS:* `{str(e)[:40]}`\n"

        inst = random.choice(REDLIB_INSTANCES)
        try:
            async with session.get(f"{inst}/r/memes/hot.json?limit=1") as resp:
                icon = "✅" if resp.status == 200 else "⚠️"
                report += f"{icon} *Redlib ({inst.split('//')[-1]}):* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *Redlib:* `{str(e)[:40]}`\n"

        try:
            async with session.get("https://api.imgflip.com/get_memes") as resp:
                icon = "✅" if resp.status == 200 else "⚠️"
                report += f"{icon} *ImgFlip:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *ImgFlip:* `{str(e)[:40]}`\n"

        try:
            async with session.get("https://9gag.com/hot.rss", headers={"User-Agent": "Mozilla/5.0 (compatible; RSS reader)"}) as resp:
                icon = "✅" if resp.status == 200 else "⚠️"
                report += f"{icon} *9gag RSS:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *9gag RSS:* `{str(e)[:40]}`\n"

        giphy_key = await db.get("giphy_api_key") or os.getenv("GIPHY_API_KEY", "")
        if giphy_key:
            try:
                async with session.get(f"https://api.giphy.com/v1/gifs/trending?api_key={giphy_key}&limit=1") as resp:
                    icon = "✅" if resp.status == 200 else "⚠️"
                    report += f"{icon} *Giphy:* `{resp.status}`\n"
            except Exception as e:
                report += f"❌ *Giphy:* `{str(e)[:40]}`\n"
        else:
            report += "⬜ *Giphy:* Not configured\n"

    report += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    report += "💡 *Priority:* MemeAPI → RSS → Redlib → OAuth2 → Direct → ImgFlip → 9gag → Giphy\n"
    r_cid, _ = await _get_reddit_creds()
    if not r_cid:
        report += "\n🔧 *Tip:* `.setreddit <client_id> <secret>` for OAuth2"
    if not giphy_key:
        report += "\n🔧 *Tip:* `.setgiphy <api_key>` for Giphy GIFs"
    await safe_edit(status_msg, report)


@astra_command(name="setreddit", description="Set Reddit OAuth2 credentials", category="Config", usage=".setreddit <client_id> <client_secret>", owner_only=True)
async def setreddit_handler(client: Client, message: Message):
    args = extract_args(message)
    if len(args) < 2:
        cid, _ = await _get_reddit_creds()
        return await smart_reply(
            message,
            f"🔑 *Reddit OAuth2 Config*\n━━━━━━━━━━━━━━━━━━━━\n*Status:* {'✅ Configured' if cid else '❌ Not set'}\n\n💡 *Usage:* `.setreddit <client_id> <client_secret>`\nGet free creds → reddit.com/prefs/apps *(script type)*",
        )
    cid, csec = args[0], args[1]
    status_msg = await smart_reply(message, "🔄 *Validating credentials...*")
    try:
        auth = aiohttp.BasicAuth(cid, csec)
        async with aiohttp.ClientSession(headers={"User-Agent": REDDIT_UA}, timeout=REQUEST_TIMEOUT) as session:
            async with session.post("https://www.reddit.com/api/v1/access_token", auth=auth, data={"grant_type": "client_credentials"}) as resp:
                if resp.status != 200:
                    return await safe_edit(status_msg, f"❌ *Invalid credentials* (HTTP {resp.status})")
                d = await resp.json()
                if not d.get("access_token"):
                    return await safe_edit(status_msg, "❌ *Token response invalid.*")
    except Exception as e:
        return await safe_edit(status_msg, f"❌ *Validation failed:* `{str(e)[:80]}`")
    await db.set("reddit_client_id", cid)
    await db.set("reddit_client_secret", csec)
    global _oauth_token_cache
    _oauth_token_cache = {"token": None, "expires_at": 0}
    await safe_edit(status_msg, f"✅ *Reddit OAuth2 credentials saved!*\n━━━━━━━━━━━━━━━━━━━━\n*Client ID:* `{'*' * 8 + cid[-4:]}`\n*Status:* Token validated ✅\n\n💡 Run `.memedebug` to confirm.")


@astra_command(name="setgiphy", description="Set Giphy API key", category="Config", usage=".setgiphy <api_key>", owner_only=True)
async def setgiphy_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args:
        key = await db.get("giphy_api_key") or os.getenv("GIPHY_API_KEY", "")
        return await smart_reply(
            message,
            f"🎞️ *Giphy Config*\n━━━━━━━━━━━━━━━━━━━━\n*Status:* {'✅ Configured' if key else '❌ Not set'}\n\n💡 *Usage:* `.setgiphy <api_key>`\nGet free key → developers.giphy.com",
        )
    api_key = args[0]
    status_msg = await smart_reply(message, "🔄 *Validating Giphy key...*")
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(f"https://api.giphy.com/v1/gifs/trending?api_key={api_key}&limit=1") as resp:
                if resp.status != 200:
                    return await safe_edit(status_msg, f"❌ *Invalid Giphy key* (HTTP {resp.status})")
    except Exception as e:
        return await safe_edit(status_msg, f"❌ *Validation failed:* `{str(e)[:80]}`")
    await db.set("giphy_api_key", api_key)
    await safe_edit(status_msg, f"✅ *Giphy API key saved!*\n*Key:* `{'*' * 8 + api_key[-4:]}`\n\n💡 Giphy GIFs are now active.")
