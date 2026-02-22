# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *

@astra_command(
    name="id",
    description="Description: Retrieve unique identifiers for chats, users, and quoted messages.\nSyntax: .id [reply]\nExample: .id",
    category="Utility",
    aliases=["info", "whois"],
    usage=".id (reply to message to inspect its IDs)",
    is_public=True
)
async def id_handler(client: Client, message: Message):
    """Renders a detailed identity card with JID information."""
    try:
        chat_id = message.chat_id
        sender_id = message.sender_id
        
        # Resolve names (Core logic preserved)
        chat_name = "Unknown"
        chat_type = "Chat"
        try:
            chat_entity = await client.get_entity(chat_id)
            chat_name = getattr(chat_entity, 'title', "Unknown")
            if getattr(chat_entity, 'is_group', False):
                chat_type = "Group"
        except Exception:
            pass

        sender_name = await get_contact_name(client, sender_id)
        reply_info = ""

        if message.has_quoted_msg and message.quoted.sender:
            target_jid = message.quoted.sender
            target_name = await get_contact_name(client, target_jid)
            reply_info = f"\n👤 **Target:** {target_name}\n🆔 **Target ID:** `{target_jid}`"

        # Professional Layout
        info_text = (
            "🆔 **ASTRA IDENTITY CARD** 🆔\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 **{chat_type}:** `{chat_name}`\n"
            f"🆔 **{chat_type} ID:** `{chat_id}`\n\n"
            f"👤 **Sender:** `{sender_name}`\n"
            f"🆔 **Sender ID:** `{sender_id}`"
            f"{reply_info}\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        await smart_reply(message, info_text)

    except Exception as e:
        await report_error(client, e, context='ID command failure')
