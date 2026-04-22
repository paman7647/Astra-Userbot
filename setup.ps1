param (
    [switch]$Auto
)

function Info($m){Write-Host "INFO  $m" -ForegroundColor Cyan}
function Ok($m){Write-Host "OK    $m" -ForegroundColor Green}
function Warn($m){Write-Host "WARN  $m" -ForegroundColor Yellow}
function Err($m){Write-Host "ERR   $m" -ForegroundColor Red}

function Ask($q) {
    return Read-Host "$q"
}

function ValidatePhone($p) {
    return $p -match '^[0-9]{8,15}$'
}

Write-Host ""
Write-Host "Astra Userbot Setup" -ForegroundColor White
Write-Host "----------------------------------" -ForegroundColor DarkGray
Write-Host ""

# =========================
# INPUT MODE
# =========================
if (-not $Auto) {

    do {
        $PHONE = Ask "Enter WhatsApp number (country code, no +)"
        if (-not (ValidatePhone $PHONE)) {
            Warn "Invalid format. Example: 919876543210"
        }
    } while (-not (ValidatePhone $PHONE))

    do {
        $OWNER_NAME = Ask "Enter owner name"
        if ([string]::IsNullOrWhiteSpace($OWNER_NAME)) {
            Warn "Owner name cannot be empty"
        }
    } while ([string]::IsNullOrWhiteSpace($OWNER_NAME))

    $useMongo = Ask "Use MongoDB? (y/N)"
    if ($useMongo -match '^[Yy]$') {
        do {
            $MONGO_URI = Ask "Enter MongoDB URI"
            if ([string]::IsNullOrWhiteSpace($MONGO_URI)) {
                Warn "Mongo URI cannot be empty"
            }
        } while ([string]::IsNullOrWhiteSpace($MONGO_URI))
    } else {
        $MONGO_URI = ""
    }

    $GEMINI_API_KEY = Ask "Gemini API key (optional)"
    $NEWS_GEMINI_API_KEY = Ask "News Gemini API key (optional)"

} else {
    Info "Auto mode enabled (using environment variables)"

    if (-not $env:PHONE_NUMBER) {
        Err "PHONE_NUMBER required in auto mode"
        exit 1
    }

    $PHONE = $env:PHONE_NUMBER
    $OWNER_NAME = $env:OWNER_NAME
    $MONGO_URI = $env:MONGO_URI
    $GEMINI_API_KEY = $env:GEMINI_API_KEY
    $NEWS_GEMINI_API_KEY = $env:NEWS_GEMINI_API_KEY
}

# =========================
# DERIVED
# =========================
$OWNER_WHATSAPP_ID = "$PHONE@c.us"
$BOT_OWNER_ID = $PHONE

# =========================
# WRITE ENV
# =========================
Info "Creating .env file..."

@"
BOT_NAME=Astra Userbot
COMMAND_PREFIX=.

OWNER_WHATSAPP_ID=$OWNER_WHATSAPP_ID
OWNER_NAME=$OWNER_NAME
BOT_OWNER_ID=$BOT_OWNER_ID
PHONE_NUMBER=$PHONE

ENABLE_AI=true
ENABLE_YOUTUBE=true
ENABLE_INSTAGRAM=true
ENABLE_PM_PROTECTION=true
PM_WARN_LIMIT=5

ASTRA_HEADLESS=true
ASTRA_SESSION_ID=ASTRA
ASTRA_PHONE_PAIRING=false

MONGO_URI=$MONGO_URI
SQLITE_PATH=bot_state.db
DATABASE_SYNC_INTERVAL=300

GEMINI_API_KEY=$GEMINI_API_KEY
NEWS_GEMINI_API_KEY=$NEWS_GEMINI_API_KEY

MAX_FILE_SIZE_MB=50
REQUEST_TIMEOUT=30000

FFMPEG_PATH=ffmpeg
"@ | Out-File -Encoding utf8 .env

Ok ".env created"

Write-Host ""
Write-Host "Next steps:"
Write-Host ".\venv\Scripts\activate"
Write-Host "python bot.py"
