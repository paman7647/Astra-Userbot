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
    category="Fun & Memes",
    aliases=["trivia"],
    usage=".fact (no arguments)",
    is_public=True,
)
async def fact_handler(client: Client, message: Message):
    """
    Fetches a random fact and renders it with clean formatting.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(FACT_API_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                return await edit_or_reply(message, "⚠️ **Astra Knowledge Base:** Trivia service offline.")

            data = await resp.json()
            await edit_or_reply(message, f"💡 **Astra Fact Generator**\n━━━━━━━━━━━━━━━━━━━━\n{data['text']}")
