# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Educational Utility: Dictionary
------------------------------
Retrieves word definitions, phonetics, and usage examples from the Free Dictionary API.
"""

import aiohttp
from . import *

@astra_command(
    name="define",
    description="Look up the definition and phonetics of an English word.",
    category="Education",
    aliases=["dict", "meaning"],
    usage="<word> (e.g. automobile)",
    is_public=True
)
async def define_handler(client: Client, message: Message):
    """
    Queries the dictionary API and renders a clean semantic report.
    """
    try:
        args_list = extract_args(message)
        if not args_list:
            return await smart_reply(message, " 📋 **Dictionary Utility**\n\nPlease provide a word to define.")

        word = args_list[0].lower()
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10) as resp:
                if resp.status != 200:
                    return await smart_reply(message, f" ❌ **Word Not Found:** `{word}`")
        
                data = await resp.json()
                entry = data[0]
                
                # Construct clean definition
                definition = entry['meanings'][0]['definitions'][0]['definition']
                part_of_speech = entry['meanings'][0]['partOfSpeech']
                phonetic = entry.get('phonetic', '')

                report = (
                    f"📖 **Definition: {word.capitalize()}**\n"
                    f"_{part_of_speech}_ {f' | {phonetic}' if phonetic else ''}\n\n"
                    f"{definition}\n\n"
                    f"🌐 *Source: DictionaryAPI*"
                )
                
                await smart_reply(message, report)

    except Exception as e:
        await smart_reply(message, " ⚠️ Dictionary service failure.")
        await report_error(client, e, context='Define command lookup failure')
