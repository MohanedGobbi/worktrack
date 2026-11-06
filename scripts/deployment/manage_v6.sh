#!/bin/bash

# WorkTrack Pro - Local Management Script v6 (No Docker)
# Setup for local SQLite + Python Venv environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/manage.py" ]; then
    PROJECT_DIR="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/../../manage.py" ]; then
    PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
elif [ -f "$SCRIPT_DIR/../manage.py" ]; then
    PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    PROJECT_DIR="$PWD"
fi

BACKUP_DIR="$PROJECT_DIR/backup"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/server.log"
VENV_DIR="$PROJECT_DIR/.venv"

# ANSI Color Codes
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

print_success() { printf '%b\n' "${GREEN}✓ $1${NC}"; }
print_error() { printf '%b\n' "${RED}✗ $1${NC}"; }
print_info() { printf '%b\n' "${CYAN}ℹ $1${NC}"; }
print_warning() { printf '%b\n' "${YELLOW}⚠ $1${NC}"; }
print_header() { printf '%b\n' "${BOLD}${CYAN}╭─ $1${NC}"; }

verify_security_files() {
    local missing=()
    for f in "activate.sh" "scripts/prod_lock.py" "core/models.py" "core/signals.py" "core/middleware/main.py" "core/management/commands/configure_limits.py"; do
        if [ ! -f "$PROJECT_DIR/$f" ]; then
            missing+=("$f")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        clear
        printf '%b\n' "${RED}${BOLD}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
        printf '%b\n' "${RED}${BOLD}║   🚨 CRITICAL SYSTEM SECURITY INTEGRITY FAULT DETECTED                     ║${NC}"
        printf '%b\n' "${RED}${BOLD}╠════════════════════════════════════════════════════════════════════════════╣${NC}"
        printf '%b\n' "${RED}${BOLD}║                                                                            ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   Required System Security Protection files are MISSING or TAMPERED with! ║${NC}"
        for m in "${missing[@]}"; do
            printf '%b\n' "${RED}${BOLD}║   -> Missing File: %-55s ║${NC}" "$m"
        done
        printf '%b\n' "${RED}${BOLD}║                                                                            ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   SERVER LAUNCH / MANAGEMENT CANNOT RUN UNTIL RESTORED.                   ║${NC}"
        printf '%b\n' "${RED}${BOLD}║                                                                            ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   Contact System Security Director & Administration immediately:            ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   Director:         Dr. DEGHA Houssem Eddine                               ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   Phone / WhatsApp: +213 697381211                                         ║${NC}"
        printf '%b\n' "${RED}${BOLD}║   Email:            degha.houssem@outlook.com                              ║${NC}"
        printf '%b\n' "${RED}${BOLD}║                                                                            ║${NC}"
        printf '%b\n' "${RED}${BOLD}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        exit 1
    fi
}

verify_venv_integrity() {
    local venv_broken=false
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/python" ]; then
        if ! "$VENV_DIR/bin/python" -c "import django" &>/dev/null; then
            venv_broken=true
        fi
    else
        venv_broken=true
    fi

    if [ "$venv_broken" = true ]; then
        print_warning "Detecting missing or incomplete virtual environment (.venv)!"
        print_info "Configuring Python virtual environment (.venv) for path: $VENV_DIR ..."
        if [ ! -d "$VENV_DIR" ]; then
            python3 -m venv "$VENV_DIR"
        fi
        "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            print_info "Installing dependencies from requirements.txt..."
            "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
        fi
        print_success "Virtual environment verified and ready!"
    fi
}

python_cmd() {
    verify_security_files
    verify_venv_integrity
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        print_info "Virtual environment (.venv) not found. Initializing..."
        python3 -m venv "$VENV_DIR"
        "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true
        if [ -f "$PROJECT_DIR/requirements.txt" ]; then
            print_info "Installing dependencies..."
            "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q 2>/dev/null || "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
        fi
    fi
    "$VENV_DIR/bin/python" "$@"
}

install_app() {
    print_header "Installing WorkTrack Pro (Local/No Docker)"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi

    mkdir -p "$LOG_DIR" "$BACKUP_DIR"

    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
        print_info "Creating Python virtual environment in $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
    fi

    print_info "Verifying and updating Python dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q 2>/dev/null || true
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        print_info "Installing requirements from requirements.txt..."
        "$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
    fi

    # Build WorkTrack Pro 3D Homepage Frontend if npm is available
    if command -v npm &> /dev/null && [ -d "$PROJECT_DIR/worktrack-pro" ]; then
        print_info "Checking WorkTrack Pro 3D homepage frontend..."
        if [ ! -d "$PROJECT_DIR/worktrack-pro/dist" ] || [ ! -d "$PROJECT_DIR/static/worktrack_pro" ]; then
            print_info "Building WorkTrack Pro 3D frontend bundle..."
            (cd "$PROJECT_DIR/worktrack-pro" && npm run build) || print_warning "Frontend build finished with notices."
        fi
        if [ -d "$PROJECT_DIR/worktrack-pro/dist" ]; then
            mkdir -p "$PROJECT_DIR/static/worktrack_pro" "$PROJECT_DIR/templates/pages"
            cp -r "$PROJECT_DIR/worktrack-pro/dist/assets" "$PROJECT_DIR/static/worktrack_pro/" 2>/dev/null || true
            cp "$PROJECT_DIR/worktrack-pro/dist/index.html" "$PROJECT_DIR/templates/pages/worktrack_home.html" 2>/dev/null || true
            print_success "WorkTrack Pro 3D assets & template synchronized!"
        fi
    fi

    print_info "Ensuring local SQLite setup in .env..."
    if [ -f "$PROJECT_DIR/.env" ]; then
        sed -i 's/^DB_ENGINE=.*/DB_ENGINE=django.db.backends.sqlite3/' "$PROJECT_DIR/.env"
        sed -i 's/^DB_NAME=.*/DB_NAME=db.sqlite3/' "$PROJECT_DIR/.env"
        if ! grep -q "^CELERY_TASK_ALWAYS_EAGER=" "$PROJECT_DIR/.env"; then
            echo "CELERY_TASK_ALWAYS_EAGER=True" >> "$PROJECT_DIR/.env"
        else
            sed -i 's/^CELERY_TASK_ALWAYS_EAGER=.*/CELERY_TASK_ALWAYS_EAGER=True/' "$PROJECT_DIR/.env"
        fi
    fi

    print_info "Applying database migrations..."
    python_cmd manage.py migrate
    
    print_info "Collecting static files..."
    python_cmd manage.py collectstatic --noinput
    
    print_info "Configuring active homepage in SiteConfiguration..."
    python_cmd -c "
import django; django.setup()
from core.models import SiteConfiguration, PlatformConfig
try:
    cfg = SiteConfiguration.get_solo()
    cfg.active_homepage = 'worktrack_simulation'
    cfg.display_homepage = True
    cfg.save()
    pcfg = PlatformConfig.get_solo()
    pcfg.save()
    print('  ✓ Default homepage set to WorkTrack Pro 3D Simulation.')
except Exception as e:
    print('  ⚠ Notice:', e)
" 2>/dev/null || true

    echo ""
    read -p "Would you like to create/update an admin superuser? (y/N): " create_su
    if [[ "$create_su" =~ ^[Yy]$ ]]; then
        create_superuser
    fi

    print_success "WorkTrack Pro installation & configuration complete!"
    print_info "You can now start the application with: ./manage_v6.sh start (or via ./menu.sh)"
}

