# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import random
import aiohttp
import base64
import time
import logging
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
from . import *
from utils.helpers import safe_edit, smart_reply, report_error
from utils.database import db

logger = logging.getLogger("Astra.Memes")

# ── Config ──────────────────────────────────
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=20)
REDDIT_UA = 'AstraUserbot/1.0 (by /u/AstraBot)'
REDDIT_HEADERS = {
    'User-Agent': REDDIT_UA,
    'Accept': 'application/json'
}

# ── Reddit OAuth2 Token Cache ────────────────
_oauth_token_cache: Dict = {'token': None, 'expires_at': 0}

# ── Subreddit Lists ────────────────────────
INDIAN_MEMES = [
    'IndianDankMemes', 'SaimanSays', 'indiameme', 'DHHMemes', 
    'FingMemes', 'jeeneetards', 'MandirGang', '2bharat4you',
    'teenindia', 'DesiMemeTemplates', 'MechanicalPandey', 
    'Indiancolleges', 'IndianMemeTemplates'
]

INDIAN_NSFW_MEMES = [
    'sunraybee', 'okbhaibudbak', 'IndianDankTemplates',
    'IndianDankMemes'
]

GLOBAL_MEMES = [
    'dankmemes', 'memes', 'wholesomememes', 'PrequelMemes', 
    'terriblefacebookmemes', 'funny', 'ProgrammerHumor'
]

GLOBAL_VIDEO_MEMES = [
    'MemeVideos', 'VideoMemes', 'perfectlycutscreams', 'unexpected', 
    'maybemaybemaybe', 'nonononoyes', 'yesyesyesno'
]

GLOBAL_NSFW_MEMES = [
    'HolUp', 'cursedimages', 'ImFinnaGoToHell',
    'dankmemes', 'memes'
]

ALL_MEMES = INDIAN_MEMES + GLOBAL_MEMES
ALL_VIDEO_MEMES = INDIAN_MEMES + GLOBAL_VIDEO_MEMES
ALL_NSFW_MEMES = list(set(INDIAN_NSFW_MEMES + GLOBAL_NSFW_MEMES))

# ── Database Helpers ────────────────────────

async def _db_ok() -> bool:
    try: return db.sqlite_conn is not None
    except: return False

async def cleanup_old_seen(hours: int = 24):
    """Purge seen entries older than N hours so memes recycle."""
    try:
        if not await _db_ok(): return
        cutoff = int(time.time()) - (hours * 3600)
        await db.sqlite_conn.execute("DELETE FROM seen_memes WHERE fetched_at < ?", (cutoff,))
        await db.sqlite_conn.commit()
    except Exception: pass

async def is_meme_seen(post_id: str) -> bool:
    try:
        if not await _db_ok(): return False
        cur = await db.sqlite_conn.execute("SELECT 1 FROM seen_memes WHERE post_id = ?", (post_id,))
        return await cur.fetchone() is not None
    except: return False

async def mark_meme_seen(post_id: str, subreddit: str):
    try:
        if not await _db_ok(): return
        await db.sqlite_conn.execute(
            "INSERT OR IGNORE INTO seen_memes (post_id, subreddit, fetched_at) VALUES (?, ?, ?)",
            (post_id, subreddit, int(time.time()))
        )
        await db.sqlite_conn.commit()
    except Exception as e:
        logger.debug(f"mark_seen: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 1: MEME-API (Primary — fast, reliable)
# Uses meme-api.com which proxies Reddit server-side
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_video_post(pdata: dict, url: str) -> bool:
    """Enhanced video detection."""
    low_url = url.lower()
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        pdata.get('post_hint') == 'rich:video' or
        any(ext in low_url for ext in ['.mp4', '.gifv', '.mkv', '.webm', '.mov']) or
        'v.redd.it' in low_url or
        'youtube.com/shorts' in low_url or
        'youtube.com/watch' in low_url or
        'youtu.be' in low_url
    )

async def _fetch_via_meme_api(subreddits: List[str], nsfw: bool = False, video_only: bool = False) -> Optional[Dict]:
    """Fetch from meme-api.com — handles Reddit scraping server-side."""
    subs = list(subreddits)
    random.shuffle(subs)
    
    # Use a safer batch size (20 instead of 50) to avoid 400/403 errors
    count = 20 if video_only else 5
    
    try:
        async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
            # Phase 1: Try specific subreddits
            for sub in subs[:10]:
                try:
                    url = f"https://meme-api.com/gimme/{sub}/{count}"
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            logger.debug(f"MemeAPI Failed | /r/{sub} | Status: {resp.status}")
                            continue
                        data = await resp.json()
                        memes = data.get('memes', [])
                        if not memes and data.get('url'): memes = [data]
                        
                        random.shuffle(memes)
                        for meme in memes:
                            pid = meme.get('postLink', '')
                            if await is_meme_seen(pid): continue
                            if not nsfw and meme.get('nsfw'): continue
                            
                            m_url = meme.get('url', '')
                            if not m_url: continue
                            
                            is_vid = _is_video_post({}, m_url)
                            if video_only and not is_vid: continue
                            
                            return {
                                "id": pid, "url": m_url,
                                "title": meme.get('title', 'Meme'),
                                "subreddit": meme.get('subreddit', sub),
                                "is_video": is_vid, "is_nsfw": meme.get('nsfw', False),
                                "is_text": False
                            }
                except Exception: continue
            
            # Phase 2: Global Fallback for videos if subs failed
            if video_only:
                try:
                    url = f"https://meme-api.com/gimme/50"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            memes = data.get('memes', [])
                            random.shuffle(memes)
                            for meme in memes:
                                pid = meme.get('postLink', '')
                                if await is_meme_seen(pid): continue
                                if not nsfw and meme.get('nsfw'): continue
                                m_url = meme.get('url', '')
                                if _is_video_post({}, m_url):
                                    return {
                                        "id": pid, "url": m_url,
                                        "title": meme.get('title', 'Meme'),
                                        "subreddit": meme.get('subreddit', meme.get('subreddit', 'unknown')),
                                        "is_video": True, "is_nsfw": meme.get('nsfw', False),
                                        "is_text": False
                                    }
                        else:
                            logger.debug(f"MemeAPI Global Failed | Status: {resp.status}")
                except Exception: pass
                
    except Exception as e:
        logger.debug(f"meme-api session error: {e}")
    
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 2: DIRECT REDDIT (Fallback)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _is_video_post(pdata: dict, url: str) -> bool:
    return bool(
        pdata.get('is_video') or 
        pdata.get('post_hint') == 'video' or
        'v.redd.it' in url or
        url.lower().endswith(('.mp4', '.gifv', '.webm'))
    )

