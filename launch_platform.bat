@echo off
setlocal
cd /d "%~dp0"
title NEXUS-1 Launcher
chcp 65001 >nul

echo [1/4] Checking dependencies...
py -c "import torch, fastapi, uvicorn, httpx" 2>nul
if errorlevel 1 (
    echo Installing dependencies - first run only...
    py -m pip install -r requirements-train.txt --extra-index-url https://download.pytorch.org/whl/cpu
)

echo [2/4] Checking trained brain...
if not exist "models\router.pt" py -m core.trainer all medium
if not exist "models\coder.pt" py -m core.trainer coder medium

echo Stopping any old NEXUS-1 server or tunnel still running...
powershell -NoProfile -Command "$ids = @((Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue).OwningProcess); Get-CimInstance Win32_Process | Where-Object { ($ids -contains $_.ProcessId -and $_.CommandLine -like '*app.py*') -or $_.CommandLine -like '*NEXUS-1-AI*cloudflared*' -or $_.CommandLine -like '*deploy\tunnel.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

echo [3/4] Starting server on http://localhost:8000 ...
start "NEXUS-1 Server" /min py app.py

echo [4/4] Opening public tunnel...
py deploy\tunnel.py
pause
