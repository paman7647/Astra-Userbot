from . import *
from utils.helpers import edit_or_reply


@astra_command(
    name="afk",
    description="Set AFK status.",
    category="Tools & Utilities",
    aliases=[],
    usage="[reason] (optional; e.g. 'dinner')",
    owner_only=True,
)
async def afk_handler(client: Client, message: Message):
    """Set AFK status."""
    args_list = extract_args(message)
    from utils.state import state

    if args_list and args_list[0].lower() in ["off", "false", "disable"]:
        if state.get_afk()["is_afk"]:
            state.set_afk(False)
            await edit_or_reply(message, "☀️ **Astra AFK Mode:** Disabled manually.")
        else:
            await edit_or_reply(message, "⚠️ **Astra AFK Mode:** Already disabled.")
        return

    reason = " ".join(args_list) if args_list else "Currently away."
    state.set_afk(True, reason)
    await edit_or_reply(
        message,
        f"🌙 **Astra AFK Mode Enabled**\n━━━━━━━━━━━━━━━━━━━━\n💬 **Reason:** `{reason}`\n\n_Type `.afk off` to disable._",
    )


@Client.on_message(Filters.all & ~Filters.me)
async def afk_mention_responder(client: Client, message: Message):
    """Responds to mentions or DMs when the owner is AFK."""
    try:
        from utils.state import state

        afk_state = state.get_afk()
        if not afk_state["is_afk"]:
            return

        is_tagged = False
        me = await client.get_me()
        my_num = str(me.id).split("@")[0]

        if f"@{my_num}" in (message.body or ""):
            is_tagged = True

        if not str(message.chat_id).endswith("@g.us") or is_tagged:
            await edit_or_reply(
                message, f"🌙 **Astra User is AFK**\n━━━━━━━━━━━━━━━━━━━━\n💬 **Reason:** `{afk_state['reason']}`"
            )
    except Exception:
        pass
