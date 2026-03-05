from urllib.parse import quote_plus

import aiohttp

from . import *


@astra_command(
    name="lyrics",
    description="Fetch lyrics for a song.",
    category="Tools & Utilities",
    aliases=["lyrical"],
    usage="<song name> [artist] (e.g. .lyrics Blinding Lights)",
    is_public=True,
)
async def lyrics_handler(client: Client, message: Message):
    """Lyrics lookup plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.lyrics <song name>`")

    query = " ".join(args)
    status_msg = await edit_or_reply(message, f"🎵 **Searching lyrics for:** `{query}`...")

    # Lyrist API is generally more robust and returns JSON directly
    # Format: https://lyrist.vercel.app/api/<song>/<artist> or just /api/<song>
    api_url = f"https://lyrist.vercel.app/api/{quote_plus(query)}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                data = await resp.json()

                lyrics = data.get("lyrics")
                title = data.get("title")
                artist = data.get("artist")

                if not lyrics:
                    return await status_msg.edit(f"❌ No lyrics found for `{query}`.")

                # Formatting lyrics (cap at max message length)
                final_lyrics = lyrics.strip()
                if len(final_lyrics) > 3000:
                    final_lyrics = final_lyrics[:3000] + "..."

                text = (
                    f"🎶 **LYRICS ENGINE**\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🆔 **Song:** `{title}`\n"
                    f"👤 **Artist:** `{artist}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"{final_lyrics}\n\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"🚀 *Powered by Astra Intelligence*"
                )
                return await status_msg.edit(text)
            else:
                return await status_msg.edit(
                    f"⚠️ Lyrics search failed (Status: `{resp.status}`). Try adding the artist name."
                )
