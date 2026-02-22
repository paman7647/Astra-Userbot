# -----------------------------------------------------------
# Astra-Userbot - WhatsApp Userbot Framework
# Copyright (c) 2026 Aman Kumar Pandey
# https://github.com/paman7647/Astra-Userbot
# Licensed under the MIT License.
# -----------------------------------------------------------

import logging
import os
import sys

# Standard ANSI Color Escapes
class Colors:
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"
    GRAY = "\033[90m"

class AstraFormatter(logging.Formatter):
    """
    Modern, emoji-free logging formatter with high-contrast ANSI styling.
    """
    LEVEL_STYLES = {
        logging.DEBUG: (Colors.GRAY, "»"),
        logging.INFO: (Colors.CYAN, "»"),
        logging.WARNING: (Colors.YELLOW, "⚠"), # Minimalist warning char
        logging.ERROR: (Colors.RED, "✖"),    # Minimalist error char
        logging.CRITICAL: (Colors.BOLD + Colors.RED, "✘")
    }

    def format(self, record):
        color, symbol = self.LEVEL_STYLES.get(record.levelno, (Colors.END, "»"))
        
        # Smart Module Namespacing
        name_parts = record.name.split('.')
        mod_name = name_parts[-1].lower() if len(name_parts) > 1 else record.name.lower()
        
        # Unique Module Coloring
        mod_color = Colors.BOLD + Colors.GRAY
        if "bridge" in mod_name or "protocol" in mod_name: mod_color = Colors.BLUE
        if "auth" in mod_name: mod_color = Colors.YELLOW

        # Build Parts
        time_part = f"{Colors.GRAY}{self.formatTime(record, '%H:%M:%S')}{Colors.END}"
        level_part = f"{color}{record.levelname[:1].upper()}{Colors.END}" # U, I, W, E, C
        mod_part = f"{mod_color}{mod_name.upper():^10}{Colors.END}"
        
        message = record.getMessage()
        
        # Sophisticated line build
        #格式: 03:42:42 [I] BRIDGE » Establishing connection...
        return f"{time_part} {Colors.GRAY}[{Colors.END}{level_part}{Colors.GRAY}]{Colors.END} {mod_part} {color}{symbol}{Colors.END} {message}"


def setup_logging(script_dir: str):
    """Configures the global Astra logging system."""
    
    # 1. Plain Text File Logger (Complete Debug)
    log_file = os.path.join(script_dir, "astra_full_debug.txt")
    file_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # 2. Modern Colored Console Logger
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(AstraFormatter())

    # 3. Configure Root
    root_log = logging.getLogger()
    root_log.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for h in root_log.handlers[:]:
        root_log.removeHandler(h)
        
    root_log.addHandler(file_handler)
    root_log.addHandler(console_handler)

    # Silence noisy dependencies
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_log
