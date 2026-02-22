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
"""

import asyncio
import logging
import os
import sys
import signal
from typing import Optional

# Setup Script Directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


from astra import Client, Filters, Message
from utils.logger import setup_logging, Colors

# 1. Initialize Modern Logging
setup_logging(SCRIPT_DIR)
logger = logging.getLogger("AstraBot")

# Initial configuration load
from config import config

def print_banner():
    """Renders a futuristic, minimalist branding banner."""
    import socket
    ip = "127.0.0.1"
    try: ip = socket.gethostbyname(socket.gethostname())
    except: pass
    
    # Futuristic thin-line layout
    print(f"\n {Colors.BOLD}{Colors.CYAN}ASTRA{Colors.END} {Colors.GRAY}MANAGED INSTANCE{Colors.END}")
    print(f" {Colors.GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}")
    print(f" {Colors.CYAN}IDENT{Colors.END}  {Colors.BOLD}userbot{Colors.END} {Colors.GRAY}@{Colors.END} {config.VERSION}")
    print(f" {Colors.CYAN}NETID{Colors.END}  {Colors.BOLD}{ip}{Colors.END} {Colors.GRAY}»{Colors.END} {Colors.GREEN}SECURE{Colors.END}")
    print(f" {Colors.CYAN}STATE{Colors.END}  {Colors.BOLD}ACTIVE{Colors.END}   {Colors.GRAY}»{Colors.END} {Colors.BLUE}HEADLESS{Colors.END}")
    print(f" {Colors.CYAN}PROC {Colors.END}  {Colors.BOLD}{os.getpid()}{Colors.END}   {Colors.GRAY}»{Colors.END} {Colors.BOLD}STABLE{Colors.END}")
    print(f" {Colors.GRAY}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.END}\n")

# Bridge Patch for Web Dashboard
def patch_authenticator(client_instance):
    """
    Redirects QR and Pairing code data to files for the web dashboard (render.py).
    """
    auth = client_instance.authenticator
    original_qr = auth._display_qr
    original_code = auth._display_code
    
    def patched_qr(data):
        with open(os.path.join(SCRIPT_DIR, "qr_data.txt"), "w") as f:
            f.write(data)
        original_qr(data)
        
    def patched_code(code):
        with open(os.path.join(SCRIPT_DIR, "pairing_code.txt"), "w") as f:
            f.write(code)
        original_code(code)
    
    auth._display_qr = patched_qr
    auth._display_code = patched_code
    logger.info("✅ Authenticator patched for Web Dashboard support.")

# Global Client Instance
client = Client(
    session_id=os.getenv("ASTRA_SESSION_ID", "userbot"),
    phone=os.getenv("PHONE_NUMBER"),
    headless=os.getenv("ASTRA_HEADLESS", "False").lower() == "true"
)

# Apply patch immediately
patch_authenticator(client)

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
        
        print_banner()
        logger.info(f"🚀 ASTRA USERBOT IS ONLINE! Logged in as: {user.name}")

        
        # 1. Initialize Persistent State Manager
        from utils.state import state
        await state.initialize()
        
        # 2. Dynamic Plugin Discovery
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
        try:
            target_id = user.id.serialized if hasattr(user.id, "serialized") else str(user.id)
            msg = await client.send_message(
                target_id, 
                f"🤖 **Astra Userbot Online!**\nBuild: `dev-beta` (v{config.VERSION})"
            )
            await msg.react("✅")
        except Exception as notify_err:
             logger.debug(f"Self-notification failed: {notify_err}")

    except Exception as e:
        logger.error(f"Critical error during startup sequence: {e}", exc_info=True)

# 4. PM Protection Integration
# ---------------------------
from utils.pm_permit_manager import enforce_pm_protection

@client.on("message")
async def pm_protection_listener(msg: Message):
    """
    Global listener for PM protection enforcement.
    Intercepts messages in private chats and applies security filters.
    """
    try:
        # We don't block messages that already have a command match 
        # unless you want extreme protection. Usually, unpermitted 
        # users shouldn't even trigger commands.
        # Here we just run the enforcement logic.
        await enforce_pm_protection(client, msg)
    except Exception as e:
        logger.error(f"Error in PM protection listener: {e}")

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


async def main():
    """Main runner for the Astra Userbot."""
    # Register OS signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    # Start the client engine
    async with client:
        logger.info("Astra Engine active. Listening for events...")
        await client.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as fatal_err:
        logger.critical(f"FATAL: Application crashed: {fatal_err}", exc_info=True)
        sys.exit(1)
