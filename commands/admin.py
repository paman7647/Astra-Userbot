import time

from utils.plugin_utils import PLUGIN_HANDLES, load_plugin, unload_plugin

from . import *


@astra_command(
    name="admin",
    description="Group administration commands.",
    category="Group Management",
    aliases=["group", "g"],
    usage="<kick|add|promote|demote|tagall|create|leave> [@user|title] (e.g. .admin kick @1234567890)",
    owner_only=True,
)
async def admin_handler(client: Client, message: Message):
    """Admin Tools"""
    args = getattr(message, "command", None)
    args_list = extract_args(message)

    if not args_list:
        usage = "<kick|add|promote|demote|tagall|create|leave> [@user|title]"
        return await edit_or_reply(message, f"⚠️ **Usage:** `{config.PREFIX}admin {usage}`")

    is_group = str(message.chat_id).endswith("@g.us")
    action = args_list[0].lower()

    import re

    if action == "create":
        if len(args_list) < 2:
            return await edit_or_reply(message, "Please provide a group title.")
        me = await client.get_me()
        participants = [str(me.id)]
        title_parts = []

        for arg in args_list[1:]:
            if arg.startswith("@"):
                participants.append(f"{arg[1:]}@c.us")
            elif re.match(r"^\d{8,15}$", arg):
                participants.append(f"{arg}@c.us")
            else:
                title_parts.append(arg)

        title = " ".join(title_parts)
        if not title:
            title = "New Group"

        if message.has_quoted_msg:
            quoted = message.quoted
            qid = str(quoted.sender or quoted.chat_id)
            if qid and qid not in participants:
                participants.append(qid)

        gid = await client.group.create(title, participants)
        try:
            invite_code = await client.group.get_invite_link(gid)
            invite_link = f"https://chat.whatsapp.com/{invite_code}"
        except:
            try:
                invite_code = await client.group.revoke_invite_link(gid)
                invite_link = f"https://chat.whatsapp.com/{invite_code}"
            except Exception as e:
                invite_link = f"(Failed to get invite link: {e})"

        await edit_or_reply(message, f" ✅ Group *{title}* created!\nID: `{gid}`\nLink: {invite_link}")
        return

    if not is_group:
        return await edit_or_reply(message, "This action only works in groups.")

    if action == "leave":
        await edit_or_reply(message, "👋 **Astra Admin:** Leaving group...")
        await client.group.leave(message.chat_id)
        return

    # Actions requiring a target
    target_ids = []

    # 1. Collect from mentions
    if message.mentioned_jids:
        target_ids.extend([str(jid) for jid in message.mentioned_jids])

    # 2. Collect from arguments (phone numbers or explicit JIDs)
    if len(args_list) > 1:
        for arg in args_list[1:]:
            raw = arg.replace("@", "").strip()
            if re.match(r"^\d{8,15}$", raw):
                target_ids.append(f"{raw}@c.us")
            elif raw.endswith("@c.us") or raw.endswith("@lid"):
                target_ids.append(raw)

    # 3. Collect from quoted message
    if not target_ids and message.has_quoted_msg:
        quoted = message.quoted
        qid = str(quoted.sender or quoted.chat_id)
        if qid:
            target_ids.append(qid)

    # Normalize and Deduplicate (Prevents double counting for s.whatsapp.net vs c.us)
    unique_targets = {}
    for jid in target_ids:
        clean = str(jid).replace("@s.whatsapp.net", "@c.us").strip()
        unique_targets[clean] = True

    target_ids = list(unique_targets.keys())
    # print(f"DEBUG: Targets for {action}: {target_ids}") # Uncomment for debugging if needed

    if action in ["kick", "remove"]:
        if not target_ids:
            return await edit_or_reply(message, "Mention users or reply to their message to kick.")
        await client.group.remove_participants(message.chat_id, target_ids)
        await edit_or_reply(message, f"Processed `{len(target_ids)}` removals.")

    elif action == "add":
        if not target_ids:
            return await edit_or_reply(message, "Provide user IDs, phone numbers or mention someone to add.")
        await client.group.add_participants(message.chat_id, target_ids)
        await edit_or_reply(message, f"Processed `{len(target_ids)}` additions.")

    elif action == "promote":
        if not target_ids:
            return await edit_or_reply(message, "Mention users to promote.")
        await client.group.promote_participants(message.chat_id, target_ids)
        await edit_or_reply(message, f"Processed `{len(target_ids)}` promotions.")

    elif action == "demote":
        if not target_ids:
            return await edit_or_reply(message, "Mention users to demote.")
        await client.group.demote_participants(message.chat_id, target_ids)
        await edit_or_reply(message, f"Processed `{len(target_ids)}` demotions.")

    elif action in ["tagall", "everyone"]:
        status = await edit_or_reply(message, "Tagging everyone...")
        info = await client.group.get_info(message.chat_id)
        if not info or not info.participants:
            time.sleep(0.5)
            return await status.edit("Failed to fetch group info.")

        text = "📢 **Everyone Check!** \n━━━━━━━━━━━━━━━━━━━━\n"
        mentions = []
        for p in info.participants:
            jid = str(p.id)
            mentions.append(jid)
            text += f" @{jid.split('@')[0]}"

        await client.send_message(message.chat_id, text, mentions=mentions)
        await status.delete()

    else:
        await edit_or_reply(message, " Unknown action. Use kick, add, promote, demote, tagall, create, leave.")


