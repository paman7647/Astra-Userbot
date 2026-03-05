from urllib.parse import quote_plus

import aiohttp

from . import *


@astra_command(
    name="urban",
    description="Search Urban Dictionary for definitions.",
    category="Tools & Utilities",
    aliases=["ud", "slang"],
    usage="<word> (e.g. .urban chill)",
    is_public=True,
)
async def urban_handler(client: Client, message: Message):
    """Urban Dictionary lookup plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.urban <word>`")

    word = " ".join(args)
    status_msg = await edit_or_reply(message, f"🏙️ **Searching Urban Dictionary for:** `{word}`...")

    try:
        api_url = f"http://api.urbandictionary.com/v0/define?term={quote_plus(word)}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("list", [])

                    if not results:
                        return await status_msg.edit(f"❌ No definitions found for `{word}`.")

                    top = results[0]
                    definition = top.get("definition", "No definition").replace("[", "").replace("]", "")
                    example = top.get("example", "No example").replace("[", "").replace("]", "")

                    text = (
                        f"📖 **URBAN DICTIONARY**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🅰️ **Word:** `{top['word']}`\n\n"
                        f"📝 **Definition:**\n{definition}\n\n"
                        f"💡 **Example:**\n_{example}_\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👍 `{top['thumbs_up']}`    👎 `{top['thumbs_down']}`\n"
                        f"🚀 *Astra Slang Dictionary*"
                    )
                    return await status_msg.edit(text)

        await status_msg.edit("⚠️ Urban Dictionary API is unreachable.")

    except Exception as e:
        await status_msg.edit(f"❌ **Urban Error:** {str(e)}")
