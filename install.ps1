param (
    [switch]$Auto
)

function Info($m){Write-Host "INFO  $m" -ForegroundColor Cyan}
function Ok($m){Write-Host "OK    $m" -ForegroundColor Green}
function Warn($m){Write-Host "WARN  $m" -ForegroundColor Yellow}
function Err($m){Write-Host "ERR   $m" -ForegroundColor Red}

Write-Host ""
Write-Host "Astra Userbot Installer" -ForegroundColor White
Write-Host "----------------------------------" -ForegroundColor DarkGray
Write-Host ""

# Ensure Git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Warn "Git not found. Installing..."
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements | Out-Null
        Ok "Git installed (restart terminal if needed)"
    } else {
        Err "winget not available. Install Git manually."
        exit 1
    }
} else { Ok "Git ready" }

# Ensure Python is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Warn "Python not found. Installing..."
    winget install --id Python.Python.3.11 -e --accept-source-agreements --accept-package-agreements | Out-Null
    Ok "Python installed"
} else { Ok "Python ready" }

$Repo="https://github.com/paman7647/Astra-Userbot.git"
$Dir="Astra-Userbot"

# Clone or update repository
if (Test-Path $Dir) {
    Warn "Repository exists. Updating..."
    Set-Location $Dir
    git pull origin main
} else {
    Info "Cloning repository..."
    git clone $Repo
    Set-Location $Dir
}

# Allow script execution for current session
Set-ExecutionPolicy Bypass -Scope Process -Force

# Ensure setup script exists
if (-not (Test-Path ".\setup.ps1")) {
    Err "setup.ps1 not found"
    exit 1
}

# Run setup
if ($Auto) {
    Info "Running setup in auto mode"
    powershell -ExecutionPolicy Bypass -File .\setup.ps1 -Auto
} else {
    Info "Running setup"
    powershell -ExecutionPolicy Bypass -File .\setup.ps1
}

Ok "Installation complete"
Write-Host ""
Write-Host "Run the bot using:"
Write-Host "python bot.py"
