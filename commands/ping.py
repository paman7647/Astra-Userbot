# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Diagnostic Tool: Latency Check
-----------------------------
Measures the round-trip time between the userbot and WhatsApp servers.
"""

import time
from . import *

@astra_command(
    name="ping",
    description="Measure the bot's response latency.",
    category="Utility",
    aliases=["p"],
    usage="",
    is_public=True
)
async def ping_handler(client: Client, message: Message):
    """
    Calculates RTT (Round Trip Time) by measuring the delay 
    in sending a response message.
    """
    try:
        start_time = time.time()
        
        # Initial response to measure latency
        status_msg = await message.reply("📡 *Pinging...*")
        
        end_time = time.time()
        latency = round((end_time - start_time) * 1000)
        
        # Final result with clean formatting
        try:
            await status_msg.edit(f"🏓 **Pong!**\n`Latency: {latency}ms`")
        except:
            await message.reply(f"🏓 **Pong!**\n`Latency: {latency}ms`")

    except Exception as e:
        await smart_reply(message, " ⚠️ Latency check failed.")
        await report_error(client, e, context='Ping command failure')
