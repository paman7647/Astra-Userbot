# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Information Utility: Weather Forecast
-------------------------------------
Provides real-time weather reports and visual forecast cards using wttr.in.
Supports worldwide city lookups.
"""

import time
import aiohttp
import base64
from . import *

@astra_command(
    name="weather",
    description="Get the current weather forecast for a specific city.",
    category="Utility",
    aliases=["wttr", "forecast"],
    usage="<city> (e.g. London)",
    is_public=True
)
async def weather_handler(client: Client, message: Message):
    """
    Retrieves weather data in both text (for speed) and image (for detail) formats.
    """
    try:
        args_list = extract_args(message)
        city = " ".join(args_list) or "London"
        
        status_msg = await smart_reply(message, f" ☁️ *Checking weather conditions for '{city}'...*")
        
        # wttr.in endpoints
        text_url = f"https://wttr.in/{city}?format=%C+%t+%w+%h+%m"
        img_url = f"https://wttr.in/{city}.png"

        async with aiohttp.ClientSession() as session:
            # 1. Fetch text data
            async with session.get(text_url, timeout=10) as resp:
                if resp.status != 200:
                    time.sleep(0.5)
                    return await status_msg.edit(" ⚠️ Failed to retrieve weather data.")
                data = await resp.text()
            
            weather_report = (
                f"🌍 **Weather: {city.capitalize()}**\n\n"
                f"{data}\n\n"
                f"_Powered by wttr.in_"
            )

            # 2. Attempt to fetch and send visual forecast
            async with session.get(img_url, timeout=15) as img_resp:
                if img_resp.status == 200:
                    img_data = await img_resp.read()
                    b64_data = base64.b64encode(img_data).decode('utf-8')
            
                    media = {
                        "mimetype": "image/png",
                        "data": b64_data,
                        "filename": f"weather_{city}.png"
                    }
                    await client.chat.send_media(message.chat_id, media, caption=weather_report)
                    return await status_msg.delete()

            # Fallback to text only
            time.sleep(0.5)
            await status_msg.edit(weather_report)

    except Exception as e:
        await smart_reply(message, " ⚠️ Weather lookup failed.")
        await report_error(client, e, context='Weather command failure')
