# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *

@astra_command(
    name="setprefix",
    description="Change the command prefix.",
    category="System",
    aliases=[],
    usage="<new_prefix> (e.g. !)",
    owner_only=True
)
async def setprefix_handler(client: Client, message: Message):
    """Change the command prefix."""
    try:
        args_list = extract_args(message)
        
        if not args_list:
            return await smart_reply(message, f" ⚠️ Please provide a new prefix. Example: `.setprefix !`")
    
        new_prefix = args_list[0]
        if len(new_prefix) > 2:
            return await smart_reply(message, " ❌ Prefix must be 1 or 2 characters long.")
        
        from utils.state import state
        state.set_prefix(new_prefix)
        await smart_reply(message, f" ✅ Prefix updated to `{new_prefix}` successfully!")
    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command setprefix failed')
