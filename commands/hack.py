# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Fun Utility: Fake Hack
----------------------
Simulates a hacking sequence for entertainment purposes.
WARNING: This is purely visual and does not actually hack anything.
"""

import asyncio
import random
import time
from . import *

@astra_command(
    name="hack",
    description="Simulate a hacking attack on a user or chat.",
    category="Fun",
    aliases=["hacker"],
    usage="<target>",
    is_public=True
)
async def hack_handler(client: Client, message: Message):
    """
    Plays an animated sequence of "hacking" steps.
    """
    try:
        args_list = extract_args(message)
        target_name = "Target System"
        target_jid = None

        if args_list:
            input_target = " ".join(args_list)
            # Handle @number or raw number targets
            clean_target = input_target.replace("@", "").strip()
            if clean_target.isdigit() and len(clean_target) > 5:
                target_jid = f"{clean_target}@c.us"
                target_name = input_target
            else:
                target_name = input_target
        elif message.has_quoted_msg:
            if message.quoted_participant:
                target_jid = message.quoted_participant
                target_name = f"@{message.quoted_participant.user}"
            else:
                target_name = "Current Chat"

        # Resolve real name if JID available
        if target_jid:
            try:
                entity = await client.get_entity(target_jid)
                if entity:
                    target_name = entity.title
            except:
                pass

        status_msg = await smart_reply(message, f" 💻 *Initiating Hack on {target_name}...*")
        
        steps = [
            f" 🔍 *Scanning vulnerabilities on {target_name}...*",
            " 🔓 *Infiltrating local network...*",
            " ⚠️ *Firewall Detected! Attempting SQL Injection...*",
            " 🔑 *Bypassing Secure Firewall...* ✅",
            " ⚡ *Brute-forcing PIN...* `1234` ❌",
            " ⚡ *Brute-forcing PIN...* `0000` ❌",
            " ⚡ *Brute-forcing PIN...* `8888` ❌",
            f" 🔑 *Accessing {target_name}'s database...* ✅",
            f" 📂 *Downloading {target_name}'s Chat History...* `[24%]`",
            f" 📂 *Downloading {target_name}'s Chat History...* `[67%]`",
            f" 📂 *Downloading {target_name}'s Chat History...* `[99%]`",
            " 📂 *Download Complete.* ✅",
            f" 📸 *Accessing Camera...* `Success`",
            f" 📸 *Stealing Private Gallery of {target_name}...*",
            " 🤐 *Exporting Account Private Keys...*",
            " 💣 *Injecting Ransomware into System Root...*",
            " ☁️ *Uploading Data to Dark Web...*",
            f" ✅ **HACK COMPLETE!**\n\n_Target **{target_name}** has been successfully compromised._"
        ]

        for step in steps:
            await asyncio.sleep(random.uniform(0.7, 1.5))
            try:
                await status_msg.edit(step)
            except:
                break

    except Exception as e:
        await report_error(client, e, context='Hack command failure')
