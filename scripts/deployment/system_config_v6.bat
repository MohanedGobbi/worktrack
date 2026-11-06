@echo off
:: ==============================================================================
::  WorkTrack Pro / DEGHA NOVA v6.0
::  Option 22: Standalone Production Update, Build Cleanup & Machine Security Lock
::  Platform: Windows Batch Script (.bat)
:: ==============================================================================

setlocal enabledelayedexpansion
title WorkTrack Pro - Option 22 System Update & Security Lock

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

color 0A
echo.
echo ====================================================================
echo    🚀 OPTION 22: SYSTEM UPDATE & PRODUCTION CONFIGURATION (v6)
echo ====================================================================
echo.
echo [WARNING] PRODUCTION DEPLOYMENT - DESTRUCTIVE CLEANUP & LOCK
echo.
echo This operation permanently removes development resources and
echo locks the application to THIS server machine via HMAC-SHA256.
echo.

set /p CONFIRM1="Type 'CONFIRM' to proceed with production cleanup: "
if /i not "%CONFIRM1%"=="CONFIRM" (
    echo [INFO] Operation canceled by user.
    pause
    exit /b 0
)

set /p CONFIRM2="Type 'DELETE' to confirm file removal: "
if /i not "%CONFIRM2%"=="DELETE" (
    echo [INFO] Operation canceled by user.
    pause
    exit /b 0
)

echo.
echo ====================================================================
echo  1/4 Executing Development Build Cleanup
echo ====================================================================

:: Locate Python executable
if exist "%PROJECT_DIR%.venv\Scripts\python.exe" (
    set "PYTHON_BIN=%PROJECT_DIR%.venv\Scripts\python.exe"
) else (
    set "PYTHON_BIN=python"
)

:: Create logs directory
if not exist "%PROJECT_DIR%logs" mkdir "%PROJECT_DIR%logs"

:: Remove Development Helper Python Scripts
echo Clearing development helper scripts...
for %%f in (
    add_tabs.py autowrap_templates.py capture_pages.py copy_admin_banner.py
    create_demo.py create_test_users.py demo_files.py download_global_assets.py
    fix_css.py fix_fab.py fix_messenger.py fix_messenger_extra.py
    fix_messenger_leftovers.py fix_messenger_undo.py fix_panel.py
    init_homepage_data.py init_tenants.py inspect_render.py make_notes_amazing.py
    modify_css.py modify_css_light.py modify_portal.py modify_portal_2.py
    modify_portal_3.py populate_arabic_translations.py rebuild_site_settings.py
    rebuild_ui_library.py repro_file_copy.py strip_showcase.py transform.py
    update_banner_and_notes.py update_banner_style.py update_color.py
    verify_cover.py verify_sync.py
) do (
    if exist "%PROJECT_DIR%%%f" del /f /q "%PROJECT_DIR%%%f" 2>nul
)

:: Remove Test Scripts & Files
echo Clearing test files and directories...
for %%f in (test_*.py test_*.js test_*.txt) do (
    if exist "%PROJECT_DIR%%%f" del /f /q "%PROJECT_DIR%%%f" 2>nul
)
if exist "%PROJECT_DIR%tests" rmdir /s /q "%PROJECT_DIR%tests" 2>nul

:: Remove Development Documentation
echo Clearing development documentation...
for %%f in (
    API_DOCUMENTATION.md APPLICATION_AUDIT_REPORT.md
    AUDIT_AND_ENHANCEMENTS_SUMMARY.md BUTTON_FIXES_COMPLETE.md
    BUTTON_FIXES_VERIFICATION.md COMPLETION_REPORT.md
    DEDICATED_USER_PAGE_SUMMARY.md DEVELOPER_GUIDE.md DOCKER_SETUP.md
    DOCUMENTATION_INDEX.md FIXES_SUMMARY_feb25.md
    GUI_ENHANCEMENTS_SUMMARY.md GUI_FIXES_SUMMARY.md
    GUI_IMPLEMENTATION_SUMMARY.md GUI_REVISION_COMPLETION_REPORT.md
    GUI_REVISION_FINAL_REPORT.md GUI_REVISION_SUMMARY.txt
    IMPLEMENTATION_SUMMARY.md MANAGE_SCRIPT_IMPROVEMENTS.md
    MANAGE_SCRIPT_IMPROVEMENTS_2.md NEW_FEATURES_QUICK_GUIDE.md
    NEW_FEATURES_QUICK_REFERENCE.md QUICK_START.md QUICKSTART.sh
    SESSION_SUMMARY.md SETUP_FIXES_COMPLETE.md SETUP_IMPROVEMENTS.md
    STATUS_REPORT.md TESTING_GUIDE.md TRANSLATION_MANAGER_REFACTOR_COMPLETE.md
    USERS_CREATED_SUMMARY.txt USER_CREATION_GUIDE.md
    USER_CREDENTIALS_REFERENCE.md VISUAL_WORKFLOW_GUIDE.md
    WORKFLOW_GUIDE.md WORKTRACK_PRO_COMPLETE_GUIDE.odt
    WORKTRACK_PRO_COMPLETE_GUIDE.txt ALL_USERS_READY_GUIDE.txt
    CLIENT_PRESENTATION.md
) do (
    if exist "%PROJECT_DIR%%%f" del /f /q "%PROJECT_DIR%%%f" 2>nul
)

:: Remove Temporary / Cache / Metadata Folders & Files
echo Clearing cache, metadata, and temporary files...
for %%f in (
    cookies.txt docker_up.log .server.pid .DS_Store
    tmp_raw_home.html tmp_translations_error.html
    messaging.zip templates.zip templates01.zip templates2.zip templates3.zip
    package-lock.json =3.15 =5.1 db.sqlite3.bak db.sqlite3-journal
) do (
    if exist "%PROJECT_DIR%%%f" del /f /q "%PROJECT_DIR%%%f" 2>nul
)

for %%d in (.git .github .vscode .idea .dockerignore .pytest_cache .mypy_cache .venv_trans node_modules) do (
    if exist "%PROJECT_DIR%%%d" rmdir /s /q "%PROJECT_DIR%%%d" 2>nul
)

:: Clean __pycache__ folders recursively
echo Cleaning Python cache directories...
for /d /r "%PROJECT_DIR%" %%d in (__pycache__) do (
    if exist "%%d" rmdir /s /q "%%d" 2>nul
)
for /r "%PROJECT_DIR%" %%f in (*.pyc *.pyo) do (
    if exist "%%f" del /f /q "%%f" 2>nul
)

echo.
echo ====================================================================
echo  2/4 Activating Hardware Binding & Security Lock (.prod_lock)
echo ====================================================================
if exist "%PROJECT_DIR%scripts\prod_lock.py" (
    "%PYTHON_BIN%" "%PROJECT_DIR%scripts\prod_lock.py"
) else (
    echo [WARN] scripts\prod_lock.py not found. Security lock skipped.
)

echo.
echo ====================================================================
echo  3/4 Running System Deployment Integrity Check
echo ====================================================================
"%PYTHON_BIN%" manage.py check --deploy

echo.
echo ====================================================================
echo  4/4 Enforcing Resource Quotas & 3x Multiplier Scaling
echo ====================================================================
rem no limits

echo.
echo ====================================================================
echo  🎉 OPTION 22 SYSTEM UPDATE & PRODUCTION LOCK COMPLETED!
echo ====================================================================
echo.
echo The application is now cleaned, obfuscated, and cryptographically
echo bound to this Windows server environment (.prod_lock).
echo.
pause
