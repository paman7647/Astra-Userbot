#!/bin/bash

set -e

# =========================
# COLORS
# =========================
RESET="\033[0m"
BOLD="\033[1m"
DIM="\033[2m"

GREEN="\033[32m"
YELLOW="\033[33m"
RED="\033[31m"
CYAN="\033[36m"

log()   { echo -e "${CYAN}INFO${RESET} $1"; }
ok()    { echo -e "${GREEN}OK${RESET}   $1"; }
warn()  { echo -e "${YELLOW}WARN${RESET} $1"; }
fail()  { echo -e "${RED}ERR${RESET}  $1"; }

line() { printf "%b\n" "${DIM}--------------------------------------------------${RESET}"; }

# =========================
# VALIDATION
# =========================
validate_phone() {
    [[ "$1" =~ ^[0-9]{8,15}$ ]]
}

# =========================
# HEADER
# =========================
clear 2>/dev/null || true
echo -e "${BOLD}Astra Userbot Setup${RESET}"
line

echo "This will configure your bot environment (.env)"
echo ""

# =========================
# INPUTS
# =========================

# Phone number
while true; do
    read -rp "Enter WhatsApp number (with country code, no +): " PHONE
    if validate_phone "$PHONE"; then break; fi
    warn "Invalid format. Example: 919876543210"
done

# Owner name
while true; do
    read -rp "Enter owner name: " OWNER_NAME
    [ -n "$OWNER_NAME" ] && break
    warn "Owner name cannot be empty"
done

# MongoDB (optional)
echo ""
read -rp "Use MongoDB? (y/N): " USE_MONGO

if [[ "$USE_MONGO" =~ ^[Yy]$ ]]; then
    while true; do
        read -rp "Enter MongoDB URI: " MONGO_URI
        [ -n "$MONGO_URI" ] && break
        warn "Mongo URI cannot be empty"
    done
else
    MONGO_URI=""
fi

# Gemini API
echo ""
read -rp "Enter Gemini API key (optional): " GEMINI_API_KEY
read -rp "Enter News Gemini API key (optional): " NEWS_GEMINI_API_KEY

# =========================
# DERIVED VALUES
# =========================
OWNER_WHATSAPP_ID="${PHONE}@c.us"
BOT_OWNER_ID="$PHONE"

# =========================
# DEFAULTS
# =========================
BOT_NAME="Astra Userbot"
COMMAND_PREFIX="."

ENABLE_AI=true
ENABLE_YOUTUBE=true
ENABLE_INSTAGRAM=true
ENABLE_PM_PROTECTION=true
PM_WARN_LIMIT=5

ASTRA_HEADLESS=true
ASTRA_SESSION_ID="ASTRA"
ASTRA_PHONE_PAIRING=false

SQLITE_PATH="bot_state.db"
DATABASE_SYNC_INTERVAL=300

MAX_FILE_SIZE_MB=50
REQUEST_TIMEOUT=30000

FFMPEG_PATH="ffmpeg"

# =========================
# WRITE .env
# =========================
line
log "Creating .env file..."

cat > .env <<EOF
# =========================
# Bot Configuration
# =========================
BOT_NAME="${BOT_NAME}"
COMMAND_PREFIX="${COMMAND_PREFIX}"

OWNER_WHATSAPP_ID="${OWNER_WHATSAPP_ID}"
OWNER_NAME="${OWNER_NAME}"
BOT_OWNER_ID="${BOT_OWNER_ID}"
PHONE_NUMBER="${PHONE}"

# =========================
# Feature Flags
# =========================
ENABLE_AI=${ENABLE_AI}
ENABLE_YOUTUBE=${ENABLE_YOUTUBE}
ENABLE_INSTAGRAM=${ENABLE_INSTAGRAM}
ENABLE_PM_PROTECTION=${ENABLE_PM_PROTECTION}
PM_WARN_LIMIT=${PM_WARN_LIMIT}

# =========================
# Client Configuration
# =========================
ASTRA_HEADLESS=${ASTRA_HEADLESS}
ASTRA_SESSION_ID="${ASTRA_SESSION_ID}"
ASTRA_PHONE_PAIRING=${ASTRA_PHONE_PAIRING}

# =========================
# Database
# =========================
MONGO_URI="${MONGO_URI}"
SQLITE_PATH="${SQLITE_PATH}"
DATABASE_SYNC_INTERVAL=${DATABASE_SYNC_INTERVAL}

# =========================
# API Keys
# =========================
GEMINI_API_KEY="${GEMINI_API_KEY}"
NEWS_GEMINI_API_KEY="${NEWS_GEMINI_API_KEY}"

# =========================
# Limits
# =========================
MAX_FILE_SIZE_MB=${MAX_FILE_SIZE_MB}
REQUEST_TIMEOUT=${REQUEST_TIMEOUT}

# =========================
# System Paths
# =========================
FFMPEG_PATH="${FFMPEG_PATH}"
EOF

ok ".env file created successfully"

# =========================
# FINAL NOTES
# =========================
line

echo "Setup complete."
echo ""
echo "Next steps:"
echo "1. Activate environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the bot:"
echo "   python bot.py"
echo ""

# =========================
# SAFETY CHECK
# =========================
if [ ! -f ".env" ]; then
    fail ".env file missing. Something went wrong."
    exit 1
fi

ok "All done. You're ready to run Astra."
