# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *
import time
from utils.plugin_utils import load_plugin, unload_plugin, PLUGIN_HANDLES

@astra_command(
    name="admin",
    description="Group administration commands.",
    category="Group",
    aliases=["group", "g"],
    usage="<kick|add|promote|demote|tagall|create|leave> [@user|title]",
    owner_only=True
)
async def admin_handler(client: Client, message: Message):
    """Group administration commands."""
    args = getattr(message, 'command', None)
    args_list = extract_args(message)
    
    if not args_list:
        usage = "<kick|add|promote|demote|tagall|create|leave> [@user|title]"
        return await smart_reply(message, f" *Usage:* `.admin {usage}`")
    
    is_group = message.chat_id.endswith('@g.us')
    action = args_list[0].lower()

    try:
        if action == 'create':
            if len(args_list) < 2: return await smart_reply(message, "Please provide a group title.")
            title = " ".join(args_list[1:])
            me = await client.get_me()
            participants = [me.id]
            
            if message.has_quoted_msg:
                quoted = message.quoted
                qid = quoted.author or quoted.chat_id
                if qid and qid not in participants: participants.append(qid)
            
            gid = await client.group.create(title, participants)
            await smart_reply(message, f" ✅ Group *{title}* created!\nID: `{gid}`")
            return

        if not is_group:
            return await smart_reply(message, " This action only works in groups.")

        if action == 'leave':
            await smart_reply(message, " 👋 Leaving group...")
            await client.group.leave(message.chat_id)
            return

        # Actions requiring a target
        target_id = None
        if len(args_list) > 1:
            target_id = args_list[1].replace('@', '').strip()
            if not target_id.endswith('@c.us') and not target_id.endswith('@lid'): 
                target_id = f"{target_id}@c.us"
        elif message.has_quoted_msg:
            quoted = message.quoted
            target_id = quoted.author or quoted.chat_id
        
        if action in ['kick', 'remove']:
            if not target_id: return await smart_reply(message, " Mention a user or reply to their message to kick.")
            await client.group.remove_participants(message.chat_id, [target_id])
            await smart_reply(message, " 💥 User removed.")
        
        elif action == 'add':
            if not target_id: return await smart_reply(message, " Provide a user ID or mention someone to add.")
            await client.group.add_participants(message.chat_id, [target_id])
            await smart_reply(message, " ➕ User added.")

        elif action == 'promote':
            if not target_id: return await smart_reply(message, " Mention a user to promote.")
            await client.group.promote_participants(message.chat_id, [target_id])
            await smart_reply(message, " 🛡️ User promoted to Admin.")

        elif action == 'demote':
            if not target_id: return await smart_reply(message, " Mention a user to demote.")
            await client.group.demote_participants(message.chat_id, [target_id])
            await smart_reply(message, " 👤 User demoted.")

        elif action in ['tagall', 'everyone']:
            status = await smart_reply(message, " 📢 Tagging everyone...")
            info = await client.group.get_info(message.chat_id)
            if not info or not info.participants: 
                try:
                    return await status.edit(" Failed to fetch group info.")
                except:
                    return await message.reply(" Failed to fetch group info.")
            
            text = " 📢 *Everyone Check!* \n\n"
            mentions = []
            for p in info.participants:
                jid = str(p.id)
                mentions.append(jid)
                text += f" @{jid.split('@')[0]}"
            
            await client.send_message(message.chat_id, text, mentions=mentions)
            await status.delete()

        else:
            await smart_reply(message, " Unknown action. Use kick, add, promote, demote, tagall, create, leave.")

    except Exception as e:
        await smart_reply(message, f" ❌ Error: `{str(e)}`")

@astra_command(
    name="reload",
    description="Reload a plugin without restarting.",
    category="System",
    aliases=["re"],
    usage="<plugin_name>",
    owner_only=True
)
async def reload_handler(client: Client, message: Message):
    """Reload a plugin dynamically."""
    try:
        import os
        import sys
        
        args = extract_args(message)
        if not args:
            return await smart_reply(message, " Provide a plugin name to reload (or 'all').")
            
        target = args[0].lower()
        
        if target == 'all':
             status_msg = await smart_reply(message, " 🔄 Reloading ALL plugins...")
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
                     failed.append(plugin.split('.')[-1])
             
             if failed:
                 try:
                     await status_msg.edit(f" ⚠️ Reloaded {count} plugins.\nFailed: {', '.join(failed)}")
                 except: pass
             else:
                 try:
                     await status_msg.edit(f" ✅ Successfully reloaded {count} plugins!")
                 except: pass
             return

        # Single Plugin Logic
        # 1. Normalize name (e.g. 'meme' -> 'commands.meme')
        plugin_name = f"commands.{target}"
        
        # 2. Check if exists
        commands_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(commands_dir, f"{target}.py")
        
        if not os.path.exists(file_path) and plugin_name not in PLUGIN_HANDLES:
             return await smart_reply(message, f" ❌ Plugin '{target}' not found.")

        status_msg = await smart_reply(message, f" 🔄 Reloading `{target}`...")
        
        # 3. specific unload/load
        unload_plugin(client, plugin_name)
        if load_plugin(client, plugin_name):
            try:
                await status_msg.edit(f" ✅ Plugin `{target}` reloaded successfully!")
            except: pass
        else:
            try:
                await status_msg.edit(f" ❌ Failed to reload `{target}`. Check logs.")
            except: pass

    except Exception as e:
         await smart_reply(message, f" ❌ Reload Error: {e}")
