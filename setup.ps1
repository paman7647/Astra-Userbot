<#
.SYNOPSIS
Unattended Windows setup for Astra Userbot.
#>

function Info($m){Write-Host "INFO  $m" -ForegroundColor Cyan}
function Ok($m){Write-Host "OK    $m" -ForegroundColor Green}
function Warn($m){Write-Host "WARN  $m" -ForegroundColor Yellow}
function Err($m){Write-Host "ERR   $m" -ForegroundColor Red}

Write-Host ""
Write-Host "Astra Userbot Setup (Unattended)" -ForegroundColor White
Write-Host "----------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Install deps via winget if available
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Info "Installing FFmpeg..."
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements | Out-Null

    Info "Installing Node.js..."
    winget install -e --id OpenJS.NodeJS --accept-source-agreements --accept-package-agreements | Out-Null
} else {
    Warn "winget not found. Install FFmpeg and Node.js manually."
}

# Check Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Err "Python not found. Install Python 3.10+ and retry."
    exit 1
}
Ok "Python ready"

# Create venv
Info "Creating virtual environment..."
python -m venv venv

if (-not (Test-Path "venv\Scripts\activate.ps1")) {
    Err "Virtual environment creation failed"
    exit 1
}
Ok "Virtual environment ready"

# Install Python deps (force-safe)
Info "Installing Python dependencies..."
& .\venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null

& .\venv\Scripts\python.exe -m pip install -r requirements.txt `
    || & .\venv\Scripts\python.exe -m pip install -r requirements.txt --break-system-packages `
    || Warn "Some dependencies may have failed"

Ok "Dependencies installed"

# Install browser
Info "Installing Playwright browser..."

& .\venv\Scripts\playwright.exe install chrome `
    || & .\venv\Scripts\playwright.exe install chromium

Ok "Browser setup complete"

# Final instructions
Write-Host ""
Ok "Setup complete"
Write-Host ""
Write-Host "Next steps:"
Write-Host "copy .env.example .env"
Write-Host "edit .env with your values"
Write-Host ".\venv\Scripts\activate"
Write-Host "python bot.py"
