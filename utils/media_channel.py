import asyncio
import json
import os
import re
import time

from config import config
from utils.helpers import safe_edit
from utils.media_exceptions import (
    ContentAgeRestrictedException,
    ContentPrivateException,
    ContentUnavailableException,
    InvalidURLException,
    MediaException,
    RateLimitException,
)
from utils.progress import get_progress_bar

from astra.client import Client
from astra.types import Message


class MediaChannel:
    """
    Centralized Media Downloader and Uploader Channel.
    Provides real-time progress tracking and optimized delivery.
    """

    def __init__(self, client: Client, message: Message, status_msg: Message):
        self.client = client
        self.message = message
        self.status_msg = status_msg
        self.last_update = 0
        self.update_interval = 0.5  # Dynamic high-speed updates (0.5s)

    async def _update_status(self, text: str, force: bool = False, is_progress: bool = False):
        """Throttled status updates for smooth UI."""
        from utils.state import state

        # Silent mode (FAST_MEDIA) bypasses progress updates
        if is_progress and state.get_config("FAST_MEDIA"):
            return

        now = time.time()
        if force or (now - self.last_update >= self.update_interval):
            await safe_edit(self.status_msg, text)
            self.last_update = now

    async def run_bridge(self, url: str, mode: str):
        """Executes the JS downloader bridge, utilizing cache for speed."""
        from utils.cache_manager import cache

        # 1. Check Cache
        cached_file, cached_meta = await cache.get_cached_file(url, mode)
        if cached_file:
            await self._update_status(
                f"⚡ **Astra Media Gateway**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ *{cached_meta.get('title', 'Media')}*\n"
                f"🟢 *Cache Hit:* Delivered instantly.\n\n"
                f"📤 *Preparing upload...*",
                force=True,
            )
            # Small delay to let the user read the cache hit message
            await asyncio.sleep(1)
            return cached_file, cached_meta

        bridge_script = os.path.join(os.path.dirname(__file__), "js_downloader.js")
        cookies_file = getattr(config, "YOUTUBE_COOKIES_FILE", "") or ""
        cookies_browser = getattr(config, "YOUTUBE_COOKIES_FROM_BROWSER", "") or ""

        import sys

        process = await asyncio.create_subprocess_exec(
            "node",
            bridge_script,
            url,
            mode,
            cookies_file,
            cookies_browser,
            sys.executable,  # Pass current python path
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        metadata = {"title": "Media Content", "platform": "Astra", "uploader": "Unknown", "url": url}
        file_path = None

        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode("utf-8", errors="ignore").strip()

            # Metadata Capture
            if line_str.startswith("METADATA:"):
                metadata.update(json.loads(line_str.replace("METADATA:", "")))
                await self._update_status(
                    f"⚡ **Astra Media Gateway**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ *{metadata['title']}*\n"
                    f"🌐 *Platform:* {metadata['platform']}\n"
                    f"📂 *Format:* {mode.capitalize()}\n\n"
                    f"⏳ *Initializing download stream...*",
                    force=True,
                )

            # Progress Capture
            if "[download]" in line_str and "%" in line_str:
                match = re.search(r"(\d+\.\d+)% of\s+([\d\.]+\w+)\s+at\s+([\d\.]+\w+/s)\s+ETA\s+(\d+:\d+)", line_str)
                if match:
                    pct, size, speed, eta = match.groups()
                    bar = get_progress_bar(float(pct))
                    await self._update_status(
                        f"⚡ **Astra Media Gateway**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"✨ *{metadata['title']}*\n\n"
                        f"📥 *Stream:* {bar}\n"
                        f"📋 *Size:* `{size}`\n"
                        f"🚀 *Speed:* `{speed}`\n"
                        f"🕒 *ETA:* `{eta}`",
                        is_progress=True,
                    )

            # Success Capture
            if line_str.startswith("SUCCESS:"):
                res = json.loads(line_str.replace("SUCCESS:", ""))
                files = res.get("files", [])
                if files:
                    file_path = files[0]

        await process.wait()
        if process.returncode != 0:
            stderr = (await process.stderr.read()).decode(errors="ignore")

            # Smart Error Parsing
            if "This video is private" in stderr or "Private account" in stderr:
                raise ContentPrivateException()
            elif "Video unavailable" in stderr or "this video has been removed" in stderr.lower():
                raise ContentUnavailableException()
            elif "Confirm your age" in stderr or "age-restricted" in stderr.lower():
                raise ContentAgeRestrictedException()
            elif "429" in stderr or "Too Many Requests" in stderr:
                raise RateLimitException()
            elif "Unsupported URL" in stderr or "invalid URL" in stderr.lower():
                raise InvalidURLException()

            # Generic Bridge Error with snippet
            raise MediaException(f"Stream Error: {stderr[:200]}...")

        if not file_path or not os.path.exists(file_path):
            raise MediaException("File stream failed or was not written to disk.")

        # Save to Cache automatically
        cached_path = await cache.save_to_cache(url, mode, file_path, metadata)
        return cached_path, metadata

    async def upload_file(self, file_path: str, metadata: dict, mode: str):
        """Uploads file with real-time status updates."""
        from utils.state import state

        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        size_str = f"{file_size_mb:.2f} MB" if file_size_mb < 1024 else f"{file_size_mb / 1024:.2f} GB"

        start_time = time.time()
        fast_mode = state.get_config("FAST_MEDIA")

        async def on_progress(current, total):
            if fast_mode:
                return

            # Non-fastmode: Show a simple "Uploading" status without a granular progress bar for a cleaner look
            # as per user request to "show uploading etc in non fastmode without progress etc"
            await self._update_status(
                f"⚡ **Astra Media Gateway**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ *{metadata['title']}*\n\n"
                f"📤 **Uploading to WhatsApp...**\n"
                f"📂 *Size:* `{size_str}`",
                is_progress=True,
            )

        caption = (
            f"✨ *{metadata['title']}*\n"
            f"👤 *Author:* {metadata.get('uploader', 'Unknown')}\n"
            f"📁 *Size:* `{size_str}`\n"
            f"🔗 *Source:* {metadata.get('url', 'Unknown')}\n\n"
            f"🚀 *Powered by Astra UserBot*"
        )

        try:
            # Initial upload status
            if not fast_mode:
                await self._update_status(
                    f"⚡ **Astra Media Gateway**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✨ *{metadata['title']}*\n\n"
                    f"📤 **Uploading to WhatsApp...**\n"
                    f"📂 *Size:* `{size_str}`",
                    force=True,
                )

            if mode == "audio":
                await self.client.send_audio(
                    self.message.chat_id, file_path, reply_to=self.message.id, progress=on_progress
                )
            else:
                await self.client.send_video(
                    self.message.chat_id, file_path, caption=caption, reply_to=self.message.id, progress=on_progress
                )

            await self.status_msg.delete()
        except MediaException:
            # Re-raise custom exceptions to be handled by the command's generic error handler
            raise
        except Exception as e:
            # Wrap unexpected errors in a general MediaException
            raise MediaException(f"Media Engine Fault: {str(e)}")
        finally:
            # We don't remove file_path anymore here because it's serving from the cache directory
            pass
