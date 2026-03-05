"""
Fun Utility: Fake Persona Generator
-----------------------------------
Generates a random fake identity for privacy or fun.
Uses randomuser.me API.
"""

import time

import aiohttp
from utils.helpers import safe_edit

from . import *


@astra_command(
    name="fake",
    description="Generate a fake identity.",
    category="Fun & Memes",
    aliases=["identity", "fakeperson"],
    usage=".fake (generate random identity)",
    is_public=True,
)
async def fake_handler(client: Client, message: Message):
    """
    Fetches random user data and formats it into an identity card.
    """
    status_msg = await edit_or_reply(message, " 🕵️ *Generating fake identity...*")

    url = "https://randomuser.me/api/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                time.sleep(0.5)
                return await safe_edit(status_msg, " ⚠️ Failed to fetch identity.")

            data = await resp.json()
            user = data["results"][0]

            name = f"{user['name']['first']} {user['name']['last']}"
            gender = user["gender"]
            location = f"{user['location']['city']}, {user['location']['country']}"
            email = user["email"]
            login = user["login"]["username"]
            pw = user["login"]["password"]
            dob = user["dob"]["date"][:10]

            # Format Identity Card
            identity_card = (
                "🕵️ **Fake Identity Generated**\n\n"
                f"👤 **Name:** `{name}` ({gender})\n"
                f"🎂 **DOB:** `{dob}`\n"
                f"📍 **Address:** `{location}`\n\n"
                f"📧 **Email:** `{email}`\n"
                f"🔑 **Username:** `{login}`\n"
                f"🗝️ **Password:** `{pw}`\n\n"
                f"⚠️ _For educational/fun purposes only._"
            )

            # Send photo if available
            pic_url = user["picture"]["large"]
            if pic_url:
                import base64

                async with session.get(pic_url) as img_resp:
                    if img_resp.status == 200:
                        img_data = await img_resp.read()
                        b64_data = base64.b64encode(img_data).decode("utf-8")

                        media = {"mimetype": "image/jpeg", "data": b64_data, "filename": "identity.jpg"}
                        await client.send_media(message.chat_id, media, caption=identity_card)
                        await status_msg.delete()
                        return

            time.sleep(0.5)
            await safe_edit(status_msg, identity_card)
