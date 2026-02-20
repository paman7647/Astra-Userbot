# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
History Utility: Fetch Range
---------------------------
Experimental tool for range-based message retrieval.
- Fetch: Retrieves messages after a specific quoted message.
"""

from . import *
import asyncio

@astra_command(
    name="fetch",
    description="Fetch message history starting from a replied-to message.",
    category="Utility",
    aliases=["history", "dump"],
    usage="<limit/reply>",
    is_public=True
)
async def fetch_history_handler(client: Client, message: Message):
    """
    Fetches all messages in the chat *after* the replied message.
    """
    try:
        args = extract_args(message)
        limit = int(args[0]) if args and args[0].isdigit() else 10
        
        # Start ID is the quoted message (optional)
        anchor_id = message.quoted_message_id
        
        status_msg = await smart_reply(message, f" ⏳ *Fetching {'latest ' if not anchor_id else ''}{limit} messages...*")
        
        target_chat = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)
        
        # Directional support: Default to 'before' for anchorless (history)
        # or if 'before' is explicitly mentioned. Otherwise 'after' for anchors.
        direction = 'before' if "before" in message.body.lower() or not anchor_id else 'after'
        
        # Use our new direction capability
        history = await client.fetch_messages(
            target_chat, 
            limit=limit, 
            message_id=anchor_id,
            direction=direction
        )
        
        if not history:
            return await status_msg.edit(f" ❌ No messages found {direction} the specified anchor. Check bridge logs for details.")
            
        anchor_label = anchor_id[-8:] if anchor_id else "Latest"
        header = f"📜 **History from `{anchor_label}`**\n"
        header += f"📍 *Found {len(history)} messages*\n\n"
        
        lines = []
        for msg in history:
            sender = "Me" if msg.from_me else (msg.sender.user[:8] if msg.sender else "Unknown")
            body = msg.body or f"<{msg.type.name} Media>"
            
            # Clean up body for display
            display_body = body.replace("\n", " ").strip()
            if len(display_body) > 60:
                display_body = display_body[:57] + "..."
                
            lines.append(f"▫️ `{sender}`: {display_body}")
            
        # Combine with length awareness
        final_content = header + "\n".join(lines)
        
        if len(final_content) > 3500:
            final_content = final_content[:3400] + "\n\n... (Content too long, truncated)"

        await status_msg.edit(final_content)

    except Exception as e:
        await report_error(client, e, context='Fetch history command failure')
