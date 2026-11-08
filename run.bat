@echo off
rem Start WorkTrack Pro locally and open it in the browser. Close this window to stop the server.
chcp 65001 >nul
cd /d "%~dp0"
title WorkTrack Pro (local server)

if not exist ".venv\Scripts\python.exe" (
    echo The virtual environment .venv was not found in this folder.
    echo Create it once with:  python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
if not exist ".env" (
    echo DEBUG=True> .env
)

rem Apply any new database changes, then open the browser a moment after the server starts.
".venv\Scripts\python.exe" manage.py migrate --noinput
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000/"
".venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
pause
