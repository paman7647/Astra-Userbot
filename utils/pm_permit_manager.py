# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import logging
from astra import Client
from astra.models import Message
from config import config
from utils.state import state
from utils.helpers import smart_reply, get_contact_name

logger = logging.getLogger("Astra.PMPermit")

async def enforce_pm_protection(client: Client, message: Message):
    """
    Enforces PM protection by checking if the sender is permitted.
    If not, it issues warnings or blocks depending on the configuration.
    """
    if not config.ENABLE_PM_PROTECTION:
        return True

    # 1. Resolve IDs safely (handles both JID objects and strings)
    # We always use the primary JID (stripping device stickers like :4) for logic checks
    def get_primary(jid: Any) -> str:
        s = jid.serialized if hasattr(jid, "serialized") else str(jid)
        if "@" in s and ":" in s.split("@")[0]:
            return s.split(":")[0] + "@" + s.split("@")[1]
        return s

    chat_id = get_primary(message.chat_id)
    sender_id = get_primary(message.sender) if message.sender else chat_id

    # 2. Skip if not a private message (@c.us or @lid)
    is_private = chat_id.endswith('@c.us') or chat_id.endswith('@lid')
    if not is_private:
        return True

    # 3. Skip if security exclusions apply
    # Exclude Bot Owner
    sender_num = sender_id.split('@')[0]
    if str(config.OWNER_ID) == sender_num:
        return True

    # Exclude From Me (Self Account / My own replies)
    if message.from_me:
        return True

    # Exclude Sudo Users
    if state.is_sudo(sender_id):
        return True

    # Exclude Whitelisted/Permitted Users
    if state.is_permitted(sender_id):
        return True

    # 3. Handle Violation
    logger.info(f"PM Protection triggered for {sender_id}")
    
    # Increment Warning Count
    warnings = state.state["pm_warnings"].get(sender_id, 0) + 1
    state.state["pm_warnings"][sender_id] = warnings
    # Note: StateManager could be improved to handle this increment and save automatically, 
    # but for now we manually call save or just use the transient memory.
    # Actually, state.save() background tasks everything.
    from utils.database import db
    import asyncio
    asyncio.create_task(db.set("pm_warnings", state.state["pm_warnings"]))

    if warnings > config.PM_WARN_LIMIT:
        await smart_reply(message, f" 🚫 *Automatic Block:* You have exceeded the warning limit ({config.PM_WARN_LIMIT}).")
        try:
            # We use the bridge call directly if client doesn't have a high-level block
            await client.bridge.call("blockContact", {"contactId": sender_id})
            logger.warning(f"Blocked user {sender_id} due to PM protection violation.")
        except Exception as e:
            logger.error(f"Failed to block user {sender_id}: {e}")
        return False

    # Issue Warning
    pm_name = await get_contact_name(client, sender_id)
    warning_text = (
        f"🛡️ *PM Protection Active*\n\n"
        f"Hello *{pm_name}*, I do not accept private messages unless approved by my owner.\n\n"
        f"⚠️ *Warning:* {warnings}/{config.PM_WARN_LIMIT}\n"
        f"Please wait for my owner to approve you. Further messages may result in an automatic block."
    )
    await smart_reply(message, warning_text)
    return False
