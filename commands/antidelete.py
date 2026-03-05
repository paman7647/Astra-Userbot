import logging

from utils.database import db

from . import *
from utils.helpers import edit_or_reply

logger = logging.getLogger("Plugins.AntiDelete")


@astra_command(
    name="antidelete", description="Toggle Anti-Delete engine.", category="Owner", usage="<on/off>", owner_only=True
)
async def antidelete_toggle_handler(client: Client, message: Message):
    """Toggles the Anti-Delete engine."""
    args = extract_args(message)
    if not args:
        current = await db.get("antidelete_status") or "off"
        return await edit_or_reply(
            message,
            f"🛡️ **Anti-Delete Engine**\n━━━━━━━━━━━━━━━━━━━━\nStatus: `{'Enabled' if current == 'on' else 'Disabled'}`\n\nUsage: `.antidelete on` to enable.",
        )

    status = args[0].lower()
    if status not in ["on", "off"]:
        return await edit_or_reply(message, "❌ Use `on` or `off`.")

    await db.set("antidelete_status", status)
    await edit_or_reply(message, f"✅ **Anti-Delete Engine** turned `{status.upper()}`.")


# --- ENGINE LOGIC ---
# This part requires hooking into the framework's message_revoke event.
# In a standard Astra implementation, this would be:
# @client.on("message_revoke")
async def antidelete_revoked_handler(client: Client, message: Message, revoked_msg: Message):
    """
    Handles revoked (deleted for everyone) messages.
    Logs the content to the owner's chat.
    """
    status = await db.get("antidelete_status") or "off"
    if status != "on":
        return

    try:
        sender = await get_contact_name(client, revoked_msg.sender)
        chat_name = "Private Chat"
        if str(revoked_msg.chat_id).endswith("@g.us"):
            chat_info = await client.group.get_info(revoked_msg.chat_id)
            chat_name = chat_info.subject

        log_text = (
            f"🛡️ **ASTRA ANTI-DELETE**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **From:** `{sender}`\n"
            f"🏢 **Chat:** `{chat_name}`\n"
            f"🕒 **Time:** `{revoked_msg.timestamp}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 **Message Content:**\n{revoked_msg.body or '📦 Media Content'}\n"
        )

        owner_id = client.session_id  # Or resolve from config
        # Sending to owner's own chat as a log
        await client.send_message(message.chat_id, log_text)

        # If it's media, we'd ideally have it cached in temp/ or a dedicated AntiDelete cache
        # For MVP, we log the text.
    except Exception as e:
        logger.error(f"Anti-Delete failed to log: {e}")


# Note: Registration of 'message_revoke' listener must be supported by the host.
