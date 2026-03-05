import json

from utils.state import state

from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="db",
    description="🛠️ Advanced Database & State Manager. Directly manipulate bot memory.",
    category="System",
    usage="set <key> <value> | get <key> | list | del <key>",
    owner_only=True,
)
async def db_tool_handler(client: Client, message: Message):
    """Developer tool for real-time state and database manipulation."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, f"❌ **Usage:** `{state.get_prefix()}db <set/get/list/del> [args]`")

    sub = args[0].lower()

    # 1. DB SET
    if sub == "set" and len(args) >= 3:
        key = args[1]
        raw_val = " ".join(args[2:])
        # Try to parse as JSON for complex types, fallback to string
        try:
            val = json.loads(raw_val)
        except:
            val = raw_val

        state.set_config(key, val)
        return await edit_or_reply(message, f"✅ **DB Update:** `{key}` set to `{val}`")

    # 2. DB GET
    elif sub == "get" and len(args) >= 2:
        key = args[1]
        val = state.get_config(key)
        if val is None:
            # Check top-level state too
            val = state.state.get(key, "Not Found")

        return await edit_or_reply(message, f"🔎 **Key:** `{key}`\n📦 **Value:** `{val}`")

    # 3. DB LIST
    elif sub == "list":
        configs = state.get_all_configs()
        if not configs:
            return await edit_or_reply(message, "📂 **DB:** No custom overrides found.")

        list_text = "📂 **DATABASE OVERRIDES**\n━━━━━━━━━━━━━━━━━━━━\n"
        for k, v in configs.items():
            list_text += f"🔹 `{k}`: `{v}`\n"
        return await edit_or_reply(message, list_text)

    # 4. DB DELETE
    elif sub in ["del", "delete", "rm"] and len(args) >= 2:
        key = args[1]
        if key in state.state["configs"]:
            del state.state["configs"][key]
            from utils.database import db as db_core

            asyncio.create_task(db_core.set("configs", state.state["configs"]))
            return await edit_or_reply(message, f"🗑️ **DB:** Deleted override `{key}`.")
        return await edit_or_reply(message, f"❌ **DB:** Override `{key}` not found.")

    return await edit_or_reply(message, "❌ Invalid sub-command. Use `set`, `get`, `list`, or `del`.")


@astra_command(
    name="setcfg",
    description="⚙️ Manage bot configuration dynamically.",
    category="System",
    aliases=["updatecfg"],
    usage="<key> <value> (e.g. .setcfg FAST_MEDIA on)",
    owner_only=True,
)
async def setcfg_handler(client: Client, message: Message):
    """User-friendly frontend for dynamic configuration."""
    args = extract_args(message)
    if not args:
        # Show help if no args
        help_text = (
            "⚙️ **DYNAMIC CONFIGURATION**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 **Common Keys:**\n"
            "🔹 `FAST_MEDIA`: `on/off` (Hide progress bars)\n"
            "🔹 `BOT_NAME`: Your custom bot brand name\n"
            "🔹 `COMMAND_PREFIX`: Change prefix instantly\n\n"
            f"**Usage:** `{state.get_prefix()}setcfg <key> <value>`"
        )
        return await edit_or_reply(message, help_text)

    if len(args) < 2:
        return await edit_or_reply(message, " ⚠️ Usage: `.setcfg <key> <value>`")

    key = args[0].upper()
    val_raw = " ".join(args[1:])

    # Map boolean-like strings
    low_val = val_raw.lower()
    if low_val in ["on", "true", "yes", "enabled"]:
        val = True
    elif low_val in ["off", "false", "no", "disabled"]:
        val = False
    else:
        val = val_raw

    # Logic for specific keys
    if key == "COMMAND_PREFIX":
        state.set_prefix(val)
    else:
        state.set_config(key, val)

    await edit_or_reply(message, f"✨ **Config Updated:** `{key}` is now `{val}`")


@astra_command(
    name="delcfg",
    description="🗑️ Delete a dynamic configuration key.",
    category="System",
    usage="<key> (e.g. .delcfg ALIVE_IMG)",
    owner_only=True,
)
async def delcfg_handler(client: Client, message: Message):
    """Deletes a custom configuration from the database."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " ⚠️ Usage: `.delcfg <key>`")

    key = args[0].upper()

    if key in state.state.get("configs", {}):
        del state.state["configs"][key]
        import asyncio

        from utils.database import db as db_core

        asyncio.create_task(db_core.set("configs", state.state["configs"]))
        await edit_or_reply(message, f"🗑️ **Config Deleted:** `{key}`")
    else:
        await edit_or_reply(message, f"❌ **Config Not Found:** `{key}`")


