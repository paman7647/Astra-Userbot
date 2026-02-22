# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *

@astra_command(
    name="afk",
    description="Set AFK status.",
    category="General",
    aliases=[],
    usage="[reason] (optional; e.g. 'dinner')",
    owner_only=True
)
async def afk_handler(client: Client, message: Message):
    """Set AFK status."""
    try:
        args_list = extract_args(message)
        
        from utils.state import state
        reason = " ".join(args_list) if args_list else "I'm busy right now."
        state.set_afk(True, reason)
        await smart_reply(message, f" 🌙 *AFK Mode Enabled*\n*Reason:* {reason}")
    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command afk failed')

@Client.on_message(Filters.all & Filters.me)
async def afk_off_handler(client: Client, message: Message):
    """Automatically disable AFK when owner sends a message."""
    try:
        from utils.state import state
        if state.get_afk()["is_afk"]:
            state.set_afk(False)
            await smart_reply(message, " *Welcome back! AFK mode disabled automatically.*")
    except Exception:
        pass

@Client.on_message(Filters.all & ~Filters.me)
async def afk_mention_responder(client: Client, message: Message):
    """Responds to mentions or DMs when the owner is AFK."""
    try:
        from utils.state import state
        afk_state = state.get_afk()
        if not afk_state["is_afk"]:
            return
            
        is_tagged = False
        me = await client.get_me()
        my_num = str(me.id).split('@')[0]
        
        if f"@{my_num}" in (message.body or ""):
            is_tagged = True
            
        if not message.is_group or is_tagged:
            await smart_reply(message, f" *I am currently AFK*\n\n*Reason:* {afk_state['reason']}")
    except Exception:
        pass
