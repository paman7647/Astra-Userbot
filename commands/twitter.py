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
    name="twitter",
    description="Download Twitter/X video",
    category="Media",
    aliases=["tw", "x"],
    usage="<url> (Twitter/X status link)",
    owner_only=False
)
async def twitter_handler(client: Client, message: Message):
    """Download Twitter/X video with live progress"""
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a Twitter/X URL.")

        url = args_list[0]
        status_msg = await smart_reply(message, f" 🔍 *Initializing Twitter Engine...*")

        # Bridge Execution
        bridge_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "js_downloader.js")
        cookies_file = getattr(config, 'YOUTUBE_COOKIES_FILE', '') or ''
        cookies_browser = getattr(config, 'YOUTUBE_COOKIES_FROM_BROWSER', '') or ''

        process = await asyncio.create_subprocess_exec(
            "node", bridge_script,
            url, "video", 
            cookies_file, cookies_browser,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        metadata = {"title": "X Video", "platform": "Twitter", "uploader": "Unknown", "url": url}
        files = []
        last_update_time = 0

        # 1. Read progress from stdout
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
            return await status_msg.edit(f"❌ X/Twitter Core Error:\n```{err_text}```")

        if not files:
            time.sleep(0.5)
            return await status_msg.edit(" ❌ Video not found or incompatible.")

        file_path = files[0]
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        start_upload_time = time.time()
        upload_last_update = 0
        
        # Enhanced Caption
        caption = (
            f"✨ *{metadata['title']}*\n"
            f"👤 *Handle:* {metadata.get('uploader', 'Unknown')}\n"
            f"🔗 *Source:* {metadata.get('url', url)}\n\n"
            f"🚀 *Powered by Astra UserBot*"
        )

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
            await client.send_video(message.chat_id, file_path, caption=caption, reply_to=message.id, progress=on_upload_progress)
            await status_msg.delete()
        except Exception as e:
            time.sleep(0.5)
            await status_msg.edit(f" ❌ Delivery failed: {str(e)}")

        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='Twitter command root failure')
