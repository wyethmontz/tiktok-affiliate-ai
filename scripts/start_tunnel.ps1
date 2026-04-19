# Start Cloudflare Tunnels for both frontend (3000) and backend (8000)
# Auto-updates ai-frontend/.env.local with backend tunnel URL

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "Starting Cloudflare Tunnels..." -ForegroundColor Cyan

# Check if cloudflared is installed
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: cloudflared not found. Download from https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Red
    exit 1
}

# Temp files to capture tunnel URLs
$FrontendLog = "$env:TEMP\cf_frontend.log"
$BackendLog = "$env:TEMP\cf_backend.log"

# Clean up old logs
Remove-Item $FrontendLog, $BackendLog -ErrorAction SilentlyContinue

# Start backend tunnel in background
Write-Host "Starting backend tunnel (port 8000)..." -ForegroundColor Yellow
$BackendJob = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:8000" -RedirectStandardError $BackendLog -PassThru -WindowStyle Hidden

# Start frontend tunnel in background
Write-Host "Starting frontend tunnel (port 3000)..." -ForegroundColor Yellow
$FrontendJob = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:3000" -RedirectStandardError $FrontendLog -PassThru -WindowStyle Hidden

# Wait for URLs to appear in logs
Write-Host "Waiting for tunnel URLs..." -ForegroundColor Yellow
$BackendUrl = $null
$FrontendUrl = $null
$Tries = 0

while (($null -eq $BackendUrl -or $null -eq $FrontendUrl) -and $Tries -lt 30) {
    Start-Sleep -Seconds 1
    $Tries++

    if ($null -eq $BackendUrl -and (Test-Path $BackendLog)) {
        $BackendMatch = Select-String -Path $BackendLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | Select-Object -First 1
        if ($BackendMatch) { $BackendUrl = $BackendMatch.Matches[0].Value }
    }

    if ($null -eq $FrontendUrl -and (Test-Path $FrontendLog)) {
        $FrontendMatch = Select-String -Path $FrontendLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | Select-Object -First 1
        if ($FrontendMatch) { $FrontendUrl = $FrontendMatch.Matches[0].Value }
    }
}

if (-not $BackendUrl -or -not $FrontendUrl) {
    Write-Host "ERROR: Could not get tunnel URLs after 30 seconds" -ForegroundColor Red
    Stop-Process $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
    exit 1
}

# Update frontend .env.local
$EnvFile = "$ProjectRoot\ai-frontend\.env.local"
Write-Host "Updating $EnvFile with backend URL..." -ForegroundColor Yellow

if (Test-Path $EnvFile) {
    $EnvContent = Get-Content $EnvFile -Raw
    if ($EnvContent -match "NEXT_PUBLIC_API_URL=") {
        $EnvContent = $EnvContent -replace "NEXT_PUBLIC_API_URL=.*", "NEXT_PUBLIC_API_URL=$BackendUrl"
    } else {
        $EnvContent += "`nNEXT_PUBLIC_API_URL=$BackendUrl"
    }
    Set-Content -Path $EnvFile -Value $EnvContent
} else {
    Set-Content -Path $EnvFile -Value "NEXT_PUBLIC_API_URL=$BackendUrl"
}

# Done
Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " TUNNELS ACTIVE" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host " FRONTEND (open on phone): $FrontendUrl" -ForegroundColor Cyan
Write-Host " BACKEND API: $BackendUrl" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host " 1. Rebuild Docker so frontend picks up the new API URL:" -ForegroundColor Yellow
Write-Host "    docker-compose up --build" -ForegroundColor White
Write-Host " 2. Open the FRONTEND URL on your phone" -ForegroundColor Yellow
Write-Host ""
Write-Host "Keep this window open — closing it will kill the tunnels." -ForegroundColor Red
Write-Host "Press Ctrl+C to stop." -ForegroundColor Red

# Keep script running until user kills it
try {
    while ($BackendJob.HasExited -eq $false -and $FrontendJob.HasExited -eq $false) {
        Start-Sleep -Seconds 5
    }
} finally {
    Stop-Process -Id $BackendJob.Id, $FrontendJob.Id -ErrorAction SilentlyContinue
    Write-Host "Tunnels stopped." -ForegroundColor Yellow
}