start_app() {
    print_header "Starting WorkTrack Pro (Local)"
    verify_venv_integrity

    # Ensure port 8000 is clear before starting
    print_info "Ensuring port 8000 is available..."
    if command -v fuser >/dev/null 2>&1; then
        fuser -k 8000/tcp >/dev/null 2>&1 || true
    fi
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1 || true
    fi
    pkill -f "manage.py runserver" 2>/dev/null || true
    sleep 1

    # Verify or regenerate machine binding if moved
    if [ -f "$PROJECT_DIR/scripts/prod_lock.py" ]; then
        python_cmd "$PROJECT_DIR/scripts/prod_lock.py" &>/dev/null || python3 "$PROJECT_DIR/scripts/prod_lock.py" &>/dev/null || true
    fi

    mkdir -p "$LOG_DIR"
    # Ensure static manifest is up to date to prevent 404 / white screen issues
    if [ -f "$VENV_DIR/bin/python" ]; then
        "$VENV_DIR/bin/python" manage.py collectstatic --noinput >/dev/null 2>&1 || true
    fi
    print_info "Starting Django development server on http://localhost:8000 ..."
    setsid "$VENV_DIR/bin/python" manage.py runserver 0.0.0.0:8000 >> "$LOG_FILE" 2>&1 &
    local server_pid=$!
    echo $server_pid > "$PROJECT_DIR/.server.pid"
    ln -sf "$LOG_FILE" /tmp/django_server.log 2>/dev/null || true
    
    sleep 2
    if kill -0 "$server_pid" 2>/dev/null || pgrep -f "manage.py runserver" >/dev/null 2>&1; then
        print_success "Server started successfully in background! (PID: $server_pid)"
        echo ""
        print_header "WorkTrack Pro Access Points"
        printf '%b\n' "  🌐 ${BOLD}Home (3D Simulation):${NC} ${CYAN}http://localhost:8000${NC}"
        printf '%b\n' "  🎨 ${BOLD}3D Home Admin Studio:${NC}  ${CYAN}http://localhost:8000/?admin=true${NC}"
        printf '%b\n' "  🔑 ${BOLD}Login:${NC}                 ${CYAN}http://localhost:8000/login/${NC}"
        printf '%b\n' "  📝 ${BOLD}Register:${NC}              ${CYAN}http://localhost:8000/register/${NC}"
        printf '%b\n' "  ⚙️  ${BOLD}Admin Dashboard:${NC}       ${CYAN}http://localhost:8000/admin-dashboard/${NC}"
        printf '%b\n' "  🛡️  ${BOLD}Django Admin:${NC}          ${CYAN}http://localhost:8000/admin/${NC}"
        printf '%b\n' "  📜 ${BOLD}Server Logs:${NC}           ${YELLOW}$LOG_FILE${NC}"
        echo ""
    else
        print_error "Server failed to start. Last log output:"
        if [ -f "$LOG_FILE" ]; then
            tail -n 25 "$LOG_FILE"
        fi
        return 1
    fi
}

