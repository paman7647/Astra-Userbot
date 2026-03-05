from utils.state import state

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="mute",
    description="Mute or unmute group notifications/commands (Bot internal)",
    category="Group Management",
    aliases=["unmute"],
    usage="<on|off> (enable or disable mute)",
    owner_only=False,
)
async def mute_handler(client: Client, message: Message):
    """Mute or unmute group notifications/commands (Bot internal)"""
    args_list = extract_args(message)

    is_group = str(message.chat_id).endswith("@g.us")
    if not is_group:
        return await edit_or_reply(message, " ❌ This command only works in groups.")

    action = args_list[0].lower() if args_list else ("on" if message.body.lower().startswith(".mute") else "off")

    is_muted = action in ["on", "mute"]

    # Store in state
    gid = message.chat_id
    if "group_configs" not in state.state:
        state.state["group_configs"] = {}
    if gid not in state.state["group_configs"]:
        state.state["group_configs"][gid] = {}

    state.state["group_configs"][gid]["muted"] = is_muted
    await state.save()

    await edit_or_reply(message, f" 🤫 Group commands are now *{'MUTED' if is_muted else 'UNMUTED'}* for this group.")
