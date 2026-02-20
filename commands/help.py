# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from . import *

@astra_command(
    name="help",
    aliases=["h", "menu"],
    description="List all commands or get help for a specific one.",
    category="Utility",
    usage="[command]",
    is_public=True
)
async def help_handler(client: Client, message: Message):
    """
    Renders an interactive help menu by parsing the global COMMANDS_METADATA registry.
    """
    import logging
    import asyncio
    logger = logging.getLogger("Astra.Help")
    try:
        from utils.state import state
        curr_prefix = state.get_prefix()
        
        # Initial status message to provide the "editing" experience requested
        status_msg = await smart_reply(message, "📖 *Loading Astra Help Menu...*")
        
        args = extract_args(message)
        
        if args:
            # Normalize query: strip whitespace, handle case, and remove common command prefixes
            cmd_query = args[0].lower().strip().lstrip('.!/')
            
            # Search with robustness: check name and aliases
            cmd = None
            for entry in COMMANDS_METADATA:
                if entry['name'].lower() == cmd_query:
                    cmd = entry
                    break
                if any(alias.lower() == cmd_query for alias in entry.get('aliases', [])):
                    cmd = entry
                    break
            
            if not cmd:
                try:
                    return await status_msg.edit(f"❌ Command `{cmd_query}` not found.")
                except:
                    return await message.reply(f"❌ Command `{cmd_query}` not found.")
            
            # Compose detailed help
            help_text = f"📖 *Help:* `{curr_prefix}{cmd['name']}`\n"
            help_text += f"*Description:* {cmd['description']}\n"
            if cmd.get('aliases'):
                help_text += f"*Aliases:* `{curr_prefix}{f', {curr_prefix}'.join(cmd['aliases'])}`\n"
            help_text += f"*Category:* {cmd.get('category', 'General')}\n"
            help_text += f"*Usage:* `{curr_prefix}{cmd['name']} {cmd.get('usage', '')}`".strip()
            
            try:
                return await status_msg.edit(help_text)
            except:
                return await message.reply(help_text)

        # Get category grouping for main menu
        categories = {}
        # Log count to debug "not showing" issue
        logger.info(f"Generating help menu for {len(COMMANDS_METADATA)} commands")
        
        for cmd_entry in COMMANDS_METADATA:
            cat = cmd_entry.get('category', 'General')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(cmd_entry['name'])

        # Build Main menu
        help_text = "🚀 *Astra Userbot Menu*\n\n"
        for cat in sorted(categories.keys()):
            help_text += f"*{cat}*\n"
            cmds = sorted(categories[cat])
            help_text += f"`{', '.join([f'{curr_prefix}{c}' for c in cmds])}`\n\n"
        
        help_text += f"💡 Use `{curr_prefix}help <cmd>` for details."
        
        try:
            await status_msg.edit(help_text)
        except:
            await message.reply(help_text)

    except Exception as e:
        logger.error(f"Help command failed: {e}", exc_info=True)
        await smart_reply(message, f"❌ Help Error: {e}")
