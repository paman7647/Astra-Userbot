import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="shorten",
    description="Shorten long URLs using tinyurl.",
    category="Tools & Utilities",
    aliases=["short", "urlshort"],
    usage="<url> (e.g. .shorten https://github.com/paman7647/Astra-Userbot)",
    is_public=True,
)
async def shorten_handler(client: Client, message: Message):
    """URL shortener plugin."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, "❌ **Usage:** `.shorten <url>`")

    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    status_msg = await edit_or_reply(message, "✂️ **Shortening URL...**")

    try:
        api_url = f"http://tinyurl.com/api-create.php?url={url}"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    short_url = await resp.text()
                    text = (
                        f"🔗 **URL SHORTENER**\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"📤 **Original:** {url}\n"
                        f"📥 **Shortened:** {short_url}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🚀 *Powered by Astra*"
                    )
                    return await status_msg.edit(text)

        await status_msg.edit("⚠️ Failed to shorten URL. TinyURL may be down.")

    except Exception as e:
        await status_msg.edit(f"❌ **Shorten Error:** {str(e)}")
