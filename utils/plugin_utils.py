import asyncio
from typing import Dict, List, Optional

from config import config
from utils.state import state

from astra import Client, Filters, Message

# Central metadata registry for help command
COMMANDS_METADATA: List[Dict] = []


async def is_authorized(event) -> bool:
    """
    Checks if the event sender is the owner, a sudo user, or the bot account itself.
    """
    sender_id = getattr(event, "sender_id", None) or getattr(event, "chat_id", None)
    if not sender_id:
        return False

    # 1. From Me (Self/Bot Account)
    from_me = getattr(event, "from_me", False)
    if from_me:
        return True

    # Normalize sender_id for lookup (Primary JID only, handle multi-device)
    sid_str = str(sender_id)
    primary_id = sid_str.split("@")[0].split(":")[0] + "@" + sid_str.split("@")[1] if "@" in sid_str else sid_str

    # 2. Sudo Users
    if state.is_sudo(primary_id):
        return True

    # 3. Owner
    sender_num = primary_id.split("@")[0]
    if str(config.OWNER_ID) == sender_num:
        return True

    return False


async def is_owner(event) -> bool:
    """Strictly checks if the event sender is the bot owner."""
    sender_id = getattr(event, "sender_id", None) or getattr(event, "chat_id", None)
    if not sender_id:
        return False

    # Check if message is from the bot account itself (considered owner)
    if getattr(event, "from_me", False):
        return True

    # Normalize sender_id for lookup (Primary JID only, handle multi-device)
    sid_str = str(sender_id)
    primary_id = sid_str.split("@")[0].split(":")[0] + "@" + sid_str.split("@")[1] if "@" in sid_str else sid_str

    sender_num = primary_id.split("@")[0]
    return str(config.OWNER_ID) == sender_num


# Exported filters
authorized_filter = Filters.create(is_authorized)
owner_filter = Filters.create(is_owner)


# Filter to prevent processing messages sent before bot startup
async def is_new_message(event) -> bool:
    """Checks if the message timestamp is after the bot's boot time."""
    msg_time = getattr(event, "timestamp", 0)
    # state.BOOT_TIME is defined in utils.state
    from utils.state import BOOT_TIME

    return msg_time >= BOOT_TIME


startup_filter = Filters.create(is_new_message)


def astra_command(
    name: str,
    description: str = "",
    category: str = "General",
    aliases: Optional[List[str]] = None,
    usage: str = "",
    owner_only: bool = False,
    is_public: bool = False,
):
    """
    Unified decorator for Astra Userbot commands.
    Registers the command as a native handler and stores metadata for the help menu.
    """
    if aliases is None:
        aliases = []

    # 1. Capture calling module info (Helpful for plugin-wise categorization like CatUserbot)
    import inspect

    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    module_name = module.__name__.split(".")[-1] if module else "General"

    # Register metadata (Replacing if exists)
    global COMMANDS_METADATA
    new_entry = {
        "name": name,
        "description": description,
        "category": category,
        "module": module_name,  # Stored module name (e.g. 'instagram' or 'utility_cmds')
        "aliases": aliases,
        "usage": usage,
        "owner_only": owner_only,
        "is_public": is_public,
    }
    # Mutate in-place to ensure all modules see the updates
    for i, cmd in enumerate(COMMANDS_METADATA):
        if cmd["name"] == name:
            COMMANDS_METADATA.pop(i)
            break
    COMMANDS_METADATA.append(new_entry)

    def decorator(func):
        # Build the native filter by ORing name and aliases
        names = [name] + aliases

        crit = Filters.command(names[0], prefixes="!./")
        for alias in names[1:]:
            crit |= Filters.command(alias, prefixes="!./")

        # Apply Global Startup Filter (Ignore old messages)
        crit = crit & startup_filter

        # Apply Authorization Logic
        if owner_only:
            crit = crit & owner_filter
        elif not is_public:
            crit = crit & authorized_filter

        # --- Global Wrapper for Error Handling & Analytics ---
        import functools
        @functools.wraps(func)
        async def global_wrapper(client: Client, message: Message, *args, **kwargs):
            # 1. Analytics: Track command usage
            try:
                from utils.database import db
                # We use the primary command name for stats
                asyncio.create_task(db.increment(f"cmd_usage:{name}"))
                asyncio.create_task(db.increment("total_commands_v2"))
            except:
                pass

            # 2. Execution & Error Handling
            try:
                return await func(client, message, *args, **kwargs)
            except Exception as e:
                from utils.error_reporter import ErrorReporter
                module_name = func.__module__.split(".")[-1] if hasattr(func, "__module__") else "unknown"
                return await ErrorReporter.report(
                    client, message, e, context=f"{module_name}.{func.__name__}"
                )

        # Register as a class-level handler for Client.load_plugins()
        Client.on_message(crit)(global_wrapper)
        return global_wrapper

    return decorator


def extract_args(message) -> List[str]:
    """
    Safely extracts command arguments from a message object.
    Handles distinct cases where message.command is an object or string,
    or falls back to manual body parsing.
    """
    try:
        args_attr = getattr(message, "command", None)

        # Case 1: Filter attached an object with .args (Standard Astra)
        if args_attr and not isinstance(args_attr, str) and hasattr(args_attr, "args"):
            return args_attr.args

        # Case 2: Filter attached a list (Some versions)
        if isinstance(args_attr, list):
            return args_attr

        # Case 3: Fallback - Manual Body Parsing
        body = getattr(message, "body", "") or ""
        parts = body.split()
        if len(parts) > 1:
            return parts[1:]

    except Exception:
        pass

    return []


# --- Dynamic Plugin Loading System ---
import importlib
import logging
import sys

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
        if hasattr(Client, "_class_handlers"):
            for event, func, criteria in Client._class_handlers:
                # Better Filtering: Automatically inject Startup Isolation for all message events
                # This ensures any plugin (even without astra_command) ignores old messages.
                if event == "message":
                    criteria = (criteria & startup_filter) if criteria else startup_filter

                # Pass-through wrapper for loading
                async def load_wrapper(event_payload, _f=func):
                    return await _f(client, event_payload)

                # Register and capture handle
                handle = client.on(event, criteria=criteria)(load_wrapper)
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
        COMMANDS_METADATA = [
            cmd for cmd in COMMANDS_METADATA if not str(cmd.get("name", "")).startswith(f"{plugin_name}.")
        ]
        # Note: If duplicate names exist across modules, this might be tricky,
        # but astra_command handles deduplication by name anyway.

        del PLUGIN_HANDLES[plugin_name]
        logger.info(f"Unloaded plugin: {plugin_name}")


def reload_all_plugins(client: Client) -> int:
    """
    Hot-reloads all plugins and project modules without restarting the client.
    """
    import importlib
    import os
    import pkgutil
    import sys
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
            if name != "__main__" and name != "utils.plugin_utils":  # Reload us last or not at all?
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
        # Clear metadata and help cache to start fresh
        global COMMANDS_METADATA
        COMMANDS_METADATA.clear()

        try:
            from commands.help import HELP_CACHE

            HELP_CACHE["categories"].clear()
            logger.info("Cleared Help System cache for re-indexing.")
        except ImportError:
            pass

        for loader, mod_name, is_pkg in pkgutil.walk_packages([commands_dir], prefix="commands."):
            if load_plugin(client, mod_name):
                success += 1

    return success
