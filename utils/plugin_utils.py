# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

from astra import Filters, Client
from utils.state import state
from config import config
from typing import List, Optional, Dict

# Central metadata registry for help command
COMMANDS_METADATA: List[Dict] = []

async def is_authorized(event) -> bool:
    """
    Checks if the event sender is the owner, a sudo user, or the bot account itself.
    """
    sender_id = getattr(event, 'sender_id', None) or getattr(event, 'chat_id', None)
    if not sender_id: return False
    
    # 1. From Me (Self/Bot Account)
    from_me = getattr(event, 'from_me', False)
    if from_me: return True
    
    # 2. Sudo Users
    if state.is_sudo(sender_id): return True
    
    # 3. Owner
    sender_num = sender_id.split('@')[0]
    if str(config.OWNER_ID) == sender_num: return True
    
    return False

async def is_owner(event) -> bool:
    """Strictly checks if the event sender is the bot owner."""
    sender_id = getattr(event, 'sender_id', None) or getattr(event, 'chat_id', None)
    if not sender_id: return False
    
    # Check if message is from the bot account itself (considered owner)
    if getattr(event, 'from_me', False): return True
    
    sender_num = sender_id.split('@')[0]
    return str(config.OWNER_ID) == sender_num

# Exported filters
authorized_filter = Filters.create(is_authorized)
owner_filter = Filters.create(is_owner)

def astra_command(
    name: str, 
    description: str = "", 
    category: str = "General", 
    aliases: Optional[List[str]] = None, 
    usage: str = "", 
    owner_only: bool = False,
    is_public: bool = False
):
    """
    Unified decorator for Astra Userbot commands.
    Registers the command as a native handler and stores metadata for the help menu.
    """
    if aliases is None: aliases = []
    
    # Register metadata (Replacing if exists)
    global COMMANDS_METADATA
    new_entry = {
        "name": name,
        "description": description,
        "category": category,
        "aliases": aliases,
        "usage": usage,
        "owner_only": owner_only,
        "is_public": is_public
    }
    # Mutate in-place to ensure all modules see the updates
    for i, cmd in enumerate(COMMANDS_METADATA):
        if cmd['name'] == name:
            COMMANDS_METADATA.pop(i)
            break
    COMMANDS_METADATA.append(new_entry)

    def decorator(func):
        # Build the native filter by ORing name and aliases
        # astra-engine's Filters.command only accepts single strings.
        names = [name] + aliases
        
        crit = Filters.command(names[0], prefixes="!./")
        for alias in names[1:]:
            crit |= Filters.command(alias, prefixes="!./")
            
        # Apply Authorization Logic
        # 1.owner_only: Only the configured owner can trigger.
        # 2.is_public: Everyone can trigger (useful for fun/info commands).
        # 3.Default: Only Sudo users and the Owner can trigger.
        if owner_only:
            crit = crit & owner_filter
        elif not is_public:
            crit = crit & authorized_filter
            
        # Register as a class-level handler for Client.load_plugins()
        Client.on_message(crit)(func)
        return func
    return decorator

def extract_args(message) -> List[str]:
    """
    Safely extracts command arguments from a message object.
    Handles distinct cases where message.command is an object or string,
    or falls back to manual body parsing.
    """
    try:
        args_attr = getattr(message, 'command', None)
        
        # Case 1: Filter attached an object with .args (Standard Astra)
        if args_attr and not isinstance(args_attr, str) and hasattr(args_attr, 'args'):
            return args_attr.args
            
        # Case 2: Filter attached a list (Some versions)
        if isinstance(args_attr, list):
            return args_attr
            
        # Case 3: Fallback - Manual Body Parsing
        body = getattr(message, 'body', "") or ""
        parts = body.split()
        if len(parts) > 1:
            return parts[1:]
            
    except Exception:
        pass
        
    return []

# --- Dynamic Plugin Loading System ---
import sys
import importlib
import logging

logger = logging.getLogger("Astra.Plugins")
PLUGIN_HANDLES: Dict[str, List[int]] = {}