def _get_video_url(pdata: dict) -> Optional[str]:
    for src in [pdata.get('media'), pdata.get('secure_media')]:
        if src and src.get('reddit_video', {}).get('fallback_url'):
            return src['reddit_video']['fallback_url']
    for cp in pdata.get('crosspost_parent_list', []):
        for src in [cp.get('media'), cp.get('secure_media')]:
            if src and src.get('reddit_video', {}).get('fallback_url'):
                return src['reddit_video']['fallback_url']
    url = pdata.get('url', '')
    if 'v.redd.it' in url or url.lower().endswith(('.mp4', '.gifv')):
        return url
    return None

def get_reddit_headers():
    """Returns randomized headers to avoid fingerprinting."""
    browsers = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
    ]
    return {
        'User-Agent': random.choice(browsers),
        'Accept': 'application/json',
        'Cache-Control': 'no-cache'
    }

async def _fetch_via_reddit_search(subreddits: List[str], nsfw: bool = False) -> Optional[Dict]:
    """Search for video-specific URLs on Reddit directly."""
    subs = list(subreddits)
    random.shuffle(subs)
    
    # Target video formats directly, then keywords
    queries = ['url:v.redd.it', 'url:mp4', 'url:gifv', 'video', 'meme']
    random.shuffle(queries)
    
    try:
        async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:6]:
                for query in queries:
                    try:
                        search_url = f"https://www.reddit.com/r/{sub}/search.json?q={query}&restrict_sr=1&sort=new&limit=25&raw_json=1"
                        async with session.get(search_url) as resp:
                            if resp.status != 200:
                                logger.debug(f"Reddit Search Failed | /r/{sub} | Q:{query} | Status:{resp.status}")
                                continue
                            data = await resp.json()
                        
                        posts = data.get('data', {}).get('children', [])
                        if not posts: continue
                        random.shuffle(posts)
                        
                        for post in posts:
                            p = post.get('data', {})
                            if not p or p.get('stickied'): continue
                            
                            pid = p.get('name', '')
                            if not pid or await is_meme_seen(pid): continue
                            if not nsfw and p.get('over_18'): continue
                            
                            url = p.get('url', '')
                            # If it's a video search, we strictly check for video
                            is_vid = _is_video_post(p, url)
                            if not is_vid: continue
                            
                            vid_url = _get_video_url(p)
                            if not vid_url: continue
                            
                            return {
                                "id": pid, "url": vid_url,
                                "title": p.get('title', ''),
                                "subreddit": p.get('subreddit', sub),
                                "is_video": True, "is_nsfw": bool(p.get('over_18')),
                                "is_text": False
                            }
                    except Exception as e:
                        logger.debug(f"reddit search error [{sub}/{query}]: {e}")
                        continue
    except Exception as e:
        logger.debug(f"reddit search session error: {e}")
    
    return None

