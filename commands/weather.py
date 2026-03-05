import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="weather",
    description="Get the current weather forecast for a specific city.",
    category="Tools & Utilities",
    aliases=["wttr", "forecast"],
    usage="<city> (e.g. London)",
    is_public=True,
)
async def weather_handler(client: Client, message: Message):
    """
    Retrieves weather data in both text (for speed) and image (for detail) formats.
    """
    args_list = extract_args(message)
    city = " ".join(args_list) or "London"

    status_msg = await edit_or_reply(
        message, f"☁️ **Astra Weather Radar**\n━━━━━━━━━━━━━━━━━━━━\n🔍 **Target:** `{city}`..."
    )

    # wttr.in endpoints
    text_url = f"https://wttr.in/{city}?format=%C+%t+%w+%h+%m"
    img_url = f"https://wttr.in/{city}.png"

    headers = {"User-Agent": "curl/7.64.1"}
    async with aiohttp.ClientSession(headers=headers) as session:
        # 1. Fetch text data
        async with session.get(text_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            if resp.status != 200:
                time.sleep(0.5)
                return await status_msg.edit("❌ **Astra Weather Radar:** Failed to retrieve weather data.")
            data = await resp.text()

        weather_report = (
            f"🌍 **Astra Weather: {city.capitalize()}**\n━━━━━━━━━━━━━━━━━━━━\n{data}\n\n_Powered by wttr.in_"
        )

        # 2. Attempt to fetch and send visual forecast
        async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as img_resp:
            if img_resp.status == 200:
                img_data = await img_resp.read()
                b64_data = base64.b64encode(img_data).decode("utf-8")

                media = {"mimetype": "image/png", "data": b64_data, "filename": f"weather_{city}.png"}
                try:
                    await client.send_media(message.chat_id, media, caption=weather_report)
                    return await status_msg.delete()
                except Exception as upload_err:
                    return await status_msg.edit(f"❌ **Astra Weather:** Failed to send image. ({str(upload_err)})")

        # Fallback to text only
        time.sleep(0.5)
        await status_msg.edit(weather_report)