def load_plugin(client: Client, plugin_name: str) -> bool:
    """
    Loads or reloads a plugin module and registers its handlers.
    """
    try:
        # 1. Import or Reload Module
        if plugin_name in sys.modules:
            module = importlib.reload(sys.modules[plugin_name])
            logger.info(f"Reloaded plugin: {plugin_name}")
        else:
            module = importlib.import_module(plugin_name)
            logger.info(f"Loaded plugin: {plugin_name}")

        # 2. Register Handlers
        handles = []
        if hasattr(Client, '_class_handlers'):
            for event, func, criteria in Client._class_handlers:
                # Wrap handler to inject 'client' (self) as first argument
                async def wrapper(event_payload, _f=func):
                    return await _f(client, event_payload)
                
                # Register and capture handle
                # client.on returns a decorator, calling it registers and returns handle
                handle = client.on(event, criteria=criteria)(wrapper)
                handles.append(handle)
            
            Client._class_handlers.clear()
        
        PLUGIN_HANDLES[plugin_name] = handles
        return True

    except Exception as e:
        logger.error(f"Failed to load plugin {plugin_name}: {e}", exc_info=True)
        return False

def unload_plugin(client: Client, plugin_name: str):
    """
    Unregisters all handlers associated with a plugin.
    """
    if plugin_name in PLUGIN_HANDLES:
        for handle in PLUGIN_HANDLES[plugin_name]:
            client.events.off(handle)
        
        # Remove from metadata registry
        global COMMANDS_METADATA
        COMMANDS_METADATA = [cmd for cmd in COMMANDS_METADATA if not str(cmd.get('name', '')).startswith(f"{plugin_name}.")]
        # Note: If duplicate names exist across modules, this might be tricky,
        # but astra_command handles deduplication by name anyway.
        
        del PLUGIN_HANDLES[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")

def reload_all_plugins(client: Client) -> int:
    """
    Hot-reloads all plugins and project modules without restarting the client.
    """
    import os
    import sys
    import importlib
    import pkgutil
    from pathlib import Path

    from astra import Client as AstraClient

    # 0. Emergency Patch: If Client.fetch_messages is old, update it dynamically
    # This allows engine changes to apply via reload!
    async def _patched_fetch(self, *args, **kwargs):
        return await self.chat.fetch_messages(*args, **kwargs)
    
    if "args" not in str(AstraClient.fetch_messages.__code__.co_varnames):
        logger.info("Applying dynamic patch to Client.fetch_messages...")
        AstraClient.fetch_messages = _patched_fetch
        # Also patch the live instance
        client.fetch_messages = _patched_fetch.__get__(client, AstraClient)

    # 1. Capture and Unload
    current_plugins = list(PLUGIN_HANDLES.keys())
    for p in current_plugins:
        unload_plugin(client, p)
    
    # 2. Core Project Reload
    # We identify modules belonging to the bot (excluding 'astra' engine)
    project_root = str(Path(__file__).parent.parent.resolve())
    
    to_reload = []
    for name, mod in list(sys.modules.items()):
        if not mod or not hasattr(mod, "__file__") or not mod.__file__:
            continue
        
        mod_path = str(Path(mod.__file__).resolve())
        if project_root in mod_path and "astra/" not in mod_path.replace(project_root, ""):
            if name != "__main__" and name != "utils.plugin_utils": # Reload us last or not at all?
                to_reload.append(name)

    # Reload Config & Utils first
    to_reload.sort(key=lambda x: (0 if "config" in x or "utils" in x else 1, x))
    
    for mod_name in to_reload:
        try:
            importlib.reload(sys.modules[mod_name])
        except Exception as e:
            logger.debug(f"Could not reload {mod_name}: {e}")

    # 3. Discovery & Load
    commands_dir = os.path.join(project_root, "commands")
    success = 0
    if os.path.exists(commands_dir):
        # Clear metadata to start fresh
        global COMMANDS_METADATA
        COMMANDS_METADATA.clear()
        
        for loader, mod_name, is_pkg in pkgutil.walk_packages([commands_dir], prefix="commands."):
            if load_plugin(client, mod_name):
                success += 1
                
    return success
