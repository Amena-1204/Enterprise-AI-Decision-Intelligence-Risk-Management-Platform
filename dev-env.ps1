<#
.SYNOPSIS
    Local development stack control for the Enterprise AI Platform.

.DESCRIPTION
    Starts the three moving parts this project needs locally:

      MySQL   : isolated instance on port 3307 with its own datadir
                (E:\ai-buisness\.mysql-dev\data). The pre-existing "MySQL80"
                Windows service on port 3306 is NOT touched - its credentials
                are unknown, so this project uses a separate instance instead.
      Backend : Flask API on http://localhost:5000
      Frontend: React dev server on http://localhost:3000

    `backend/run.py` does `from backend.app import create_app`, so the project
    root must be importable (PYTHONPATH) and the process must run from the root
    (that is where .env is loaded from).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File dev-env.ps1 start
    powershell -ExecutionPolicy Bypass -File dev-env.ps1 status
    powershell -ExecutionPolicy Bypass -File dev-env.ps1 stop
#>
param(
    [ValidateSet("start", "stop", "restart", "status")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Continue"

$ProjectDir = $PSScriptRoot
$MySqlBase  = "C:\Program Files\MySQL\MySQL Server 8.0"
$DataDir    = "E:\ai-buisness\.mysql-dev\data"
$LogDir     = "E:\ai-buisness\.mysql-dev"
$VenvPy     = "E:\ai-buisness\.venv\Scripts\python.exe"
$Npm        = "C:\Program Files\nodejs\npm.cmd"
$MySqlPort  = 3307

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

function Get-DevMysqld {
    Get-CimInstance Win32_Process -Filter "name='mysqld.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*$DataDir*" }
}

function Get-BackendProcs {
    Get-CimInstance Win32_Process -Filter "name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*backend\run.py*" }
}

function Get-FrontendProcs {
    Get-CimInstance Win32_Process -Filter "name='node.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like "*react-scripts*" }
}

function Start-MySql {
    if (Get-DevMysqld) { Write-Host "MySQL (dev, :$MySqlPort) already running."; return }
    Write-Step "Starting MySQL dev instance on port $MySqlPort"
    if (-not (Test-Path $DataDir)) {
        Write-Step "Datadir missing, initializing"
        New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
        & "$MySqlBase\bin\mysqld.exe" --initialize-insecure --basedir="$MySqlBase" --datadir="$DataDir" --log-error="$LogDir\init.err"
    }
    # ArgumentList is space-joined, so paths containing spaces must stay quoted
    Start-Process -FilePath "$MySqlBase\bin\mysqld.exe" `
        -ArgumentList "--basedir=`"$MySqlBase`"", "--datadir=`"$DataDir`"", "--port=$MySqlPort", "--mysqlx=0", "--console" `
        -RedirectStandardOutput "$LogDir\mysqld.out.log" -RedirectStandardError "$LogDir\mysqld.err.log" `
        -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        if (Get-NetTCPConnection -State Listen -LocalPort $MySqlPort -ErrorAction SilentlyContinue) { break }
    }
}

function Start-Backend {
    if (Get-BackendProcs) { Write-Host "Backend (:5000) already running."; return }
    Write-Step "Starting Flask backend on port 5000"
    $env:PYTHONPATH = $ProjectDir
    # .env cannot override an env var that is already set, so pin development config
    $env:FLASK_ENV  = "development"
    Start-Process -FilePath $VenvPy -ArgumentList "backend\run.py" -WorkingDirectory $ProjectDir `
        -RedirectStandardOutput "$env:TEMP\backend.out.log" -RedirectStandardError "$env:TEMP\backend.err.log" `
        -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 2
        if (Get-NetTCPConnection -State Listen -LocalPort 5000 -ErrorAction SilentlyContinue) { break }
    }
}

function Start-Frontend {
    if (Get-FrontendProcs) { Write-Host "Frontend (:3000) already running."; return }
    Write-Step "Starting React dev server on port 3000"
    Start-Process -FilePath $Npm -ArgumentList "start" -WorkingDirectory "$ProjectDir\frontend" `
        -RedirectStandardOutput "$env:TEMP\frontend.out.log" -RedirectStandardError "$env:TEMP\frontend.err.log" `
        -WindowStyle Hidden | Out-Null
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        if (Get-NetTCPConnection -State Listen -LocalPort 3000 -ErrorAction SilentlyContinue) { break }
    }
}

function Stop-All {
    Write-Step "Stopping frontend / backend / dev MySQL"
    foreach ($p in @(Get-FrontendProcs) + @(Get-BackendProcs) + @(Get-DevMysqld)) {
        if ($p) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    }
    Start-Sleep -Seconds 2
    Write-Host "Stopped."
}

function Show-Status {
    Write-Host ""
    Write-Host "Enterprise AI Platform - local dev stack" -ForegroundColor White
    Write-Host "----------------------------------------"
    $checks = @(
        @{ Name = "MySQL (dev)"; Port = $MySqlPort; Url = $null },
        @{ Name = "Backend    "; Port = 5000;      Url = "http://localhost:5000/health" },
        @{ Name = "Frontend   "; Port = 3000;      Url = "http://localhost:3000/" }
    )
    foreach ($c in $checks) {
        $listening = [bool](Get-NetTCPConnection -State Listen -LocalPort $c.Port -ErrorAction SilentlyContinue)
        if ($listening) {
            Write-Host ("  {0} UP   (:{1})" -f $c.Name, $c.Port) -ForegroundColor Green
            if ($c.Url) {
                try {
                    $r = Invoke-WebRequest $c.Url -UseBasicParsing -TimeoutSec 10
                    Write-Host ("               {0} -> {1}" -f $c.Url, $r.StatusCode) -ForegroundColor DarkGray
                } catch {
                    Write-Host ("               {0} -> {1}" -f $c.Url, $_.Exception.Message) -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host ("  {0} DOWN (:{1})" -f $c.Name, $c.Port) -ForegroundColor Red
        }
    }
    Write-Host ""
    Write-Host "  Demo logins (seeded):" -ForegroundColor White
    Write-Host "    admin@enterprise.ai  / AdminPass1    (admin)"
    Write-Host "    alice@enterprise.ai  / AnalystPass1  (analyst)"
    Write-Host "    bob@enterprise.ai    / ViewerPass1   (viewer)"
    Write-Host ""
    Write-Host "  Logs: $env:TEMP\backend.out.log | $LogDir\mysqld.err.log"
    Write-Host ""
}

switch ($Action) {
    "start"   { Start-MySql; Start-Backend; Start-Frontend; Show-Status }
    "stop"    { Stop-All; Show-Status }
    "restart" { Stop-All; Start-MySql; Start-Backend; Start-Frontend; Show-Status }
    "status"  { Show-Status }
}