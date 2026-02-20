# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import platform
import time
from . import *

# --- Platform Command ---
@astra_command(
    name="platform",
    description="Show platform info",
    usage="",
    aliases=["sys"],
    owner_only=True
)
async def platform_cmd(client: Client, message: Message):
    try:
        status_msg = await message.reply("🖥️ Fetching system info...")
        
        sys_info = f"🖥️ **System Info**\n"
        sys_info += f"OS: {platform.system()} {platform.release()}\n"
        sys_info += f"Version: {platform.version()}\n"
        sys_info += f"Machine: {platform.machine()}"

        try:
            await status_msg.edit(sys_info)
        except:
            await message.reply(sys_info)
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# --- Start Command ---
@astra_command(
    name="start",
    description="Check bot status",
    usage="",
    aliases=["alive_test"],
    owner_only=True
)
async def start_cmd(client: Client, message: Message):
    try:
        msg = await message.reply("🤖 Starting Astra...")
        # Verify edit capabilities
        try:
            await msg.edit("🤖 **Astra Userbot is Online!**\nSystem is ready to serve.")
        except:
            await message.reply("🤖 **Astra Userbot is Online!**\nSystem is ready to serve.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")
