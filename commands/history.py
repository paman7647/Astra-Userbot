"""
History Utility: Fetch Range
---------------------------
Experimental tool for range-based message retrieval.
- Fetch: Retrieves messages after a specific quoted message.
"""

import time

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="fetch",
    description="Fetch message history starting from a replied-to message.",
    category="Tools & Utilities",
    aliases=["history", "dump"],
    usage="<limit/reply> (e.g. 10 or reply to a message)",
    is_public=True,
)
async def fetch_history_handler(client: Client, message: Message):
    """
    Fetches all messages in the chat *after* the replied message.
    """
    args = extract_args(message)
    limit = int(args[0]) if args and args[0].isdigit() else 10

    # Start ID is the quoted message (optional)
    anchor_id = message.quoted.id if message.quoted else message.quoted_message_id

    status_msg = await edit_or_reply(
        message, f" ⏳ *Fetching {'latest ' if not anchor_id else ''}{limit} messages...*"
    )

    target_chat = message.chat_id.serialized if hasattr(message.chat_id, "serialized") else str(message.chat_id)

    # Directional support: Default to 'before' for anchorless (history)
    # or if 'before' is explicitly mentioned. Otherwise 'after' for anchors.
    direction = "before" if "before" in message.body.lower() or not anchor_id else "after"

    # Use our new direction capability and anchor control
    history = await client.chat.fetch_messages(
        target_chat, limit=limit, message_id=anchor_id, direction=direction, include_anchor=True
    )

    if not history:
        time.sleep(0.5)
        return await status_msg.edit(
            f" ❌ No messages found {direction} the specified anchor. Check bridge logs for details."
        )

    anchor_label = anchor_id[-8:] if anchor_id else "Latest"
    header = f"📜 **History from `{anchor_label}`**\n"
    header += f"📍 *Found {len(history)} messages*\n\n"

    lines = []
    for msg in history:
        sender = "Me" if msg.from_me else await get_contact_name(client, msg.sender)
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

    time.sleep(0.5)
    await status_msg.edit(final_content)
