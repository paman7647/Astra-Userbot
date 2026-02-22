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

@astra_command(
    name="platform",
    description="Description: Display detailed information about the bot's hosting environment.\nSyntax: .platform\nExample: .platform",
    usage=".platform (show system info)",
    aliases=["sys", "os"],
    owner_only=True
)
async def platform_cmd(client: Client, message: Message):
    """Shows technical specifications of the hosting environment."""
    try:
        # First edit without delay
        status_msg = await message.reply("🖥️ *Fetching system architecture...*")
        
        # Gathering info (Core logic preserved)
        os_info = f"{platform.system()} {platform.release()}"
        arch_info = platform.machine()
        python_ver = platform.python_version()
        
        premium_sys_info = (
            "🖥️ **SYSTEM ARCHITECTURE** 🖥️\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏠 **OS:** `{os_info}`\n"
            f"🧠 **Machine:** `{arch_info}`\n"
            f"🐍 **Python:** `{python_ver}`\n"
            f"⚙️ **Platform:** `{platform.platform()}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )

        # Second edit with manual delay
        time.sleep(0.5)
        await status_msg.edit(premium_sys_info)
    except Exception as e:
        await message.reply(f"❌ Platform Error: {e}")

@astra_command(
    name="start",
    description="Description: Simple test to verify the bot and edit functionality.\nSyntax: .start\nExample: .start",
    usage=".start (bot health check)",
    aliases=["test"],
    owner_only=True
)
async def start_cmd(client: Client, message: Message):
    """Test command to verify bot responsiveness."""
    try:
        # First edit without delay
        msg = await message.reply("🤖 *Initializing Astra...*")
        
        # Second edit with manual delay
        time.sleep(0.5)
        await msg.edit("🤖 **Astra Userbot is active!**\n\nYour personal assistant is ready to serve. 🚀")
    except Exception as e:
        await message.reply(f"❌ Start Error: {e}")
