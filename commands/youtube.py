# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import shutil
import asyncio
import json
import re
import random
import time
from . import *
from config import config
from utils.helpers import get_progress_bar, safe_edit

@astra_command(
    name="youtube",
    description="Download media from YouTube (Audio or Video).",
    category="Media",
    aliases=["yt", "ytdl"],
    usage="<url> [video|audio] [--doc] (e.g. .youtube <link> video)",
    owner_only=False
)
async def youtube_handler(client: Client, message: Message):
    """
    Handles media download requests with live progress bar.
    """
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " ❌ Please provide a valid YouTube URL.")

        # System validation
        if not shutil.which("node"):
            return await smart_reply(message, "⚠️ `Node.js` is required for media operations.")

        # Argument parsing
        url = args_list[0]
        as_doc = any(opt in args_list for opt in ["doc", "document", "--doc", "--document"])
        
        # Robust mode detection
        video_keywords = ["video", "vid", "mp4", "mkv", "720p", "1080p"]
        args_lower = [arg.lower() for arg in args_list]
        mode = "video" if any(kw in args_lower for kw in video_keywords) else "audio"

        status_msg = await smart_reply(message, f" 🔍 *Initializing Astra Media Engine...*")

        # Cross-language Bridge Execution
        bridge_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils", "js_downloader.js")
        cookies_file = getattr(config, 'YOUTUBE_COOKIES_FILE', '') or ''
        cookies_browser = getattr(config, 'YOUTUBE_COOKIES_FROM_BROWSER', '') or ''

        process = await asyncio.create_subprocess_exec(
            "node", bridge_script,
            url, mode, 
            cookies_file, cookies_browser,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        metadata = {"title": "Pending...", "platform": "YouTube", "uploader": "Unknown", "url": url}
        files = []
        last_update_time = 0

        # Read output stream for Metadata and Progress
        while True:
            line = await process.stdout.readline()
            if not line: break
            
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            # 1. Capture Metadata
            if line_str.startswith("METADATA:"):
                metadata.update(json.loads(line_str.replace("METADATA:", "")))
                # use helper which includes the delay + fallback
                await safe_edit(
                    status_msg,
                    f"✨ *{metadata['title']}*\n"
                    f"🌐 *Platform:* {metadata['platform']}\n"
                    f"📂 *Mode:* {mode.capitalize()}\n\n"
                    f"⏳ *Preparing download...*"
                )
            # 2. Capture Progress
            if "[download]" in line_str and "%" in line_str:
                match = re.search(r"(\d+\.\d+)% of\s+([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+(\d+:\d+)", line_str)
                if match:
                    pct, size, speed, eta = match.groups()
                    pct = float(pct)
                    
                    current_time = time.time()
                    if current_time - last_update_time > 2.0 or pct >= 100:
                        bar = get_progress_bar(pct)
                        await safe_edit(
                            status_msg,
                            f"✨ *{metadata['title']}*\n"
                            f"🌐 *Platform:* {metadata['platform']}\n\n"
                            f"📥 *Downloading:* {bar}\n"
                            f"📋 *Size:* `{size}`\n"
                            f"⚡ *Speed:* `{speed}`\n"
                            f"⏳ *Remaining:* `{eta}`"
                        )
                        last_update_time = current_time

            # 3. Capture Success
            if line_str.startswith("SUCCESS:"):
                res = json.loads(line_str.replace("SUCCESS:", ""))
                files = res.get('files', [])

        await process.wait()

        if process.returncode != 0:
            stderr = await process.stderr.read()
            err_log = stderr.decode(errors='ignore')[:500]
            return await safe_edit(status_msg, f" ❌ Media Core Error:\n```{err_log}```")

        file_path = files[0]
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        start_upload_time = time.time()
        upload_last_update = 0
        
        # Enhanced Caption
        caption = (
            f"✨ *{metadata['title']}*\n"
            f"👤 *Channel:* {metadata.get('uploader', 'Unknown')}\n"
            f"🔗 *Source:* {metadata.get('url', url)}\n\n"
            f"🚀 *Powered by Astra UserBot*"
        )

        async def on_upload_progress(current, total):
            nonlocal upload_last_update
            now = time.time()
            if now - upload_last_update < 2.0: return
            
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            
            # Calculate speed based on percentage of file size
            elapsed = now - start_upload_time
            if elapsed > 0:
                sent_mb = (current / total) * file_size_mb
                speed = sent_mb / elapsed
                speed_text = f"{speed:.2f} MiB/s"
            else:
                speed_text = "Checking..."

            await safe_edit(
                status_msg,
                f"✨ *{metadata['title']}*\n"
                f"🌐 *Platform:* {metadata['platform']}\n\n"
                f"📤 *Uploading:* {bar}\n"
                f"⚡ *Speed:* `{speed_text}`"
            )
            upload_last_update = now

        try:
            if mode == "audio":
                await client.send_audio(message.chat_id, file_path, reply_to=message.id, progress=on_upload_progress)
            else:
                # Use send_video for playback, but fallback to file if video flag is issues
                await client.send_video(message.chat_id, file_path, caption=caption, reply_to=message.id, progress=on_upload_progress)
            
            await status_msg.delete()
        except Exception as e:
            await safe_edit(status_msg, f" ❌ Delivery failed: {str(e)}")

        # Cleanup
        if os.path.exists(file_path):
            os.remove(file_path)

    except Exception as e:
        await smart_reply(message, f" ❌ System Error: {str(e)}")
        await report_error(client, e, context='YouTube command root failure')
