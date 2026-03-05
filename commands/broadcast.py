import asyncio

from . import *


@astra_command(
    name="bc", description="Broadcast a message to all your chats.", category="Owner", usage="<text>", owner_only=True
)
async def broadcast_handler(client: Client, message: Message):
    """Mass broadcast to all chats."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.bc <text>`")

    text = " ".join(args)
    status_msg = await edit_or_reply(
        message, "📡 **Astra Broadcast Engine**\n━━━━━━━━━━━━━━━━━━━━\n🔄 *Fetching chats and initializing...*"
    )

    all_chats = await client.chat.get_all_chats()
    total = len(all_chats) or 0
    success = 0
    failed = 0

    await status_msg.edit(
        f"📡 **Astra Broadcast Engine**\n━━━━━━━━━━━━━━━━━━━━\n📤 **Sending to {total} chats...**\n🚀 *Progress updates every 5 chats...*"
    )

    for i, chat in enumerate(all_chats):
        try:
            # Basic Spam Protection: 1.5s delay
            await asyncio.sleep(1.5)
            await client.send_message(chat.id, text)
            success += 1
        except:
            failed += 1

        if (i + 1) % 5 == 0:
            await status_msg.edit(
                f"📡 **Astra Broadcast Engine**\n━━━━━━━━━━━━━━━━━━━━\n📤 **Progress:** `{i + 1}/{total}`\n✅ **Sent:** `{success}`\n❌ **Failed:** `{failed}`"
            )

    await status_msg.edit(
        f"📡 **Astra Broadcast Complete**\n━━━━━━━━━━━━━━━━━━━━\n✅ **Success:** `{success}`\n❌ **Failed:** `{failed}`\n🕒 **Total Chats:** `{total}`"
    )


@astra_command(
    name="bcgc",
    description="Broadcast a message to all your groups.",
    category="Owner",
    usage="<text>",
    owner_only=True,
)
async def broadcast_gc_handler(client: Client, message: Message):
    """Mass broadcast to groups only."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.bcgc <text>`")

    text = " ".join(args)
    status_msg = await edit_or_reply(
        message, "🏢 **Astra Group Broadcast**\n━━━━━━━━━━━━━━━━━━━━\n🔄 *Filtering groups...*"
    )

    all_chats = await client.chat.get_all_chats()
    groups = [c for c in all_chats if str(c.id).endswith("@g.us")]
    total = len(groups)
    success = 0
    failed = 0

    if not groups:
        return await status_msg.edit("❌ No groups found.")

    await status_msg.edit(
        f"🏢 **Astra Group Broadcast**\n━━━━━━━━━━━━━━━━━━━━\n📤 **Sending to {total} groups...**"
    )

    for i, gc in enumerate(groups):
        try:
            await asyncio.sleep(2)  # Slower for groups
            await client.send_message(gc.id, text)
            success += 1
        except:
            failed += 1

        if (i + 1) % 3 == 0:
            await status_msg.edit(
                f"🏢 **Astra Group Broadcast**\n━━━━━━━━━━━━━━━━━━━━\n📤 **Progress:** `{i + 1}/{total}`\n✅ **Sent:** `{success}`"
            )

    await status_msg.edit(
        f"🏢 **Astra Group Broadcast Complete**\n━━━━━━━━━━━━━━━━━━━━\n✅ **Success:** `{success}`\n❌ **Failed:** `{failed}`\n🏢 **Total Groups:** `{total}`"
    )
