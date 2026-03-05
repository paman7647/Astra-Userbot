from utils.state import state

from . import *


@astra_command(
    name="pmpermit",
    description="Toggle PM Protection or permit/deny users",
    category="Owner",
    aliases=[],
    usage="<on|off|approve|deny> [user_id] (e.g. .pmpermit approve @123)",
    owner_only=True,
)
async def pmpermit_handler(client: Client, message: Message):
    """Toggle PM Protection or permit/deny users"""
    args_list = extract_args(message)

    if not args_list:
        status = "Active 🛡️" if state.get_config("ENABLE_PM_PROTECTION") else "Inactive 🔓"
        permitted_count = len(state.state.get("pm_permits", []))

        help_text = (
            f"🛡️ **Astra PM Security**\n━━━━━━━━━━━━━━━━━━━━\n"
            f"📍 **Status:** {status}\n"
            f"👥 **Permitted Users:** `{permitted_count}`\n"
            f"⚠️ **Warning Limit:** `{state.get_config('PM_WARN_LIMIT')}`\n\n"
            f"📝 **Commands:**\n"
            f"▫️ `.pmpermit <on|off>` - Toggle Protection\n"
            f"▫️ `.pmpermit approve` - Permit user (in reply or with ID)\n"
            f"▫️ `.pmpermit deny` - Revoke access\n"
            f"▫️ `.pmpermit list` - Show permitted users"
        )
        return await edit_or_reply(message, help_text)

    action = args_list[0].lower()

    if action == "on":
        state.set_config("ENABLE_PM_PROTECTION", True)
        await edit_or_reply(message, "✅ **Astra PM Security:** Protection Enabled! 🛡️")
    elif action == "off":
        state.set_config("ENABLE_PM_PROTECTION", False)
        await edit_or_reply(message, "🔓 **Astra PM Security:** Protection Disabled.")
    elif action in ["approve", "permit", "a"]:
        target_id = None
        if len(args_list) > 1:
            target_id = args_list[1]
        elif message.has_quoted_msg:
            quoted = message.quoted
            target_id = quoted.sender or quoted.chat_id
        elif not str(message.chat_id).endswith("@g.us"):
            target_id = message.chat_id

        if not target_id:
            return await edit_or_reply(
                message, "⚠️ **Astra PM Security:** Please provide a user ID or reply to a message."
            )

        # Handle JID objects or strings
        target_str = target_id.serialized if hasattr(target_id, "serialized") else str(target_id)
        if "@" not in target_str:
            target_str = f"{target_str}@c.us"

        # Normalization: Ensure we only store primary JID (stripping :x)
        if ":" in target_str.split("@", 1)[0]:
            target_str = target_str.split(":", 1)[0] + "@" + target_str.split("@", 1)[1]

        state.permit_user(target_str)
        name = await get_contact_name(client, target_str)
        await edit_or_reply(message, f"✅ **Astra PM Security:** `{name}` has been permitted to DM. 🛡️")

    elif action in ["deny", "d"]:
        target_id = None
        if len(args_list) > 1:
            target_id = args_list[1]
        elif message.has_quoted_msg:
            quoted = message.quoted
            target_id = quoted.sender or quoted.chat_id
        elif not str(message.chat_id).endswith("@g.us"):
            target_id = message.chat_id

        if not target_id:
            return await edit_or_reply(
                message, "⚠️ **Astra PM Security:** Please provide a user ID or reply to a message."
            )

        # Handle JID objects or strings
        target_str = target_id.serialized if hasattr(target_id, "serialized") else str(target_id)
        if "@" not in target_str:
            target_str = f"{target_str}@c.us"

        state.deny_user(target_str)
        name = await get_contact_name(client, target_str)
        await edit_or_reply(message, f"❌ **Astra PM Security:** `{name}` access has been revoked.")
    elif action == "list":
        permitted = state.state.get("pm_permits", [])
        if not permitted:
            return await edit_or_reply(message, "🚫 **Astra PM Security:** No users permitted yet.")

        list_text = "📑 **Astra Permitted Users:**\n━━━━━━━━━━━━━━━━━━━━\n"
        for i, uid in enumerate(permitted, 1):
            name = await get_contact_name(client, uid)
            list_text += f"{i}. **{name}** (`{uid.split('@')[0]}`)\n"

        await edit_or_reply(message, list_text)

    else:
        await edit_or_reply(message, "❌ **Astra PM Security:** Invalid action. Use on/off/approve/deny/list.")
