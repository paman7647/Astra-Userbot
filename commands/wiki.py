import base64
import time

import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="wiki",
    description="Search Wikipedia for information on any topic.",
    category="Tools & Utilities",
    aliases=["wikipedia"],
    usage="<query> (search term)",
    is_public=True,
)
async def wiki_handler(client: Client, message: Message):
    """
    Fetches the most relevant Wikipedia page summary and thumbnail.
    """
    args_list = extract_args(message)
    if not args_list:
        return await edit_or_reply(message, " 📚 **Wikipedia Search**\n\nPlease provide a search term.")

    query = " ".join(args_list)
    status_msg = await edit_or_reply(message, f"📚 Searching Wikipedia for `{query}`...")

    headers = {
        "User-Agent": "AstraUserbot/1.0 (https://github.com/paman7647/Astra-Userbot; contact@example.com) aiohttp/3.8"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Search for titles
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
        async with session.get(search_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            search_data = await resp.json()

        if not search_data["query"]["search"]:
            time.sleep(0.5)
            return await status_msg.edit(f" ⚠️ No exact results found for `{query}`.")

        best_match = search_data["query"]["search"][0]["title"]

        # 2. Fetch specialized summary
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{best_match.replace(' ', '_')}"
        async with session.get(summary_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                time.sleep(0.5)
                return await status_msg.edit(" ⚠️ Failed to retrieve article summary.")
            data = await resp.json()

        # Compose text report
        response = (
            f"📚 **Wikipedia: {data['title']}**\n\n"
            f"{data['extract']}\n\n"
            f"🔗 [Read More]({data['content_urls']['desktop']['page']})"
        )

        # Handle Thumbnail if present
        thumbnail_url = data.get("thumbnail", {}).get("source")
        if thumbnail_url:
            async with session.get(thumbnail_url) as img_resp:
                if img_resp.status == 200:
                    img_data = await img_resp.read()
                    b64_data = base64.b64encode(img_data).decode("utf-8")
                    media = {"mimetype": "image/jpeg", "data": b64_data, "filename": f"wiki_{best_match}.jpg"}
                    await client.send_media(message.chat_id, media, caption=response)
                    return await status_msg.delete()

        time.sleep(0.5)
        await status_msg.edit(response)
