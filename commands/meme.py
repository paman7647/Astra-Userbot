import base64
import io
import json
import logging
import os
import random
import textwrap
import time
from typing import Dict, List, Optional, Tuple

import aiohttp
from PIL import Image, ImageDraw, ImageFont
from utils.bridge_downloader import bridge_downloader
from utils.database import db
from utils.helpers import safe_edit

from . import *

logger = logging.getLogger("Astra.Meme")

# ── Configuration & Constants ────────────────
LOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "utils", "logos")
os.makedirs(LOGOS_DIR, exist_ok=True)

REDDIT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AstraUserbot/1.0"
REQUEST_TIMEOUT = 10
REDLIB_INSTANCES = [
    "https://redlib.ducks.party",
    "https://reddit.invidious.io",
    "https://safereddit.com",
    "https://rx.proxy.com",
]

# Cache for Reddit OAuth2 tokens
_oauth_token_cache = {"token": None, "expires_at": 0}


async def _get_reddit_creds() -> Tuple[Optional[str], Optional[str]]:
    """Fetch credentials from DB or Environment."""
    cid = await db.get("reddit_client_id") or os.getenv("REDDIT_CLIENT_ID")
    csec = await db.get("reddit_client_secret") or os.getenv("REDDIT_CLIENT_SECRET")
    return cid, csec


