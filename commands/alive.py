# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import base64
import time
from . import *
from config import config

@astra_command(
    name="alive",
    description="Description: Check if the bot is responsive and see system status.\nSyntax: .alive\nExample: .alive",
    category="General",
    aliases=[],
    usage=".alive (check bot is operational)",
    owner_only=True
)
async def alive_handler(client: Client, message: Message):
    """Renders a professional status report with branding image."""
    try:
        # Resolve owner name dynamically from the library
        owner_name = config.OWNER_NAME
        try:
            me = await client.get_me()
            if me and hasattr(me, 'name') and me.name:
                owner_name = me.name
            elif me and hasattr(me, 'pushname') and me.pushname:
                owner_name = me.pushname
        except Exception:
            # Fallback to config if library call fails
            pass

        # Professional Alive Text
        alive_text = (
            "✨ **ASTRA USERBOT IS ONLINE** ✨\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **Owner:** `{owner_name}`\n"
            f"🏷️ **Version:** `{config.VERSION}`\n"
            "🛰️ **Status:** `Running Smoothly`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 *System is operational and ready to serve.*"
        )

        # Image path (Branding Image)
        img_path = os.path.join(os.getcwd(), "utils", "ub.png")
        
        if os.path.exists(img_path):
            try:
                with open(img_path, "rb") as img_file:
                    b64_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                media = {
                    "mimetype": "image/png",
                    "data": b64_data,
                    "filename": "ub.png"
                }
                
                # Send media with professional caption
                await client.send_media(
                    message.chat_id, 
                    media, 
                    caption=alive_text,
                    reply_to=message.id
                )
                return
            except Exception:
                # Silently fallback to text if media sending fails
                pass
        
        # Fallback to text-only if image is missing or sending failed
        await smart_reply(message, alive_text)
        
    except Exception as e:
        # Ultimate fallback
        await smart_reply(message, f"❌ Alive Check Failed: {str(e)}")