async def _fetch_via_reddit(
    subreddits: List[str], video_only: bool = False, 
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Direct Reddit JSON fallback."""
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ['hot', 'new', 'top']
    random.shuffle(sorts)
    
    try:
        async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:5]:
                for sort in sorts:
                    try:
                        params = f"/{sort}.json?limit=50&raw_json=1"
                        if sort == 'top':
                            params += "&t=" + random.choice(['day', 'week', 'month'])
                        
                        async with session.get(f"https://www.reddit.com/r/{sub}{params}") as resp:
                            if resp.status != 200:
                                logger.debug(f"Direct Reddit Failed | /r/{sub}/{sort} | Status: {resp.status}")
                                continue
                            data = await resp.json()
                        
                        posts = data.get('data', {}).get('children', [])
                        if not posts: continue
                        random.shuffle(posts)
                        
                        for post in posts:
                            p = post.get('data', {})
                            if not p or p.get('stickied'): continue
                            
                            pid = p.get('name', '')
                            if not pid or await is_meme_seen(pid): continue
                            if not nsfw and p.get('over_18'): continue
                            
                            url = p.get('url', '')
                            is_vid = _is_video_post(p, url)
                            is_text = p.get('is_self', False)
                            is_gallery = p.get('is_gallery') or 'reddit.com/gallery/' in url
                            
                            # Text posts (stories)
                            if is_text:
                                if not allow_text: continue
                                text = p.get('selftext', '')
                                if len(text) < 20: continue
                                return {
                                    "id": pid, "title": p.get('title', ''),
                                    "subreddit": p.get('subreddit', sub),
                                    "text": text, "is_video": False,
                                    "is_nsfw": bool(p.get('over_18')), "is_text": True
                                }
                            
                            # Video posts
                            if video_only:
                                if not is_vid: continue
                                vid_url = _get_video_url(p)
                                if not vid_url: continue
                                return {
                                    "id": pid, "url": vid_url,
                                    "title": p.get('title', ''),
                                    "subreddit": p.get('subreddit', sub),
                                    "is_video": True, "is_nsfw": bool(p.get('over_18')),
                                    "is_text": False
                                }
                            
                            # Image posts
                            if is_vid or is_gallery or is_text: continue
                            low = url.lower()
                            if not any(low.endswith(e) for e in ['.jpg','.jpeg','.png','.gif','.webp']):
                                if 'i.redd.it' not in low and 'imgur.com' not in low:
                                    continue
                                if 'imgur.com' in url and '/a/' not in url and '/gallery/' not in url:
                                    url += '.jpg'
                            
                            return {
                                "id": pid, "url": url,
                                "title": p.get('title', ''),
                                "subreddit": p.get('subreddit', sub),
                                "is_video": False, "is_nsfw": bool(p.get('over_18')),
                                "is_text": False
                            }
                    except Exception as e:
                        logger.debug(f"reddit fallback error [{sub}/{sort}]: {e}")
                        continue
    except Exception as e:
        logger.debug(f"reddit session error: {e}")
    
    return None

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 3: REDDIT OAUTH2 (Authenticated — bypasses IP blocks)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _get_reddit_creds() -> tuple:
    """Return (client_id, client_secret) — DB takes priority over env vars."""
    cid = await db.get('reddit_client_id') or os.getenv('REDDIT_CLIENT_ID', '')
    csec = await db.get('reddit_client_secret') or os.getenv('REDDIT_CLIENT_SECRET', '')
    return cid, csec


async def _get_reddit_oauth_token() -> Optional[str]:
    """Fetch Reddit OAuth2 client-credentials token (cached).
    Credentials come from DB (set via .setreddit) or REDDIT_CLIENT_ID env var.
    Get free credentials at https://www.reddit.com/prefs/apps
    """
    global _oauth_token_cache
    now = time.time()
    if _oauth_token_cache['token'] and now < _oauth_token_cache['expires_at'] - 60:
        return _oauth_token_cache['token']

    cid, csec = await _get_reddit_creds()
    if not cid or not csec:
        return None

    try:
        auth = aiohttp.BasicAuth(cid, csec)
        headers = {'User-Agent': REDDIT_UA}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data={'grant_type': 'client_credentials'},
                timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status == 200:
                    d = await resp.json()
                    token = d.get('access_token')
                    if token:
                        _oauth_token_cache = {
                            'token': token,
                            'expires_at': now + d.get('expires_in', 3600)
                        }
                        return token
                logger.debug(f"Reddit OAuth token failed: {resp.status}")
    except Exception as e:
        logger.debug(f"Reddit OAuth error: {e}")
    return None


async def _fetch_via_reddit_oauth(
    subreddits: List[str], video_only: bool = False,
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Authenticated Reddit API via OAuth2 — avoids IP-based 403 blocks."""
    token = await _get_reddit_oauth_token()
    if not token:
        return None

    headers = {
        'Authorization': f'bearer {token}',
        'User-Agent': REDDIT_UA,
        'Accept': 'application/json'
    }
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ['hot', 'new', 'top']
    random.shuffle(sorts)

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:5]:
                for sort in sorts:
                    try:
                        params = f"/{sort}.json?limit=50&raw_json=1"
                        if sort == 'top':
                            params += "&t=" + random.choice(['day', 'week', 'month'])
                        async with session.get(f"https://oauth.reddit.com/r/{sub}{params}") as resp:
                            if resp.status != 200:
                                logger.debug(f"Reddit OAuth Failed | /r/{sub}/{sort} | {resp.status}")
                                continue
                            data = await resp.json()

                        posts = data.get('data', {}).get('children', [])
                        if not posts: continue
                        random.shuffle(posts)

                        for post in posts:
                            p = post.get('data', {})
                            if not p or p.get('stickied'): continue
                            pid = p.get('name', '')
                            if not pid or await is_meme_seen(pid): continue
                            if not nsfw and p.get('over_18'): continue

                            url = p.get('url', '')
                            is_vid = _is_video_post(p, url)
                            is_text = p.get('is_self', False)
                            is_gallery = p.get('is_gallery') or 'reddit.com/gallery/' in url

                            if is_text:
                                if not allow_text: continue
                                text = p.get('selftext', '')
                                if len(text) < 20: continue
                                return {
                                    'id': pid, 'title': p.get('title', ''),
                                    'subreddit': p.get('subreddit', sub),
                                    'text': text, 'is_video': False,
                                    'is_nsfw': bool(p.get('over_18')), 'is_text': True
                                }

                            if video_only:
                                if not is_vid: continue
                                vid_url = _get_video_url(p)
                                if not vid_url: continue
                                return {
                                    'id': pid, 'url': vid_url,
                                    'title': p.get('title', ''),
                                    'subreddit': p.get('subreddit', sub),
                                    'is_video': True, 'is_nsfw': bool(p.get('over_18')),
                                    'is_text': False
                                }

                            if is_vid or is_gallery or is_text: continue
                            low = url.lower()
                            if not any(low.endswith(e) for e in ['.jpg','.jpeg','.png','.gif','.webp']):
                                if 'i.redd.it' not in low and 'imgur.com' not in low:
                                    continue
                                if 'imgur.com' in url and '/a/' not in url and '/gallery/' not in url:
                                    url += '.jpg'

                            return {
                                'id': pid, 'url': url,
                                'title': p.get('title', ''),
                                'subreddit': p.get('subreddit', sub),
                                'is_video': False, 'is_nsfw': bool(p.get('over_18')),
                                'is_text': False
                            }
                    except Exception as e:
                        logger.debug(f"reddit oauth error [{sub}/{sort}]: {e}")
                        continue
    except Exception as e:
        logger.debug(f"reddit oauth session error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 4: IMGFLIP (Free image memes — no auth)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_imgflip(nsfw: bool = False) -> Optional[Dict]:
    """Fetch a random meme image from ImgFlip's public template API."""
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get('https://api.imgflip.com/get_memes') as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                memes = data.get('data', {}).get('memes', [])
                if not memes:
                    return None
                meme = random.choice(memes)
                return {
                    'id': f"imgflip_{meme['id']}",
                    'url': meme['url'],
                    'title': meme['name'],
                    'subreddit': 'imgflip',
                    'is_video': False,
                    'is_nsfw': False,
                    'is_text': False
                }
    except Exception as e:
        logger.debug(f"ImgFlip error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 5: 9GAG RSS (Public feed — no auth)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_9GAG_FEEDS = [
    'https://9gag.com/hot.rss',
    'https://9gag.com/trending.rss',
    'https://9gag.com/fresh.rss',
]

async def _fetch_via_9gag(nsfw: bool = False) -> Optional[Dict]:
    """Fetch a random meme from 9gag's public RSS feed (no API key needed)."""
    feed_url = random.choice(_9GAG_FEEDS)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; RSS reader)'}
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            async with session.get(feed_url) as resp:
                if resp.status != 200:
                    logger.debug(f"9gag RSS failed: {resp.status}")
                    return None
                text = await resp.text()

        root = ET.fromstring(text)
        ns = {'media': 'http://search.yahoo.com/mrss/'}
        items = root.findall('.//item')
        if not items:
            return None
        random.shuffle(items)

        for item in items:
            # Extract image from media:thumbnail or enclosure
            img_url = None
            thumb = item.find('media:thumbnail', ns)
            if thumb is not None:
                img_url = thumb.get('url')
            if not img_url:
                enc = item.find('enclosure')
                if enc is not None:
                    img_url = enc.get('url')
            if not img_url:
                # Try parsing description for img src
                desc = item.findtext('description', '')
                import re
                match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc)
                if match:
                    img_url = match.group(1)

            if not img_url:
                continue

            low = img_url.lower()
            is_vid = any(ext in low for ext in ['.mp4', '.webm', '.gifv'])
            title = item.findtext('title', '9gag meme')
            link = item.findtext('link', '')
            post_id = f"9gag_{link.split('/')[-1] if link else random.randint(1000,9999)}"

            return {
                'id': post_id,
                'url': img_url,
                'title': title,
                'subreddit': '9gag',
                'is_video': is_vid,
                'is_nsfw': False,
                'is_text': False
            }
    except ET.ParseError as e:
        logger.debug(f"9gag RSS parse error: {e}")
    except Exception as e:
        logger.debug(f"9gag RSS error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 6: GIPHY (GIF memes — needs GIPHY_API_KEY) 
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_giphy(nsfw: bool = False) -> Optional[Dict]:
    """Fetch a trending GIF from Giphy.
    API key comes from DB (set via .setgiphy) or GIPHY_API_KEY env var.
    """
    api_key = await db.get('giphy_api_key') or os.getenv('GIPHY_API_KEY', '')
    if not api_key:
        return None
    try:
        rating = 'r' if nsfw else 'g'
        params = f"api_key={api_key}&limit=25&rating={rating}&bundle=messaging_non_clips"
        url = f"https://api.giphy.com/v1/gifs/trending?{params}"
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.debug(f"Giphy failed: {resp.status}")
                    return None
                data = await resp.json()
                gifs = data.get('data', [])
                if not gifs:
                    return None
                gif = random.choice(gifs)
                # Prefer mp4 for smaller size, fallback to gif URL
                mp4 = gif.get('images', {}).get('original_mp4', {}).get('mp4')
                gif_url = mp4 or gif.get('images', {}).get('original', {}).get('url')
                if not gif_url:
                    return None
                is_vid = bool(mp4)
                return {
                    'id': f"giphy_{gif['id']}",
                    'url': gif_url,
                    'title': gif.get('title') or 'Giphy meme',
                    'subreddit': 'giphy',
                    'is_video': is_vid,
                    'is_nsfw': nsfw,
                    'is_text': False
                }
    except Exception as e:
        logger.debug(f"Giphy error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 7: REDDIT RSS (Free, no auth — different endpoint from JSON)
# Reddit's Atom/RSS feeds often bypass the IP blocks that hit .json
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_via_reddit_rss(
    subreddits: List[str], video_only: bool = False,
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Fetch from Reddit's public RSS/Atom feed — free, no API key.
    Uses /r/sub/hot.rss|new.rss|top.rss which is a different endpoint
    from the JSON API and much less likely to be IP-blocked.
    """
    subs = list(subreddits)
    random.shuffle(subs)
    sorts = ['hot', 'new', 'top']

    # Atom namespace
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'media': 'http://search.yahoo.com/mrss/'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; RSS reader)',
        'Accept': 'application/rss+xml, application/xml, text/xml'
    }

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for sub in subs[:6]:
                sort = random.choice(sorts)
                t_param = '&t=week' if sort == 'top' else ''
                url = f'https://www.reddit.com/r/{sub}/{sort}.rss?limit=25{t_param}'
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            logger.debug(f"Reddit RSS failed | /r/{sub}/{sort} | {resp.status}")
                            continue
                        text = await resp.text()

                    root = ET.fromstring(text)

                    # Reddit uses Atom format
                    entries = root.findall('atom:entry', ns)
                    if not entries:
                        # Try plain RSS <item> fallback
                        entries = root.findall('.//item')

                    if not entries:
                        continue
                    random.shuffle(entries)

                    for entry in entries:
                        # --- Atom entry parsing ---
                        entry_id = (entry.findtext('atom:id', '', ns) or
                                    entry.findtext('id', '') or
                                    entry.findtext('link', ''))
                        title = (entry.findtext('atom:title', '', ns) or
                                 entry.findtext('title', 'Meme'))

                        # Get content / summary to extract image URL
                        content = (entry.findtext('atom:content', '', ns) or
                                   entry.findtext('content', '') or
                                   entry.findtext('atom:summary', '', ns) or
                                   entry.findtext('description', ''))

                        # Check NSFW marker in title/content
                        is_nsfw_post = '[nsfw]' in title.lower() or 'nsfw' in content.lower()
                        if not nsfw and is_nsfw_post:
                            continue

                        # Skip if already seen
                        post_id = f'rss_{entry_id.split("/")[-1] or entry_id[-16:]}'
                        if await is_meme_seen(post_id):
                            continue

                        # Extract media: check thumbnail/enclosure in content
                        import re
                        # Look for img src in the HTML content
                        img_match = re.search(
                            r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE
                        )
                        img_url = img_match.group(1) if img_match else None

                        # Also check for direct link that looks like media
                        link_el = entry.find('atom:link', ns)
                        direct_link = ''
                        if link_el is not None:
                            direct_link = link_el.get('href', '')
                        if not direct_link:
                            direct_link = entry.findtext('link', '')

                        low_link = direct_link.lower()
                        is_vid = _is_video_post({}, direct_link)

                        if not img_url:
                            # Fall back to the post link itself if it's a media URL
                            if any(low_link.endswith(e) for e in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4']):
                                img_url = direct_link
                            elif 'i.redd.it' in low_link or 'i.imgur.com' in low_link:
                                img_url = direct_link

                        if allow_text and not img_url:
                            # Text post fallback
                            text_body = re.sub(r'<[^>]+>', '', content).strip()
                            if len(text_body) > 20:
                                return {
                                    'id': post_id, 'title': title,
                                    'subreddit': sub, 'text': text_body[:2000],
                                    'is_video': False, 'is_nsfw': is_nsfw_post, 'is_text': True
                                }
                            continue

                        if not img_url:
                            continue

                        is_vid = _is_video_post({}, img_url)
                        if video_only and not is_vid:
                            continue

                        return {
                            'id': post_id, 'url': img_url, 'title': title,
                            'subreddit': sub, 'is_video': is_vid,
                            'is_nsfw': is_nsfw_post, 'is_text': False
                        }

                except ET.ParseError as e:
                    logger.debug(f"Reddit RSS parse error [{sub}]: {e}")
                    continue
                except Exception as e:
                    logger.debug(f"Reddit RSS error [{sub}]: {e}")
                    continue
    except Exception as e:
        logger.debug(f"Reddit RSS session error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SOURCE 8: REDLIB / LibReddit PROXY (Free — own IPs, no auth needed)
# Public instances that proxy Reddit — completely bypass IP blocks
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Known public Redlib instances (shuffled each call for load distribution)
REDLIB_INSTANCES = [
    'https://redlib.kylrth.com',
    'https://redlib.catsarch.com',
    'https://rl.bloat.cat',
    'https://redlib.privacydev.net',
    'https://redlib.tux.pizza',
    'https://reddit.invak.id',
]


async def _fetch_via_redlib(
    subreddits: List[str], video_only: bool = False,
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Fetch via public Redlib/LibReddit proxy instances.
    Each instance has its own IP so Reddit's blocks don't apply.
    They serve the same JSON structure as Reddit's API.
    """
    subs = list(subreddits)
    random.shuffle(subs)
    instances = list(REDLIB_INSTANCES)
    random.shuffle(instances)
    sorts = ['hot', 'new', 'top']

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; AstraBot)',
        'Accept': 'application/json'
    }

    try:
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            for instance in instances[:3]:
                for sub in subs[:4]:
                    sort = random.choice(sorts)
                    t_param = '&t=week' if sort == 'top' else ''
                    url = f'{instance}/r/{sub}/{sort}.json?limit=50&raw_json=1{t_param}'
                    try:
                        async with session.get(url) as resp:
                            if resp.status != 200:
                                logger.debug(f"Redlib {instance} | /r/{sub}/{sort} | {resp.status}")
                                continue
                            data = await resp.json(content_type=None)

                        posts = data.get('data', {}).get('children', [])
                        if not posts:
                            continue
                        random.shuffle(posts)

                        for post in posts:
                            p = post.get('data', {})
                            if not p or p.get('stickied'):
                                continue
                            pid = p.get('name', '')
                            if not pid or await is_meme_seen(pid):
                                continue
                            if not nsfw and p.get('over_18'):
                                continue

                            url_post = p.get('url', '')
                            is_vid = _is_video_post(p, url_post)
                            is_text = p.get('is_self', False)
                            is_gallery = p.get('is_gallery') or 'reddit.com/gallery/' in url_post

                            if is_text:
                                if not allow_text:
                                    continue
                                text = p.get('selftext', '')
                                if len(text) < 20:
                                    continue
                                return {
                                    'id': pid, 'title': p.get('title', ''),
                                    'subreddit': p.get('subreddit', sub),
                                    'text': text, 'is_video': False,
                                    'is_nsfw': bool(p.get('over_18')), 'is_text': True
                                }

                            if video_only:
                                if not is_vid:
                                    continue
                                vid_url = _get_video_url(p)
                                if not vid_url:
                                    # For redlib, the fallback_url may be on the original domain
                                    vid_url = url_post if 'v.redd.it' in url_post else None
                                if not vid_url:
                                    continue
                                return {
                                    'id': pid, 'url': vid_url,
                                    'title': p.get('title', ''),
                                    'subreddit': p.get('subreddit', sub),
                                    'is_video': True, 'is_nsfw': bool(p.get('over_18')),
                                    'is_text': False
                                }

                            if is_vid or is_gallery or is_text:
                                continue
                            low = url_post.lower()
                            if not any(low.endswith(e) for e in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                if 'i.redd.it' not in low and 'imgur.com' not in low:
                                    continue
                                if 'imgur.com' in url_post and '/a/' not in url_post:
                                    url_post += '.jpg'

                            return {
                                'id': pid, 'url': url_post,
                                'title': p.get('title', ''),
                                'subreddit': p.get('subreddit', sub),
                                'is_video': False, 'is_nsfw': bool(p.get('over_18')),
                                'is_text': False
                            }
                    except Exception as e:
                        logger.debug(f"Redlib error [{instance}/{sub}]: {e}")
                        continue
    except Exception as e:
        logger.debug(f"Redlib session error: {e}")
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIFIED FETCHER (tries sources in order)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_meme(
    subreddits: List[str], video_only: bool = False,
    nsfw: bool = False, allow_text: bool = False
) -> Optional[Dict]:
    """Multi-source meme fetcher — 8 independent sources.
    Order: meme-api → reddit-rss → redlib-proxy → reddit-oauth → reddit-direct → imgflip → 9gag → giphy
    For videos: reddit-search → meme-api → reddit-rss → redlib → reddit-oauth → reddit-direct.
    """
    await cleanup_old_seen(24)

    # ── Video: specialized URL search first ──
    if video_only and not allow_text:
        result = await _fetch_via_reddit_search(subreddits, nsfw=nsfw)
        if result: return result

    # ── 1: meme-api.com (fast, proxies Reddit server-side) ──
    if not allow_text:
        result = await _fetch_via_meme_api(subreddits, nsfw=nsfw, video_only=video_only)
        if result: return result

    # ── 2: Reddit RSS Atom feeds (free, no auth, often not IP-blocked) ──
    result = await _fetch_via_reddit_rss(subreddits, video_only=video_only, nsfw=nsfw, allow_text=allow_text)
    if result: return result

    # ── 3: Redlib/LibReddit public proxies (own IPs, no auth, very reliable) ──
    result = await _fetch_via_redlib(subreddits, video_only=video_only, nsfw=nsfw, allow_text=allow_text)
    if result: return result

    # ── 4: Reddit OAuth2 (authenticated token, bypasses IP blocks) ──
    result = await _fetch_via_reddit_oauth(subreddits, video_only=video_only, nsfw=nsfw, allow_text=allow_text)
    if result: return result

    # ── 5: Direct Reddit JSON (last Reddit resort, may 403 on VPS) ──
    result = await _fetch_via_reddit(subreddits, video_only=video_only, nsfw=nsfw, allow_text=allow_text)
    if result: return result

    # ── Global-sub fallbacks ──
    if not allow_text:
        if video_only:
            result = await _fetch_via_reddit_search(GLOBAL_VIDEO_MEMES, nsfw=nsfw)
            if result: return result
            result = await _fetch_via_reddit_rss(GLOBAL_VIDEO_MEMES, video_only=True, nsfw=nsfw)
            if result: return result
            result = await _fetch_via_redlib(GLOBAL_VIDEO_MEMES, video_only=True, nsfw=nsfw)
            if result: return result
            result = await _fetch_via_reddit_oauth(GLOBAL_VIDEO_MEMES, video_only=True, nsfw=nsfw)
            if result: return result

        fallback_subs = ALL_VIDEO_MEMES if video_only else ALL_MEMES
        result = await _fetch_via_meme_api(fallback_subs, nsfw=nsfw, video_only=video_only)
        if result: return result

        # ── 6: ImgFlip (images — always reachable) ──
        if not video_only:
            result = await _fetch_via_imgflip(nsfw=nsfw)
            if result: return result

        # ── 7: 9gag RSS ──
        result = await _fetch_via_9gag(nsfw=nsfw)
        if result:
            if not video_only or result.get('is_video'):
                return result

        # ── 8: Giphy (if key configured) ──
        result = await _fetch_via_giphy(nsfw=nsfw)
        if result:
            if not video_only or result.get('is_video'):
                return result

    logger.warning(f"All 8 sources exhausted. video={video_only} nsfw={nsfw} text={allow_text}")
    return None

# ── Media Sender ────────────────────────────

import asyncio
import json
import tempfile
import os as _os

# Path to the reddit.js downloader (same dir hierarchy as js_downloader.js)
_REDDIT_JS = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'utils', 'reddit.js')


async def _download_video_via_js(url: str) -> Optional[bytes]:
    """Download a Reddit video using utils/reddit.js (mirrors js_downloader.js pattern).
    Returns raw bytes of the MP4, or None on failure.
    """
    if not _os.path.exists(_REDDIT_JS):
        logger.debug("reddit.js not found, skipping JS downloader")
        return None

    try:
        proc = await asyncio.create_subprocess_exec(
            'node', _REDDIT_JS, url, 'video',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        logger.warning(f"reddit.js timed out for {url}")
        return None
    except FileNotFoundError:
        logger.debug("node not found, skipping JS downloader")
        return None
    except Exception as e:
        logger.warning(f"reddit.js subprocess error: {e}")
        return None

    output = stdout.decode('utf-8', errors='replace')
    file_paths = []
    for line in output.splitlines():
        if line.startswith('SUCCESS:'):
            try:
                data = json.loads(line[len('SUCCESS:'):])
                file_paths = data.get('files', [])
            except Exception:
                pass
            break

    if not file_paths:
        logger.warning(f"reddit.js: no SUCCESS line. stderr: {stderr.decode()[:200]}")
        return None

    mp4_path = file_paths[0]
    try:
        if _os.path.exists(mp4_path):
            with open(mp4_path, 'rb') as f:
                data = f.read()
            _os.unlink(mp4_path)
            return data
    except Exception as e:
        logger.warning(f"reddit.js file read error: {e}")
    return None


async def _download_video_ytdlp_fallback(url: str) -> Optional[bytes]:
    """Fallback: Python yt-dlp in thread executor if Node.js is unavailable."""
    import yt_dlp
    tmp = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        ydl_opts = {
            'outtmpl': tmp_path,
            'quiet': True,
            'no_warnings': True,
            'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'socket_timeout': 20,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.reddit.com/',
            },
        }
        loop = asyncio.get_event_loop()
        def _dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        await loop.run_in_executor(None, _dl)
        final = tmp_path if _os.path.exists(tmp_path) else tmp_path + '.mp4'
        if _os.path.exists(final):
            with open(final, 'rb') as f:
                return f.read()
    except Exception as e:
        logger.warning(f"yt-dlp fallback failed for {url}: {e}")
    finally:
        for p in [tmp_path, tmp_path + '.mp4']:
            try:
                if _os.path.exists(p): _os.unlink(p)
            except Exception: pass
    return None


async def _download_video_ytdlp(url: str) -> Optional[bytes]:
    """Primary: use reddit.js (Node.js + yt-dlp with geo-bypass, H.264 forced).
    Fallback: pure Python yt-dlp if Node.js unavailable.
    """
    result = await _download_video_via_js(url)
    if result:
        return result
    logger.debug(f"JS downloader failed, trying Python yt-dlp for {url}")
    return await _download_video_ytdlp_fallback(url)


async def send_meme_media(client, chat_id, meme_data, reply_to):
    """Downloads and sends the meme media to chat.
    - Videos (v.redd.it, YouTube shorts, etc.): uses yt-dlp for proper audio+video merge.
    - Images/GIFs: plain aiohttp download.
    """
    if meme_data.get('is_text'):
        caption = f"📖 *{meme_data['title']}*\n\n{meme_data['text']}\n\n📍 *Sub:* r/{meme_data['subreddit']}"
        if meme_data.get('is_nsfw'): caption = "🔞 " + caption
        if len(caption) > 4000: caption = caption[:3997] + "..."
        await client.send_message(chat_id, caption, reply_to=reply_to)
        return True

    url = meme_data.get('url', '')
    is_vid = meme_data.get('is_video', False)
    subreddit = meme_data.get('subreddit', 'meme')

    caption = f"🔥 *{meme_data['title']}*\n\n📍 *Sub:* r/{subreddit}"
    if meme_data.get('is_nsfw'): caption = "🔞 " + caption

    # ── Video path: use yt-dlp for proper audio+video merge ──
    if is_vid:
        vid_data = await _download_video_ytdlp(url)
        if vid_data:
            b64 = base64.b64encode(vid_data).decode('utf-8')
            media = {
                "mimetype": "video/mp4",
                "data": b64,
                "filename": f"meme_{subreddit}.mp4"
            }
            await client.send_media(chat_id, media, caption=caption, reply_to=reply_to)
            return True
        logger.warning(f"yt-dlp failed, falling back to direct HTTP for {url}")

    # ── Image path (or video yt-dlp fallback) ──
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Media download HTTP {resp.status}: {url}")
                    return False
                raw = await resp.read()
                content_type = resp.headers.get('Content-Type', 'image/jpeg')
    except Exception as e:
        logger.warning(f"Media download error: {e}")
        return False

    b64_data = base64.b64encode(raw).decode('utf-8')
    ext_map = {
        'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif',
        'image/webp': 'webp', 'video/mp4': 'mp4'
    }
    ext = ext_map.get(content_type.split(';')[0].strip(), 'jpg')
    media = {
        "mimetype": content_type,
        "data": b64_data,
        "filename": f"meme_{subreddit}.{ext}"
    }
    await client.send_media(chat_id, media, caption=caption, reply_to=reply_to)
    return True

# ── Generic Handler (DRY) ──────────────────

async def _meme_handler(client, message, subs, label, fallback_subs=None, **kwargs):
    """Generic meme command handler."""
    status_msg = await smart_reply(message, f"*{label}*")
    
    try:
        meme = await fetch_meme(subs, **kwargs)
        
        if not meme and fallback_subs:
            meme = await fetch_meme(fallback_subs, **kwargs)
        
        if meme:
            ok = await send_meme_media(client, message.chat_id, meme, message.id)
            if ok:
                await mark_meme_seen(meme['id'], meme['subreddit'])
                await status_msg.delete()
            else:
                await safe_edit(status_msg, f"❌ Media download failed.\n📎 URL: `{meme.get('url', '?')[:80]}`")
        else:
            subs_tried = ', '.join(subs[:3])
            mode = []
            if kwargs.get('video_only'): mode.append('video')
            if kwargs.get('nsfw'): mode.append('nsfw')
            if kwargs.get('allow_text'): mode.append('text')
            mode_str = '+'.join(mode) if mode else 'image'
            await safe_edit(status_msg, f"❌ No fresh content found.\n🔍 Subs: `{subs_tried}`\n📂 Mode: `{mode_str}`\n💡 Use `.memedebug` to check if your server's IP is blocked by Reddit.")
    except Exception as e:
        logger.error(f"_meme_handler error: {e}")
        await safe_edit(status_msg, f"❌ Meme Error: `{str(e)[:100]}`")

# ── Command Handlers ───────────────────────

@astra_command(name="imeme", description="Get a spicy Indian meme", category="Fun & Memes", usage=".imeme")
async def imeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳 Fetching Indian meme...")

@astra_command(name="idmdmes", description="Get a NSFW/Edgy Indian meme", category="Fun & Memes", usage=".idmdmes")
async def idmdmes_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞 Fetching edgy Indian meme...", fallback_subs=INDIAN_MEMES, nsfw=True)

@astra_command(name="meme", description="Get a random global meme", category="Fun & Memes", usage=".meme")
async def meme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_MEMES, "🌍 Fetching global meme...")

