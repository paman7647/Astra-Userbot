import base64

import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="anime",
    description="Search for anime information on MyAnimeList.",
    category="Tools & Utilities",
    aliases=["mal"],
    usage="<anime name> (e.g. .anime Naruto)",
    is_public=True,
)
async def anime_handler(client: Client, message: Message):
    """Anime lookup plugin using Jikan API."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.anime <anime name>`")

    query = " ".join(args)
    status_msg = await edit_or_reply(
        message, f"⛩️ **Astra Anime Search**\n━━━━━━━━━━━━━━━━━━━━\n🔍 **Query:** `{query}`..."
    )

    # Jikan API v4 (Public MyAnimeList API)
    api_url = f"https://api.jikan.moe/v4/anime?q={query}&limit=1"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status == 200:
                data = await resp.json()
                results = data.get("data", [])

                if not results:
                    return await status_msg.edit(f"❌ No anime found for `{query}`.")

                anime = results[0]
                title = anime.get("title")
                english_title = anime.get("title_english") or title
                score = anime.get("score", "N/A")
                episodes = anime.get("episodes", "N/A")
                status = anime.get("status", "N/A")
                synopsis = anime.get("synopsis", "No synopsis available.")[:400] + "..."
                url = anime.get("url")
                image_url = anime.get("images", {}).get("jpg", {}).get("large_image_url")

                text = (
                    f"⛩️ **ANIME DATABASE**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **Title:** `{english_title}`\n"
                    f"🌟 **Score:** `{score}` | 📺 **EPs:** `{episodes}`\n"
                    f"📡 **Status:** `{status}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{synopsis}\n\n"
                    f"🔗 [MyAnimeList]({url})\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 *Powered by Astra*"
                )

                if image_url:
                    async with session.get(image_url) as img_resp:
                        if img_resp.status == 200:
                            img_data = await img_resp.read()
                            b64_data = base64.b64encode(img_data).decode("utf-8")
                            media = {
                                "mimetype": "image/jpeg",
                                "data": b64_data,
                                "filename": f"anime_{anime.get('mal_id')}.jpg",
                            }
                            await client.send_media(message.chat_id, media, caption=text)
                            return await status_msg.delete()

                return await status_msg.edit(text)

    await status_msg.edit("⚠️ Anime service is currently unavailable.")
