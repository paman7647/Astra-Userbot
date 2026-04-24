#!/bin/bash

set -e

REPO_URL="https://github.com/paman7647/Astra-Userbot.git"
DIR_NAME="Astra-Userbot"

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


command_exists() {
    command -v "$1" >/dev/null 2>&1
}

install_git() {
    if command_exists git; then
        ok "Git already installed"
        return
    fi

    log "Installing Git..."

    if command_exists apt; then
        sudo apt update
        sudo apt install -y git
    elif command_exists brew; then
        brew install git
    else
        fail "Could not install Git automatically"
        exit 1
    fi

    ok "Git installed"
}

install_system_deps() {
    log "Installing system dependencies..."

    OS="$(uname)"

    if [ "$OS" = "Darwin" ]; then
        if ! command_exists brew; then
            log "Installing Homebrew..."
            NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi

        brew install node ffmpeg yt-dlp python3

    elif [ "$OS" = "Linux" ]; then
        if command_exists apt; then
            sudo apt update
            sudo apt install -y \
                nodejs npm \
                ffmpeg \
                python3 python3-venv python3-pip \
                wget curl
        else
            fail "Unsupported Linux distribution"
            exit 1
        fi
    fi

    ok "System dependencies installed"
}

setup_python() {
    log "Setting up Python environment..."

    VENV_SUCCESS=false

    # TRY: Create the virtual environment
    if [ ! -d venv ]; then
        if python3 -m venv venv; then
            ok "Virtual environment created"
        else
            warn "Venv creation failed"
        fi
    fi

    # TRY: Activate and use venv
    if [ -d venv ] && source venv/bin/activate 2>/dev/null; then
        log "Installing dependencies in venv..."
        pip install --upgrade pip
        
        if [ -f requirements.txt ]; then
            pip install -r requirements.txt || warn "Venv dependencies failed"
        fi
        VENV_SUCCESS=true
        ok "Python dependencies installed in venv"
    fi

    # EXCEPT: Fallback to global --user installation if venv failed
    if [ "$VENV_SUCCESS" = false ]; then
        warn "Venv failed.  installing global"
        
        # Upgrade pip for user
        pip3 install --user --upgrade pip --break-system-packages 2>/dev/null || true
        
        if [ -f requirements.txt ]; then
            log "Installing dependencies ..."
            pip3 install --user -r requirements.txt --break-system-packages || \
            warn "Global user installation failed"
        fi
        ok "Python dependencies installed globally via --user"
    fi
}


setup_browser() {
    log "Setting up browser..."

    # Termux detection
    if [ -d "/data/data/com.termux" ]; then
        ok "Termux detected → installing Chromium"

        pkg update -y
        pkg install -y chromium

        playwright install chromium || true
        return
    fi

    # Standard systems → Chrome
    if command_exists google-chrome; then
        ok "Google Chrome already installed"
    else
        log "Installing Google Chrome..."

        OS="$(uname)"

        if [ "$OS" = "Darwin" ]; then
            brew install --cask google-chrome || warn "Chrome install failed"
        elif [ "$OS" = "Linux" ]; then
            wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
            sudo apt install -y ./google-chrome-stable_current_amd64.deb || true
            rm -f google-chrome-stable_current_amd64.deb
        fi
    fi

    log "Installing Playwright browser..."

    playwright install chrome || playwright install chromium

    ok "Browser setup complete"
}

clone_or_update_repo() {
    if [ -d "$DIR_NAME" ]; then
        log "Repository exists → updating..."
        cd "$DIR_NAME"
        git pull origin main
    else
        log "Cloning repository..."
        git clone "$REPO_URL"
        cd "$DIR_NAME"
    fi

    ok "Repository ready"
}

run_setup() {
    log "Running setup.sh (interactive configuration)..."

    chmod +x setup.sh
    ./setup.sh

    ok "Setup completed"
}

clear 2>/dev/null || true
echo -e "${BOLD}Astra Userbot Local Installer${RESET}"
line

install_git
clone_or_update_repo
install_system_deps
setup_python
setup_browser
run_setup

line
ok "Astra installation complete"

echo ""
echo "Run the bot using:"
echo "source venv/bin/activate"
echo "python bot.py"
