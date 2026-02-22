# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# See LICENSE file in the project root for full license text.
# -----------------------------------------------------------

"""
Configuration Management
------------------------
Handles loading and validation of environment variables for the userbot.
Uses python-dotenv for local development convenience.
"""

import os
import logging
from typing import List
from dotenv import load_dotenv

# Define base directory for relative path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load .env file from the project root
load_dotenv(os.path.join(BASE_DIR, ".env"))

logger = logging.getLogger("Astra.Config")

class Config:
    """
    Central configuration container.
    Provides typed access to environment variables with sensible defaults.
    """
    
    # Versioning & Branding
    # ---------------------
    VERSION = "0.0.1b8"

    # Bot Identity & Ownership
    # ------------------------
    BOT_NAME = os.getenv('BOT_NAME', 'Astra Userbot')
    
    # OWNER_ID is critical for security and administrative commands.
    # We resolve it from either OWNER_WHATSAPP_ID or BOT_OWNER_ID.
    OWNER_ID = os.getenv('OWNER_WHATSAPP_ID') or os.getenv('BOT_OWNER_ID')
    OWNER_NAME = os.getenv('OWNER_NAME', 'Aman Kumar Pandey')
    
    PREFIX = os.getenv('COMMAND_PREFIX', '.')
    # Support for multiple common command prefixes
    PREFIXES = [PREFIX, '!', '/'] if PREFIX not in ['!', '/'] else ['.', '!', '/']

    # Operational Feature Flags
    # -------------------------
    ENABLE_AI = os.getenv('ENABLE_AI', 'true').lower() == 'true'
    ENABLE_YOUTUBE = os.getenv('ENABLE_YOUTUBE', 'true').lower() == 'true'
    ENABLE_INSTAGRAM = os.getenv('ENABLE_INSTAGRAM', 'true').lower() == 'true'
    ENABLE_PM_PROTECTION = os.getenv('ENABLE_PM_PROTECTION', 'false').lower() == 'true'
    PM_WARN_LIMIT = int(os.getenv('PM_WARN_LIMIT', '5'))

    # Prefix handling: toggle multiple prefix support
    ALLOW_MULTI_PREFIX = os.getenv('ALLOW_MULTI_PREFIX', 'false').lower() == 'true'
    
    # Persistence & Synchronization
    # -----------------------------
    MONGO_URI = os.getenv('MONGO_URI')
    _sqlite_path = os.getenv('SQLITE_PATH', 'bot_state.db')
    
    # Resolve SQLite path relative to the script directory if it's not absolute
    SQLITE_PATH = _sqlite_path if os.path.isabs(_sqlite_path) else os.path.join(BASE_DIR, _sqlite_path)
    
    # Interval for background database sync (in seconds)
    DATABASE_SYNC_INTERVAL = int(os.getenv('DATABASE_SYNC_INTERVAL', '300'))

    # Third-party API Orchestration
    # -----------------------------
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    NEWS_API_KEY = os.getenv('NEWS_GEMINI_API_KEY')

    # Media Processing & Binary Paths
    # -------------------------------
    FFMPEG_PATH = os.getenv('FFMPEG_PATH', 'ffmpeg')
    
    # YouTube session handling
    YOUTUBE_COOKIES_FILE = os.getenv('YOUTUBE_COOKIES_FILE')
    YOUTUBE_COOKIES_FROM_BROWSER = os.getenv('YOUTUBE_COOKIES_FROM_BROWSER')

    # Resource Constraints & Timeouts
    # -------------------------------
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '2048'))
    # Request timeout in milliseconds
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30000'))

    def __init__(self):
        self._validate()

    def _validate(self):
        """Perform basic integrity checks on the loaded configuration."""
        if not self.OWNER_ID:
            logger.warning("OWNER_ID is not configured. Administrative commands will be inaccessible.")

# Singleton instance for global access
config = Config()
