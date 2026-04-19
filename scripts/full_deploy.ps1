# Full deployment: git pull → Docker up → Cloudflare tunnels → rebuild with tunnel URLs
# Usage: .\scripts\full_deploy.ps1

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location $ProjectRoot

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " STEP 1: Sync with GitHub" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
git fetch origin
git reset --hard origin/master

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " STEP 2: Starting Docker (backend + frontend)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
docker-compose down
docker-compose up --build -d
Write-Host "Waiting 15s for containers to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " STEP 3: Starting Cloudflare Tunnels" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Check cloudflared is installed
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: cloudflared not found. Install from https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor Red
    Write-Host "Docker is still running. Visit http://localhost:3000 on your PC." -ForegroundColor Yellow
    exit 1
}

$FrontendLog = "$env:TEMP\cf_frontend.log"
$BackendLog = "$env:TEMP\cf_backend.log"
Remove-Item $FrontendLog, $BackendLog -ErrorAction SilentlyContinue

Write-Host "Starting backend tunnel (port 8000)..." -ForegroundColor Yellow
$BackendJob = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:8000" -RedirectStandardError $BackendLog -PassThru -WindowStyle Hidden

Write-Host "Starting frontend tunnel (port 3000)..." -ForegroundColor Yellow
$FrontendJob = Start-Process cloudflared -ArgumentList "tunnel --url http://localhost:3000" -RedirectStandardError $FrontendLog -PassThru -WindowStyle Hidden

# Wait for URLs
Write-Host "Waiting for tunnel URLs..." -ForegroundColor Yellow
$BackendUrl = $null
$FrontendUrl = $null
$Tries = 0

while (($null -eq $BackendUrl -or $null -eq $FrontendUrl) -and $Tries -lt 30) {
    Start-Sleep -Seconds 1
    $Tries++

    if ($null -eq $BackendUrl -and (Test-Path $BackendLog)) {
        $Match = Select-String -Path $BackendLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | Select-Object -First 1
        if ($Match) { $BackendUrl = $Match.Matches[0].Value }
    }

    if ($null -eq $FrontendUrl -and (Test-Path $FrontendLog)) {
        $Match = Select-String -Path $FrontendLog -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches | Select-Object -First 1
        if ($Match) { $FrontendUrl = $Match.Matches[0].Value }
    }
}

if (-not $BackendUrl -or -not $FrontendUrl) {
    Write-Host "ERROR: Could not get tunnel URLs" -ForegroundColor Red
    Stop-Process $BackendJob, $FrontendJob -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " STEP 4: Updating frontend config with tunnel URL" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

$EnvFile = "$ProjectRoot\ai-frontend\.env.local"
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

Write-Host "Rebuilding frontend with new API URL..." -ForegroundColor Yellow
docker-compose up --build -d frontend

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " READY — MOBILE ACCESS ENABLED" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Frontend URL - open on phone: $FrontendUrl" -ForegroundColor Cyan
Write-Host " Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Keep this window open — closing kills tunnels." -ForegroundColor Red
Write-Host "Press Ctrl+C to stop everything." -ForegroundColor Red

# Copy frontend URL to clipboard for convenience
try {
    Set-Clipboard -Value $FrontendUrl
    Write-Host "Frontend URL copied to clipboard" -ForegroundColor Green
} catch {}

# Keep running until killed
try {
    while ($BackendJob.HasExited -eq $false -and $FrontendJob.HasExited -eq $false) {
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host "`nStopping tunnels..." -ForegroundColor Yellow
    Stop-Process -Id $BackendJob.Id, $FrontendJob.Id -ErrorAction SilentlyContinue
}