async def _get_reddit_token(cid: str, csec: str) -> Optional[str]:
    """Get or refresh Reddit OAuth2 token."""
    global _oauth_token_cache
    now = time.time()

    if _oauth_token_cache["token"] and now < _oauth_token_cache["expires_at"]:
        return _oauth_token_cache["token"]

    try:
        auth = aiohttp.BasicAuth(cid, csec)
        headers = {"User-Agent": REDDIT_UA}
        async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
            async with session.post(
                "https://www.reddit.com/api/v1/access_token", auth=auth, data={"grant_type": "client_credentials"}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    _oauth_token_cache["token"] = data["access_token"]
                    _oauth_token_cache["expires_at"] = now + data["expires_in"] - 60
                    return _oauth_token_cache["token"]
    except Exception as e:
        logger.error(f"Reddit Auth Failed: {e}")
    return None


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
    # Check for image: direct or quoted
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

    # Download image
    media_data = await bridge_downloader.download_media(client, message)
    if not media_data:
        return await status_msg.edit("❌ Failed to download image.")

    # Process with PIL
    img = Image.open(io.BytesIO(media_data)).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Load font (Astra standard path)
    font_path = os.path.join(LOGOS_DIR, "font1.ttf")
    if not os.path.exists(font_path):
         font_path = None # Fallback to default if font missing
    
    def get_font(text_line, max_w, max_h):
        size = int(height / 10)
        try:
            font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
            while font_path and font.getlength(text_line) > max_w and size > 12:
                size -= 2
                font = ImageFont.truetype(font_path, size)
            return font
        except: return ImageFont.load_default()

    def draw_text(text_val, pos_type):
        if not text_val: return
        wrapped = textwrap.wrap(text_val, width=20)
        y_curr = 20 if pos_type == "top" else (height - (len(wrapped) * (height/10)) - 20)
        
        for line in wrapped:
            fnt = get_font(line, width * 0.9, height / 10)
            bbox = draw.textbbox((0, 0), line, font=fnt)
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (width - w) / 2
            
            # Outline
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


# ── Meme Fetcher (API/Reddit) ────────────────

@astra_command(
    name="meme",
    description="Fetch a random meme from Reddit/APIs.",
    category="Fun & Games",
    aliases=["m"],
    is_public=True,
)
async def meme_fetcher_handler(client: Client, message: Message):
    """Fetch high-quality memes (images only, no videos)."""
    status_msg = await smart_reply(message, "🚀 *Hunting for fresh memes...*")
    
    # Priority order: MemeAPI -> RSS -> Redlib -> OAuth2 -> Direct -> ImgFlip -> 9gag -> Giphy
    
    # 1. Try Meme-API (Reddit aggregator)
    try:
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get("https://meme-api.com/gimme") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Filter: skip if it's a video
                    if not data.get("url", "").lower().endswith((".mp4", ".gifv", ".m4v")):
                        return await _send_meme_from_url(client, message, status_msg, data["url"], data.get("title"))
    except: pass

    # 2. Try Reddit RSS (free, no auth)
    subreddits = ["memes", "dankmemes", "wholesomememes", "IndianDankMemes", "pata_h_aaj_kya_hua"]
    try:
        sub = random.choice(subreddits)
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=10") as resp:
                if resp.status == 200:
                    posts = (await resp.json())["data"]["children"]
                    images = [p["data"] for p in posts if p["data"].get("url", "").lower().endswith((".jpg", ".png", ".jpeg"))]
                    if images:
                        p = random.choice(images)
                        return await _send_meme_from_url(client, message, status_msg, p["url"], p.get("title"))
    except: pass

    # 3. Try Reddit OAuth2 (if configured)
    cid, csec = await _get_reddit_creds()
    if cid and csec:
        token = await _get_reddit_token(cid, csec)
        if token:
            try:
                headers = {"Authorization": f"Bearer {token}", "User-Agent": REDDIT_UA}
                async with aiohttp.ClientSession(headers=headers, timeout=REQUEST_TIMEOUT) as session:
                    async with session.get("https://oauth.reddit.com/r/memes/hot?limit=25") as resp:
                        if resp.status == 200:
                            posts = (await resp.json())["data"]["children"]
                            images = [p["data"] for p in posts if not p["data"].get("is_video") and p["data"].get("url", "").lower().endswith((".jpg", ".png", ".jpeg"))]
                            if images:
                                p = random.choice(images)
                                return await _send_meme_from_url(client, message, status_msg, p["url"], p.get("title"))
            except: pass

    # 4. Fallback: Redlib (No Auth)
    try:
        inst = random.choice(REDLIB_INSTANCES)
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            async with session.get(f"{inst}/r/memes/hot.json?limit=10") as resp:
                if resp.status == 200:
                    posts = (await resp.json())["data"]["children"]
                    images = [p["data"] for p in posts if p["data"].get("url", "").lower().endswith((".jpg", ".png"))]
                    if images:
                        p = random.choice(images)
                        return await _send_meme_from_url(client, message, status_msg, p["url"])
    except: pass

    await status_msg.edit("❌ **Meme supply dry!** All sources failed or returned videos.")


async def _send_meme_from_url(client, message, status_msg, url, title=None):
    """Helper to download and send meme."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    b64 = base64.b64encode(data).decode()
                    mtype = "image/jpeg" if url.lower().endswith((".jpg", ".jpeg")) else "image/png"
                    cap = f"🤡 **{title}**" if title else "🤡 **Fresh Meme!**"
                    await client.send_media(str(message.chat_id), {"mimetype": mtype, "data": b64}, caption=cap)
                    return await status_msg.delete()
    except: pass
    await status_msg.edit("❌ Failed to download the meme image.")


# ── Config & Debug Commands ─────────────────────────

@astra_command(name="setreddit", category="Config", owner_only=True)
async def setreddit_handler(client: Client, message: Message):
    """Config Reddit OAuth."""
    args = extract_args(message)
    if len(args) < 2:
        cid, _ = await _get_reddit_creds()
        return await smart_reply(message, f"🔑 **Reddit OAuth Config**\nStatus: {'✅ set' if cid else '❌ unset'}\nUsage: `.setreddit <id> <secret>`")
    await db.set("reddit_client_id", args[0])
    await db.set("reddit_client_secret", args[1])
    # Clear cache
    global _oauth_token_cache
    _oauth_token_cache = {"token": None, "expires_at": 0}
    await smart_reply(message, "✅ Reddit UI/Secret saved. Memes will now use OAuth2.")

@astra_command(name="setgiphy", category="Config", owner_only=True)
async def setgiphy_handler(client: Client, message: Message) -> None:
    """Store Giphy API key in DB."""
    args = extract_args(message)
    if not args:
        return await smart_reply(message, "🎞️ Usage: `.setgiphy <api_key>`")
    await db.set("giphy_api_key", args[0])
    await smart_reply(message, "✅ Giphy API key saved.")

@astra_command(name="memedebug", category="Fun & Games", owner_only=True)
async def memedebug_handler(client: Client, message: Message):
    """Check meme system connectivity."""
    status_msg = await smart_reply(message, "🕵️ *Probing meme sources...*")
    report = "🕵️ **Meme System Debug**\n━━━━━━━━━━━━━━━━━━━━\n"
    
    async with aiohttp.ClientSession() as s:
        # MemeAPI
        try:
            async with s.get("https://meme-api.com/gimme") as r:
                report += f"{'✅' if r.status == 200 else '❌'} *MemeAPI:* `{r.status}`\n"
        except Exception as e: report += f"❌ *MemeAPI:* `{str(e)[:40]}`\n"
        
        # Reddit RSS
        try:
            async with s.get("https://www.reddit.com/r/memes/hot.json?limit=1") as r:
                report += f"{'✅' if r.status == 200 else '❌'} *Reddit JSON:* `{r.status}`\n"
        except Exception as e: report += f"❌ *Reddit:* `{str(e)[:40]}`\n"

        # Redlib
        inst = random.choice(REDLIB_INSTANCES)
        try:
            async with s.get(f"{inst}/r/memes/hot.json?limit=1") as r:
                report += f"{'✅' if r.status == 200 else '❌'} *Redlib ({inst.split('//')[-1]}):* `{r.status}`\n"
        except Exception as e: report += f"❌ *Redlib:* `{str(e)[:40]}`\n"

    cid, _ = await _get_reddit_creds()
    report += f"\n🔑 *Reddit Auth:* {'✅ Configured' if cid else '❌ Missing'}"
    await safe_edit(status_msg, report)
