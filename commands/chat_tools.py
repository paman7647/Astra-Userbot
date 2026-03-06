"""Chat and contact tools using the new Astra v3 API."""

import asyncio

from . import *
from utils.helpers import edit_or_reply, edit_or_reply


@astra_command(
    name="pinchat",
    description="Pin or unpin the current chat.",
    category="Tools & Utilities",
    aliases=["unpin"],
    usage="[unpin]",
    owner_only=True,
)
async def pinchat_handler(client: Client, message: Message):
    """Pins or unpins a chat."""
    args = extract_args(message)
    api = client.api
    unpin = (args and args[0].lower() == "unpin") or message.text.split()[0].lower().endswith("unpin")

    try:
        if unpin:
            await api.pin_chat(message.chat_id, pin=False)
            await edit_or_reply(message, "📌 Chat unpinned.")
        else:
            result = await api.pin_chat(message.chat_id, pin=True)
            if result:
                await edit_or_reply(message, "📌 Chat pinned.")
            else:
                await edit_or_reply(message, "⚠️ Max pinned chats reached (3). Unpin one first.")
    except Exception as e:
        await edit_or_reply(message, f"❌ Failed: {e}")


@astra_command(
    name="clearchat",
    description="Clear all messages from the current chat.",
    category="Tools & Utilities",
    usage="",
    owner_only=True,
)
async def clearchat_handler(client: Client, message: Message):
    """Clears all messages in the current chat."""
    status = await edit_or_reply(message, "🗑️ Clearing chat...")
    try:
        await client.api.clear_chat(message.chat_id)
        await status.edit("✅ Chat cleared.")
    except Exception as e:
        await status.edit(f"❌ Failed: {e}")


@astra_command(
    name="delchat",
    description="Delete the current chat entirely.",
    category="Tools & Utilities",
    usage="",
    owner_only=True,
)
async def delchat_handler(client: Client, message: Message):
    """Deletes the current chat."""
    try:
        await client.api.delete_chat(message.chat_id)
    except Exception as e:
        await edit_or_reply(message, f"❌ Failed: {e}")


@astra_command(
    name="numcheck",
    description="Check if a phone number is on WhatsApp.",
    category="Tools & Utilities",
    aliases=["iswa", "check"],
    usage="<number> (e.g. .numcheck 919876543210)",
    is_public=True,
)
async def numcheck_handler(client: Client, message: Message):
    """Checks if a number is registered on WhatsApp."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.numcheck <number>`")

    number = args[0].replace("+", "").replace(" ", "")
    status = await edit_or_reply(message, f"🔍 Checking {number}...")

    try:
        result = await client.api.get_number_id(number)
        if result:
            wid = result.get("_serialized", result.get("user", number))
            await status.edit(f"✅ **{number}** is on WhatsApp.\nWID: `{wid}`")
        else:
            await status.edit(f"❌ **{number}** is **not** on WhatsApp.")
    except Exception as e:
        await status.edit(f"❌ Error: {e}")


@astra_command(
    name="commongroups",
    description="Get common groups with a contact.",
    category="Tools & Utilities",
    aliases=["cgroups", "mutual"],
    usage="<@user or number>",
    owner_only=True,
)
async def commongroups_handler(client: Client, message: Message):
    """Shows groups you share with a contact."""
    args = extract_args(message)
    contact_id = None

    if message.has_quoted_msg and message.quoted:
        contact_id = message.quoted.sender
    elif args:
        num = args[0].replace("@", "").replace("+", "")
        contact_id = f"{num}@c.us"

    if not contact_id:
        return await edit_or_reply(message, "⚠️ Reply to a user or provide a number.")

    status = await edit_or_reply(message, "🔍 Finding common groups...")

    try:
        groups = await client.api.get_common_groups(contact_id)
        if not groups:
            return await status.edit(f"📋 No common groups with {contact_id.split('@')[0]}.")

        text = f"📋 **Common Groups ({len(groups)}):**\n\n"
        for g in groups[:15]:
            gid = g if isinstance(g, str) else str(g)
            text += f"• `{gid}`\n"
        if len(groups) > 15:
            text += f"\n_...and {len(groups) - 15} more_"
        await status.edit(text)
    except Exception as e:
        await status.edit(f"❌ Error: {e}")


@astra_command(
    name="search",
    description="Search messages in this chat.",
    category="Tools & Utilities",
    aliases=["find"],
    usage="<query> (e.g. .search hello)",
    owner_only=True,
)
async def search_handler(client: Client, message: Message):
    """Searches messages matching a query."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.search <query>`")

    query = " ".join(args)
    status = await edit_or_reply(message, f"🔍 Searching for: _{query}_...")

    try:
        results = await client.api.search_messages(query, chat_id=message.chat_id, limit=10)
        if not results:
            return await status.edit(f"📋 No messages found for: _{query}_")

        text = f"📋 **Search Results ({len(results)}):**\n\n"
        for msg in results[:10]:
            body = (msg.body or "")[:60]
            sender = str(getattr(msg, 'sender', '')).split('@')[0]
            text += f"• [{sender}] {body}\n"

        await status.edit(text)
    except Exception as e:
        await status.edit(f"❌ Error: {e}")


