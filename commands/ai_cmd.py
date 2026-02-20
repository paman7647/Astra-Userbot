# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import time
from . import *

@astra_command(
    name="ai",
    description="Chat with Google Gemini AI",
    category="AI",
    aliases=["chat", "ask", "gemini"],
    usage="<prompt>",
    owner_only=False
)
async def ai_handler(client: Client, message: Message):
    """Chat with Google Gemini AI"""
    try:
        args_list = extract_args(message)
        
        prompt = " ".join(args_list)

        # Handle quoted message if no prompt provided
        if not prompt and message.has_quoted_msg:
            quoted = message.quoted
            if quoted:
                prompt = quoted.body

        if not prompt:
            return await smart_reply(message, " 📋 Please provide a prompt or reply to a message. Example: `.ai What is the capital of France?`")

        from config import config
        api_key = os.getenv("GEMINI_API_KEY") or getattr(config, 'GEMINI_API_KEY', None)
        if not api_key:
            return await smart_reply(message, " ❌ Gemini API key not found. Please set `GEMINI_API_KEY` environment variable.")

        from google import genai
        gen_client = genai.Client(api_key=api_key)

        status_msg = await smart_reply(message, " ✨ *AI is thinking...*")
        
        import asyncio
        # Run in a thread if it's blocking
        response = await asyncio.to_thread(gen_client.models.generate_content, model='gemini-3-flash-preview', contents=prompt)

        if response and response.text:
            try:
                await status_msg.edit(response.text)
            except:
                await message.reply(response.text)
        else:
            try:
                await status_msg.edit(" AI returned an empty response.")
            except: pass
    except Exception as e:
        await smart_reply(message, f" ❌ Error: {str(e)}")
        await report_error(client, e, context='Command ai failed')
