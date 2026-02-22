# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import random
import aiohttp
import base64
import time
from . import *
from utils.helpers import safe_edit

# Shared configuration for requests
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'application/json'
}

@astra_command(
    name="meme",
    description="Get a random meme from Reddit",
    category="Fun",
    aliases=[],
    usage=".meme (no arguments)",
    owner_only=False
)
async def meme_handler(client: Client, message: Message):
    """Get a random meme from Reddit"""
    try:
        import asyncio
        _ = extract_args(message)
        status_msg = await smart_reply(message, " 🇮🇳 *Fetching a spicy meme...*")
        
        subreddits = [
            'IndianDankMemes', 'indiameme', 'indiamemer', 'DesiMeme', 
            'bakchodi', 'bollywoodmemes', 'IndianMeyMeys', 'SaimanSays',
            'dankmemes', 'memes', 'wholesomememes', 'ProgrammerHumor', 'techhumor'
        ]
        
        found_meme = False
        last_error = None

        async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
            for attempt in range(1, 4):
                random_sub = random.choice(subreddits)
                # Use meme-api for proxying
                async with session.get(f"https://meme-api.com/gimme/{random_sub}") as resp:
                    if resp.status != 200:
                        last_error = f"MemeAPI Error {resp.status}"
                        continue

                    data = await resp.json()
                    if data.get('nsfw'): continue

                    url, title, subreddit = data.get('url'), data.get('title'), data.get('subreddit')
                    if not url: continue

                    async with session.get(url) as img_resp:
                        if img_resp.status != 200: continue
                        img_data = await img_resp.read()
                        
                    b64_data = base64.b64encode(img_data).decode('utf-8')
                    media = {
                        "mimetype": img_resp.headers.get('Content-Type', 'image/jpeg'),
                        "data": b64_data,
                        "filename": f"meme_{subreddit}.jpg"
                    }

                    await client.send_media(
                        message.chat_id, 
                        media, 
                        caption=f"*{title}*\nSubreddit: r/{subreddit}",
                        reply_to=message.id
                    )
                    found_meme = True
                    if status_msg: await status_msg.delete()
                    break

            if not found_meme:
                await safe_edit(status_msg, f" ❌ Failed to fetch meme: {last_error or 'Unknown issue'}")

    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command meme failed')

@astra_command(
    name="dmeme",
    description="Get a random NSFW/Dark meme from Reddit",
    category="Fun",
    aliases=["nsfwmeme", "darkmeme"],
    usage=".dmeme (no arguments)",
    owner_only=False
)
async def dmeme_handler(client: Client, message: Message):
    """Get a random NSFW/Dark meme from Reddit"""
    try:
        import asyncio
        _ = extract_args(message)
        status_msg = await smart_reply(message, " 🔞 *Fetching a spicy NSFW meme...*")
        
        # Subreddits that are generally active and not 403-heavy
        subreddits = [
            'nsfw_memes', 'HolUp', 'dark_memes', 'hentaimemes', 
            'animememes', 'GoodAnimemes', 'cursedimages', 'SaimanSays'
        ]
        found_meme = False
        last_error = None

        async with aiohttp.ClientSession(headers=REQUEST_HEADERS) as session:
            # Try specific subreddits first
            for attempt in range(1, 6):
                random_sub = random.choice(subreddits)
                api_url = f"https://meme-api.com/gimme/{random_sub}"
                
                async with session.get(api_url) as resp:
                    if resp.status == 403:
                        last_error = "Access Restricted (403)"
                        continue
                    if resp.status != 200:
                        last_error = f"API Service Error {resp.status}"
                        continue
                        
                    data = await resp.json()
                    image_url = data.get('url')
                    title = data.get('title')
                    subreddit = data.get('subreddit')
                    
                    if not image_url: continue

                # Download final image
                async with session.get(image_url) as img_resp:
                    if img_resp.status != 200: continue
                    img_data = await img_resp.read()

                b64_data = base64.b64encode(img_data).decode('utf-8')
                media = {
                    "mimetype": img_resp.headers.get('Content-Type', 'image/jpeg'),
                    "data": b64_data,
                    "filename": f"dmeme_{subreddit}.jpg"
                }

                await client.send_media(
                    message.chat_id, 
                    media, 
                    caption=f"*{title}*\nSubreddit: r/{subreddit}",
                    reply_to=message.id
                )
                found_meme = True
                if status_msg: await status_msg.delete()
                break

            if not found_meme:
                await safe_edit(status_msg, f" ❌ NSFW Meme Error: {last_error or 'Could not find a valid meme'}")

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Command dmeme failed')
