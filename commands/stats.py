# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import psutil
import time
from . import *

@astra_command(
    name="stats",
    description="Description: View detailed system health, memory usage, and runtime metrics.\nSyntax: .stats\nExample: .stats",
    category="Utility",
    aliases=["status", "sysinfo"],
    usage=".stats (display bot statistics)",
    is_public=True
)
async def stats_handler(client: Client, message: Message):
    """Aggregates system metrics for a professional health report."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        
        # Resolve Uptime (Core logic preserved)
        uptime_val = time.time() - process.create_time()
        hours, rem = divmod(int(uptime_val), 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        # Professional Premium Formatting
        stats_text = (
            "📊 **ASTRA RUNTIME ANALYTICS** 📊\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ **Uptime:** `{uptime_str}`\n"
            f"🧠 **Memory:** `{round(mem_info.rss / 1024 / 1024, 2)} MB`\n"
            f"⚡ **CPU Load:** `{psutil.cpu_percent()}%`\n"
            f"🚀 **Process ID:** `{os.getpid()}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "✨ *System is running optimally.*"
        )
    
        await smart_reply(message, stats_text)

    except Exception as e:
        await smart_reply(message, " ⚠️ Failed to retrieve system statistics.")
        await report_error(client, e, context='Stats command reporting failure')
