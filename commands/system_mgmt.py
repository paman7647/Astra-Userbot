# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

import os
import sys
import asyncio
import time
from . import *

@astra_command(
    name="restart",
    description="Restarts the bot process",
    category="System",
    owner_only=True
)
async def restart_cmd(client: Client, message: Message):
    """Restarts the bot process"""
    await smart_reply(message, "🚀 *Restarting Astra Userbot...*")
    # Wait a bit so the reply actually sends before we kill the process
    time.sleep(1.0)
    
    # Restart the application
    os.execv(sys.executable, [sys.executable] + sys.argv)

@astra_command(
    name="shutdown",
    description="Shuts down the bot process",
    category="System",
    owner_only=True
)
async def shutdown_cmd(client: Client, message: Message):
    """Shuts down the bot process"""
    await smart_reply(message, "🛑 *Shutting down Astra Userbot...*")
    # Wait a bit so the reply actually sends before we kill the process
    time.sleep(1.0)
    
    # Exit the application
    sys.exit(0)

@astra_command(
    name="update",
    description="Updates the bot from master branch",
    category="System",
    owner_only=True
)
async def update_cmd(client: Client, message: Message):
    """Updates the bot from git master branch"""
    status_msg = await smart_reply(message, "⏳ *Checking for updates and pulling from master...*")
    repo_url = "https://github.com/paman7647/Astra-Userbot-Userbot"
    
    try:
        # Check if it's a git repo
        is_repo = os.path.isdir(".git")
        if not is_repo:
            try:
                await status_msg.edit(f"📦 *Initializing git repository and linking to {repo_url}...*")
            except: pass
            process = await asyncio.create_subprocess_exec(
                'git', 'init',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            process = await asyncio.create_subprocess_exec(
                'git', 'remote', 'add', 'origin', repo_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

        # Run git pull origin master
        process = await asyncio.create_subprocess_exec(
            'git', 'pull', 'origin', 'master',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode().strip()
        stderr_text = stderr.decode().strip()
        
        if process.returncode == 0:
            if "Already up to date" in stdout_text:
                try:
                    await status_msg.edit(f"✅ *Astra Userbot is already up to date with {repo_url}.*")
                except:
                    await message.reply(f"✅ *Astra Userbot is already up to date with {repo_url}.*")
            else:
                # Limit the log so it doesn't overflow the message
                update_log = stdout_text[:1000]
                try:
                    await status_msg.edit(f"✅ *Update successful!*\n\n```\n{update_log}\n```\n\n*Restarting to apply changes...*")
                except:
                    await message.reply(f"✅ *Update successful!*\n\n```\n{update_log}\n```\n\n*Restarting to apply changes...*")
                time.sleep(1.5)
                os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            try:
                await status_msg.edit(f"❌ *Update failed!*\n\n```\n{stderr_text}\n```")
            except:
                await message.reply(f"❌ *Update failed!*\n\n```\n{stderr_text}\n```")
    except Exception as e:
        try:
            await status_msg.edit(f"❌ *Update Error:* {str(e)}")
        except:
            await message.reply(f"❌ *Update Error:* {str(e)}")

@astra_command(
    name="reload",
    description="Hot-reloads all plugins and project modules.",
    category="System",
    owner_only=True
)
async def reload_cmd(client: Client, message: Message):
    """Hot-reloads all plugins and project modules."""
    status_msg = await smart_reply(message, "⏳ *Hot-reloading Astra Userbot...*")
    
    try:
        from utils.plugin_utils import reload_all_plugins
        count = reload_all_plugins(client)
        
        await status_msg.edit(
            f"✅ **Reload Successful!**\n"
            f"📦 **Modules:** {count} plugins resynced.\n"
            f"🕒 **Time:** {time.strftime('%H:%M:%S')}"
        )
    except Exception as e:
        await report_error(client, e, context='Reload command failure')
