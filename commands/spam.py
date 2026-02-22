# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Spam Utility: Message Flooding
------------------------------
Repeatedly sends messages to a chat.
WARNING: Use with caution to avoid account bans.
"""

import asyncio
from . import *

@astra_command(
    name="spam",
    description="Flood the chat with messages.",
    category="Spam",
    aliases=[],
    usage="<count> <text> (e.g. .spam 5 hello)",
    owner_only=True # Safety: Only owner/sudo can spam
)
async def spam_handler(client: Client, message: Message):
    """
    Rapidly sends a specified number of messages.
    """
    try:
        args_list = extract_args(message)
        if len(args_list) < 2:
            return await smart_reply(message, " 📋 Usage: `.spam <count> <message>`")

        try:
            count = int(args_list[0])
            text = " ".join(args_list[1:])
        except ValueError:
            return await smart_reply(message, " ⚠️ Count must be a number.")

        if count > 100:
            return await smart_reply(message, " ⚠️ Safety Limit: Max 100 messages allowed.")

        await message.delete()

        for _ in range(count):
            await client.send_message(message.chat_id, text)
            await asyncio.sleep(0.1) # Slight delay to prevent immediate ban

    except Exception as e:
        await report_error(client, e, context='Spam command failure')


@astra_command(
    name="dspam",
    description="Flood the chat with delayed messages.",
    category="Spam",
    aliases=["delayspam"],
    usage="<delay_sec> <count> <text> (e.g. .dspam 1 5 hi)",
    owner_only=True
)
async def dspam_handler(client: Client, message: Message):
    """
    Sends messages with a specified delay interval.
    """
    try:
        args_list = extract_args(message)
        if len(args_list) < 3:
            return await smart_reply(message, " 📋 Usage: `.dspam <delay> <count> <message>`")

        try:
            delay = float(args_list[0])
            count = int(args_list[1])
            text = " ".join(args_list[2:])
        except ValueError:
            return await smart_reply(message, " ⚠️ Delay and Count must be numbers.")

        if count > 100:
            return await smart_reply(message, " ⚠️ Safety Limit: Max 100 messages allowed.")

        await message.delete()

        for _ in range(count):
            await client.send_message(message.chat_id, text)
            await asyncio.sleep(delay)

    except Exception as e:
        await report_error(client, e, context='DelaySpam command failure')
