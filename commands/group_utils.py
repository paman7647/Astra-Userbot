import asyncio
import random

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="pick",
    description="Pick a random user from the group.",
    category="Group Management",
    aliases=["randomuser"],
    usage="",
    is_public=True,
)
async def pick_handler(client: Client, message: Message):
    """Random user picker."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "❌ Groups only.")

    status_msg = await edit_or_reply(message, "🎲 **Rolling the dice...**")

    info = await client.group.get_info(message.chat_id)
    participants = info.participants
    if not participants:
        return await status_msg.edit("❌ No participants found.")

    winner = random.choice(participants)
    winner_id = str(winner.id).split("@")[0]

    await status_msg.edit(f"🎉 **Lucky Winner:** @{winner_id}", mentions=[str(winner.id)])


@astra_command(
    name="tagall",
    description="Tag everyone in the group in batches.",
    category="Group Management",
    usage="",
    is_public=True,
)
async def tagall_handler(client: Client, message: Message):
    """Batched tagging to avoid spam flags."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "❌ Groups only.")

    status_msg = await edit_or_reply(message, "📣 **Preparing batched notification...**")

    info = await client.group.get_info(message.chat_id)
    participants = info.participants
    if not participants:
        return await status_msg.edit("❌ No participants found.")

    batch_size = 5
    total = len(participants)
    await status_msg.edit(f"📣 **Tagging {total} members in batches...**")

    for i in range(0, total, batch_size):
        batch = participants[i : i + batch_size]
        mentions = [str(p.id) for p in batch]
        text = "📣 **Group Notification:**\n"
        for p in batch:
            text += f"• @{str(p.id).split('@')[0]}\n"

        await client.send_message(message.chat_id, text, mentions=mentions)
        await asyncio.sleep(1.5)

    await status_msg.delete()


@astra_command(
    name="tagadmin",
    description="Tag all group admins.",
    category="Group Management",
    aliases=["admins"],
    usage="",
    is_public=True,
)
async def tagadmin_handler(client: Client, message: Message):
    """Admin tagger."""
    if not str(message.chat_id).endswith("@g.us"):
        return await edit_or_reply(message, "❌ Groups only.")

    status_msg = await edit_or_reply(message, "🛡️ **Calling all admins...**")

    info = await client.group.get_info(message.chat_id)
    admins = [p.id for p in info.participants if p.is_admin or p.is_super_admin]

    if not admins:
        return await status_msg.edit("❌ No admins found.")

    text = "🛡️ **Group Administrators:**\n\n"
    for adm in admins:
        text += f"• @{str(adm).split('@')[0]}\n"

    await client.send_message(message.chat_id, text, mentions=[str(a) for a in admins])
    await status_msg.delete()


@astra_command(
    name="sd",
    description="Send a self-destructing message.",
    category="Tools & Utilities",
    aliases=["selfdestruct"],
    usage="<seconds> <text> (e.g. .sd 5 secret)",
    owner_only=True,
)
async def sd_handler(client: Client, message: Message):
    """Self-destructing message."""
    args = extract_args(message)
    if len(args) < 2:
        return await edit_or_reply(message, "❌ **Usage:** `.sd <seconds> <text>`")

    try:
        timer = int(args[0])
        text = " ".join(args[1:])
    except ValueError:
        return await edit_or_reply(message, "❌ Seconds must be a number.")

    await message.delete()  # Remove the command

    sent_msg = await client.send_message(message.chat_id, f"🕒 **Destructing in {timer}s:**\n\n{text}")

    await asyncio.sleep(timer)
    try:
        await client.chat.delete_messages(message.chat_id, [sent_msg.id])
    except:
        pass
