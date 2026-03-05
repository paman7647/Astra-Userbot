from . import *


@astra_command(
    name="setprefix",
    description="Change the command prefix.",
    category="Owner",
    aliases=[],
    usage="<new_prefix> (e.g. !)",
    owner_only=True,
)
async def setprefix_handler(client: Client, message: Message):
    """Change the command prefix."""
    args_list = extract_args(message)

    if not args_list:
        return await edit_or_reply(message, " ⚠️ Please provide a new prefix. Example: `.setprefix !`")

    new_prefix = args_list[0]
    if len(new_prefix) > 2:
        return await edit_or_reply(message, " ❌ Prefix must be 1 or 2 characters long.")

    from utils.state import state

    state.set_prefix(new_prefix)
    await edit_or_reply(message, f" ✅ Prefix updated to `{new_prefix}` successfully!")