@astra_command(name="dmeme", description="Get a NSFW/Dark global meme", category="Fun & Memes", usage=".dmeme")
async def dmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_NSFW_MEMES, "🔞 Fetching dark meme...", fallback_subs=ALL_MEMES, nsfw=True)

@astra_command(name="vmemes", description="Get a random video meme", category="Fun & Memes", usage=".vmemes")
async def vmemes_handler(client: Client, message: Message):
    await _meme_handler(client, message, ALL_VIDEO_MEMES, "🎥 Fetching video meme...", video_only=True)

@astra_command(name="vdmemes", description="Get a NSFW video meme", category="Fun & Memes", usage=".vdmemes [subreddit]")
async def vdmemes_handler(client: Client, message: Message):
    args = extract_args(message)
    target_sub = args[0] if args else None
    subs = [target_sub] if target_sub else ALL_NSFW_MEMES
    label = f"🔞🎥 Fetching dark video{' from r/' + target_sub if target_sub else ''}..."
    await _meme_handler(client, message, subs, label, fallback_subs=ALL_MEMES, video_only=True, nsfw=True)

@astra_command(name="idm", description="Get a meme from r/IndianDankMemes", category="Fun & Memes", usage=".idm [-v]")
async def idm_handler(client: Client, message: Message):
    args = extract_args(message)
    video_only = "-v" in args
    label = f"🇮🇳 {'🎥 ' if video_only else ''}Fetching IDM meme..."
    await _meme_handler(client, message, ['IndianDankMemes'], label, fallback_subs=ALL_VIDEO_MEMES, video_only=video_only)

