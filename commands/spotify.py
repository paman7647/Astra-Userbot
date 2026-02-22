# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import asyncio
import os
import time
import json
import re
import shutil
import random
from config import config
from . import *
from utils.helpers import get_progress_bar

@astra_command(
    name="spotify",
    description="Download/Search Spotify track",
    category="Media",
    aliases=[],
    usage="<query|url> (search term or Spotify link)",
    owner_only=False
)
async def spotify_handler(client: Client, message: Message):
    """Download/Search Spotify track with live progress"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Provide a Spotify link or song name.")

        query = " ".join(args_list)
        status_msg = await smart_reply(message, f" 🔍 *Initializing Spotify Engine...*")

        # Searching on YouTube as fallback/source for downloads
        search_query = f"ytsearch:{query}" if "spotify.com" not in query else query

        bridge_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "js_downloader.js")
        cookies_file = getattr(config, 'YOUTUBE_COOKIES_FILE', '') or ''
        cookies_browser = getattr(config, 'YOUTUBE_COOKIES_FROM_BROWSER', '') or ''

        process = await asyncio.create_subprocess_exec(
            "node", bridge_script,
            search_query, "audio", 
            cookies_file, cookies_browser,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        metadata = {"title": query, "platform": "Spotify/Search", "uploader": "Unknown", "url": query}
        files = []
        last_update_time = 0

        # Read output stream
        while True:
            line = await process.stdout.readline()
            if not line: break
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            if line_str.startswith("METADATA:"):
                metadata.update(json.loads(line_str.replace("METADATA:", "")))
                time.sleep(0.5)
                await status_msg.edit(
                    f"✨ *{metadata['title']}*\n"
                    f"🌐 *Platform:* {metadata['platform']}\n\n"
                    f"⏳ *Accessing content...*"
                )
                continue

            if "[download]" in line_str and "%" in line_str:
                match = re.search(r"(\d+\.\d+)% of\s+([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+(\d+:\d+)", line_str)
                if match:
                    pct, size, speed, eta = match.groups()
                    pct = float(pct)
                    current_time = time.time()
                    if current_time - last_update_time > 2.0 or pct >= 100:
                        bar = get_progress_bar(pct)
                        time.sleep(0.5)
                        await status_msg.edit(
                            f"✨ *{metadata['title']}*\n"
                            f"🌐 *Platform:* {metadata['platform']}\n\n"
                            f"📥 *Downloading:* {bar}\n"
                            f"📋 *Size:* `{size}`\n"
                            f"⚡ *Speed:* `{speed}`\n"
                            f"⏳ *Remaining:* `{eta}`"
                        )
                        last_update_time = current_time

            if line_str.startswith("SUCCESS:"):
                res = json.loads(line_str.replace("SUCCESS:", ""))
                files = res.get('files', [])

        await process.wait()

        if process.returncode != 0:
            stderr = await process.stderr.read()
            err_text = stderr.decode(errors='ignore')[:300]
            time.sleep(0.5)
            return await status_msg.edit(f"❌ Spotify Core Error:\n```{err_text}```")

        if not files:
            time.sleep(0.5)
            return await status_msg.edit(" ❌ Could not find track.")

        file_path = files[0]
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        start_upload_time = time.time()
        upload_last_update = 0
        
        async def on_upload_progress(current, total):
            nonlocal upload_last_update
            now = time.time()
            if now - upload_last_update < 2.0: return
            
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            
            elapsed = now - start_upload_time
            if elapsed > 0:
                sent_mb = (current / total) * file_size_mb
                speed = sent_mb / elapsed
                speed_text = f"{speed:.2f} MiB/s"
            else:
                speed_text = "Checking..."

            time.sleep(0.5)
            await status_msg.edit(
                f"✨ *{metadata['title']}*\n"
                f"🌐 *Platform:* {metadata['platform']}\n\n"
                f"📤 *Uploading:* {bar}\n"
                f"⚡ *Speed:* `{speed_text}`"
            )
            upload_last_update = now

        try:
            await client.send_audio(message.chat_id, file_path, reply_to=message.id, progress=on_upload_progress)
            await status_msg.delete()
        except Exception as e:
            time.sleep(0.5)
            await status_msg.edit(f" ❌ Delivery failed: {str(e)}")

        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Spotify command root failure')
