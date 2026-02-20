# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Linguistic Utility: Translation
-------------------------------
Instant text translation using Google Translate's single-fetch API.
Supports 100+ languages with automatic source detection.
"""

import aiohttp
from . import *

@astra_command(
    name="translate",
    description="Translate text or replies to another language.",
    category="Utility",
    aliases=["tr"],
    usage="[lang_code] <text/reply>",
    is_public=True
)
async def translate_handler(client: Client, message: Message):
    """
    Handles translation logic by detecting target language and resolving 
    source text from arguments or quoted messages.
    """
    try:
        args_list = extract_args(message)
        text = ""
        target_lang = "en" # Default to English

        # 1. Resolve Text & Target Lang
        if message.has_quoted_msg:
            quoted = message.quoted
            text = quoted.body
            if args_list: 
                target_lang = args_list[0].lower()
        else:
            if not args_list:
                return await smart_reply(message, " 📋 **Translation Utility**\n\nPlease provide text or reply to a message.")
    
            # Check if first arg is a language code (2 chars)
            if len(args_list[0]) == 2 and len(args_list) > 1:
                target_lang = args_list[0].lower()
                text = " ".join(args_list[1:])
            else:
                text = " ".join(args_list)

        if not text:
            return await smart_reply(message, " ⚠️ No translatable text found.")

        # 2. API Execution
        status_msg = await smart_reply(message, " 🌍 *Translating...*")
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status != 200:
                    try:
                        return await status_msg.edit(" ⚠️ Translation service is unreachable.")
                    except:
                        return await message.reply(" ⚠️ Translation service is unreachable.")
                
                data = await resp.json()
                translated = "".join([part[0] for part in data[0]])
                
                report = (
                    f"🌍 **Astra Translate**\n\n"
                    f"*Target:* `{target_lang.upper()}`\n\n"
                    f"{translated}"
                )
                try:
                    await status_msg.edit(report)
                except:
                    await message.reply(report)

    except Exception as e:
        await smart_reply(message, f" ⚠️ Translation failed: {str(e)}")
        await report_error(client, e, context='Translation command failure')
