@echo off
setlocal
cd /d "%~dp0"
title SADAH Update
chcp 65001 >nul
set "GIT=git"
where git >nul 2>nul || set "GIT=C:\Program Files\Git\cmd\git.exe"

echo [1/3] Running smoke tests...
py -m tests.smoke_test
if errorlevel 1 (
    echo Tests failed - nothing was pushed. Fix the errors and try again.
    pause
    exit /b 1
)

echo [2/3] Saving changes...
set /p "MSG=Describe your change: "
if "%MSG%"=="" set "MSG=Update SADAH v1"
"%GIT%" add -A
"%GIT%" commit -m "%MSG%"

echo [3/3] Pushing to GitHub...
"%GIT%" push
echo.
rem Private Render Deploy Hook URL (gitignored): triggers the redeploy without opening Render.
set "HOOK="
if exist ".render_hook" set /p HOOK=<.render_hook
if defined HOOK (
    curl -s -X POST "%HOOK%" >nul && echo Render deploy started - the live link updates in about 5 minutes.
) else (
    echo Done. Now open Render and click Manual Deploy - Deploy latest commit.
)
pause