@astra_command(name="phakh", description="Get a story from r/PataHaiAajKyaHua", aliases=["story"], category="Fun & Memes", usage=".phakh")
async def phakh_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['PataHaiAajKyaHua'], "📖 Fetching story...", allow_text=True)

@astra_command(name="ivdmeme", description="Get an Indian NSFW video", category="Fun & Memes", usage=".ivdmeme")
async def ivdmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_NSFW_MEMES, "🔞🇮🇳🎥 Fetching Indian dark video...", fallback_subs=ALL_VIDEO_MEMES, video_only=True, nsfw=True)

@astra_command(name="idmvd", description="Get a NSFW video from r/IndianDankMemes", category="Fun & Memes", usage=".idmvd")
async def idmvd_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🔞🇮🇳🎥 Fetching IDM dark video...", video_only=True, nsfw=True)

@astra_command(name="ivmeme", description="Get an Indian safe video meme", category="Fun & Memes", usage=".ivmeme")
async def ivmeme_handler(client: Client, message: Message):
    await _meme_handler(client, message, INDIAN_MEMES, "🇮🇳🎥 Fetching Indian video meme...", fallback_subs=ALL_VIDEO_MEMES, video_only=True)

@astra_command(name="idmv", description="Get a safe video from r/IndianDankMemes", category="Fun & Memes", usage=".idmv")
async def idmv_handler(client: Client, message: Message):
    await _meme_handler(client, message, ['IndianDankMemes'], "🇮🇳🎥 Fetching IDM video...", fallback_subs=ALL_VIDEO_MEMES, video_only=True)

