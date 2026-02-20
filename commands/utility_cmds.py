# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Essential Utilities: Paste, Carbon, Quotly
------------------------------------------
A suite of tools for developers and power users.
- Paste: Upload text to pastebin.
- Carbon: Generate beautiful code images.
- Quotly: Create sticker quotes from messages.
"""

import aiohttp
import base64
import time
from . import *

# --- PASTEBIN UTILITY ---
@astra_command(
    name="paste",
    description="Upload text to dpaste.org (Pastebin).",
    category="Utility",
    aliases=["bin"],
    usage="<text/reply>",
    is_public=True
)
async def paste_handler(client: Client, message: Message):
    """
    Uploads text to dpaste.org and returns a viewing link.
    """
    try:
        args_list = extract_args(message)
        content = ""
        
        if message.has_quoted_msg:
            content = message.quoted.body
        elif args_list:
            content = " ".join(args_list)
            
        if not content:
            return await smart_reply(message, " 📋 **Paste Utility**\n\nReply to text or provide arguments.")

        status_msg = await smart_reply(message, " ⏳ *Uploading to dpaste...*")
        
        # Using dpaste.org API (Simple POST, returns URL)
        url = "https://dpaste.org/api/"
        payload = {"content": content, "expiry_days": 7}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload) as resp:
                if resp.status == 200:
                    paste_url = await resp.text()
                    
                    try:
                        await status_msg.edit(
                            f"🗒️ **Paste Uploaded!**\n\n"
                            f"🔗 **Link:** [View Paste]({paste_url})\n"
                            f"⏳ **Expires:** 7 days"
                        )
                    except:
                        await message.reply(
                            f"🗒️ **Paste Uploaded!**\n\n"
                            f"🔗 **Link:** [View Paste]({paste_url})\n"
                            f"⏳ **Expires:** 7 days"
                        )
                else:
                    try:
                        await status_msg.edit(" ⚠️ Upload failed. dpaste.org returned error.")
                    except:
                        await message.reply(" ⚠️ Upload failed. dpaste.org returned error.")

    except Exception as e:
        await report_error(client, e, context='Paste command failure')


# --- CARBON CODE IMAGE ---
@astra_command(
    name="carbon",
    description="Create a beautiful code snippet image.",
    category="Utility",
    aliases=["code"],
    usage="<text/reply>",
    is_public=True
)
async def carbon_handler(client: Client, message: Message):
    """
    Uses Carbonara API to generate code images.
    """
    try:
        args_list = extract_args(message)
        code = ""
        
        if message.has_quoted_msg:
            code = message.quoted.body
        elif args_list:
            code = " ".join(args_list)
            
        if not code:
            return await smart_reply(message, " 💻 **Carbon Utility**\n\nReply to code or text.")

        status_msg = await smart_reply(message, " 🎨 *Generating Carbon image...*")
        
        # Carbonara API
        url = "https://carbonara.solopov.dev/api/cook"
        payload = {
            "code": code,
            "backgroundColor": "rgba(171, 184, 195, 1)",
            "theme": "seti"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    b64_data = base64.b64encode(image_data).decode('utf-8')
                    
                    media = {
                        "mimetype": "image/jpeg",
                        "data": b64_data,
                        "filename": "carbon.jpg"
                    }
                    await client.send_media(message.chat_id, media, caption="💻 **Code Snippet**")
                    await status_msg.delete()
                else:
                    try:
                        await status_msg.edit(" ⚠️ Failed to generate image.")
                    except:
                        await message.reply(" ⚠️ Failed to generate image.")

    except Exception as e:
        await report_error(client, e, context='Carbon command failure')


# --- QUOTLY STICKER ---
@astra_command(
    name="quotly",
    description="Create a sticker quote from a message.",
    category="Fun",
    aliases=["q", "quote"],
    usage="(reply to message)",
    is_public=True
)
async def quotly_handler(client: Client, message: Message):
    """
    Generates a sticker quoting the replied message.
    """
    try:
        if not message.has_quoted_msg:
            return await smart_reply(message, " 🗨️ Reply to a message to quote it.")

        status_msg = await smart_reply(message, " 🎨 *Making quote...*")
        
        quoted = message.quoted
        text = quoted.body or "Media"
        sender_name = "User"
        sender_id = 0
        
        if message.quoted_participant:
            sender_id = message.quoted_participant.user
            # Name resolution would ideally happen here if we had a user cache
            sender_name = sender_id[:6] 
        
        # Using a public Quotly API mirror (bot.lyo.su)
        payload = {
            "type": "quote",
            "format": "webp",
            "backgroundColor": "#1b1429",
            "width": 512,
            "height": 768,
            "scale": 2,
            "messages": [
                {
                    "entities": [],
                    "avatar": True,
                    "from": {
                        "id": int(float(sender_id)) if sender_id else 123456, 
                        "name": sender_name,
                        "photo": {
                            "url": "https://telegra.ph/file/18a28f73177695376046e.jpg" # Default avatar
                        }
                    },
                    "text": text,
                    "replyMessage": {}
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post("https://bot.lyo.su/quote/generate", json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data['ok']:
                        sticker_buffer = base64.b64decode(data['result']['image'])
                        b64_sticker = base64.b64encode(sticker_buffer).decode('utf-8')
                        
                        media_pkg = {
                            "mimetype": "image/webp",
                            "data": b64_sticker,
                            "filename": "quote.webp",
                            "type": "sticker"
                        }
                        
                        await client.send_media(
                            message.chat_id, 
                            media_pkg, 
                            reply_to=quoted.id
                        )
                        await status_msg.delete()
                        return
                    
        try:
            await status_msg.edit(" ⚠️ Failed to create quote.")
        except:
            await message.reply(" ⚠️ Failed to create quote.")

    except Exception as e:
        await report_error(client, e, context='Quotly command failure')