@astra_command(
    name="reload",
    description="Reload a plugin without restarting.",
    category="System",
    aliases=["re"],
    usage="<plugin_name> (e.g. meme)",
    owner_only=True,
)
async def reload_handler(client: Client, message: Message):
    """Reload a plugin dynamically."""
    import os

    args = extract_args(message)
    if not args:
        return await edit_or_reply(message, " Provide a plugin name to reload (or 'all').")

    target = args[0].lower()

    if target == "all":
        status_msg = await edit_or_reply(message, " 🔄 Reloading ALL plugins...")
        count = 0
        failed = []

        # Snapshot keys to avoid runtime dict change errors
        current_plugins = list(PLUGIN_HANDLES.keys())

        # Also scan directory to pick up NEW files
        commands_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(commands_dir):
            for f in os.listdir(commands_dir):
                if f.endswith(".py") and not f.startswith("_"):
                    p_name = f"commands.{f[:-3]}"
                    if p_name not in current_plugins:
                        current_plugins.append(p_name)

        for plugin in current_plugins:
            unload_plugin(client, plugin)
            if load_plugin(client, plugin):
                count += 1
            else:
                failed.append(plugin.split(".")[-1])

        if failed:
            time.sleep(0.5)
            await status_msg.edit(f" ⚠️ Reloaded {count} plugins.\nFailed: {', '.join(failed)}")
        else:
            time.sleep(0.5)
            await status_msg.edit(f" ✅ Successfully reloaded {count} plugins!")
        return

    # Single Plugin Logic
    # 1. Normalize name (e.g. 'meme' -> 'commands.meme')
    plugin_name = f"commands.{target}"

    # 2. Check if exists
    commands_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(commands_dir, f"{target}.py")

    if not os.path.exists(file_path) and plugin_name not in PLUGIN_HANDLES:
        return await edit_or_reply(message, f" ❌ Plugin '{target}' not found.")

    status_msg = await edit_or_reply(message, f" 🔄 Reloading `{target}`...")

    # 3. specific unload/load
    unload_plugin(client, plugin_name)
    time.sleep(0.5)
    if load_plugin(client, plugin_name):
        time.sleep(0.5)
        await status_msg.edit(f" ✅ Plugin `{target}` reloaded successfully!")
    else:
        time.sleep(0.5)
        await status_msg.edit(f" ❌ Failed to reload `{target}`. Check logs.")
