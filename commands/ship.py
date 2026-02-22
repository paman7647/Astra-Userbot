# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Social Utility: Ship Compatibility
----------------------------------
Calculates the "love compatibility" between two users with a playful rating.
Supports manual JID input, mentions, or replies.
"""

import random
from . import *

@astra_command(
    name="ship",
    description="Check the compatibility match between two souls.",
    category="Fun/Lite",
    aliases=["match", "love"],
    usage="[@user1] [@user2] (e.g. .ship @alice @bob)",
    is_public=True
)
async def ship_handler(client: Client, message: Message):
    """
    Executes the compatibility calculation and renders a clean report card.
    """
    try:
        args_list = extract_args(message)
        
        user1 = "Astra User"
        user2 = "Target User"

        # 1. Resolve Targets
        if len(args_list) >= 2:
            user1 = args_list[0]
            user2 = args_list[1]
        elif len(args_list) == 1:
            me = await client.get_me()
            user1 = await get_contact_name(client, me.id)
            user2 = await get_contact_name(client, args_list[0])
        elif message.has_quoted_msg:
            me = await client.get_me()
            user1 = await get_contact_name(client, me.id)
            quoted = message.quoted
            target_jid = quoted.sender or quoted.chat_id
            user2 = await get_contact_name(client, target_jid)

        # 2. Logic & Branding
        percentage = random.randint(0, 100)
        
        if percentage > 90: 
            comment = "💍 **Perfect Match!** Future confirmed."
            emoji = "💖"
        elif percentage > 70: 
            comment = "❤️ **Amazing chemistry.**"
            emoji = "💕"
        elif percentage > 50: 
            comment = "🌚 **Potential.** Worth a try."
            emoji = "✨"
        elif percentage > 30: 
            comment = "🤷 **Friendzone.**"
            emoji = "🤝"
        else: 
            comment = "💀 **No compatibility.** Stay away."
            emoji = "🚫"

        # 3. Render
        report = (
            f"🛳️ **Astra Compatibility Ship** {emoji}\n\n"
            f"👤 *Mate 1:* `{user1}`\n"
            f"👤 *Mate 2:* `{user2}`\n\n"
            f"📊 **Score:** `{percentage}%`\n"
            f"💬 **Result:** {comment}"
        )

        await smart_reply(message, report)

    except Exception as e:
        await smart_reply(message, " ⚠️ Ship calculation failed.")
        await report_error(client, e, context='Ship command failure')
