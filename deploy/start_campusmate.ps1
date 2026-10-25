# start_campusmate.ps1 - Automated 1-Click Launcher for CampusMate AI
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting CampusMate AI (Fetch.ai Student Twin)..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Kill previous dangling tunnel / agent on port 8000
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

# 2. Locate cloudflared binary
$cfPath = "C:\Users\mksin\.omniroute\cloudflared\bin\cloudflared.exe"
if (-not (Test-Path $cfPath)) {
    $cfPath = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
}

$logFile = Join-Path $PSScriptRoot "tunnel.log"
if (Test-Path $logFile) { Remove-Item $logFile -Force }

$env:GODEBUG = "netdns=cgo"
Write-Host "Establishing secure public tunnel..." -ForegroundColor Yellow
$cfProcess = Start-Process -FilePath $cfPath -ArgumentList "tunnel", "--url", "http://127.0.0.1:8000" -RedirectStandardError $logFile -PassThru -NoNewWindow

# 3. Wait for tunnel URL
$tunnelUrl = ""
$retries = 30
while ($retries -gt 0 -and [string]::IsNullOrEmpty($tunnelUrl)) {
    Start-Sleep -Seconds 1
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        if ($content -match "https://[a-zA-Z0-9-]+\.trycloudflare\.com") {
            $tunnelUrl = $matches[0]
            break
        }
    }
    $retries--
}

if ([string]::IsNullOrEmpty($tunnelUrl)) {
    Write-Host "Failed to extract Cloudflare tunnel URL. Check $logFile." -ForegroundColor Red
    exit 1
}

$submitUrl = "$tunnelUrl/submit"
Write-Host "Tunnel Established: $tunnelUrl" -ForegroundColor Green
Write-Host "Agent Ingress:     $submitUrl" -ForegroundColor Cyan
Write-Host "Starting Agent with ACP 0.3.0..." -ForegroundColor Yellow

$env:AGENT_ENDPOINT = $submitUrl
python agent_student_twin.py
