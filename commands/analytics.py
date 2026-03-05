import json
import time

from utils.database import db

from . import *


@astra_command(
    name="analytics",
    description="Detailed command usage and bot engagement report.",
    category="System",
    owner_only=True,
)
async def analytics_handler(client: Client, message: Message):
    """Owner-only analytics dashboard."""
    status_msg = await edit_or_reply(message, "📊 **Generating Astra Intelligence Report...**")

    # 1. Fetch Total Stats
    total_cmds = await db.get("total_commands_v1", 0)

    # 2. Fetch Full Usage List
    cursor = await db.sqlite_conn.execute(
        "SELECT key, value FROM state WHERE key LIKE 'cmd_usage:%' ORDER BY CAST(json_extract(value, '$') AS INTEGER) DESC"
    )
    rows = await cursor.fetchall()

    usage_lines = []
    for i, row in enumerate(rows):
        cmd = row[0].split(":")[-1]
        count = json.loads(row[1])
        usage_lines.append(f"{i + 1}. `{cmd}`: **{count}**")

    usage_text = "\n".join(usage_lines[:20]) if usage_lines else "_No data recorded yet._"
    if len(usage_lines) > 20:
        usage_text += f"\n\n_...and {len(usage_lines) - 20} more commands._"

    report = (
        f"📈 **ASTRA ANALYTICS DASHBOARD**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 **Total Commands:** `{total_cmds}`\n"
        f"🕒 **Snapshot at:** `{time.strftime('%H:%M:%S')}`\n\n"
        f"🔥 **COMMAND ATTRIBUTIONS (Top 20)**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{usage_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *Tracking enabled in Astra Engine v1.1*"
    )

    await status_msg.edit(report)
