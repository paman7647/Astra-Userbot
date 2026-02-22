# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Trivia Plugin: Random Facts
--------------------------
Delivers useless but interesting facts from public APIs.
"""

import aiohttp
from . import *

# Configuration: Reliable public trivia API
FACT_API_URL = "https://uselessfacts.jsph.pl/random.json?language=en"

@astra_command(
    name="fact",
    description="Get an interesting random fact.",
    category="Fun/Lite",
    aliases=["trivia"],
    usage=".fact (no arguments)",
    is_public=True
)
async def fact_handler(client: Client, message: Message):
    """
    Fetches a random fact and renders it with clean formatting.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(FACT_API_URL, timeout=10) as resp:
                if resp.status != 200:
                    return await smart_reply(message, " ⚠️ Trivia service is offline. Try again later.")
                
                data = await resp.json()
                await smart_reply(message, f"💡 *Did you know?*\n\n{data['text']}")

    except Exception as e:
        await smart_reply(message, " ⚠️ Failed to fetch a fact.")
        await report_error(client, e, context='Fact command delivery failure')