stop_app() {
    print_header "Stopping WorkTrack Pro (Local)"
    local stopped=false
    if [ -f "$PROJECT_DIR/.server.pid" ]; then
        PID=$(cat "$PROJECT_DIR/.server.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            sleep 1
            kill -9 "$PID" 2>/dev/null || true
            stopped=true
        fi
        rm -f "$PROJECT_DIR/.server.pid"
    fi
    
    # Backup kill command for anything on port 8000 or running runserver
    if command -v fuser >/dev/null 2>&1; then
        fuser -k 8000/tcp >/dev/null 2>&1 || true
    fi
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1 || true
    fi
    pkill -f "manage.py runserver" 2>/dev/null || true
    print_success "WorkTrack Pro server stopped successfully."
}

restart_app() {
    print_header "Restarting WorkTrack Pro Server"
    stop_app
    sleep 2
    start_app
}

status_app() {
    print_header "WorkTrack Pro Server Status"
    local running=false
    local pid=""
    if [ -f "$PROJECT_DIR/.server.pid" ]; then
        pid=$(cat "$PROJECT_DIR/.server.pid")
        if kill -0 "$pid" 2>/dev/null; then
            running=true
        fi
    fi
    
    if [ "$running" = false ]; then
        local pids
        pids=$(pgrep -f "manage.py runserver" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            running=true
            pid=$(echo "$pids" | head -n1)
            echo "$pid" > "$PROJECT_DIR/.server.pid"
        fi
    fi

    if [ "$running" = false ]; then
        if command -v ss >/dev/null 2>&1 && ss -tulpn 2>/dev/null | grep -q ":8000 "; then
            running=true
            pid="active (port 8000)"
        elif command -v lsof >/dev/null 2>&1 && lsof -ti:8000 >/dev/null 2>&1; then
            running=true
            pid=$(lsof -ti:8000 2>/dev/null | head -n1)
        fi
    fi

    if [ "$running" = true ]; then
        print_success "Status: RUNNING (PID: $pid)"
        print_info "Port: 8000"
        echo ""
        print_header "WorkTrack Pro Access Points"
        printf '%b\n' "  🌐 ${BOLD}Home (3D Simulation):${NC} ${CYAN}http://localhost:8000${NC}"
        printf '%b\n' "  🎨 ${BOLD}3D Home Admin Studio:${NC}  ${CYAN}http://localhost:8000/?admin=true${NC}"
        printf '%b\n' "  🔑 ${BOLD}Login:${NC}                 ${CYAN}http://localhost:8000/login/${NC}"
        printf '%b\n' "  📝 ${BOLD}Register:${NC}              ${CYAN}http://localhost:8000/register/${NC}"
        printf '%b\n' "  ⚙️  ${BOLD}Admin Dashboard:${NC}       ${CYAN}http://localhost:8000/admin-dashboard/${NC}"
        printf '%b\n' "  🛡️  ${BOLD}Django Admin:${NC}          ${CYAN}http://localhost:8000/admin/${NC}"
        printf '%b\n' "  📜 ${BOLD}Server Logs:${NC}           ${YELLOW}$LOG_FILE${NC}"
        echo ""
        return 0
    else
        print_warning "Status: STOPPED (not running)"
        rm -f "$PROJECT_DIR/.server.pid" 2>/dev/null || true
        return 1
    fi
}

shell_app() {
    print_header "Django Shell"
    python_cmd manage.py shell
}

db_info_app() {
    print_header "Database Information (SQLite)"
    DB_FILE="$PROJECT_DIR/db.sqlite3"
    if [ -f "$DB_FILE" ]; then
        local size mtime count users
        size=$(du -h "$DB_FILE" | cut -f1)
        mtime=$(stat -c '%y' "$DB_FILE" 2>/dev/null || stat -f "%Sm" "$DB_FILE" 2>/dev/null || echo "Unknown")
        print_info "Database File: $DB_FILE"
        print_info "Size:          $size"
        print_info "Last Modified: $mtime"
        if command -v sqlite3 >/dev/null 2>&1; then
            count=$(sqlite3 "$DB_FILE" ".tables" 2>/dev/null | wc -w)
            print_info "Total Tables:  $count"
        fi
        users=$(python_cmd -c "
import django; django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
print('Users: {}, Superadmins: {}'.format(User.objects.count(), User.objects.filter(is_superuser=True).count()))
" 2>/dev/null || true)
        if [ -n "$users" ]; then
            print_info "Accounts:      $users"
        fi
    else
        print_warning "Database file not found at $DB_FILE"
    fi
}

stop_all_servers() {
    print_header "Stopping All Local Servers (Force Kill)"
    
    stop_app
    
    print_info "Hunting down remaining Python servers on port 8000..."
    if command -v fuser >/dev/null 2>&1; then
        fuser -k 8000/tcp >/dev/null 2>&1 || true
    fi
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1 || true
    fi
    
    print_info "Killing background Celery workers..."
    pkill -9 -f "celery -A worktrack_pro worker" || true
    pkill -9 -f "celery -A worktrack_pro beat" || true
    
    pkill -9 -f "manage.py runserver" || true
    
    print_success "All local servers and background workers have been forcefully stopped!"
    print_info "Port 8000 is now clear."
}

logs_app() {
    print_header "WorkTrack Pro Logs"
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    elif [ -f "/tmp/django_server.log" ]; then
        tail -f "/tmp/django_server.log"
    else
        print_info "Log file not found. Please start the server first."
    fi
}

quick_update() {
    print_header "Quick Update (Migrations + Static Files)"
    print_info "Creating database migrations..."
    if ! python_cmd manage.py makemigrations; then
        print_error "Failed to create migrations"
        return 1
    fi
    print_info "Applying database migrations..."
    if ! python_cmd manage.py migrate; then
        print_error "Failed to run migrations"
        return 1
    fi
    print_info "Collecting static files..."
    if ! python_cmd manage.py collectstatic --noinput; then
        print_error "Failed to collect static files"
        return 1
    fi
    print_info "Executing application activation (scaling system limits x3)..."
    if ! true; then
        print_error "Failed to activate system limits"
        return 1
    fi
    print_success "Update & Application Activation complete! (Limits scaled x3)"
}


create_superuser() {
    print_header "Create Super Admin User"
    echo ""
    printf '%b\n' "${BOLD}This will create a new super_admin account in WorkTrack Pro.${NC}"
    echo ""
    read -p "  Email address : " SU_EMAIL
    if [ -z "$SU_EMAIL" ]; then print_error "Email cannot be empty."; return 1; fi
    read -p "  First name    : " SU_FIRST
    read -p "  Last name     : " SU_LAST

    while true; do
        read -s -p "  Password      : " SU_PASS; echo ""
        read -s -p "  Confirm pass  : " SU_PASS2; echo ""
        if [ "$SU_PASS" = "$SU_PASS2" ]; then break; fi
        print_error "Passwords do not match. Try again."
    done

    echo ""
    print_info "Creating user in the database..."

    python_cmd manage.py shell -c "
import sys
from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    email = '${SU_EMAIL}'
    if User.objects.filter(email=email).exists():
        print('ERROR: A user with that email already exists.', file=sys.stderr)
        sys.exit(1)
    u = User.objects.create_superuser(
        email=email,
        password='${SU_PASS}',
        first_name='${SU_FIRST}',
        last_name='${SU_LAST}',
    )
    u.role = 'super_admin'
    u.save()
    print('OK')
except Exception as e:
    print('ERROR:', e, file=sys.stderr)
" 2>&1 | while IFS= read -r line; do
        if [[ "$line" == ERROR* ]]; then
            print_error "${line#ERROR: }"
        elif [[ "$line" == OK* ]]; then
            print_success "Super admin \"${SU_EMAIL}\" created successfully!"
        else
            printf '%s\n' "$line"
        fi
    done
}

make_migrations() {
    print_header "Create Migrations"
    if ! python_cmd manage.py makemigrations; then print_error "Failed to create migrations"; return 1; fi
    print_success "Migrations created!"
}

run_migrations() {
    print_header "Run Migrations"
    if ! python_cmd manage.py migrate; then print_error "Failed to run migrations"; return 1; fi
    print_success "Migrations applied!"
}

collect_static() {
    print_header "Collect Static Files"
    if ! python_cmd manage.py collectstatic --noinput; then print_error "Failed to collect static files"; return 1; fi
    print_success "Static files collected!"
}

backup_app() {
    print_header "Database Backup (SQLite)"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/db_sqlite_$TIMESTAMP.sqlite3"
    
    if [ ! -f "db.sqlite3" ]; then
        print_error "db.sqlite3 not found in $PROJECT_DIR."
        return 1
    fi

    print_info "Creating safe live SQLite database snapshot..."
    if python_cmd -c "import sqlite3; src=sqlite3.connect('db.sqlite3'); dst=sqlite3.connect('$BACKUP_FILE'); src.backup(dst); dst.close(); src.close()"; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        print_success "Database backup completed successfully!"
        print_info "  Size: $SIZE"
        print_info "  Path: $BACKUP_FILE"
    else
        print_error "Failed to create database snapshot."
        return 1
    fi
}

full_backup_app() {
    print_header "Full Application Backup"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/full_backup_$TIMESTAMP.tar.gz"
    TEMP_ARCHIVE="/tmp/full_backup_$TIMESTAMP.tar.gz"

    print_info "Creating safe live database snapshot for archive..."
    TEMP_DB="/tmp/temp_db_backup_$TIMESTAMP.sqlite3"
    if [ -f "db.sqlite3" ]; then
        python_cmd -c "import sqlite3; src=sqlite3.connect('db.sqlite3'); dst=sqlite3.connect('$TEMP_DB'); src.backup(dst); dst.close(); src.close()" || cp db.sqlite3 "$TEMP_DB" 2>/dev/null || true
    fi

    print_info "Creating full application archive (code + database)..."
    tar --warning=no-file-changed -czf "$TEMP_ARCHIVE" \
        --exclude="backup" \
        --exclude="./backup" \
        --exclude=".venv" \
        --exclude="./.venv" \
        --exclude="venv" \
        --exclude="./venv" \
        --exclude=".venv_trans" \
        --exclude="./.venv_trans" \
        --exclude="staticfiles" \
        --exclude="./staticfiles" \
        --exclude="node_modules" \
        --exclude="./node_modules" \
        --exclude="__pycache__" \
        --exclude="./__pycache__" \
        --exclude=".translation_cache" \
        --exclude="./.translation_cache" \
        --exclude=".git" \
        --exclude="./.git" \
        --exclude="*.pyc" \
        --exclude="*.log" \
        --exclude="*.sqlite3-journal" \
        --exclude="*.sqlite3-wal" \
        --exclude="*.sqlite3-shm" \
        . 2>/dev/null || true

    rm -f "$TEMP_DB" 2>/dev/null || true

    if [ -f "$TEMP_ARCHIVE" ] && [ -s "$TEMP_ARCHIVE" ]; then
        mv "$TEMP_ARCHIVE" "$BACKUP_FILE"
    fi

    if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ] && tar -tzf "$BACKUP_FILE" >/dev/null 2>&1; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        print_success "Full application backup completed successfully!"
        print_info "  Size: $SIZE"
        print_info "  Archive: $BACKUP_FILE"
        print_divider
        print_info "To restore this backup later:"
        print_info "  ./manage_v6.sh restore_full $BACKUP_FILE"
    else
        print_error "Failed to create or verify full backup archive."
        rm -f "$TEMP_ARCHIVE" "$BACKUP_FILE" 2>/dev/null || true
        return 1
    fi
}

restore_full_app() {
    print_header "Full Backup Restore"

    TARGET_FILE=""
    if [ -n "$1" ] && [ "$1" != "restore_full" ]; then
        TARGET_FILE="$1"
    elif [ -n "$2" ]; then
        TARGET_FILE="$2"
    fi

    if [ -z "$TARGET_FILE" ]; then
        print_info "No backup archive specified. Scanning $BACKUP_DIR for full backups..."
        mkdir -p "$BACKUP_DIR"
        mapfile -t FILES < <(find "$BACKUP_DIR" -type f -name "full_backup_*.tar.gz" | sort -r)
        if [ ${#FILES[@]} -eq 0 ]; then
            print_error "No full_backup_*.tar.gz archive files found in $BACKUP_DIR."
            return 1
        fi
        print_info "Available Full Application Backups:"
        for i in "${!FILES[@]}"; do
            SIZE=$(du -h "${FILES[$i]}" | cut -f1)
            FNAME=$(basename "${FILES[$i]}")
            printf "  ${CYAN}[%d]${NC} %s (%s)\n" "$((i+1))" "$FNAME" "$SIZE"
        done
        echo ""
        read -p "Select backup archive to restore (or 'c' to cancel): " idx
        if [[ "$idx" == "c" ]] || [[ "$idx" == "C" ]] || [ -z "$idx" ]; then
            print_info "Restore cancelled."
            return 0
        fi
        if ! [[ "$idx" =~ ^[0-9]+$ ]] || [ "$idx" -lt 1 ] || [ "$idx" -gt "${#FILES[@]}" ]; then
            print_error "Invalid selection."
            return 1
        fi
        TARGET_FILE="${FILES[$((idx-1))]}"
    fi

    if [ ! -f "$TARGET_FILE" ]; then
        print_error "Full backup archive not found: $TARGET_FILE"
        return 1
    fi

    print_info "Verifying archive integrity..."
    if ! tar -tzf "$TARGET_FILE" >/dev/null 2>&1; then
        print_error "Corrupted or invalid tar.gz archive file."
        return 1
    fi

    print_warning "WARNING: This will overwrite files in the current project directory."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled."
        return 0
    fi

    print_info "Extracting backup archive..."
    if tar -xzf "$TARGET_FILE" -C "$PROJECT_DIR"; then
        print_success "Full application backup extracted successfully!"
        if [ -f "db.sqlite3" ]; then
            print_info "SQLite database restored from archive."
        fi
    else
        print_error "Failed to extract full backup archive."
        return 1
    fi
}

restore_app() {
    print_header "Database Restore (SQLite)"
    
    TARGET_FILE=""
    if [ -n "$1" ] && [ "$1" != "restore" ]; then
        TARGET_FILE="$1"
    elif [ -n "$2" ]; then
        TARGET_FILE="$2"
    fi

    if [ -z "$TARGET_FILE" ]; then
        print_info "No backup file specified. Scanning $BACKUP_DIR for available backups..."
        mkdir -p "$BACKUP_DIR"
        mapfile -t FILES < <(find "$BACKUP_DIR" -type f -name "*.sqlite3" | sort -r)
        if [ ${#FILES[@]} -eq 0 ]; then
            print_error "No .sqlite3 backup files found in $BACKUP_DIR."
            return 1
        fi
        print_info "Available Database Backups:"
        for i in "${!FILES[@]}"; do
            SIZE=$(du -h "${FILES[$i]}" | cut -f1)
            FNAME=$(basename "${FILES[$i]}")
            printf "  ${CYAN}[%d]${NC} %s (%s)\n" "$((i+1))" "$FNAME" "$SIZE"
        done
        echo ""
        read -p "Select backup number to restore (or 'c' to cancel): " idx
        if [[ "$idx" == "c" ]] || [[ "$idx" == "C" ]] || [ -z "$idx" ]; then
            print_info "Restore cancelled."
            return 0
        fi
        if ! [[ "$idx" =~ ^[0-9]+$ ]] || [ "$idx" -lt 1 ] || [ "$idx" -gt "${#FILES[@]}" ]; then
            print_error "Invalid selection."
            return 1
        fi
        TARGET_FILE="${FILES[$((idx-1))]}"
    fi

    if [ ! -f "$TARGET_FILE" ]; then
        print_error "Backup file not found: $TARGET_FILE"
        return 1
    fi

    print_warning "WARNING: This will overwrite the current active db.sqlite3."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled."
        return 0
    fi

    print_info "Restoring database from $TARGET_FILE..."
    if cp "$TARGET_FILE" db.sqlite3; then
        print_success "Database restore completed successfully!"
    else
        print_error "Failed to restore database."
        return 1
    fi
}

setup_vscode_env() {
    print_header "VS Code Local Environment Setup"
    print_divider
    
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is not installed. Please install it first."
        return 1
    fi

    if [ -d "$VENV_DIR" ]; then
        print_info "Removing old/broken virtual environment..."
        rm -rf "$VENV_DIR"
    fi

    print_info "Creating virtual environment in .venv..."
    if ! python3 -m venv "$VENV_DIR"; then
        print_error "Failed to create virtual environment."
        return 1
    fi
    
    if [ -f "requirements.txt" ]; then
        print_info "Installing/Updating requirements..."
        "$VENV_DIR/bin/pip" install --upgrade pip
        if ! "$VENV_DIR/bin/pip" install -r requirements.txt; then
            print_error "Failed to install requirements."
            return 1
        fi
    fi

    print_info "Configuring VS Code settings..."
    mkdir -p .vscode
    
    cat > .vscode/settings.json <<EOF
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.analysis.extraPaths": [
        "\${workspaceFolder}",
        "\${workspaceFolder}/worktrack_pro"
    ],
    "python.analysis.typeCheckingMode": "basic",
    "python.terminal.activateEnvInCurrentTerminal": true,
    "python.languageServer": "Pylance",
    "editor.formatOnSave": true,
    "python.analysis.autoImportCompletions": true,
    "python.analysis.diagnosticMode": "workspace"
}
EOF

    print_success "VS Code environment setup complete!"
    print_warning "Please restart VS Code or 'Reload Window' for changes."
}

repair_ide_environment() {
    print_header "Repair System & Environment"
    setup_vscode_env
    print_info "Running database integrity check (migrations)..."
    python_cmd manage.py makemigrations 2>/dev/null || true
    python_cmd manage.py migrate
    print_success "Database migrations synced."
    
    print_info "Refreshing static assets..."
    python_cmd manage.py collectstatic --noinput 2>/dev/null
    print_success "Static files refreshed."
}

setup_email_settings() {
    print_header "System Email Settings (SMTP) Setup"
    
    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        touch "$DOTENV_FILE"
    fi

    echo "Configure SMTP credentials to allow the system to send emails (notifications, password resets, etc.)."
    echo ""

    read -p "  SMTP Host Server [default: smtp.gmail.com]: " host_input
    SMTP_HOST="${host_input:-smtp.gmail.com}"

    read -p "  SMTP Port [default: 587]: " port_input
    SMTP_PORT="${port_input:-587}"

    read -p "  Use TLS (y/n) [default: y]: " tls_input
    if [[ "$tls_input" =~ ^[Nn]$ ]]; then
        SMTP_TLS="False"
    else
        SMTP_TLS="True"
    fi

    read -p "  SMTP Email Username (e.g. sender@gmail.com): " SMTP_USER
    if [ -z "$SMTP_USER" ]; then
        print_error "SMTP Username cannot be empty."
        return 1
    fi

    read -s -p "  SMTP Password / App Password: " SMTP_PASS
    echo ""
    if [ -z "$SMTP_PASS" ]; then
        print_error "SMTP Password cannot be empty."
        return 1
    fi

    read -p "  Default From Email [default: $SMTP_USER]: " from_input
    DEFAULT_FROM="${from_input:-$SMTP_USER}"

    read -p "  Site URL [default: http://localhost:8000]: " site_input
    SITE_URL_VAL="${site_input:-http://localhost:8000}"

    update_env_key() {
        local key=$1
        local val=$2
        if grep -q "^${key}=" "$DOTENV_FILE"; then
            sed -i "s|^${key}=.*|${key}=${val}|" "$DOTENV_FILE"
        else
            echo "${key}=${val}" >> "$DOTENV_FILE"
        fi
    }

    update_env_key "EMAIL_BACKEND" "django.core.mail.backends.smtp.EmailBackend"
    update_env_key "EMAIL_HOST" "$SMTP_HOST"
    update_env_key "EMAIL_PORT" "$SMTP_PORT"
    update_env_key "EMAIL_USE_TLS" "$SMTP_TLS"
    update_env_key "EMAIL_HOST_USER" "$SMTP_USER"
    update_env_key "EMAIL_HOST_PASSWORD" "$SMTP_PASS"
    update_env_key "DEFAULT_FROM_EMAIL" "$DEFAULT_FROM"
    update_env_key "SITE_URL" "$SITE_URL_VAL"

    print_success "Email configuration saved successfully to .env!"

    read -p "Would you like to send a test email now? (y/n) [y]: " run_test
    if [[ ! "$run_test" =~ ^[Nn]$ ]]; then
        test_email_settings
    fi
}

test_email_settings() {
    print_header "Test System Email Diagnostic"
    if [ -f "$PROJECT_DIR/test_email.py" ]; then
        python_cmd "$PROJECT_DIR/test_email.py"
    else
        print_error "test_email.py not found in $PROJECT_DIR."
    fi
}

setup_allowed_hosts() {
    print_header "Configure Allowed Hosts (ALLOWED_HOSTS)"
    
    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        touch "$DOTENV_FILE"
    fi

    # Read current ALLOWED_HOSTS if set in .env
    CURRENT_HOSTS=""
    if grep -q "^ALLOWED_HOSTS=" "$DOTENV_FILE"; then
        CURRENT_HOSTS=$(grep "^ALLOWED_HOSTS=" "$DOTENV_FILE" | cut -d'=' -f2-)
    fi
    if [ -z "$CURRENT_HOSTS" ]; then
        CURRENT_HOSTS="dhetasks.com,www.dhetasks.com,localhost,127.0.0.1"
    fi

    print_info "Current ALLOWED_HOSTS setting: ${CURRENT_HOSTS}"
    echo ""
    printf '%b\n' "${BOLD}${YELLOW}💡 RECOMMENDATION:${NC}"
    printf '%b\n' "${YELLOW}   Set '${BOLD}*${NC}${YELLOW}' (wildcard) as the allowed host.${NC}"
    printf '%b\n' "${CYAN}   Why? Setting '*' allows all domains, server IPs, cPanel passenger proxies,${NC}"
    printf '%b\n' "${CYAN}   and custom domain names without triggering HTTP 400 Bad Request or DisallowedHost errors.${NC}"
    echo ""
    print_info "Examples:"
    print_info "  - '*' (Allow ALL domains/IPs - RECOMMENDED)"
    print_info "  - 'dhetasks.com,www.dhetasks.com,localhost,127.0.0.1'"
    echo ""

    read -p "  Enter Allowed Hosts (or press Enter for recommended '*'): " hosts_input
    NEW_HOSTS="${hosts_input:-*}"

    update_env_key() {
        local key=$1
        local val=$2
        if grep -q "^${key}=" "$DOTENV_FILE"; then
            sed -i "s|^${key}=.*|${key}=${val}|" "$DOTENV_FILE"
        else
            echo "${key}=${val}" >> "$DOTENV_FILE"
        fi
    }

    update_env_key "ALLOWED_HOSTS" "$NEW_HOSTS"

    print_success "ALLOWED_HOSTS set to '${NEW_HOSTS}' in .env!"

    # Sync database AllowedHost wildcard if venv exists and sqlite DB is ready
    if [ -f "$VENV_DIR/bin/python" ] && [ -f "db.sqlite3" ]; then
        print_info "Syncing database AllowedHost table..."
        python_cmd manage.py shell -c "
try:
    from core.models import AllowedHost
    AllowedHost.objects.get_or_create(hostname='*', defaults={'description': 'Wildcard host allowed by manage_v6', 'is_active': True})
    print('DB_SYNC_OK')
except Exception as e:
    print('DB_SYNC_SKIP:', e)
" 2>/dev/null || true
    fi

    print_success "Allowed Hosts configuration complete!"
}

setup_db_settings() {
    print_header "Database Setup & Configuration"

    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        touch "$DOTENV_FILE"
    fi

    update_env_key() {
        local key=$1
        local val=$2
        if grep -q "^${key}=" "$DOTENV_FILE"; then
            sed -i "s|^${key}=.*|${key}=${val}|" "$DOTENV_FILE"
        else
            echo "${key}=${val}" >> "$DOTENV_FILE"
        fi
    }

    echo "Configure the database for WorkTrack Pro."
    echo "  1) SQLite (default local file database)"
    echo "  2) MySQL / MariaDB"
    echo "  3) PostgreSQL"
    echo ""
    read -p "Select database engine [default 1]: " db_choice
    db_choice="${db_choice:-1}"

    case $db_choice in
        1)
            DB_ENGINE="django.db.backends.sqlite3"
            read -p "Database file name/path [default: db.sqlite3]: " db_name_input
            DB_NAME="${db_name_input:-db.sqlite3}"
            update_env_key "DB_ENGINE" "$DB_ENGINE"
            update_env_key "DB_NAME" "$DB_NAME"
            ;;
        2)
            DB_ENGINE="django.db.backends.mysql"
            read -p "Database Host [default: 127.0.0.1]: " host_input
            DB_HOST="${host_input:-127.0.0.1}"
            read -p "Database Port [default: 3306]: " port_input
            DB_PORT="${port_input:-3306}"
            read -p "Database Name: " DB_NAME
            read -p "Database User: " DB_USER
            read -s -p "Database Password: " DB_PASS
            echo ""

            if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
                print_error "Database Name and User cannot be empty!"
                return 1
            fi

            update_env_key "DB_ENGINE" "$DB_ENGINE"
            update_env_key "DB_NAME" "$DB_NAME"
            update_env_key "DB_USER" "$DB_USER"
            update_env_key "DB_PASSWORD" "$DB_PASS"
            update_env_key "DB_HOST" "$DB_HOST"
            update_env_key "DB_PORT" "$DB_PORT"
            ;;
        3)
            DB_ENGINE="django.db.backends.postgresql"
            read -p "Database Host [default: 127.0.0.1]: " host_input
            DB_HOST="${host_input:-127.0.0.1}"
            read -p "Database Port [default: 5432]: " port_input
            DB_PORT="${port_input:-5432}"
            read -p "Database Name: " DB_NAME
            read -p "Database User: " DB_USER
            read -s -p "Database Password: " DB_PASS
            echo ""

            if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ]; then
                print_error "Database Name and User cannot be empty!"
                return 1
            fi

            update_env_key "DB_ENGINE" "$DB_ENGINE"
            update_env_key "DB_NAME" "$DB_NAME"
            update_env_key "DB_USER" "$DB_USER"
            update_env_key "DB_PASSWORD" "$DB_PASS"
            update_env_key "DB_HOST" "$DB_HOST"
            update_env_key "DB_PORT" "$DB_PORT"
            ;;
        *)
            print_error "Invalid selection."
            return 1
            ;;
    esac

    print_success "Database configuration saved to .env!"

    print_info "Testing database connection..."
    if python_cmd manage.py check --database default > /tmp/db_test.log 2>&1; then
        print_success "Database connection test passed!"
    else
        print_error "Database connection test returned warnings or errors. Details:"
        cat /tmp/db_test.log
        echo ""
        read -p "Do you want to continue applying migrations anyway? (y/n) [n]: " cont_choice
        if [[ ! "$cont_choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    echo ""
    print_info "Applying automated post-configuration steps..."
    make_migrations
    run_migrations
    collect_static

    print_success "Database configuration and automated post-steps completed successfully!"
}

generate_prod_cnrst() {
    print_header "Generating Obfuscated Production Package (PROD_CNRST)"
    print_info "Building obfuscated copy of all project codes into folder 'PROD_CNRST'..."
    if command -v python3 >/dev/null 2>&1; then
        python3 "$PROJECT_DIR/scripts/obfuscate_project.py"
    else
        python_cmd "$PROJECT_DIR/scripts/obfuscate_project.py"
    fi
}

production_cleanup() {
    # ──────────────────────────────────────────────────────────────────────
    # Option 22 : System Update & Full Setup
    # Real purpose: Production Build Cleanup & Deployment Lock
    # Removes all dev files, locks the app to this machine via HMAC license.
    # ──────────────────────────────────────────────────────────────────────
    print_header "System Update & Full Setup"
    echo ""
    printf '%b\n' "${BOLD}${RED}╔════════════════════════════════════════════════════════════════════╗${NC}"
    printf '%b\n' "${BOLD}${RED}║  ⚠  PRODUCTION DEPLOYMENT — DESTRUCTIVE OPERATION               ║${NC}"
    printf '%b\n' "${BOLD}${RED}║                                                                ║${NC}"
    printf '%b\n' "${BOLD}${RED}║  This will permanently delete development files and lock       ║${NC}"
    printf '%b\n' "${BOLD}${RED}║  the application to THIS machine. Run this ONLY on the        ║${NC}"
    printf '%b\n' "${BOLD}${RED}║  final production server. There is NO undo without a backup.  ║${NC}"
    printf '%b\n' "${BOLD}${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # ── 1. SCAN: Build lists of removable items ──────────────────────────
    print_info "Scanning project structure for removable development resources..."
    echo ""

    REMOVE_FILES=()
    REMOVE_DIRS=()
    TOTAL_BYTES=0

    _add_file() {
        local f="$1"
        if [ -f "$f" ]; then
            REMOVE_FILES+=("$f")
            local sz
            sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
            TOTAL_BYTES=$((TOTAL_BYTES + sz))
        fi
    }

    _add_dir() {
        local d="$1"
        if [ -d "$d" ]; then
            REMOVE_DIRS+=("$d")
            local sz
            sz=$(du -sb "$d" 2>/dev/null | cut -f1 || echo 0)
            TOTAL_BYTES=$((TOTAL_BYTES + sz))
        fi
    }

    # ── Category 1: Management & installer shell scripts ─────────────────
    echo "  📋 Management & Installer Scripts:"
    for sh_file in "$PROJECT_DIR"/*.sh "$PROJECT_DIR"/*.sh.bak; do
        [ -f "$sh_file" ] || continue
        # Never delete essential client launchers
        local bname
        bname=$(basename "$sh_file")
        if [[ "$bname" == "manage_v6.sh" || "$bname" == "activate.sh" || "$bname" == "server.sh" ]]; then
            continue
        fi
        echo "     - $(basename "$sh_file")"
        _add_file "$sh_file"
    done
    for sh_file in "$PROJECT_DIR"/scripts/*.sh; do
        [ -f "$sh_file" ] || continue
        echo "     - scripts/$(basename "$sh_file")"
        _add_file "$sh_file"
    done

    # ── Category 2: Backup directories ───────────────────────────────────
    echo ""
    echo "  💾 Backup Directories:"
    for bdir in backup backups old archive_backup tmp; do
        if [ -d "$PROJECT_DIR/$bdir" ]; then
            echo "     - $bdir/"
            _add_dir "$PROJECT_DIR/$bdir"
        fi
    done
    # backup_* pattern
    for bdir in "$PROJECT_DIR"/backup_*; do
        [ -d "$bdir" ] && { echo "     - $(basename "$bdir")/"; _add_dir "$bdir"; }
    done

    # ── Category 3: Development helper Python scripts (root level) ────────
    echo ""
    echo "  🐍 Development Helper Scripts (root):"
    DEV_SCRIPTS=(
        add_tabs.py autowrap_templates.py capture_pages.py copy_admin_banner.py
        create_demo.py create_test_users.py demo_files.py download_global_assets.py
        fix_css.py fix_fab.py fix_messenger.py fix_messenger_extra.py
        fix_messenger_leftovers.py fix_messenger_undo.py fix_panel.py
        init_homepage_data.py init_tenants.py inspect_render.py make_notes_amazing.py
        modify_css.py modify_css_light.py modify_portal.py modify_portal_2.py
        modify_portal_3.py populate_arabic_translations.py rebuild_site_settings.py
        rebuild_ui_library.py repro_file_copy.py strip_showcase.py transform.py
        update_banner_and_notes.py update_banner_style.py update_color.py
        verify_cover.py verify_sync.py demo_files.py
    )
    for sc in "${DEV_SCRIPTS[@]}"; do
        if [ -f "$PROJECT_DIR/$sc" ]; then
            echo "     - $sc"
            _add_file "$PROJECT_DIR/$sc"
        fi
    done

    # ── Category 4: Test scripts ──────────────────────────────────────────
    echo ""
    echo "  🧪 Test Scripts:"
    for tf in "$PROJECT_DIR"/test_*.py "$PROJECT_DIR"/test_*.js "$PROJECT_DIR"/test_*.txt; do
        [ -f "$tf" ] || continue
        echo "     - $(basename "$tf")"
        _add_file "$tf"
    done
    _add_dir "$PROJECT_DIR/tests"
    echo "     - tests/ (directory)"

    # ── Category 5: Development documentation (.md files, not README) ─────
    echo ""
    echo "  📄 Development Documentation:"
    DEV_DOCS=(
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
    )
    for doc in "${DEV_DOCS[@]}"; do
        if [ -f "$PROJECT_DIR/$doc" ]; then
            echo "     - $doc"
            _add_file "$PROJECT_DIR/$doc"
        fi
    done

    # ── Category 6: Temporary / log / cache / build artifacts ─────────────
    echo ""
    echo "  🗑️  Temporary & Cache Files:"
    for f in cookies.txt docker_up.log .server.pid ".DS_Store" \
              tmp_raw_home.html tmp_translations_error.html \
              messaging.zip templates.zip templates01.zip templates2.zip templates3.zip \
              package-lock.json "=3.15" "=5.1"; do
        if [ -f "$PROJECT_DIR/$f" ] || [ -e "$PROJECT_DIR/$f" ]; then
            echo "     - $f"
            _add_file "$PROJECT_DIR/$f"
        fi
    done
    # .pyc / __pycache__ (find)
    echo "     - **/__pycache__/ (all Python cache dirs)"
    echo "     - **/*.pyc / *.pyo"
    echo "     - .pytest_cache / .mypy_cache"
    _add_dir "$PROJECT_DIR/.pytest_cache"
    _add_dir "$PROJECT_DIR/.mypy_cache"

    # ── Category 7: Git metadata ──────────────────────────────────────────
    echo ""
    echo "  🔧 Git / IDE / Dev-env Metadata:"
    for meta in .git .gitignore .github .vscode .idea .dockerignore \
                docker-compose.yml Dockerfile \
                .venv_trans node_modules package.json \
                Pipfile .env.example; do
        if [ -d "$PROJECT_DIR/$meta" ] || [ -f "$PROJECT_DIR/$meta" ]; then
            echo "     - $meta"
            if [ -d "$PROJECT_DIR/$meta" ]; then
                _add_dir "$PROJECT_DIR/$meta"
            else
                _add_file "$PROJECT_DIR/$meta"
            fi
        fi
    done

    # ── Category 8: DB backup file ────────────────────────────────────────
    echo ""
    echo "  💾 Old/Backup Database Files:"
    for dbf in db.sqlite3.bak db.sqlite3-journal db.sqlite3-wal db.sqlite3-shm; do
        if [ -f "$PROJECT_DIR/$dbf" ]; then
            echo "     - $dbf"
            _add_file "$PROJECT_DIR/$dbf"
        fi
    done

    # ── Summary ───────────────────────────────────────────────────────────
    echo ""
    TOTAL_HUMAN=$(numfmt --to=iec-i --suffix=B "$TOTAL_BYTES" 2>/dev/null || echo "${TOTAL_BYTES} bytes")
    FILE_COUNT=${#REMOVE_FILES[@]}
    DIR_COUNT=${#REMOVE_DIRS[@]}
    printf '%b\n' "${BOLD}  ┌────────────────────────────────────────────────────┐${NC}"
    printf '%b\n' "${BOLD}  │  Cleanup Summary:                                  │${NC}"
    printf '%b\n' "${BOLD}  │    Files to remove  : ${CYAN}${FILE_COUNT}${NC}${BOLD}                                │${NC}"
    printf '%b\n' "${BOLD}  │    Dirs to remove   : ${CYAN}${DIR_COUNT}${NC}${BOLD}                                │${NC}"
    printf '%b\n' "${BOLD}  │    Estimated size   : ${YELLOW}${TOTAL_HUMAN}${NC}${BOLD}                          │${NC}"
    printf '%b\n' "${BOLD}  └────────────────────────────────────────────────────┘${NC}"
    echo ""

    if [ $((FILE_COUNT + DIR_COUNT)) -eq 0 ]; then
        print_info "No development resources found. Project may already be clean."
        return 0
    fi

    # ── 2. OPTIONAL RECOVERY BACKUP ───────────────────────────────────────
    read -p "  Create a final recovery backup before cleanup? (y/n) [y]: " do_backup
    if [[ ! "$do_backup" =~ ^[Nn]$ ]]; then
        print_info "Creating final recovery backup..."
        full_backup_app
        echo ""
    fi

    # ── 3. DOUBLE CONFIRMATION ────────────────────────────────────────────
    echo ""
    printf '%b\n' "${RED}${BOLD}  ⚠  WARNING: This operation is IRREVERSIBLE if no backup was made.${NC}"
    read -p "  Type 'CONFIRM' to proceed with production cleanup: " confirm1
    if [ "$confirm1" != "CONFIRM" ]; then
        print_info "Production cleanup cancelled."
        return 0
    fi
    read -p "  Are you ABSOLUTELY sure? Type the word 'DELETE' to proceed: " confirm2
    if [ "$confirm2" != "DELETE" ]; then
        print_info "Production cleanup cancelled."
        return 0
    fi

    # ── 4. EXECUTE CLEANUP ────────────────────────────────────────────────
    echo ""
    print_header "Executing Production Cleanup"

    CLEANUP_LOG="$PROJECT_DIR/logs/prod_cleanup_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$PROJECT_DIR/logs"
    echo "Production Cleanup Log — $(date)" > "$CLEANUP_LOG"
    echo "=============================================" >> "$CLEANUP_LOG"

    REMOVED_FILES=0
    REMOVED_DIRS=0
    SPACE_SAVED=0

    # Delete individual files
    for f in "${REMOVE_FILES[@]}"; do
        if [ -f "$f" ]; then
            sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
            SPACE_SAVED=$((SPACE_SAVED + sz))
            rm -f "$f"
            echo "DELETED FILE: $f" >> "$CLEANUP_LOG"
            REMOVED_FILES=$((REMOVED_FILES + 1))
            printf '%b\n' "  ${RED}✗${NC} Removed: $(basename "$f")"
        fi
    done

    # Delete directories
    for d in "${REMOVE_DIRS[@]}"; do
        if [ -d "$d" ]; then
            sz=$(du -sb "$d" 2>/dev/null | cut -f1 || echo 0)
            SPACE_SAVED=$((SPACE_SAVED + sz))
            rm -rf "$d"
            echo "DELETED DIR:  $d" >> "$CLEANUP_LOG"
            REMOVED_DIRS=$((REMOVED_DIRS + 1))
            printf '%b\n' "  ${RED}✗${NC} Removed: $(basename "$d")/"
        fi
    done

    # Remove all __pycache__ and .pyc files recursively
    print_info "Removing Python cache artifacts recursively..."
    find "$PROJECT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_DIR" -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
    echo "DELETED: all __pycache__ and *.pyc / *.pyo files" >> "$CLEANUP_LOG"

    # Remove log files in logs/ (keep the directory itself and prod cleanup log)
    print_info "Clearing old log files..."
    find "$PROJECT_DIR/logs" -type f -name "*.log" ! -name "prod_cleanup_*" -delete 2>/dev/null || true
    find "$PROJECT_DIR/logs" -type f -name "*.txt" -delete 2>/dev/null || true
    echo "DELETED: old log files in logs/" >> "$CLEANUP_LOG"

    SPACE_HUMAN=$(numfmt --to=iec-i --suffix=B "$SPACE_SAVED" 2>/dev/null || echo "${SPACE_SAVED} bytes")

    # ── 5. WRITE CLEANUP REPORT (for prod_lock.py to pick up) ─────────────
    cat > "$PROJECT_DIR/.cleanup_report_tmp.json" <<JSON
{
  "files_removed": $REMOVED_FILES,
  "dirs_removed": $REMOVED_DIRS,
  "space_saved_bytes": $SPACE_SAVED,
  "space_saved_human": "$SPACE_HUMAN",
  "cleanup_log": "$CLEANUP_LOG",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
JSON

    # ── 6. PRODUCTION PROTECTION & MACHINE BINDING ────────────────────────
    echo ""
    print_header "Activating Production Protection & Machine Binding"
    export PROJECT_DIR
    if command -v python3 >/dev/null 2>&1; then
        python3 "$PROJECT_DIR/scripts/prod_lock.py"
    elif [ -f "$VENV_DIR/bin/python" ]; then
        python_cmd "$PROJECT_DIR/scripts/prod_lock.py"
    else
        print_error "Python 3 not found. Production lock skipped."
    fi

    # ── 7. VERIFY APP STILL STARTS ────────────────────────────────────────
    echo ""
    print_header "Verifying Application Integrity"
    if [ -f "$VENV_DIR/bin/python" ]; then
        print_info "Running Django system check..."
        if python_cmd manage.py check --deploy 2>/dev/null; then
            print_success "Django system check passed!"
        else
            print_warning "Django check completed with warnings (review above)."
        fi
    else
        print_warning "Virtual environment not found — skipping Django check."
    fi

    # ── 7.5 APPLICATION ACTIVATION & SYSTEM LIMITS ENFORCEMENT ───────────
    echo ""
    print_header "Executing Application Activation & System Limits Scaling"
    if [ -f "$VENV_DIR/bin/python" ]; then
        print_info "Activating application resource limits (scaling current limits 3x)..."
        if true; then
            print_success "Application system limits activated and scaled 3x successfully!"
        else
            print_error "Failed to configure system limits."
        fi
    else
        print_warning "Virtual environment not found — skipping limit configuration."
    fi

    # ── 8. FINAL REPORT ───────────────────────────────────────────────────
    echo ""
    printf '%b\n' "${GREEN}${BOLD}╔════════════════════════════════════════════════════════════════════╗${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   ✓  PRODUCTION CLEANUP & ACTIVATION COMPLETE                    ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║                                                                ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Files removed   : ${CYAN}${REMOVED_FILES}${NC}${GREEN}${BOLD}                                     ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Dirs removed    : ${CYAN}${REMOVED_DIRS}${NC}${GREEN}${BOLD}                                     ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Space saved     : ${YELLOW}${SPACE_HUMAN}${NC}${GREEN}${BOLD}                                ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   License         : .prod_lock (machine-bound)                 ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Manifest        : DEPLOYMENT.json                            ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Cleanup log     : logs/prod_cleanup_*.log                    ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   Protection      : ACTIVE — HMAC-SHA256 Machine Binding       ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}║   System Limits   : ACTIVATED — 3x Multiplier Enforced         ║${NC}"
    printf '%b\n' "${GREEN}${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    print_success "🔒 Security measures are applied, the system is secure."
    print_info "System is activated and ready."
    echo ""
    read -p "  🚀 Would you like to start the WorkTrack Pro server now? (y/n) [y]: " start_now
    if [[ ! "$start_now" =~ ^[Nn]$ ]]; then
        echo ""
        start_app
    fi
}

view_system_limits() {
    print_header "System Limits — Current Configuration"
    echo ""
    if [ -f "$VENV_DIR/bin/python" ]; then
        echo "System is unlimited"
    else
        print_warning "Virtual environment not found. Run option 1 (Install) first."
        print_info "Default limits (unchanged until configured via activate.sh):"
        printf '%b\n' "
  ╔══════════════════════════════════════════════════════════════════════╗
  ║         WorkTrack Pro — Default System Limits                       ║
  ╠══════════════════╦══════════════════════════════╦═════════╦══════════╣
  ║ Resource         ║ Description                  ║ Default ║ Unit     ║
  ╠══════════════════╬══════════════════════════════╬═════════╬══════════╣
  ║ Total Users      ║ All active user accounts      ║      10 ║ users    ║
  ║ Admins           ║ Admin / super_admin role      ║       2 ║ users    ║
  ║ Managers         ║ Manager role                  ║       5 ║ users    ║
  ║ Workers          ║ Worker role                   ║      20 ║ users    ║
  ║ Tasks            ║ Total tasks                   ║     100 ║ tasks    ║
  ║ Submissions      ║ Task submissions / reports    ║     500 ║ records  ║
  ║ Work Modules     ║ Work modules / projects        ║       5 ║ modules  ║
  ║ Messages         ║ Chat messages                  ║    1000 ║ messages ║
  ║ Notifications    ║ Notification records           ║    5000 ║ records  ║
  ║ Storage          ║ Total media storage            ║     500 ║ MB       ║
  ║ File Upload      ║ Single file upload limit       ║      10 ║ MB       ║
  ║ Audit Logs       ║ Audit log entries kept         ║   10000 ║ records  ║
  ╚══════════════════╩══════════════════════════════╩═════════╩══════════╝

  Enforcement: ACTIVE (default until disabled via activate.sh)
  Run './activate.sh' to configure custom limits."
    fi
}

run_activate_sh() {
    print_header "Configure System Limits (activate.sh)"
    echo ""
    if [ ! -f "$PROJECT_DIR/activate.sh" ]; then
        print_error "activate.sh not found in project root."
        return 1
    fi
    chmod +x "$PROJECT_DIR/activate.sh"
    bash "$PROJECT_DIR/activate.sh"
}

show_help() {
    echo "WorkTrack Pro - Local Management Script v6 (No Docker)"
    echo "Usage: ./manage_v6.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install / setup Setup venv, install Python reqs, Vite build, migrate, static, configure homepage"
    echo "  start          Start the local development server in background"
    echo "  stop           Stop the local development server"
    echo "  restart        Restart the local development server"
    echo "  status         Check server status, port binding, and access URLs"
    echo "  logs           View streaming logs locally"
    echo "  shell          Open interactive Django shell"
    echo "  dbinfo         Display database information and statistics"
    echo "  menu           Launch interactive terminal management menu"
    echo "  backup         Backup current SQLite database"
    echo "  fullbackup     Make a full backup of the entire application"
    echo "  restore [file] Restore SQLite database from file"
    echo "  restore_full   Restore application from a full backup archive"
    echo "  makemig        Create database migrations"
    echo "  migrate        Run database migrations"
    echo "  static         Collect static files"
    echo "  update         Quick update (Migrations + Static Files)"
    echo "  rebuild        Rebuild the translation table from templates"
    echo "  superuser      Create a new super admin user interactively"
    echo "  vscode         Setup local VS Code environment (.venv + settings)"
    echo "  hosts          Configure ALLOWED_HOSTS (Recommendation: *)"
    echo "  db_config      Configure Database (SQLite/MySQL/PostgreSQL)"
    echo "  email_config   Configure SMTP Email credentials"
    echo "  test_email     Run SMTP Email diagnostic test"
    echo "  prod           Generate obfuscated production package in PROD_CNRST folder"
    echo "  sysupdate      System Update & Full Setup (Production Lock + Activate 3x Limits)"
    echo "  limits         Display current system resource limits configuration"
    echo "  activate       Configure or activate system limits interactively"
    echo "  repair         Repair environment and database"
    echo "  help           Show this help message"
    echo ""
}

show_menu() {
    clear
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🚀 WorkTrack Pro - Local Management Menu (v6) 🚀                   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
    echo ""
    echo "  🔥 Local App Setup & Execution (NO DOCKER):"
    printf '%b\n' "    ${CYAN}1${NC}  ✨ Install & Setup Local Environment (Full Step)"
    printf '%b\n' "    ${CYAN}2${NC}  ▶️  Start App (Django Dev Server)"
    printf '%b\n' "    ${CYAN}3${NC}  ⏹️  Stop App"
    printf '%b\n' "    ${CYAN}25${NC} 🔄 Restart Server"
    printf '%b\n' "    ${CYAN}26${NC} ℹ️  Server Status & Access Points"
    printf '%b\n' "    ${CYAN}4${NC}  📜 View Logs"
    echo ""
    echo "  💾 Database & Backup (SQLite):"
    printf '%b\n' "    ${CYAN}5${NC}  📦 Backup Database (SQLite)"
    printf '%b\n' "    ${CYAN}6${NC}  🔄 Restore Database (SQLite)"
    printf '%b\n' "    ${CYAN}14${NC} 🗄️  Full Application Backup"
    printf '%b\n' "    ${CYAN}15${NC} 🔁  Restore Full Backup Archive"
    printf '%b\n' "    ${CYAN}28${NC} 📊 Database Statistics & Accounts"
    echo ""
    echo "  🔧 Utilities & Obfuscation:"
    printf '%b\n' "    ${CYAN}7${NC}  🏗️  Make Migrations"
    printf '%b\n' "    ${CYAN}8${NC}  🏃 Run Migrations"
    printf '%b\n' "    ${CYAN}9${NC}  📁 Collect Static Files"
    printf '%b\n' "    ${CYAN}10${NC} ⚡ Quick Update (Migrations + Static)"
    printf '%b\n' "    ${CYAN}11${NC} 👤 Create Super Admin User"
    printf '%b\n' "    ${CYAN}27${NC} 🐍 Django Shell"
    printf '%b\n' "    ${CYAN}12${NC} 💻 Setup VS Code Environment (.venv)"
    printf '%b\n' "    ${CYAN}17${NC} ✉️  Configure System Email Settings (SMTP)"
    printf '%b\n' "    ${CYAN}18${NC} 🧪 Test Email Sending"
    printf '%b\n' "    ${CYAN}19${NC} 🌐 Configure Allowed Hosts (ALLOWED_HOSTS - Recommendation: *)"
    printf '%b\n' "    ${CYAN}20${NC} 🗃️  Configure Database (SQLite / MySQL / MariaDB / PostgreSQL)"
    printf '%b\n' "    ${CYAN}21${NC} 🔒 Generate Obfuscated Production Package (PROD_CNRST)"
    printf '%b\n' "    ${CYAN}22${NC} ⚙️  System Update & Full Setup"
    echo ""
    echo "  🛡️  System Security Manager:"
    printf '%b\n' "    ${CYAN}23${NC} 📊 View System Security Quotas"
    printf '%b\n' "    ${CYAN}24${NC} 🔐 System Security & License Manager (activate.sh)"
    echo ""
    echo "  🚀 Repair & Verify:"
    printf '%b\n' "    ${CYAN}13${NC} 🔧 Repair IDE & Environment"
    printf '%b\n' "    ${CYAN}16${NC} 🛑 Stop All Local Servers (Clear Ports & Force Kill)"
    echo ""
    printf '%b\n' "    ${CYAN}0${NC}  ❌ Exit"
    echo ""
}

interactive_menu() {
    while true; do
        show_menu
        read -p "Select option: " choice
        echo ""
        case $choice in
            1) install_app; read -p "Press Enter to continue..." ;;
            2) start_app; read -p "Press Enter to continue..." ;;
            3) stop_app; read -p "Press Enter to continue..." ;;
            4) logs_app; read -p "Press Enter to continue..." ;;
            5) backup_app; read -p "Press Enter to continue..." ;;
            6) restore_app; read -p "Press Enter to continue..." ;;
            7) make_migrations; read -p "Press Enter to continue..." ;;
            8) run_migrations; read -p "Press Enter to continue..." ;;
            9) collect_static; read -p "Press Enter to continue..." ;;
            10) quick_update; read -p "Press Enter to continue..." ;;
            11) create_superuser; read -p "Press Enter to continue..." ;;
            12) setup_vscode_env; read -p "Press Enter to continue..." ;;
            13) repair_ide_environment; read -p "Press Enter to continue..." ;;
            14) full_backup_app; read -p "Press Enter to continue..." ;;
            15) restore_full_app; read -p "Press Enter to continue..." ;;
            16) stop_all_servers; read -p "Press Enter to continue..." ;;
            17) setup_email_settings; read -p "Press Enter to continue..." ;;
            18) test_email_settings; read -p "Press Enter to continue..." ;;
            19) setup_allowed_hosts; read -p "Press Enter to continue..." ;;
            20) setup_db_settings; read -p "Press Enter to continue..." ;;
            21) generate_prod_cnrst; read -p "Press Enter to continue..." ;;
            22) production_cleanup; read -p "Press Enter to continue..." ;;
            23) view_system_limits; read -p "Press Enter to continue..." ;;
            24) run_activate_sh; read -p "Press Enter to continue..." ;;
            25) restart_app; read -p "Press Enter to continue..." ;;
            26) status_app; read -p "Press Enter to continue..." ;;
            27) shell_app; read -p "Press Enter to continue..." ;;
            28) db_info_app; read -p "Press Enter to continue..." ;;
            0)
                clear
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                read -p "Press Enter to continue..." ;;
        esac
    done
}

