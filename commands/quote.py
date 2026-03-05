import base64

import aiohttp

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="quote",
    description="Turns a message into a beautiful image/sticker.",
    category="Tools & Utilities",
    aliases=["q"],
    usage="<reply to message>",
    is_public=True,
)
async def quote_handler(client: Client, message: Message):
    """Message to Image Quote Generator."""
    if not message.has_quoted_msg:
        return await edit_or_reply(message, "❌ **Reply to a message** to create a quote.")

    status_msg = await edit_or_reply(
        message, "🎨 **Astra Creative Studio**\n━━━━━━━━━━━━━━━━━━━━\n🖼️ *Designing your quote...*"
    )

    quoted = message.quoted
    text = quoted.body or ""
    sender_name = await get_contact_name(client, quoted.sender)

    # 1. Fetch Profile Picture for high-fidelity quotes
    # Note: Bypassing browser bridge for speed if possible
    pp_b64 = ""
    try:
        pp_url = await client.contact.get_profile_picture(quoted.sender)
        if pp_url:
            async with aiohttp.ClientSession() as session:
                async with session.get(pp_url) as resp:
                    if resp.status == 200:
                        pp_b64 = base64.b64encode(await resp.read()).decode()
    except:
        pass

    # 2. Use a Quote API (e.g., Quotly or a custom renderer)
    # Using a reliable public Quotly-style API pattern
    payload = {
        "type": "quote",
        "format": "webp",
        "backgroundColor": "#121212",
        "width": 512,
        "height": 768,
        "scale": 2,
        "messages": [
            {
                "entities": [],
                "avatar": True,
                "from": {
                    "id": 1,
                    "name": sender_name,
                    "photo": {
                        "url": "https://telegra.ph/file/a86780c8e317e6519280d.jpg"  # Fallback
                    },
                },
                "text": text,
                "replyMessage": {},
            }
        ],
    }

    # Using a high-availability proxy for Quotly
    api_url = "https://quote-api-delta.vercel.app/generate"

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                image_b64 = data.get("result", {}).get("image")

                if image_b64:
                    media = {"mimetype": "image/webp", "data": image_b64, "filename": "quote.webp"}
                    # Send as sticker
                    await client.send_media(message.chat_id, media, is_sticker=True)
                    return await status_msg.delete()

    await status_msg.edit("❌ **Could not generate quote.** Ensure the message contains text.")
