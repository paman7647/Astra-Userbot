import os
import time

import psutil

from . import *


@astra_command(
    name="stats",
    description="Description: View detailed system health, memory usage, and runtime metrics.\nSyntax: .stats\nExample: .stats",
    category="System",
    aliases=[],
    usage=".stats (display bot statistics)",
    is_public=True,
)
async def stats_handler(client: Client, message: Message):
    """Aggregates system metrics for a professional health report."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()

    # Resolve Uptime (Core logic preserved)
    uptime_val = time.time() - process.create_time()
    hours, rem = divmod(int(uptime_val), 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"

    # Analytics: Fetch usage data
    from utils.database import db

    total_cmds = await db.get("total_commands_v1", 0)

    # Fetch Top 3 Commands
    top_cmds_text = "None"
    try:
        cursor = await db.sqlite_conn.execute(
            "SELECT key, value FROM state WHERE key LIKE 'cmd_usage:%' ORDER BY CAST(json_extract(value, '$') AS INTEGER) DESC LIMIT 3"
        )
        rows = await cursor.fetchall()
        if rows:
            import json
            top_cmds_text = ", ".join([f"`{r[0].split(':')[-1]}` ({json.loads(r[1])})" for r in rows])
    except:
        pass

    # Professional Premium Formatting
    stats_text = (
        "📊 **ASTRA RUNTIME ANALYTICS** 📊\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ **Uptime:** `{uptime_str}`\n"
        f"🧠 **Memory:** `{round(mem_info.rss / 1024 / 1024, 2)} MB`\n"
        f"⚡ **CPU Load:** `{psutil.cpu_percent()}%`\n"
        f"🛰️ **Commands:** `{total_cmds}` processed\n"
        f"🏆 **Top Hooks:** {top_cmds_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨ *System is running optimally.*"
    )

    await smart_reply(message, stats_text)
