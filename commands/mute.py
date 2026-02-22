# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
from utils.state import state

@astra_command(
    name="mute",
    description="Mute or unmute group notifications/commands (Bot internal)",
    category="Group",
    aliases=["unmute"],
    usage="<on|off> (enable or disable mute)",
    owner_only=False
)
async def mute_handler(client: Client, message: Message):
    """Mute or unmute group notifications/commands (Bot internal)"""
    try:
        args_list = extract_args(message)
        
        is_group = message.chat_id.endswith('@g.us')
        if not is_group:
            return await smart_reply(message, " ❌ This command only works in groups.")

        action = args_list[0].lower() if args_list else ("on" if message.body.lower().startswith(".mute") else "off")

        is_muted = action in ["on", "mute"]

        # Store in state
        gid = message.chat_id
        if "group_configs" not in state.state: state.state["group_configs"] = {}
        if gid not in state.state["group_configs"]: state.state["group_configs"][gid] = {}

        state.state["group_configs"][gid]["muted"] = is_muted
        await state.save()

        await smart_reply(message, f" 🤫 Group commands are now *{'MUTED' if is_muted else 'UNMUTED'}* for this group.")
    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command mute failed')