@astra_command(name="memedebug", description="Diagnose meme fetching issues", category="System", usage=".memedebug")
async def memedebug_handler(client: Client, message: Message):
    """Diagnose all meme sources and show actionable status."""
    status_msg = await smart_reply(message, "🔍 *Running Meme Diagnostics...*")
    report = "🛠️ *Astra Meme Diagnostics*\n━━━━━━━━━━━━━━━━━━━━━━\n"

    async with aiohttp.ClientSession(headers=get_reddit_headers(), timeout=REQUEST_TIMEOUT) as session:
        # 1. MemeAPI (primary)
        try:
            async with session.get('https://meme-api.com/gimme/1') as resp:
                icon = '✅' if resp.status == 200 else '⚠️'
                report += f"{icon} *MemeAPI:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *MemeAPI:* `{str(e)[:40]}`\n"

        # 2. Direct Reddit
        try:
            async with session.get('https://www.reddit.com/r/memes/hot.json?limit=1') as resp:
                icon = '✅' if resp.status == 200 else ('🚫' if resp.status == 403 else '⚠️')
                report += f"{icon} *Reddit Direct:* `{resp.status}`"
                if resp.status == 403:
                    report += " _(IP blocked — use OAuth)_"
                report += "\n"
        except Exception as e:
            report += f"❌ *Reddit Direct:* `{str(e)[:40]}`\n"

        # 3. Reddit OAuth2
        token = await _get_reddit_oauth_token()
        if token:
            try:
                oauth_headers = {'Authorization': f'bearer {token}', 'User-Agent': REDDIT_UA}
                async with session.get(
                    'https://oauth.reddit.com/r/memes/hot.json?limit=1',
                    headers=oauth_headers
                ) as resp:
                    icon = '✅' if resp.status == 200 else '⚠️'
                    report += f"{icon} *Reddit OAuth2:* `{resp.status}`\n"
            except Exception as e:
                report += f"❌ *Reddit OAuth2:* `{str(e)[:40]}`\n"
        else:
            report += "⬜ *Reddit OAuth2:* Not configured\n"
            report += "   _Set `REDDIT_CLIENT_ID` + `REDDIT_CLIENT_SECRET` env vars_\n"

        # 4. Reddit RSS (free, no auth)
        try:
            async with session.get(
                'https://www.reddit.com/r/memes/hot.rss?limit=1',
                headers={'Accept': 'application/xml'}
            ) as resp:
                icon = '✅' if resp.status == 200 else ('🚫' if resp.status == 403 else '⚠️')
                report += f"{icon} *Reddit RSS:* `{resp.status}`"
                if resp.status == 403: report += " _(blocked)_"
                report += "\n"
        except Exception as e:
            report += f"❌ *Reddit RSS:* `{str(e)[:40]}`\n"

        # 5. Redlib proxy (picks a random instance)
        inst = random.choice(REDLIB_INSTANCES)
        try:
            async with session.get(f'{inst}/r/memes/hot.json?limit=1') as resp:
                icon = '✅' if resp.status == 200 else '⚠️'
                report += f"{icon} *Redlib ({inst.split('//')[-1]}):* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *Redlib:* `{str(e)[:40]}`\n"

        # 6. ImgFlip
        try:
            async with session.get('https://api.imgflip.com/get_memes') as resp:
                icon = '✅' if resp.status == 200 else '⚠️'
                report += f"{icon} *ImgFlip:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *ImgFlip:* `{str(e)[:40]}`\n"

        # 7. 9gag RSS
        try:
            async with session.get('https://9gag.com/hot.rss',
                headers={'User-Agent': 'Mozilla/5.0 (compatible; RSS reader)'}) as resp:
                icon = '✅' if resp.status == 200 else '⚠️'
                report += f"{icon} *9gag RSS:* `{resp.status}`\n"
        except Exception as e:
            report += f"❌ *9gag RSS:* `{str(e)[:40]}`\n"

        # 8. Giphy
        giphy_key = await db.get('giphy_api_key') or os.getenv('GIPHY_API_KEY', '')
        if giphy_key:
            try:
                async with session.get(f'https://api.giphy.com/v1/gifs/trending?api_key={giphy_key}&limit=1') as resp:
                    icon = '✅' if resp.status == 200 else '⚠️'
                    report += f"{icon} *Giphy:* `{resp.status}`\n"
            except Exception as e:
                report += f"❌ *Giphy:* `{str(e)[:40]}`\n"
        else:
            report += "⬜ *Giphy:* Not configured _(use `.setgiphy <key>`)_\n"

    # Check Reddit creds for summary
    r_cid, _ = await _get_reddit_creds()
    giphy_ok = bool(await db.get('giphy_api_key') or os.getenv('GIPHY_API_KEY', ''))

    report += "\n━━━━━━━━━━━━━━━━━━━━━━\n"
    report += "💡 *Priority:* MemeAPI → RSS → Redlib → OAuth2 → Direct → ImgFlip → 9gag → Giphy\n"
    tips = []
    if not r_cid:
        tips.append("🔑 Reddit OAuth: `.setreddit <client_id> <secret>`")
        tips.append("   Get free creds: reddit.com/prefs/apps *(script type)*")
    if not giphy_ok:
        tips.append("🎞️ Giphy GIFs: `.setgiphy <api_key>`")
        tips.append("   Get free key: developers.giphy.com")
    if tips:
        report += "\n🔧 *To enable more sources:*\n" + "\n".join(tips)
    await safe_edit(status_msg, report)


