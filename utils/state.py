# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Centralized State Management
----------------------------
Orchestrates the persistent and ephemeral state of the userbot.
Synchronizes local memory cache with the SQLite backend.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from .database import db

logger = logging.getLogger("Astra.State")

class StateManager:
    """
    Maintains the runtime state of the userbot.
    Features a local cache for high-speed synchronous reads and 
    asynchronous write-through to the database.
    """
    def __init__(self):
        # Local state cache to avoid frequent database I/O for reads.
        self.state: Dict[str, Any] = {
            "afk": {"is_afk": False, "reason": "", "since": 0},
            "pm_permits": [],
            "sudo_users": [],
            "notes": {},
            "pm_warnings": {},
            "group_configs": {}, # gid -> {muted: bool, welcome: str}
            "prefix": None
        }
        self.initialized = False

    async def initialize(self):
        """
        Synchronizes the memory state with the persistent database.
        Must be called during the bot startup sequence.
        """
        if self.initialized:
            return
        
        await db.initialize()
        
        # Bulk load managed state keys
        keys = ["afk", "pm_permits", "sudo_users", "notes", "pm_warnings", "group_configs", "prefix"]
        for key in keys:
            val = await db.get(key)
            if val is not None:
                self.state[key] = val
        
        self.initialized = True
        logger.info("StateManager successfully synchronized with persistent store.")

    async def save(self):
        """
        Force-syncs the entire memory state to the database.
        Note: The class handles individual state changes automatically; 
        this remains for manual consistency checks.
        """
        tasks = [db.set(key, val) for key, val in self.state.items()]
        if tasks:
            await asyncio.gather(*tasks)

    # --- AFK Module ---

    def set_afk(self, is_afk: bool, reason: str = ""):
        """Toggles the AFK (Away From Keyboard) status."""
        self.state["afk"] = {
            "is_afk": is_afk,
            "reason": reason,
            "since": int(time.time()) if is_afk else 0
        }
        # Commit to storage in the background
        asyncio.create_task(db.set("afk", self.state["afk"]))

    def get_afk(self) -> Dict[str, Any]:
        """Retrieves current AFK status and metadata."""
        return self.state["afk"]

    # --- Direct Message Security (PM Permit) ---

    def is_permitted(self, user_id: str) -> bool:
        """Validates if a specific user is authorized to send direct messages."""
        return user_id in self.state["pm_permits"]

    def permit_user(self, user_id: str):
        """Adds a user to the whitelist for direct messages."""
        if user_id not in self.state["pm_permits"]:
            self.state["pm_permits"].append(user_id)
            asyncio.create_task(db.set("pm_permits", self.state["pm_permits"]))

    def deny_user(self, user_id: str):
        """Removes a user from the direct message whitelist."""
        if user_id in self.state["pm_permits"]:
            self.state["pm_permits"].remove(user_id)
            asyncio.create_task(db.set("pm_permits", self.state["pm_permits"]))

    # --- Administrative Sudo Privileges ---

    def is_sudo(self, user_id: str) -> bool:
        """Checks if a user has elevated sudo privileges."""
        return user_id in self.state["sudo_users"]

    def add_sudo(self, user_id: str):
        """Grants sudo privileges to a user."""
        if user_id not in self.state["sudo_users"]:
            self.state["sudo_users"].append(user_id)
            asyncio.create_task(db.set("sudo_users", self.state["sudo_users"]))

    # --- Customizable Notes System ---

    def set_note(self, keyword: str, content: str):
        """Saves a snippet of text for quick recall via a keyword."""
        self.state["notes"][keyword.lower()] = content
        asyncio.create_task(db.set("notes", self.state["notes"]))

    def get_note(self, keyword: str) -> Optional[str]:
        """Recalls a previously saved note by its keyword."""
        return self.state["notes"].get(keyword.lower())

    def delete_note(self, keyword: str):
        """Permanently deletes a saved note."""
        if keyword.lower() in self.state["notes"]:
            del self.state["notes"][keyword.lower()]
            asyncio.create_task(db.set("notes", self.state["notes"]))

    # --- Dynamic Interface Routing ---

    def get_prefix(self) -> str:
        """Resolves the current command prefix. Defaults to configuration value."""
        from config import config
        return self.state.get("prefix") or config.PREFIX

    def set_prefix(self, prefix: str):
        """Updates the global command prefix for the bot."""
        self.state["prefix"] = prefix
        asyncio.create_task(db.set("prefix", prefix))

# Singleton Export
state = StateManager()
