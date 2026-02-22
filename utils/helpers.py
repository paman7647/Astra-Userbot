# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Collection of utility functions and classes to assist with common bot operations.
Includes media handling, rate limiting, and reporting mechanisms.
"""
import time
import os
import shutil
import asyncio
import traceback
from typing import Optional, List
from astra.models import Message

# Core Utility Functions
# ----------------------

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
            "yt-dlp", "--get-title", "--no-warnings", url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
        import time
        now = time.time()
        
        if user_id not in self.records:
            self.records[user_id] = []
        
        # Purge timestamps outside the current window
        self.records[user_id] = [t for t in self.records[user_id] if now - t < self.window]
        
        if len(self.records[user_id]) >= self.limit:
            return False
            
        self.records[user_id].append(now)
        return True

async def smart_reply(message: Message, content: str, **kwargs):
    """
    An intelligent delivery mechanism that edits the message if sent by the bot,
    or replies if sent by another user. Handles edge cases where editing is restricted.
    """
    try:
        # If the bot itself sent the message, editing provides a cleaner UI.
        if message.from_me:
            await message.edit(content)
            return message
        else:
            return await message.reply(content, **kwargs)
    except Exception as e:
        # Fallback to standard reply if edit fails (e.g., message already deleted or too old).
        return await message.reply(content, **kwargs)



def get_progress_bar(pct: float, length: int = 15) -> str:
    """
    Generates a visual progress bar string.
    Example: [▰▰▰▱▱▱▱▱▱▱] 30.0%
    """
    try:
        filled = int(length * pct / 100)
        bar = "▰" * filled + "▱" * (length - filled)
        return f"[{bar}] {pct:.1f}%"
    except:
        return f"[░░░░░░░░░░░░░] {pct}%"

async def report_error(client, exc: Exception, context: str = ""):
    """
    Captures and transmits diagnostic information (tracebacks) to the bot owner.
    Provides visibility into runtime issues directly within WhatsApp.
    """
    from config import config
    try:
        # Extract full stack trace for debugging
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        
        # Determine notification targets
        owner_ids = getattr(client, 'owner_ids', [])
        if not owner_ids and config.OWNER_ID:
            owner_ids = [config.OWNER_ID]

        if not owner_ids:
            return False

        # Format report with Markdown for better readability in WhatsApp
        report = (
            f"🚨 *Astra System Alert*\n\n"
            f"*Context:* `{context}`\n"
            f"*Error:* {str(exc)[:200]}\n"
            f"\n*Stack Trace:*\n```\n{tb[:1500]}\n```"
        )

        for oid in owner_ids:
            try:
                await client.send_message(oid, report)
            except Exception:
                continue
        return True
    except Exception:
        return False

async def get_contact_name(client, jid: str) -> str:
    """
    Priority-based name resolution for any JID.
    Priority: Pushname > Contact Name > Formatted Number > Short JID
    """
    try:
        from astra.models import JID
        jid_obj = JID.parse(jid) if isinstance(jid, str) else jid
        
        # Check if it's "Me" (LID or User ID matches)
        me = await client.get_me()
        if jid_obj.primary == me.id.primary:
            return "Me"

        clean_jid = jid_obj.primary
        contact = await client.get_contact(clean_jid)
        
        # Priority Logic
        if contact.push_name: return contact.push_name
        if contact.name: return contact.name
        
        # Fallback to number or JID
        user_part = clean_jid.split('@')[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]
    except Exception:
        # Hard fallback
        user_part = str(jid).split('@')[0]
        return f"+{user_part}" if user_part.isdigit() else user_part[:10]

# Exported Singletons
# ------------------
rate_limiter = RateLimiter()
