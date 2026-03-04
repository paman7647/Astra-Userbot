import asyncio
import base64
import logging
import os
from typing import Optional

from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.BridgeDownloader")


class AstraBridge:
    """
    Universal High-Reliability Media Downloader.
    Bypasses framework-level decryption issues by injecting JS into the browser.
    """

    @staticmethod
    async def download_media(client: Client, message: Message) -> Optional[bytes]:
        """
        Downloads media from a message with a robust recursive fallback logic.
        """
        try:
            # 1. Resolve Target
            target = message.quoted if message.has_quoted_msg else message
            if not target or not target.is_media:
                logger.debug("Download aborted: Target is not media.")
                return None

            mid = target.id
            logger.info(f"📥 Bridge Attempting Download: {mid}")

            # 2. Main Strategy: Engine native download
            for attempt in range(2):
                try:
                    # Attempt 1: Raw Base64 retrieval (Fastest)
                    data_b64 = await client.download_media(mid)
                    if data_b64:
                        logger.info(f"✅ Download Success (Native B64): {mid}")
                        return base64.b64decode(data_b64)

                    # Attempt 2: File-based retrieval (More robust for large files)
                    file_path = await client.media.download(target)
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            data = f.read()
                        os.remove(file_path)
                        logger.info(f"✅ Download Success (Native File): {mid}")
                        return data
                except Exception as e:
                    logger.debug(f"Native attempt {attempt + 1} failed for {mid}: {e}")

                await asyncio.sleep(1)

            # 3. Aggressive Fallback: Custom JS Injection
            # This bypasses the engine's potentially stale repository and looks directly at the DOM
            logger.warning(f"⚠️ Native download failed for {mid}. Launching Aggressive JS Fallback...")

            js_fallback = f"""
            (async () => {{
                const msgId = "{mid}";
                
                // Try to find the blob in DOM
                let el = document.querySelector(`div[data-id="${{msgId}}"] img, div[data-id="${{msgId}}"] video`);
                if (!el) {{
                    // Try partial match for MD IDs
                    const part = msgId.split('_').pop();
                    el = document.querySelector(`div[data-id*="${{part}}"] img, div[data-id*="${{part}}"] video`);
                }}

                if (el && el.src && el.src.startsWith('blob:')) {{
                    const res = await fetch(el.src);
                    const blob = await res.blob();
                    return await new Promise((resolve, reject) => {{
                        const reader = new FileReader();
                        reader.onload = () => resolve(reader.result.split(',')[1]);
                        reader.onerror = reject;
                        reader.readAsDataURL(blob);
                    }});
                }}
                return null;
            }})()
            """

            try:
                res_b64 = await client.bridge.execute(js_fallback)
                if res_b64:
                    logger.info(f"🚀 Aggressive JS Fallback SUCCESS for {mid}!")
                    return base64.b64decode(res_b64)
            except Exception as e:
                logger.error(f"Aggressive JS Fallback failed: {e}")

        except Exception as e:
            logger.error(f"Fatal error in BridgeDownloader: {e}")

        return None

        return None


# Singleton-style access
bridge_downloader = AstraBridge()
