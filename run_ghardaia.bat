@echo off
rem University of Ghardaia version: own database and uploads, port 8001. Close this window to stop.
chcp 65001 >nul
cd /d "%~dp0"
title WorkTrack Pro - University of Ghardaia (port 8001)

set PYTHON_EXE=.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    echo The virtual environment .venv is missing. Run run.bat once first; it sets it up.
    pause
    exit /b 1
)
if not exist ".env" (
    echo DEBUG=True> .env
)

rem Keep this version apart from the ROWD demo: its own database and uploads folder.
set PYTHONIOENCODING=utf-8
set DB_NAME=db_ghardaia.sqlite3
set MEDIA_ROOT=%~dp0media_ghardaia

"%PYTHON_EXE%" manage.py migrate --noinput
if not exist "ghardaia_setup.log" (
    echo Setting up the University of Ghardaia for the first time...
    "%PYTHON_EXE%" manage.py new_institution --config institutions\ghardaia\institution.json > ghardaia_setup.log 2>&1
    rem Demo accounts for testing (DEBUG only); remove this line for a real install.
    "%PYTHON_EXE%" manage.py load_demo --config institutions\ghardaia\demo.json >> ghardaia_setup.log 2>&1
    type ghardaia_setup.log
    echo.
    echo The administrator password above is also saved in ghardaia_setup.log
    pause
)

start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8001/login/"
"%PYTHON_EXE%" manage.py runserver 127.0.0.1:8001
pause
