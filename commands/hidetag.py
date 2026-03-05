from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="hidetag",
    description="Tag everyone in the group without showing mentioned text.",
    category="Group Management",
    aliases=["htag", "ghosttag"],
    usage="[message]",
    owner_only=True,
)
async def hidetag_handler(client: Client, message: Message):
    """Hidden group mentions."""
    try:
        if not str(message.chat_id).endswith("@g.us"):
            return await edit_or_reply(message, " ❌ This command only works in groups.")

        args_list = extract_args(message)
        text = " ".join(args_list) if args_list else "📢 *Attention Everyone!*"

        status_msg = await edit_or_reply(message, " 👻 *Preparing ghost tag...*")

        # 1. Fetch participants
        info = await client.group.get_info(message.chat_id)
        if not info or not info.participants:
            return await status_msg.edit(" ⚠️ Failed to fetch participants.")

        mentions = [str(p.id) for p in info.participants]

        # 2. Send message with full mentions list but clean text
        await client.send_message(message.chat_id, text, mentions=mentions)
        await status_msg.delete()

    except Exception as e:
        await edit_or_reply(message, f" ❌ Hidetag Error: {str(e)}")
