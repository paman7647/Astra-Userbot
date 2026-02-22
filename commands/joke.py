# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Entertainment Plugin: Jokes
--------------------------
Fetches a curated selection of random jokes from external safe-API sources.
"""

import aiohttp
from . import *

# Configuration: API endpoint with safety filters
JOKE_API_URL = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"

@astra_command(
    name="joke",
    description="Fetch a random, family-friendly joke.",
    category="Fun/Lite",
    aliases=["haha"],
    usage=".joke (no arguments)",
    is_public=True
)
async def joke_handler(client: Client, message: Message):
    """
    Fetches and delivers a joke. Handles both single-part 
    and setup/delivery (two-part) joke structures.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(JOKE_API_URL, timeout=10) as resp:
                if resp.status != 200:
                    return await smart_reply(message, " ⚠️ Joke service is currently unavailable.")
                
                joke_data = await resp.json()
                
                # Render logic based on joke type
                if joke_data.get('type') == 'single':
                    content = f" 😂 *Astra Humour:*\n\n{joke_data['joke']}"
                else:
                    content = f" 😂 *Astra Humour:*\n\n{joke_data['setup']}\n\n... _{joke_data['delivery']}_"
                
                await smart_reply(message, content)

    except Exception as e:
        await smart_reply(message, " ⚠️ Failed to fetch a joke at this time.")
        await report_error(client, e, context='Joke command delivery failure')
