# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Moderation Utility: Purge
--------------------------
Efficient message range deletion.
"""

import asyncio
import time
import logging
from . import *

logger = logging.getLogger("Astra.Purge")

@astra_command(
    name="del",
    description="Delete the replied message.",
    category="Moderation",
    aliases=["delete", "d"],
    usage="(reply)",
    owner_only=True
)
async def delete_handler(client: Client, message: Message):
    """
    .del (reply) -> deletes the replied message.
    """
    try:
        if not message.has_quoted_msg:
             return await smart_reply(message, " ⚠️ Reply to a message to delete it.")

        # Use the message object itself for deletion
        # This is more robust as it uses the message's internal client
        if message.quoted_message:
            await message.quoted_message.delete(for_everyone=True)
        else:
            await client.chat.delete_message(message.quoted_message_id, everyone=True)
            
        await message.delete()

    except Exception as e:
        await smart_reply(message, f" ❌ Failed to delete: {str(e)}")

@astra_command(
    name="purge",
    description="Deletes ALL messages starting from the replied-to message forward.",
    category="Moderation",
    usage="<limit/reply>",
    owner_only=True
)
async def purge_handler(client: Client, message: Message):
    """
    .purge (reply) -> deletes all messages from that point forward.
    """
    if not message.has_quoted_msg:
        return await smart_reply(message, " 📋 **Purge Utility**\n\nReply to a message to start purging from there.")

    args = extract_args(message)
    limit = int(args[0]) if args and args[0].isdigit() else 100
    
    status_msg = await smart_reply(message, f" ⏳ *Initializing Purge...* (limit: {limit})")
    
    try:
        target_chat = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
        
        # Fetch range after the quoted one
        history = await client.fetch_messages(
            target_chat,
            limit=limit,
            message_id=message.quoted_message_id,
            direction='after'
        )

        if not history:
            await status_msg.delete()
            return await smart_reply(message, " ✅ **Purge Complete** (No new messages found in range)")

        # Prepare bulk deletion list
        msg_ids = [m.id for m in history if m.type.name not in ["REVOKED", "GP2", "UNKNOWN"]]
        
        if not msg_ids:
             await status_msg.delete()
             return await smart_reply(message, " ✅ **Purge Complete** (No deletable messages found)")
             
        time.sleep(0.5)
        # Instead of edit, delete old and send new via smart_reply for better stability
        await status_msg.delete()
        status_msg = await smart_reply(message, f" ⏳ *Executing Bulk Purge...* (`{len(msg_ids)}` messages)")
        
        # Call the new bulk delete method (one round-trip!)
        result = await client.chat.bulk_delete(msg_ids, everyone=True)
        
        count = result.get("total", len(msg_ids))
        time.sleep(0.5)
        
        await status_msg.delete()
        final_msg = await smart_reply(message, f" ✅ **Purge Successful**\n`{count}` messages cleared.")
        
        await asyncio.sleep(3)
        await final_msg.delete()
        await message.delete()
        
    except Exception as e:
        await report_error(client, e, context='Purge command failure')

@astra_command(
    name="purgeme",
    description="Deletes only YOUR messages starting from the replied-to message.",
    category="Moderation",
    usage="<limit/reply>",
    owner_only=True
)
async def purgeme_handler(client: Client, message: Message):
    """
    .purgeme (reply) -> deletes only bot's messages from that point forward.
    """
    if not message.has_quoted_msg:
        return await smart_reply(message, " 📋 **Self-Purge Utility**\n\nReply to a message to start purging your messages.")

    args = extract_args(message)
    limit = int(args[0]) if args and args[0].isdigit() else 100
    
    status_msg = await smart_reply(message, f" ⏳ *Self-purging up to {limit} messages...*")
    
    try:
        target_chat = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
        
        # Fetch only 'fromMe' history after the quoted ID
        history = await client.fetch_messages(
            target_chat,
            limit=limit,
            message_id=message.quoted_message_id,
            direction='after',
            from_me=True
        )

        if not history:
            await status_msg.delete()
            return await smart_reply(message, " ❌ No messages from you found in this range.")

        msg_ids = [m.id for m in history]
        
        time.sleep(0.5)
        await status_msg.delete()
        status_msg = await smart_reply(message, f" ⏳ *Executing Bulk Self-Purge...* (`{len(msg_ids)}` messages)")
        
        result = await client.chat.bulk_delete(msg_ids, everyone=True)
        count = result.get("total", len(msg_ids))

        time.sleep(0.5)
        await status_msg.delete()
        final_msg = await smart_reply(message, f" ✅ **Self-Purge Successful**\n`{count}` messages cleared.")
        
        await asyncio.sleep(3)
        await final_msg.delete()
        await message.delete()
        
    except Exception as e:
        await report_error(client, e, context='Purgeme command failure')
