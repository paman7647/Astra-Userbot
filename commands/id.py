# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Identity Utility: User & Chat Information
-----------------------------------------
Retrieves unique identifiers (IDs) for chats and users.
Essential for configuring permissions and debugging.
"""

import asyncio
from . import *

@astra_command(
    name="id",
    description="Get the current Chat ID and User ID.",
    category="Utility",
    aliases=["info", "whois"],
    usage="[reply]",
    is_public=True
)
async def id_handler(client: Client, message: Message):
    """
    Renders a detailed info card with Chat ID, User ID, and Sender info.
    """
    try:
        chat_id = message.chat_id
        sender_id = message.sender_id
        
        # Resolve Chat Name
        chat_name = "Unknown"
        chat_type = "Chat"
        try:
            chat_entity = await client.get_entity(chat_id, force=True)
            chat_name = chat_entity.title
            if getattr(chat_entity, 'is_group', False):
                chat_type = "Group"
        except: pass

        # Resolve Sender Name
        sender_name = "You"
        try:
            sender_entity = await client.get_entity(sender_id, force=True)
            if sender_entity.is_me:
                sender_name = f"You ({sender_entity.push_name or 'Astra User'})"
            else:
                sender_name = sender_entity.title
        except: pass

        reply_info = ""
        # Handle Quoted Reply
        if message.has_quoted_msg and message.quoted_participant:
            target_jid = message.quoted_participant
            target_name = "Target User"
            debug_meta = ""
            # Small grace period for asynchronous contact resolution to settle
            await asyncio.sleep(0.8)
            try:
                entity = await client.get_entity(target_jid, force=True)
                target_name = entity.title
                if entity.push_name:
                    debug_meta = f" (Pushname: {entity.push_name})"
                elif target_name == target_jid.user:
                    debug_meta = " (No name found)"
            except: pass
            
            reply_info = f"\n👤 **Target:** {target_name}{debug_meta}\n🆔 **Target ID:** `{target_jid}`\n"

        info_text = (
            "🆔 **Astra Identity Info**\n\n"
            f"🏠 **{chat_type}:** {chat_name}\n"
            f"🆔 **{chat_type} ID:** `{chat_id}`\n\n"
            f"👤 **Sender:** {sender_name}\n"
            f"🆔 **Sender ID:** `{sender_id}`\n"
            f"{reply_info}"
        )
        
        await smart_reply(message, info_text)

    except Exception as e:
        await report_error(client, e, context='ID command failure')
