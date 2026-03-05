"""
Astra Error Reporter
--------------------
Centralized error reporting with auto-created WhatsApp group.
All errors and system notifications go to the group first,
falling back to owner DM only if group delivery fails.
"""

import logging
import platform
import sys
import time
import traceback
from typing import Optional

from utils.database import db

logger = logging.getLogger("Astra.ErrorReporter")

_error_timestamps = []
_MAX_ERRORS_PER_MIN = 5


class ErrorReporter:

    _group_id: Optional[str] = None
    _initialized = False

    @classmethod
    async def initialize(cls, client):
        """
        Called on bot startup. Creates the error log group if not in DB.
        Skips entirely if group ID already exists in the database.
        """
        if cls._initialized:
            return

        stored = await db.get("error_log_group_id")
        if stored:
            cls._group_id = stored
            cls._initialized = True
            return

        try:
            me = await client.get_me()
            my_jid = me.id.serialized if hasattr(me.id, "serialized") else str(me.id)
            gid = await client.group.create("「Astra」Error Logs", [my_jid])

            if gid:
                if hasattr(gid, "serialized"):
                    gid = gid.serialized
                gid = str(gid)

                cls._group_id = gid
                await db.set("error_log_group_id", gid)

                try:
                    await client.group.set_description(
                        gid,
                        "🤖 Astra Userbot — Automated Error & System Logs\n"
                        "━━━━━━━━━━━━━━━━━━━━\n"
                        "This group was auto-created by Astra.\n"
                        "All errors and system alerts are logged here.\n\n"
                        "⚠️ Do not delete this group."
                    )
                except:
                    pass

                logger.info(f"Created error log group: {gid}")
        except Exception as e:
            logger.warning(f"Failed to create error log group: {e}")

        cls._initialized = True

    @classmethod
    async def _ensure_group(cls, client) -> Optional[str]:
        if cls._group_id:
            return cls._group_id
        if not cls._initialized:
            await cls.initialize(client)
        return cls._group_id

    @classmethod
    async def _send_to_group(cls, client, text: str) -> bool:
        gid = await cls._ensure_group(client)
        if not gid:
            return False
        try:
            await client.send_message(gid, text)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to error group: {e}")
            return False

    @classmethod
    async def _send_to_owner(cls, client, text: str) -> bool:
        try:
            me = await client.get_me()
            target_id = me.id.serialized if hasattr(me.id, "serialized") else str(me.id)
            await client.send_message(target_id, text)
            return True
        except Exception as e:
            logger.warning(f"Failed to send to owner DM: {e}")
        return False

    @classmethod
    async def send(cls, client, text: str):
        """Send to error group first. Falls back to owner DM."""
        if await cls._send_to_group(client, text):
            return True
        return await cls._send_to_owner(client, text)

    @classmethod
    async def report(cls, client, message, exc: Exception, context: str = "Command Failure"):
        """
        Send full error diagnostics to group/DM ONLY.
        User in the original chat sees a clean one-liner.
        """
        from utils.helpers import edit_or_reply

        global _error_timestamps
        now = time.time()
        _error_timestamps = [t for t in _error_timestamps if now - t < 60]
        if len(_error_timestamps) >= _MAX_ERRORS_PER_MIN:
            return
        _error_timestamps.append(now)

        tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        chat_info = ""
        try:
            cid = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
            chat_info = f"*Chat:* `{cid}`\n"
        except:
            pass

        cmd_text = ""
        try:
            cmd_text = f"*Command:* `{(message.body or '')[:80]}`\n"
        except:
            pass

        report_text = (
            f"🚨 *Astra System Alert*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Context:* `{context}`\n"
            f"{chat_info}"
            f"{cmd_text}"
            f"*Error:* `{str(exc)[:200]}`\n"
            f"*Time:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"*Python:* `{sys.version.split()[0]}`\n\n"
            f"*Stack Trace:*\n```\n{tb[:1500]}\n```"
        )

        # Full details ONLY to group or DM
        sent_to_group = await cls._send_to_group(client, report_text)
        sent_to_dm = False
        if not sent_to_group:
            sent_to_dm = await cls._send_to_owner(client, report_text)

        # Clean one-liner to the user in chat
        try:
            if sent_to_group:
                dest = "error log group"
            elif sent_to_dm:
                dest = "owner DM"
            else:
                dest = "logs"
            await edit_or_reply(message, f"⚠️ *An error occurred.* Details reported to *{dest}*.")
        except:
            pass

    @classmethod
    async def boot_message(cls, client, plugin_count: int = 0):
        """Send startup notification to error group (or DM fallback)."""
        from config import config

        custom_msg = await db.get("STARTUP_MESSAGE")

        boot_text = custom_msg or (
            f"✅ *Astra Userbot Online*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"*Version:* `{config.VERSION}`\n"
            f"*Plugins:* `{plugin_count}` loaded\n"
            f"*Python:* `{sys.version.split()[0]}`\n"
            f"*Platform:* `{platform.system()} {platform.release()}`\n"
            f"*Time:* `{time.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await cls.send(client, boot_text)

    @classmethod
    async def notify(cls, client, text: str):
        """Send a system notification to the group (or DM fallback)."""
        await cls.send(client, text)


# Convenience aliases
error_reporter = ErrorReporter

async def report_error(client, exc, context=""):
    await ErrorReporter.send(client, (
        f"🚨 *Astra System Alert*\n\n"
        f"*Context:* `{context}`\n"
        f"*Error:* `{str(exc)[:200]}`\n\n"
        f"*Stack Trace:*\n```\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))[:1500]}\n```"
    ))

async def handle_command_error(client, message, exc, context="Command Failure"):
    await ErrorReporter.report(client, message, exc, context=context)