# ── Config Commands ─────────────────────────

@astra_command(
    name="setreddit",
    description="Set Reddit OAuth2 credentials for meme fetching",
    category="Config",
    usage=".setreddit <client_id> <client_secret>",
    owner_only=True
)
async def setreddit_handler(client: Client, message: Message):
    """Store Reddit API credentials in DB (enables OAuth2 meme fetching)."""
    args = extract_args(message)
    if len(args) < 2:
        # Show current status
        cid, csec = await _get_reddit_creds()
        src = 'DB' if await db.get('reddit_client_id') else ('env' if cid else 'not set')
        return await smart_reply(
            message,
            f"🔑 *Reddit OAuth2 Config*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Status:* {'✅ Configured' if cid else '❌ Not set'} _({src})_\n"
            f"*Client ID:* `{'*' * 8 + cid[-4:] if cid else 'none'}`\n\n"
            f"💡 *Usage:* `.setreddit <client_id> <client_secret>`\n"
            f"Get free creds → reddit.com/prefs/apps *(script type)*"
        )

    cid, csec = args[0], args[1]

    # Validate by attempting token fetch
    status_msg = await smart_reply(message, "🔄 *Validating credentials...*")
    try:
        auth = aiohttp.BasicAuth(cid, csec)
        headers = {'User-Agent': REDDIT_UA}
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            async with session.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth, data={'grant_type': 'client_credentials'}
            ) as resp:
                if resp.status != 200:
                    return await safe_edit(
                        status_msg,
                        f"❌ *Invalid credentials* (HTTP {resp.status})\n"
                        f"Double-check your Client ID and Secret on reddit.com/prefs/apps"
                    )
                d = await resp.json()
                if not d.get('access_token'):
                    return await safe_edit(status_msg, "❌ *Token response invalid.* Check your credentials.")
    except Exception as e:
        return await safe_edit(status_msg, f"❌ *Validation failed:* `{str(e)[:80]}`")

    # Save to DB
    await db.set('reddit_client_id', cid)
    await db.set('reddit_client_secret', csec)
    # Clear token cache so next fetch uses new creds
    global _oauth_token_cache
    _oauth_token_cache = {'token': None, 'expires_at': 0}

    await safe_edit(
        status_msg,
        f"✅ *Reddit OAuth2 credentials saved!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Client ID:* `{'*' * 8 + cid[-4:]}`\n"
        f"*Storage:* DB (SQLite + MongoDB sync)\n"
        f"*Status:* Token validated ✅\n\n"
        f"💡 Run `.memedebug` to confirm Reddit OAuth2 is working."
    )