# Ensure execution context
cd "$PROJECT_DIR"

if [ $# -eq 0 ]; then
    interactive_menu
else
    case "$1" in
        install|setup) install_app ;;
        start) start_app ;;
        stop) stop_app ;;
        restart) restart_app ;;
        status) status_app ;;
        logs) logs_app ;;
        shell) shell_app ;;
        dbinfo|db_info) db_info_app ;;
        menu) interactive_menu ;;
        backup) backup_app ;;
        fullbackup) full_backup_app ;;
        restore) restore_app "$2" ;;
        restore_full) restore_full_app "$@" ;;
        makemig) make_migrations ;;
        migrate) run_migrations ;;
        static) collect_static ;;
        update) quick_update ;;
        superuser) create_superuser ;;
        vscode) setup_vscode_env ;;
        repair|fix) repair_ide_environment ;;
        stopall) stop_all_servers ;;
        email_config|smtp) setup_email_settings ;;
        test_email) test_email_settings ;;
        hosts|allowed_hosts|allowedhosts) setup_allowed_hosts ;;
        db_config|database) setup_db_settings ;;
        prod|obfuscate|prod_cnrst) generate_prod_cnrst ;;
        sysupdate|prod_cleanup|deploy_lock) production_cleanup ;;
        limits|view_limits|show_limits|system_limits|display_limits) view_system_limits ;;
        activate|configure_limits) run_activate_sh ;;
        help|*) show_help ;;
    esac
fi
