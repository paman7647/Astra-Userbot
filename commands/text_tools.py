# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import aiohttp
import base64
import io
import os
from . import *
from utils.helpers import handle_command_error

import urllib.parse

@astra_command(
    name="txtimg",
    description="Convert plain text into a beautiful image card.",
    category="Creative Suite",
    usage="<text>",
    is_public=True
)
async def txtimg_handler(client: Client, message: Message):
    args = extract_args(message)
    if not args and not message.has_quoted_msg:
        return await smart_reply(message, "📝 **Astra Text Card**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Usage:** `.txtimg Hello World` or reply to text.")

    text = " ".join(args) if args else message.quoted.body
    status_msg = await smart_reply(message, "✨ **Astra Creative Studio**\n━━━━━━━━━━━━━━━━━━━━\n🎨 *Rendering your text card...*")

    try:
        # Using a reliable free API for text-to-image
        base_url = "https://image.pollinations.ai/prompt/"
        prompt = f"A beautiful typography card with the text: '{text}'. centered, professional, clean, high resolution, soft background."
        encoded_prompt = urllib.parse.quote(prompt)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}{encoded_prompt}") as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    media = {
                        "mimetype": "image/jpeg",
                        "data": b64_data,
                        "filename": "text_card.jpg"
                    }
                    await client.send_media(message.chat_id, media, caption="📝 **Astra Text Card**")
                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ Failed to render text image.")

    except Exception as e:
        await handle_command_error(client, message, e, context='Text card failure')

@astra_command(
    name="kcode",
    description="Carbon-style rendering for plain text (not just code).",
    category="Creative Suite",
    usage="<text>",
    is_public=True
)
async def kcode_handler(client: Client, message: Message):
    """
    Uses Carbonara API but optimized for plain text descriptions.
    """
    args = extract_args(message)
    if not args and not message.has_quoted_msg:
        return await smart_reply(message, "🎨 **Astra K-Code**\n━━━━━━━━━━━━━━━━━━━━\n❌ **Usage:** `.kcode Hello World`")

    text = " ".join(args) if args else message.quoted.body
    status_msg = await smart_reply(message, "🎨 **Astra K-Code**\n━━━━━━━━━━━━━━━━━━━━\n✨ *Rendering premium card...*")

    try:
        url = "https://carbonara.solopov.dev/api/cook"
        payload = {
            "code": text,
            "backgroundColor": "rgba(27, 20, 41, 1)",
            "theme": "panda", # Slick dark theme
            "language": "plain_text"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    media = {
                        "mimetype": "image/jpeg",
                        "data": b64_data,
                        "filename": "kcode.jpg"
                    }
                    await client.send_media(message.chat_id, media, caption="🎨 **Astra Premium Card**")
                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ Failed to generate premium card.")

    except Exception as e:
        await handle_command_error(client, message, e, context='K-Code failure')
