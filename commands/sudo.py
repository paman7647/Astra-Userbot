"""
Administrative Privilege Management
---------------------------------
Commands for the bot owner to manage sudo (authorized) users.
Sudo users can execute most bot commands but cannot manage other sudo users.
"""

import asyncio

from config import config
from utils.state import state

from . import *


@astra_command(
    name="sudo",
    description="Grant or revoke administrative (sudo) privileges for a user.",
    category="Owner",
    aliases=["promote", "demote"],
    usage="<add|rem> [reply or user_id] (e.g. .sudo add @1234567890)",
    owner_only=True,
)
async def sudo_handler(client: Client, message: Message):
    """
    Manages the sudo user registry. Supports direct JID input or
    replying to a user's message for quick assignment.
    """
    args_list = extract_args(message)

    # 1. Resolve Target User ID
    target_uid = None

    # Scenario A: Reply to a message
    if message.has_quoted_msg:
        # quoted_participant is a JID object
        if message.quoted and message.quoted.sender:
            target_uid = message.quoted.sender.serialized

    # Scenario B: Manual ID provided in arguments
    if not target_uid and len(args_list) >= 2:
        target_uid = args_list[1].strip()
        if not target_uid.endswith("@c.us"):
            target_uid = f"{target_uid}@c.us"

    # 2. Validation
    if not target_uid:
        return await edit_or_reply(
            message,
            " 📋 **Sudo Management Utility**\n\n"
            f"**Usage:** `{config.PREFIX}sudo <add|rem>` (as reply)\n"
            f"**Manual:** `{config.PREFIX}sudo <add|rem> 910000000000`",
        )

    action = args_list[0].lower() if args_list else "add"

    # Prevent self-sudo (not needed)
    me = await client.get_me()
    if target_uid == me.id.serialized:
        return await edit_or_reply(message, " 🤖 The bot account always has implicit sudo privileges.")

    # 3. Execution
    if action in ["add", "promote"]:
        if state.is_sudo(target_uid):
            return await edit_or_reply(message, f" ℹ️ `{target_uid}` is already in the sudo registry.")

        state.add_sudo(target_uid)
        await edit_or_reply(
            message, f" 🛡️ **Privileges Granted!**\nUser `{target_uid}` can now execute administrative commands."
        )

    elif action in ["rem", "remove", "demote"]:
        if not state.is_sudo(target_uid):
            return await edit_or_reply(message, f" ❌ `{target_uid}` is not a registered sudo user.")

        # Update state memory
        state.state["sudo_users"].remove(target_uid)
        # Persist change
        await asyncio.to_thread(state.save)

        await edit_or_reply(
            message, f" 🗑️ **Privileges Revoked.**\nUser `{target_uid}` removed from the sudo registry."
        )

    else:
        await edit_or_reply(message, f" ❌ Unrecognized action: `{action}`. Use `add` or `rem`.")