@astra_command(
    name="setgiphy",
    description="Set Giphy API key for GIF meme fetching",
    category="Config",
    usage=".setgiphy <api_key>",
    owner_only=True
)
async def setgiphy_handler(client: Client, message: Message):
    """Store Giphy API key in DB (enables GIF memes from Giphy)."""
    args = extract_args(message)
    if not args:
        key = await db.get('giphy_api_key') or os.getenv('GIPHY_API_KEY', '')
        src = 'DB' if await db.get('giphy_api_key') else ('env' if os.getenv('GIPHY_API_KEY') else 'not set')
        return await smart_reply(
            message,
            f"🎞️ *Giphy Config*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Status:* {'✅ Configured' if key else '❌ Not set'} _({src})_\n\n"
            f"💡 *Usage:* `.setgiphy <api_key>`\n"
            f"Get free key → developers.giphy.com"
        )

    api_key = args[0]

    # Validate key
    status_msg = await smart_reply(message, "🔄 *Validating Giphy key...*")
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(
                f'https://api.giphy.com/v1/gifs/trending?api_key={api_key}&limit=1'
            ) as resp:
                if resp.status != 200:
                    return await safe_edit(
                        status_msg,
                        f"❌ *Invalid Giphy key* (HTTP {resp.status})\n"
                        f"Get a free key at developers.giphy.com"
                    )
    except Exception as e:
        return await safe_edit(status_msg, f"❌ *Validation failed:* `{str(e)[:80]}`")

    await db.set('giphy_api_key', api_key)
    await safe_edit(
        status_msg,
        f"✅ *Giphy API key saved!*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"*Key:* `{'*' * 8 + api_key[-4:]}`\n"
        f"*Storage:* DB (SQLite + MongoDB sync)\n\n"
        f"💡 Giphy GIFs are now active in meme commands."
    )
