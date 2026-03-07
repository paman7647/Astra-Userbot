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
from astra.models import Message


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
            stderr_full = (await process.stderr.read()).decode(errors="ignore")

            # Filter out non-fatal warnings from stderr to find the real error
            stderr_lines = [
                l for l in stderr_full.split("\n") 
                if "RequestsDependencyWarning" not in l and "urllib3" not in l and "chardet" not in l
            ]
            stderr = "\n".join(stderr_lines).strip()

            # If after filtering stderr is empty but returncode is non-zero, use the original for context
            if not stderr:
                stderr = stderr_full.strip()

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

            # ── Instaloader Fallback for Instagram ──
            if "instagram.com" in url:
                try:
                    import instaloader
                    L = instaloader.Instaloader(
                        dirname_pattern=os.path.join(os.path.dirname(__file__), "../temp/instaloader"),
                        filename_pattern="{target}_{mediaid}",
                        download_comments=False,
                        save_metadata=False,
                        download_geotags=False,
                        quiet=True
                    )
                    
                    await self._update_status("📡 **Astra Media Gateway**\n━━━━━━━━━━━━━━━━━━━━\n🔄 *Primary bridge failed. Attempting Instaloader fallback...*")
                    
                    # Extract shortcode/username
                    shortcode_match = re.search(r"/(?:p|reels|reel|stories)/([^/?#&]+)", url)
                    if shortcode_match:
                        shortcode = shortcode_match.group(1)
                        post = instaloader.Post.from_shortcode(L.context, shortcode)
                        metadata.update({
                            "title": post.caption[:50] if post.caption else "Instagram Post",
                            "uploader": post.owner_username,
                            "platform": "Instagram (Fallback)"
                        })
                        
                        L.download_post(post, target=shortcode)
                        
                        # Find the downloaded file
                        dl_dir = os.path.join(os.path.dirname(__file__), f"../temp/instaloader/{shortcode}")
                        if os.path.exists(dl_dir):
                            dl_files = [os.path.join(dl_dir, f) for f in os.listdir(dl_dir) if f.endswith(('.mp4', '.jpg', '.png'))]
                            if dl_files:
                                # Prioritize mp4 for "video" mode
                                videos = [f for f in dl_files if f.endswith('.mp4')]
                                file_path = videos[0] if videos else dl_files[0]
                                
                                # Move to temp for standard cleanup
                                final_path = os.path.join(os.path.dirname(__file__), f"../temp/ig_fb_{int(time.time())}_{os.path.basename(file_path)}")
                                os.rename(file_path, final_path)
                                return await cache.save_to_cache(url, mode, final_path, metadata)
                except Exception as ie:
                    # If fallback also fails, log it and continue to raise the original MediaException
                    print(f"Instaloader fallback failed: {str(ie)}")

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
            pct = (current / total) * 100
            bar = get_progress_bar(pct)
            await self._update_status(
                f"⚡ **Astra Media Gateway**\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"✨ *{metadata['title']}*\n\n"
                f"📤 **Stream:** {bar}\n"
                f"📂 **Size:** `{size_str}`",
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
                    f"📤 **Stream:** {get_progress_bar(0)}\n"
                    f"📂 **Size:* `{size_str}`",
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
