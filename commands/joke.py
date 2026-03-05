"""
Entertainment Plugin: Jokes
--------------------------
Fetches a curated selection of random jokes from external safe-API sources.
"""

import aiohttp

from . import *
from utils.helpers import edit_or_reply

# Configuration: API endpoint with safety filters
JOKE_API_URL = "https://v2.jokeapi.dev/joke/Any?blacklistFlags=nsfw,religious,political,racist,sexist,explicit"


@astra_command(
    name="joke",
    description="Fetch a random, family-friendly joke.",
    category="Fun & Memes",
    aliases=["haha"],
    usage=".joke (no arguments)",
    is_public=True,
)
async def joke_handler(client: Client, message: Message):
    """
    Fetches and delivers a joke. Handles both single-part
    and setup/delivery (two-part) joke structures.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(JOKE_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return await edit_or_reply(message, " ⚠️ Joke service is currently unavailable.")

            joke_data = await resp.json()

            # Render logic based on joke type
            if joke_data.get("type") == "single":
                content = f" 😂 *Astra Humour:*\n\n{joke_data['joke']}"
            else:
                content = f" 😂 *Astra Humour:*\n\n{joke_data['setup']}\n\n... _{joke_data['delivery']}_"

            await edit_or_reply(message, content)
