"""
Collection of utility functions and classes to assist with common bot operations.
Includes media handling, rate limiting, and reporting mechanisms.
"""

import asyncio
import shutil
import time
import traceback
from typing import Optional

from astra.types import Message

# Core Utility Functions
# ----------------------

def safe_task(coro_or_future, log_context: str = "Unhandled Task"):
    """
    Executes a coroutine or future as a background task.
    Safely catches and logs all exceptions to prevent 'Task exception was never retrieved'.
    Uses ensure_future to handle both coroutines and futures.
    """
    import logging
    logger = logging.getLogger("Astra.SafeTask")

    async def wrapper():
        try:
            if asyncio.iscoroutine(coro_or_future):
                await coro_or_future
            else:
                await asyncio.wrap_future(coro_or_future)
        except Exception as e:
            logger.error(f"[{log_context}] Background task failed: {e}", exc_info=True)

    return asyncio.ensure_future(wrapper())


async def check_binary(name: str) -> bool:
    """
    Checks if a specific binary is available in the system's execution PATH.
    Useful for validating system-level dependencies like FFmpeg or Node.
    """
    return shutil.which(name) is not None


async def get_media_message(message: Message) -> Optional[Message]:
    """
    Identifies if the given message or its quoted counterpart contains media.
    Returns the message object containing media, or None.
    """
    if message.is_media:
        return message
    if message.has_quoted_msg:
        quoted = message.quoted
        if quoted and quoted.is_media:
            return quoted
    return None


async def get_media_title(url: str) -> str:
    """
    Attempts to retrieve a human-readable title for a media URL using yt-dlp.
    Falls back to a generic title if retrieval fails.
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--get-title",
            "--no-warnings",
            url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
    except Exception:
        # Silently fail as this is often a non-critical metadata fetch
        pass
    return "Media Content"


# Operational Support Classes
# ---------------------------


class RateLimiter:
    """
    Implements a sliding window rate limiting algorithm.
    Prevents command spam by tracking user-specific execution timestamps.
    """

    def __init__(self, limit: int = 5, window: int = 60):
        self.limit = limit
        self.window = window
        self.records = {}

    def check(self, user_id: str) -> bool:
        """
        Validates if a user is within the allowed rate limit.
        Returns True if allowed, False if throttled.
        """
        now = time.time()

        if user_id not in self.records:
            self.records[user_id] = []

        # Purge timestamps outside the current window
        self.records[user_id] = [t for t in self.records[user_id] if now - t < self.window]

        if len(self.records[user_id]) >= self.limit:
            return False

        self.records[user_id].append(now)
        return True


async def edit_or_reply(message: Message, content: str, **kwargs):
    """
    Edits the triggering message if sent by us, otherwise replies.
    Falls back to a plain send if both edit and reply fail.
    Handles 'Cannot edit message' errors by immediately falling back to reply.
    """
    try:
        # Check if the message is from us and is potentially editable (not too old, not deleted)
        if message.from_me:
            try:
                # We add a small delay to avoid race conditions with bridge processing
                time.sleep(0.5)
                await message.edit(content)
                return message
            except Exception as e:
                # If editing fails (e.g., Cannot edit message error), we move on to reply
                if "Cannot edit message" in str(e) or "editMessage" in str(e):
                    pass # Handled by the next try block
                else:
                    raise e
    except Exception:
        pass

    try:
        return await message.reply(content, **kwargs)
    except Exception:
        pass

    # Last resort: just send to the chat directly
    try:
        return await message._client.send_message(message.chat_id, content, **kwargs)
    except Exception:
        return None


# Keep backward compat alias
edit_or_reply = edit_or_reply


async def safe_edit(message: Message, content: str, **kwargs):
    """
    A robust version of edit() that automatically falls back to
    edit_or_reply() or message.reply() if editing is not possible.
    Includes built-in protection against common WhatsApp edit restrictions.
    """
    try:
        # If edit is possible (it's from me), attempt it
        if message.from_me:
            time.sleep(0.5)
            return await message.edit(content, **kwargs)
        else:
            # If not from me, we must reply
            return await edit_or_reply(message, content, **kwargs)
    except Exception:
        # Global fallback for any failure (message deleted, too old, etc.)
        return await edit_or_reply(message, content, **kwargs)


# Error reporting is now handled by the centralized ErrorReporter module.
# It auto-creates a WhatsApp group for logs, falling back to owner DM.
# from utils.error_reporter import report_error, handle_command_error, ErrorReporter (unused here, triggers circularity)


async def get_contact_name(client, jid: str) -> str:
    """
    Priority-based name resolution for any JID.
    Priority: Pushname > Contact Name > Formatted Number > Short JID
    """
    try:
        from astra.types import JID

        jid_obj = JID.parse(jid) if isinstance(jid, str) else jid

        # Check if it's "Me" (LID or User ID matches)
        me = await client.get_me()
        if jid_obj.primary == me.id.primary:
            return "Me"

        clean_jid = jid_obj.primary
        contact = await client.get_contact(clean_jid)

        # Priority Logic
        if contact.push_name:
            return contact.push_name
        if contact.name:
            return contact.name

        # Fallback to number or JID
        user_part = clean_jid.split("@")[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]
    except Exception:
        # Hard fallback
        user_part = str(jid).split("@")[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]


# Exported Singletons
# ------------------
rate_limiter = RateLimiter()
