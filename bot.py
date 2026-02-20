# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Astra Userbot Core
------------------
Main entry point for the Astra Userbot. Handles initialization, 
plugin loading, and event loop management.

License: MIT
Copyright (c) 2026 Aman Kumar Pandey
"""

import asyncio
import logging
import os
import sys
import signal
from typing import Optional

# Initialization
# --------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/paman7647/Downloads/whatsapp-web.js-main")

from astra import Client, Filters

# Environment & Logging Setup
# --------------------------

# Logging setup is critical for production visibility.
# Logging setup is critical for production visibility.
# We configure a specific formatter and handlers to capture all levels.
log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')

file_handler = logging.FileHandler(os.path.join(SCRIPT_DIR, "astra_full_debug.txt"), mode='w')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.DEBUG, # Set root logger to DEBUG to allow all logs through
    handlers=[file_handler, stream_handler]
)

logger = logging.getLogger("AstraBot")

# Initial configuration load
from config import config

# Global Client Instance
# ---------------------
# We initialize the client using settings from the environment.
client = Client(
    session_id=os.getenv("ASTRA_SESSION_ID", "userbot"),
    phone=os.getenv("PHONE_NUMBER"),
    headless=os.getenv("ASTRA_HEADLESS", "True").lower() == "true"
)

# Event Handlers
# --------------

@client.on("ready")
async def on_ready(_):
    """
    Executed when the WhatsApp connection is established and the engine is ready.
    Initializes plugins, database, and sends a startup notification.
    """
    try:
        user = await client.get_me()
        
        print("\n" + "="*40)
        print(f"🚀 ASTRA USERBOT IS ONLINE!")
        print(f"👤 Logged in as: {user.name} ({user.id})")
        print(f"📦 Version: {config.VERSION}")
        print("="*40 + "\n")
        
        # 1. Initialize Persistent State Manager
        from utils.state import state
        await state.initialize()
        
        # 2. Dynamic Plugin Discovery
        # We scan the commands directory for all valid python plugins.
        commands_dir = os.path.join(SCRIPT_DIR, "commands")
        if os.path.exists(commands_dir):
            from utils.plugin_utils import load_plugin
            
            loaded_plugins = []
            for f in os.listdir(commands_dir):
                if f.endswith(".py") and not f.startswith("_"):
                    plugin_name = f"commands.{f[:-3]}"
                    if load_plugin(client, plugin_name):
                        loaded_plugins.append(f[:-3])
            
            logger.info(f"Initialized {len(loaded_plugins)} modules: {', '.join(loaded_plugins)}")
            print(f"📦 Modules: {len(loaded_plugins)} loaded.")

        # 3. Connectivity Notification
        # Send a brief status update to the self-chat.
        try:
            target_id = user.id.serialized if hasattr(user.id, "serialized") else str(user.id)
            msg = await client.send_message(
                target_id, 
                f"🤖 **Astra Userbot Online!**\nBuild: `dev-beta` (v{config.VERSION})"
            )
            await msg.react("✅")
        except Exception as notify_err:
             logger.debug(f"Self-notification suppressed: {notify_err}")

    except Exception as e:
        logger.error(f"Critical error during startup sequence: {e}", exc_info=True)

# Application Lifecycle
# --------------------

async def shutdown(sig: Optional[signal.Signals] = None):
    """Gracefully shuts down the client and handles any cleanup."""
    if sig:
        logger.info(f"Received exit signal {sig.name}...")
    
    logger.info("Closing client session...")
    try:
        if client.is_connected:
            await client.stop()
    except Exception as e:
        logger.debug(f"Error during client stop: {e}")
    
    logger.info("Astra Userbot stopped. Goodbye!")
    sys.exit(0)


import os
import subprocess
from aiohttp import web

async def health_check(request):
    """Simple health check endpoint for Render to prevent the web service from sleeping/failing."""
    return web.Response(text="Astra Userbot Web Environment is healthy and active.", status=200)

app = web.Application()
app.router.add_get('/', health_check)
app.router.add_get('/health', health_check)
async def main():
    """Main runner for the Astra Userbot."""
    # Register OS signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    # Start the client engine
    
    async with client:
        logger.info("Astra Engine active. Listening for events...")
        await web.run_app(app, host='0.0.0.0', port=10000)
        await client.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as fatal_err:
        logger.critical(f"FATAL: Application crashed: {fatal_err}", exc_info=True)
        sys.exit(1)