@astra_command(
    name="presence",
    description="Set your online/offline presence.",
    category="Tools & Utilities",
    aliases=["online", "offline"],
    usage="<on|off>",
    owner_only=True,
)
async def presence_handler(client: Client, message: Message):
    """Toggles online/offline presence."""
    args = extract_args(message)
    cmd = message.text.split()[0][1:].lower() if message.text else ""

    if cmd == "online" or (args and args[0].lower() in ("on", "online", "available")):
        available = True
    elif cmd == "offline" or (args and args[0].lower() in ("off", "offline", "unavailable")):
        available = False
    else:
        return await edit_or_reply(message, "⚠️ **Usage:** `.presence <on|off>`")

    try:
        await client.api.send_presence(available)
        state = "online" if available else "offline"
        await edit_or_reply(message, f"✅ Presence set to **{state}**.")
    except Exception as e:
        await edit_or_reply(message, f"❌ Failed: {e}")


@astra_command(
    name="archive",
    description="Archive the current chat.",
    category="Tools & Utilities",
    usage="",
    owner_only=True,
)
async def archive_handler(client: Client, message: Message):
    """Archives the current chat."""
    try:
        await client.api.archive_chat(message.chat_id)
        await edit_or_reply(message, "📦 Chat archived.")
    except Exception as e:
        await edit_or_reply(message, f"❌ Failed: {e}")


@astra_command(
    name="forward",
    description="Forward a message to another chat.",
    category="Tools & Utilities",
    aliases=["fwd"],
    usage="<chat_id> (reply to message)",
    owner_only=True,
)
async def forward_handler(client: Client, message: Message):
    """Forwards a replied message to another chat."""
    if not message.has_quoted_msg:
        return await edit_or_reply(message, "⚠️ Reply to a message to forward it.")

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "⚠️ **Usage:** `.forward <chat_id>` (reply to msg)")

    target = args[0]
    if not ("@c.us" in target or "@g.us" in target):
        target = f"{target}@c.us"

    try:
        await client.api.forward_message(target, message.quoted.id)
        await edit_or_reply(message, f"↗️ Forwarded to `{target.split('@')[0]}`")
    except Exception as e:
        await edit_or_reply(message, f"❌ Failed: {e}")


@astra_command(
    name="profilepic",
    description="Get a contact's profile picture URL.",
    category="Tools & Utilities",
    aliases=["pfp", "dp"],
    usage="[@user or reply]",
    is_public=True,
)
async def profilepic_handler(client: Client, message: Message):
    """Gets profile picture URL of a user."""
    contact_id = None

    if message.has_quoted_msg and message.quoted:
        contact_id = message.quoted.sender
    else:
        args = extract_args(message)
        if args:
            num = args[0].replace("@", "").replace("+", "")
            contact_id = f"{num}@c.us"
        else:
            contact_id = message.chat_id

    try:
        url = await client.api.get_profile_pic_url(contact_id)
        if url:
            await edit_or_reply(message, f"🖼️ **Profile Picture:**\n{url}")
        else:
            await edit_or_reply(message, "❌ Profile picture not available (privacy or not set).")
    except Exception as e:
        await edit_or_reply(message, f"❌ Error: {e}")
