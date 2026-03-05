import asyncio
import base64
import logging
import os
from typing import Optional

from astra import Client
from astra.models import Message

logger = logging.getLogger("Astra.BridgeDownloader")

# Self-contained JS that resolves a message by short/full ID and downloads its media.
# This bypasses the engine's retrieveMedia entirely for maximum reliability.
INLINE_DOWNLOAD_JS = """
(async (msgId) => {
    const Store = window.Astra.initializeEngine();
    const repo = Store.MessageRepo || Store.MsgRepo;
    let msg = null;

    // --- Resolve msg from ID (supports both full serialized and short stanza IDs) ---

    // 1. Direct repo lookup
    msg = repo.get(msgId);

    // 2. MessageIdentity lookup
    if (!msg && Store.MessageIdentity && Store.MessageIdentity.fromString) {
        try { msg = repo.get(Store.MessageIdentity.fromString(msgId)); } catch(e) {}
    }

    // 3. getMessagesById API
    if (!msg) {
        try {
            const r = await repo.getMessagesById([msgId]);
            msg = r && r.messages && r.messages[0];
        } catch(e) {}
    }

    // 4. Scan top-level repo by stanza ID (critical for quoted msg short IDs)
    if (!msg) {
        const shortId = msgId.includes('_') ? msgId.split('_').pop() : msgId;
        const models = repo.getModelsArray ? repo.getModelsArray() : (repo.models || []);
        msg = models.find(m => m.id && (m.id.id === shortId || m.id._serialized === msgId));
    }

    // 5. Per-chat message scan
    if (!msg && Store.Chat) {
        const shortId = msgId.includes('_') ? msgId.split('_').pop() : msgId;
        const chats = Store.Chat.getModelsArray ? Store.Chat.getModelsArray() : (Store.Chat.models || []);
        for (const chat of chats) {
            if (msg) break;
            if (!chat.msgs) continue;
            const msgs = chat.msgs.getModelsArray ? chat.msgs.getModelsArray() : (chat.msgs.models || []);
            msg = msgs.find(m => m.id && (m.id.id === shortId || m.id._serialized === msgId));
        }
    }

    if (!msg) return { error: 'msg_not_found' };

    // --- Download the media ---
    let buffer = null;

    // Strategy A: DownloadManager (encrypted download + decrypt)
    if (!buffer && msg.directPath && msg.mediaKey) {
        try {
            const dm = Store.DownloadManager;
            if (dm && dm.downloadAndMaybeDecrypt) {
                if (msg.mediaData && msg.mediaData.mediaStage !== 'RESOLVED') {
                    await msg.downloadMedia({ downloadEvenIfExpensive: true, rmrReason: 1 });
                }
                const qpl = { addAnnotations() { return this; }, addPoint() { return this; } };
                buffer = await dm.downloadAndMaybeDecrypt({
                    directPath: msg.directPath,
                    encFilehash: msg.encFilehash,
                    filehash: msg.filehash,
                    mediaKey: msg.mediaKey,
                    mediaKeyTimestamp: msg.mediaKeyTimestamp || msg.t,
                    type: msg.type,
                    signal: (new AbortController()).signal,
                    downloadQpl: qpl
                });
            }
        } catch(e) { console.warn('[BD] DownloadManager failed:', e); }
    }

    // Strategy B: msg.downloadMedia() then read blob
    if (!buffer && msg.downloadMedia) {
        try {
            await msg.downloadMedia({ downloadEvenIfExpensive: true, rmrReason: 1 });
            if (msg.mediaData && msg.mediaData.mediaBlob) {
                const blob = msg.mediaData.mediaBlob.forResume
                    ? msg.mediaData.mediaBlob.forResume() : msg.mediaData.mediaBlob;
                if (blob && typeof blob.arrayBuffer === 'function') {
                    buffer = new Uint8Array(await blob.arrayBuffer());
                }
            }
        } catch(e) { console.warn('[BD] downloadMedia blob failed:', e); }
    }

    // Strategy C: DOM blob scraping
    if (!buffer) {
        const fullId = msg.id && msg.id._serialized ? msg.id._serialized : msgId;
        const shortId = fullId.includes('_') ? fullId.split('_').pop() : fullId;
        try {
            if (Store.Cmd && Store.Cmd.scrollToMessage) {
                try { Store.Cmd.scrollToMessage(msg); await new Promise(r => setTimeout(r, 600)); } catch(e) {}
            }
            let el = document.querySelector(`div[data-id="${fullId}"] img, div[data-id="${fullId}"] video`);
            if (!el) el = document.querySelector(`div[data-id*="${shortId}"] img, div[data-id*="${shortId}"] video`);
            if (el && el.src && el.src.startsWith('blob:')) {
                const res = await fetch(el.src);
                const blob = await res.blob();
                buffer = new Uint8Array(await blob.arrayBuffer());
            }
        } catch(e) { console.warn('[BD] DOM scraping failed:', e); }
    }

    if (!buffer) return { error: 'download_failed' };

    // Convert to base64 using FileReader (fast, no char-by-char loop)
    const b = new Blob([buffer instanceof ArrayBuffer ? new Uint8Array(buffer) : buffer]);
    const b64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1]);
        reader.onerror = reject;
        reader.readAsDataURL(b);
    });

    return { data: b64, mimetype: msg.mimetype || 'application/octet-stream', size: buffer.byteLength };
})
"""


class AstraBridge:
    """High-reliability media downloader — self-contained JS, no engine dependency."""

    @staticmethod
    async def download_media(client: Client, message: Message) -> Optional[bytes]:
        """
        Downloads media from a message using self-contained inline JS.
        Handles quoted message resolution automatically.
        """
        try:
            target = message.quoted if message.has_quoted_msg else message
            if not target or not target.is_media:
                logger.debug("Download skipped: not a media message.")
                return None

            mid = target.id
            logger.info(f"📥 Bridge Attempting Download: {mid}")

            # Execute our self-contained JS directly on the browser page
            page = client.browser.page
            if not page:
                logger.error("No browser page available.")
                return None

            result = await page.evaluate(f'{INLINE_DOWNLOAD_JS}("{mid}")')

            if result and isinstance(result, dict):
                if "error" in result:
                    logger.warning(f"⚠️ Inline JS download result: {result['error']} for {mid}")
                elif "data" in result:
                    logger.info(f"✅ Download OK (Inline JS): {mid} ({result.get('size', '?')} bytes)")
                    return base64.b64decode(result["data"])

            # Fallback: try the engine's download_media as a last resort
            logger.warning(f"Inline JS returned nothing. Trying engine fallback for {mid}...")
            for attempt in range(2):
                try:
                    data_b64 = await client.download_media(mid)
                    if data_b64:
                        logger.info(f"✅ Download OK (Engine fallback): {mid}")
                        return base64.b64decode(data_b64)
                except Exception as e:
                    logger.debug(f"Engine fallback attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Fatal error in BridgeDownloader: {e}")

        return None


bridge_downloader = AstraBridge()
