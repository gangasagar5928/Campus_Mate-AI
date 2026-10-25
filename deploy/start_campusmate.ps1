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
Write-Host "Establishing secure public tunnel (HTTP/2 TCP)..." -ForegroundColor Yellow
$cfProcess = Start-Process -FilePath $cfPath -ArgumentList "tunnel", "--protocol", "http2", "--url", "http://127.0.0.1:8000" -RedirectStandardError $logFile -PassThru -NoNewWindow

# 3. Wait for tunnel URL
$tunnelUrl = ""
$retries = 30
while ($retries -gt 0 -and [string]::IsNullOrEmpty($tunnelUrl)) {
    Start-Sleep -Seconds 1
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrEmpty($content)) {
            $matchesList = [regex]::Matches($content, "https://([a-zA-Z0-9-]+)\.trycloudflare\.com")
            foreach ($m in $matchesList) {
                if ($m.Groups[1].Value -ne "api") {
                    $tunnelUrl = $m.Value
                    break
                }
            }
            if (-not [string]::IsNullOrEmpty($tunnelUrl)) { break }
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

# Ensure working directory is project root
Set-Location (Join-Path $PSScriptRoot "..")

$env:AGENT_ENDPOINT = $submitUrl

# Sync new endpoint with Agentverse automatically
Write-Host "Syncing endpoint with Agentverse..." -ForegroundColor Yellow
python deploy/register_agentverse.py

Write-Host "Starting Agent with ACP 0.3.0..." -ForegroundColor Yellow
python agent_student_twin.py