@astra_command(
    name="getcfg",
    description="🔎 Retrieve the value of a dynamic configuration key.",
    category="System",
    usage="<key> (e.g. .getcfg ALIVE_IMG)",
    owner_only=True,
)
async def getcfg_handler(client: Client, message: Message):
    """Retrieves a custom configuration."""
    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " ⚠️ Usage: `.getcfg <key>`")

    key = args[0].upper()
    val = state.get_config(key)

    if val is not None:
        await edit_or_reply(message, f"🔎 **Config `{key}`:** `{val}`")
    else:
        # Fallback check
        val = state.state.get(key)
        if val is not None:
            await edit_or_reply(message, f"🔎 **Core State `{key}`:** `{val}`")
        else:
            await edit_or_reply(message, f"❌ **Config Not Found:** `{key}`")


@astra_command(
    name="listcfg",
    description="📋 List all currently set dynamic configuration keys.",
    category="System",
    aliases=["configs", "cfgs"],
    owner_only=True,
)
async def listcfg_handler(client: Client, message: Message):
    """Lists all custom configurations."""
    configs = state.get_all_configs()

    if not configs:
        return await edit_or_reply(message, "📂 **Configuration:** No dynamic overrides are currently set.")

    list_text = "📋 **ACTIVE DYNAMIC CONFIGS**\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for k, v in configs.items():
        # Mask sensitive keys
        if "API" in k or "TOKEN" in k or "KEY" in k or "PASSWORD" in k:
            list_text += f"🔹 `{k}`: `********`\n"
        else:
            list_text += f"🔹 `{k}`: `{v}`\n"

    list_text += "━━━━━━━━━━━━━━━━━━━━━━\n💡 _Use `.delcfg <key>` to remove an override._"

    await edit_or_reply(message, list_text)


@astra_command(
    name="sysvars",
    description="📖 View a list of all official dynamic system configuration keys.",
    category="System",
    aliases=["cfghints", "vars"],
    owner_only=True,
)
async def sysvars_handler(client: Client, message: Message):
    """Provides a cheat sheet of all dynamic configurations supported by the bot."""

    docs = (
        "📖 **ASTRA SYSTEM VARIABLES**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Use `.setcfg <key> <value>` to change these._\n\n"
        "⚙️ **Core & Access**\n"
        "🔹 `COMMAND_PREFIX`: Bot prefix (e.g. `.` or `!`)\n"
        "🔹 `BOT_NAME`: Your custom bot brand name\n"
        "🔹 `ALLOW_MULTI_PREFIX`: `on/off` (Allow `.`, `!`, `/`)\n\n"
        "🚀 **Media Engine**\n"
        "🔹 `FAST_MEDIA`: `on/off` (Hide progress bars for speed)\n"
        "🔹 `ENABLE_MEDIA_CACHE`: `on/off` (Instant duplicate dl)\n"
        "🔹 `CACHE_AUTO_DELETE`: `on/off` (Delete cache > 2hrs)\n"
        "🔹 `ALIVE_IMG`: Custom URL for the `.alive` command\n\n"
        "🛡️ **Security & PMs**\n"
        "🔹 `ENABLE_PM_PROTECTION`: `on/off` (Anti-spam in PMs)\n"
        "🔹 `PM_WARN_LIMIT`: `number` (Max warnings before block)\n\n"
        "🤖 **Third-Party APIs**\n"
        "🔹 `GEMINI_API_KEY`: Your Google AI Studio key\n"
        "🔹 `NEWS_GEMINI_API_KEY`: Key for `.technews`\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔍 _Use `.listcfg` to see your currently active overrides._"
    )

    await edit_or_reply(message, docs)
