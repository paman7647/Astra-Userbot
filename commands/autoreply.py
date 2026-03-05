from utils.database import db

from . import *


@astra_command(
    name="setreply",
    description="Set an automated reply for a keyword.",
    category="Tools & Utilities",
    usage="<keyword> | <response>",
    owner_only=True,
)
async def setreply_handler(client: Client, message: Message):
    """Adds a new auto-reply trigger."""
    args = extract_args(message)
    if not args or "|" not in message.body:
        return await edit_or_reply(message, "❌ **Usage:** `.setreply keyword | your response`")

    parts = message.body.split(".setreply", 1)[1].split("|", 1)
    keyword = parts[0].strip().lower()
    response = parts[1].strip()

    if not keyword or not response:
        return await edit_or_reply(message, "❌ Invalid keyword or response.")

    await db.set(f"autoreply:{keyword}", response)
    await edit_or_reply(
        message, f"✅ **Auto-Reply Set**\n━━━━━━━━━━━━━━━━━━━━\nTrigger: `{keyword}`\nResponse: `{response}`"
    )


@astra_command(
    name="delreply",
    description="Delete an automated reply.",
    category="Tools & Utilities",
    usage="<keyword>",
    owner_only=True,
)
async def delreply_handler(client: Client, message: Message):
    """Removes an auto-reply trigger."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.delreply keyword`")

    keyword = args[0].lower()
    await db.delete(f"autoreply:{keyword}")
    await edit_or_reply(message, f"✅ **Auto-Reply Deleted:** `{keyword}`")


@astra_command(
    name="listreply", description="List all active auto-replies.", category="Tools & Utilities", is_public=True
)
async def listreply_handler(client: Client, message: Message):
    """Lists all triggers."""
    replies = await db.get_all_with_prefix("autoreply:")

    if not replies:
        return await edit_or_reply(message, "📝 **Auto-Reply Registry**\n━━━━━━━━━━━━━━━━━━━━\n*No triggers found.*")

    text = "📝 **Auto-Reply Registry**\n━━━━━━━━━━━━━━━━━━━━\n"
    for key, val in replies.items():
        kw = key.replace("autoreply:", "")
        text += f"• `{kw}` → {val[:50]}...\n"

    await edit_or_reply(message, text)


# --- WATCHER ---
# Note: In Astra Userbot, global listeners are often registered in bot.py
# or via a specific 'watcher' pattern. If the bot.py handles message events,
# we would hook into it here or via plugin_utils logic.
# For now, we define the logic; registration happens in the framework's core loop.
async def autoreply_watcher(client: Client, message: Message):
    """Scans incoming messages for auto-reply triggers."""
    if message.chat_id.serialized.endswith("@broadcast"):
        return  # Ignore status

    text = message.body.lower()
    replies = await db.get_all_with_prefix("autoreply:")

    for key, response in replies.items():
        keyword = key.replace("autoreply:", "")
        if f" {keyword} " in f" {text} " or text == keyword:
            await client.send_message(message.chat_id, response, reply_to=message.id)
            break
