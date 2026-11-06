#!/bin/bash

# WorkTrack Pro - Django Management Script (GUI Edition)
# Full-featured web application with Bootstrap 5 UI
# SQLite database, no Docker, no Celery

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PID_FILE="$PROJECT_DIR/.server.pid"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/server.log"

# ============================================================================
# ANSI Color Codes
# ============================================================================
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'
CYAN=$'\033[0;36m'
MAGENTA=$'\033[0;35m'
BOLD=$'\033[1m'
NC=$'\033[0m'

# ============================================================================
# Utility Functions
# ============================================================================

print_success() {
    printf '%b\n' "${GREEN}✓ $1${NC}"
}

print_error() {
    printf '%b\n' "${RED}✗ $1${NC}"
}

print_warning() {
    printf '%b\n' "${YELLOW}⚠ $1${NC}"
}

print_info() {
    printf '%b\n' "${BLUE}ℹ $1${NC}"
}

print_header() {
    printf '%b\n' "${BOLD}${CYAN}╭─ $1${NC}"
}

print_separator() {
    printf '%b\n' "${CYAN}────────────────────────────────────────────${NC}"
}

print_divider() {
    echo ""
}

# ============================================================================
# Virtual Environment Functions
# ============================================================================

activate_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_error "Virtual environment not found at $VENV_DIR"
        return 1
    fi

    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Activation script not found"
        return 1
    fi

    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    return 0
}

create_venv() {
    print_header "Creating Virtual Environment"
    
    if [ -d "$VENV_DIR" ]; then
        # Check if it's a valid venv
        if [ -f "$VENV_DIR/bin/activate" ] && [ -f "$VENV_DIR/bin/python" ]; then
            print_success "Virtual environment already exists and is valid"
            read -p "Recreate it anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_info "Using existing virtual environment"
                return 0
            fi
        fi
        print_info "Removing existing venv..."
        rm -rf "$VENV_DIR"
    fi

    print_info "Creating venv at $VENV_DIR..."
    
    # Try to create venv and handle common errors
    if ! python3 -m venv "$VENV_DIR" 2>&1 | grep -v "^$"; then
        # Check if error is about ensurepip
        if python3 -m venv "$VENV_DIR" 2>&1 | grep -q "ensurepip"; then
            print_error "Missing python3-venv package. Installing system dependency..."
            
            # Get Python version
            PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
            PYTHON_VERSION_NODOT="${PYTHON_VERSION/./}"
            
            print_info "Installing python${PYTHON_VERSION}-venv..."
            if ! sudo apt-get install -y python${PYTHON_VERSION}-venv 2>&1 | tail -3; then
                print_error "Failed to install python${PYTHON_VERSION}-venv"
                print_info "Try running manually: sudo apt install python${PYTHON_VERSION}-venv"
                return 1
            fi
            
            print_info "Retrying venv creation..."
            if ! python3 -m venv "$VENV_DIR"; then
                print_error "Failed to create virtual environment after installing system package"
                return 1
            fi
        else
            print_error "Failed to create virtual environment"
            return 1
        fi
    fi
    
    # Verify venv creation
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        print_error "Virtual environment creation failed: activate script not found"
        return 1
    fi
    
    print_success "Virtual environment created successfully"
}

setup_dependencies() {
    print_header "Installing Dependencies"

    if ! activate_venv; then
        print_error "Failed to activate virtual environment"
        return 1
    fi

    print_info "Upgrading pip, setuptools, wheel..."
    if ! pip install --upgrade pip setuptools wheel 2>&1 | grep -v "WARNING\|Requirement already" > /dev/null; then
        print_warning "Some pip tools failed to upgrade (this may be normal)"
    fi
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        print_error "requirements.txt not found at $PROJECT_DIR"
        return 1
    fi
    
    print_info "Installing requirements from requirements.txt..."
    
    # Try normal installation first, then with --break-system-packages if needed
    if ! pip install -r "$PROJECT_DIR/requirements.txt" 2>&1 | tail -5; then
        print_warning "Attempting installation with --break-system-packages flag..."
        if ! pip install --break-system-packages -r "$PROJECT_DIR/requirements.txt" 2>&1 | tail -5; then
            print_error "Failed to install dependencies"
            return 1
        fi
    fi
    
    # Verify key packages are installed with correct import names
    print_info "Verifying critical packages..."
    
    # Map of package names to their import names
    declare -A package_imports=(
        ["Django"]="django"
        ["djangorestframework"]="rest_framework"
        ["python-decouple"]="decouple"
        ["requests"]="requests"
        ["pillow"]="PIL"
        ["pytz"]="pytz"
    )
    
    local failed=0
    for package in "${!package_imports[@]}"; do
        import_name="${package_imports[$package]}"
        if python3 -c "import $import_name" 2>/dev/null; then
            print_success "$package installed"
        else
            print_error "Failed to verify $package"
            failed=$((failed + 1))
        fi
    done
    
    if [ $failed -gt 0 ]; then
        print_error "Failed to verify $failed package(s)"
        print_info "Attempting pip repair..."
        if ! pip install --force-reinstall -r "$PROJECT_DIR/requirements.txt"; then
            return 1
        fi
    fi
    
    print_success "All dependencies installed and verified"
}

# ============================================================================
# Django Management Functions
# ============================================================================

make_migrations() {
    print_header "Creating Migrations"

    if ! activate_venv; then
        print_error "Virtual environment not available"
        return 1
    fi

    cd "$PROJECT_DIR" || return 1

    # In setup mode (second argument = "auto"), don't ask for input
    if [ "$1" = "auto" ]; then
        print_info "Creating migrations for all apps..."
        if ! python3 manage.py makemigrations; then
            print_error "Failed to create migrations"
            return 1
        fi
    else
        read -p "App name (leave blank for all): " app_name
        
        if [ -z "$app_name" ]; then
            print_info "Creating migrations for all apps..."
            if ! python3 manage.py makemigrations; then
                print_error "Failed to create migrations"
                return 1
            fi
        else
            print_info "Creating migrations for app: $app_name"
            if ! python3 manage.py makemigrations "$app_name"; then
                print_error "Failed to create migrations for $app_name"
                return 1
            fi
        fi
    fi

    print_success "Migrations created successfully"
}

migrate_database() {
    print_header "Applying Database Migrations"

    if ! activate_venv; then
        print_error "Virtual environment not available"
        return 1
    fi

    cd "$PROJECT_DIR" || return 1

    print_info "Applying migrations to SQLite database..."
    if ! python3 manage.py migrate; then
        print_error "Database migration failed"
        return 1
    fi

    print_success "Database migration complete"
}

collect_static() {
    print_header "Collecting Static Files"

    if ! activate_venv; then
        print_error "Virtual environment not available"
        return 1
    fi

    cd "$PROJECT_DIR" || return 1

    # Create directories if they don't exist
    mkdir -p "$LOG_DIR" media staticfiles

    print_info "Collecting static files for production..."
    if ! python3 manage.py collectstatic --noinput; then
        print_error "Failed to collect static files"
        return 1
    fi

    print_success "Static files collected successfully"
}

createsuperuser_interactive() {
    print_header "Create Superuser Account"

    if ! activate_venv; then
        print_error "Virtual environment not available"
        return 1
    fi

    cd "$PROJECT_DIR" || return 1

    print_info "Follow the prompts to create an admin account:"
    print_divider
    if ! python3 manage.py createsuperuser; then
        print_warning "Superuser creation failed or was skipped"
        print_info "You can create one later using: ./manage.sh 7"
        return 0
    fi

    print_divider
    print_success "Superuser created successfully"
}

health_check() {
    print_header "System Health Check"
    print_divider
    
    local issues=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PY_VERSION=$(python3 --version 2>&1)
        print_success "$PY_VERSION"
    else
        print_error "Python3 not found"
        issues=$((issues + 1))
    fi
    
    # Check venv
    if [ -d "$VENV_DIR" ]; then
        if [ -f "$VENV_DIR/bin/activate" ]; then
            print_success "Virtual environment exists"
        else
            print_error "Virtual environment is corrupted"
            issues=$((issues + 1))
        fi
    else
        print_warning "Virtual environment not found"
    fi
    
    # Check database
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        DB_SIZE=$(du -h "$PROJECT_DIR/db.sqlite3" 2>/dev/null | cut -f1)
        print_success "Database exists ($DB_SIZE)"
    else
        print_warning "Database not found"
    fi
    
    # Try to activate and verify packages
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate" 2>/dev/null
        
        # Check Django
        if python3 -c "import django; print(f'Django {django.VERSION[0]}.{django.VERSION[1]}')" 2>/dev/null | grep -q "Django"; then
            DJANGO_VERSION=$(python3 -c "import django; print(f'{django.VERSION[0]}.{django.VERSION[1]}')" 2>/dev/null)
            print_success "Django $DJANGO_VERSION installed"
        else
            print_error "Django not installed properly"
            issues=$((issues + 1))
        fi
        
        # Check DRF
        if python3 -c "import rest_framework" 2>/dev/null; then
            print_success "Django REST Framework installed"
        else
            print_error "Django REST Framework not installed"
            issues=$((issues + 1))
        fi
        
        # Check static files
        if [ -d "$PROJECT_DIR/staticfiles" ] && [ "$(ls -A "$PROJECT_DIR/staticfiles" 2>/dev/null)" ]; then
            FILE_COUNT=$(find "$PROJECT_DIR/staticfiles" -type f 2>/dev/null | wc -l)
            print_success "Static files collected ($FILE_COUNT files)"
        else
            print_warning "Static files not collected"
        fi
    else
        print_error "Cannot activate virtual environment"
        issues=$((issues + 1))
    fi
    
    print_divider
    if [ $issues -eq 0 ]; then
        print_success "✅ All systems operational"
        return 0
    else
        print_error "⚠️  Found $issues issue(s) to resolve"
        return 1
    fi
}

# ============================================================================
# Server Lifecycle Functions
# ============================================================================

start_server() {
    print_header "Starting Django Development Server"

    if ! activate_venv; then
        print_error "Virtual environment not available"
        return 1
    fi

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            print_warning "Server already running with PID $OLD_PID"
            return 1
        else
            print_info "Cleaning up stale PID file..."
            rm -f "$PID_FILE"
        fi
    fi

    # Kill any stale Django processes on port 8000
    print_info "Checking for stale processes on port 8000..."
    STALE_PIDS=$(lsof -ti :8000 2>/dev/null || netstat -tlnp 2>/dev/null | grep :8000 | awk '{print $NF}' | grep -oP '^\d+' 2>/dev/null || true)
    
    if [ -n "$STALE_PIDS" ]; then
        print_warning "Found stale process(es) on port 8000, cleaning up..."
        for pid in $STALE_PIDS; do
            if [ -n "$pid" ] && [ "$pid" != "-" ]; then
                print_info "Killing process $pid..."
                kill -9 "$pid" 2>/dev/null || true
                sleep 0.5
            fi
        done
        sleep 1
    fi

    cd "$PROJECT_DIR" || return 1

    # Create log directory
    mkdir -p "$LOG_DIR"

    print_info "Starting server on http://0.0.0.0:8000..."
    python3 manage.py runserver 0.0.0.0:8000 > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!
    echo "$SERVER_PID" > "$PID_FILE"

    sleep 2

    if kill -0 "$SERVER_PID" 2>/dev/null; then
        # Verify port is actually listening
        if lsof -i :8000 >/dev/null 2>&1 || nc -z localhost 8000 >/dev/null 2>&1 || sleep 1; then
            print_success "Server started successfully (PID: $SERVER_PID)"
            print_divider
            print_warning "IMPORTANT: The development server ONLY supports HTTP."
            print_warning "Do NOT use https:// or you will get 'Bad request version' errors."
            print_divider
            print_header "Access Points"
            printf '%b\n' "  🌐 Home:          ${CYAN}http://localhost:8000${NC}"
            printf '%b\n' "  🏠 Dashboard:     ${CYAN}http://localhost:8000/dashboard${NC}"
            printf '%b\n' "  ✅ Tasks:        ${CYAN}http://localhost:8000/tasks${NC}"
            printf '%b\n' "  📥 Submissions:   ${CYAN}http://localhost:8000/submissions${NC}"
            printf '%b\n' "  🔔 Notifications: ${CYAN}http://localhost:8000/notifications${NC}"
            printf '%b\n' "  👤 Profile:      ${CYAN}http://localhost:8000/profile${NC}"
            printf '%b\n' "  ⚙️  Admin Panel:   ${CYAN}http://localhost:8000/admin${NC}"
            printf '%b\n' "  📊 API:          ${CYAN}http://localhost:8000/api${NC}"
            print_divider
            print_info "Logs: ${CYAN}tail -f $LOG_FILE${NC}"
            print_info "Stop server: ${CYAN}./manage.sh stop${NC}"
            return 0
        fi
    fi
    
    # If we get here, something went wrong
    print_error "Failed to start server"
    print_info "Check logs: tail -f $LOG_FILE"
    
    # Show log content for diagnostics
    if [ -f "$LOG_FILE" ]; then
        print_divider
        print_header "Server Log (last 20 lines)"
        tail -20 "$LOG_FILE" | head -20
        print_divider
    fi
    
    return 1
}

stop_server() {
    print_header "Stopping Django Server"

    if [ ! -f "$PID_FILE" ]; then
        print_warning "No running server found (no PID file)"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    if kill -0 "$PID" 2>/dev/null; then
        print_info "Stopping server (PID: $PID)..."
        kill "$PID" || true
        sleep 1

        if kill -0 "$PID" 2>/dev/null; then
            print_warning "Forcing termination (SIGKILL)..."
            kill -9 "$PID" || true
            sleep 1
        fi

        rm -f "$PID_FILE"
        print_success "Server stopped"
    else
        print_warning "Process (PID: $PID) is not running"
        rm -f "$PID_FILE"
    fi
}

stop_all_servers() {
    local force="${1:-false}"
    
    print_header "Stopping All Running Django Servers"
    print_divider

    # Find all Django processes
    PIDS=$(pgrep -f "python.*manage.py runserver" 2>/dev/null || true)

    if [ -z "$PIDS" ]; then
        print_info "No running Django servers found"
        return 0
    fi

    COUNT=$(echo "$PIDS" | wc -l)
    print_info "Found $COUNT Django process(es):"
    echo "$PIDS" | while read -r pid; do
        CMD=$(ps -p "$pid" -o cmd= 2>/dev/null || echo "unknown")
        printf '%b\n' "  • PID $pid: ${CYAN}$CMD${NC}"
    done
    print_divider

    if [ "$force" != "true" ]; then
        read -p "Stop all these processes? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Cancelled"
            return 0
        fi
    fi

    print_info "Terminating processes with SIGTERM..."
    echo "$PIDS" | while read -r pid; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
            sleep 0.3
        fi
    done

    sleep 1

    # Force kill any remaining processes
    REMAINING=$(pgrep -f "python.*manage.py runserver" 2>/dev/null || true)
    if [ -n "$REMAINING" ]; then
        print_warning "Force killing remaining processes..."
        echo "$REMAINING" | while read -r pid; do
            kill -9 "$pid" 2>/dev/null || true
        done
        sleep 1
    fi

    # Verify all are stopped
    FINAL_CHECK=$(pgrep -f "python.*manage.py runserver" 2>/dev/null || true)
    if [ -z "$FINAL_CHECK" ]; then
        rm -f "$PID_FILE"
        print_success "All servers stopped successfully"
        return 0
    else
        print_error "Some processes could not be stopped: $FINAL_CHECK"
        return 1
    fi
}

server_status() {
    print_header "Server Status"
    print_divider

    if [ ! -f "$PID_FILE" ]; then
        print_warning "Status: STOPPED (no PID file)"
        print_divider
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if kill -0 "$PID" 2>/dev/null; then
        print_success "Status: RUNNING"
        printf '%b\n' "  PID: ${CYAN}$PID${NC}"
        print_divider
        print_header "Access Points"
        printf '%b\n' "  🌐 Home:          ${CYAN}http://localhost:8000${NC}"
        printf '%b\n' "  🏠 Dashboard:     ${CYAN}http://localhost:8000/dashboard${NC}"
        printf '%b\n' "  ✅ Tasks:        ${CYAN}http://localhost:8000/tasks${NC}"
        printf '%b\n' "  📥 Submissions:   ${CYAN}http://localhost:8000/submissions${NC}"
        printf '%b\n' "  🔔 Notifications: ${CYAN}http://localhost:8000/notifications${NC}"
        printf '%b\n' "  👤 Profile:      ${CYAN}http://localhost:8000/profile${NC}"
        printf '%b\n' "  ⚙️  Admin Panel:   ${CYAN}http://localhost:8000/admin${NC}"
        printf '%b\n' "  📊 API:          ${CYAN}http://localhost:8000/api${NC}"
        print_divider
        return 0
    else
        print_error "Status: NOT RUNNING (PID $PID)"
        rm -f "$PID_FILE"
        print_divider
        return 1
    fi
}

tail_logs() {
    print_header "Server Logs (Press Ctrl+C to exit)"
    print_divider

    if [ ! -f "$LOG_FILE" ]; then
        print_error "Log file not found: $LOG_FILE"
        return 1
    fi

    tail -f "$LOG_FILE"
}

# ============================================================================
# Database & Info Functions
# ============================================================================

show_db_info() {
    print_header "Database Information"
    print_divider

    DB_FILE="$PROJECT_DIR/db.sqlite3"
    
    if [ -f "$DB_FILE" ]; then
        SIZE=$(du -h "$DB_FILE" | cut -f1)
        MTIME=$(stat -f "%Sm" "$DB_FILE" 2>/dev/null || stat -c '%y' "$DB_FILE" 2>/dev/null)
        printf '%b\n' "  📁 Database:   ${CYAN}$DB_FILE${NC}"
        printf '%b\n' "  📊 Size:       ${YELLOW}$SIZE${NC}"
        printf '%b\n' "  🕐 Modified:   ${YELLOW}$MTIME${NC}"
    else
        printf '%b\n' "  📁 Database:   ${RED}not created yet${NC}"
    fi

    print_divider

    # Count tables
    if [ -f "$DB_FILE" ]; then
        TABLE_COUNT=$(sqlite3 "$DB_FILE" ".tables" 2>/dev/null | wc -w)
        printf '%b\n' "  📋 Tables:     ${CYAN}$TABLE_COUNT${NC}"
        print_divider
    fi
}

show_test_accounts() {
    print_header "Test Account Credentials"
    print_divider

    printf '%b\n' "  ${BOLD}Admin (Full System Access):${NC}"
    printf '%b\n' "    Email:    ${CYAN}admin@worktrack.local${NC}"
    printf '%b\n' "    Password: ${YELLOW}Admin@123456${NC}"
    print_divider

    printf '%b\n' "  ${BOLD}Manager (Task & Submission Review):${NC}"
    printf '%b\n' "    Email:    ${CYAN}manager@worktrack.local${NC}"
    printf '%b\n' "    Password: ${YELLOW}Manager@123456${NC}"
    print_divider

    printf '%b\n' "  ${BOLD}Worker #1 (Alice Smith):${NC}"
    printf '%b\n' "    Email:    ${CYAN}worker1@worktrack.local${NC}"
    printf '%b\n' "    Password: ${YELLOW}Worker@123456${NC}"
    print_divider

    printf '%b\n' "  ${BOLD}Worker #2 (Bob Jones):${NC}"
    printf '%b\n' "    Email:    ${CYAN}worker2@worktrack.local${NC}"
    printf '%b\n' "    Password: ${YELLOW}Worker@123456${NC}"
    print_divider
}

backup_system() {
    print_header "System Backup"
    print_divider

    BACKUP_DIR="$PROJECT_DIR/backup"
    mkdir -p "$BACKUP_DIR"

    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/worktrack_pro_backup_$TIMESTAMP.tar.gz"

    print_info "Creating backup at: $BACKUP_FILE"
    print_info "This may take a moment depending on the project size..."

    cd "$PROJECT_DIR" || return 1

    if tar -czf "$BACKUP_FILE" \
        --exclude="venv" \
        --exclude="backup" \
        --exclude="node_modules" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="*.pyc" \
        --exclude=".pytest_cache" \
        .; then
        print_success "Backup completed successfully!"
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        printf '%b\n' "  📊 Size:       ${YELLOW}$SIZE${NC}"
    else
        print_error "Backup failed!"
        return 1
    fi
    print_divider
}

quick_update() {
    print_header "Quick Update (Migrations + Static Files)"
    print_divider

    if ! make_migrations "auto"; then
        print_error "Failed to create migrations"
        return 1
    fi
    echo ""

    if ! migrate_database; then
        print_error "Failed to run migrations"
        return 1
    fi
    echo ""

    if ! collect_static; then
        print_error "Failed to collect static files"
        return 1
    fi
    echo ""

    print_success "Update complete!"
    print_divider
}

setup_smtp() {
    print_header "SMTP Configuration (Gmail)"
    print_divider
    
    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        print_error ".env file not found. Please run full setup first."
        return 1
    fi
    
    print_info "This utility will help you configure Gmail for notifications."
    print_warning "Note: For Gmail, you MUST use an 'App Password', not your regular login password."
    print_info "Instructions: https://support.google.com/accounts/answer/185833"
    print_divider
    
    read -p "Gmail Address (e.g., user@gmail.com): " gmail_addr
    if [ -z "$gmail_addr" ]; then
        print_error "Gmail address cannot be empty."
        return 1
    fi
    
    read -p "Google App Password: " app_pass
    if [ -z "$app_pass" ]; then
        print_error "App password cannot be empty."
        return 1
    fi
    
    print_divider
    print_info "Updating .env configuration..."
    
    # Use sed to update or add SMTP settings
    # We use a temporary file for safety
    TEMP_ENV=$(mktemp)
    
    # Function to update or append setting
    update_setting() {
        local key=$1
        local value=$2
        if grep -q "^$key=" "$DOTENV_FILE"; then
            sed "s|^$key=.*|$key=$value|" "$DOTENV_FILE" > "$TEMP_ENV"
            cp "$TEMP_ENV" "$DOTENV_FILE"
        else
            echo "$key=$value" >> "$DOTENV_FILE"
        fi
    }
    
    update_setting "EMAIL_BACKEND" "django.core.mail.backends.smtp.EmailBackend"
    update_setting "EMAIL_HOST" "smtp.gmail.com"
    update_setting "EMAIL_PORT" "587"
    update_setting "EMAIL_USE_TLS" "True"
    update_setting "EMAIL_HOST_USER" "$gmail_addr"
    update_setting "EMAIL_HOST_PASSWORD" "$app_pass"
    update_setting "DEFAULT_FROM_EMAIL" "$gmail_addr"
    
    rm -f "$TEMP_ENV"
    
    print_success "SMTP configuration updated successfully!"
    print_divider
    
    read -p "Would you like to run the diagnostic test now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if activate_venv; then
            if [ -f "$PROJECT_DIR/test_email.py" ]; then
                python3 "$PROJECT_DIR/test_email.py"
            else
                print_error "test_email.py not found. You can test manually with ./manage.sh shell < test_email.py"
            fi
        fi
    fi
}

# ============================================================================
# Full Setup Workflow
# ============================================================================

full_setup() {
    print_header "Full Application Setup with Validation"
    print_divider

    # ========== SYSTEM CHECK ==========
    print_info "🔍 Checking system requirements..."
    
    # Check Python3
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is required but not installed"
        print_info "Install it with: sudo apt install python3-full"
        return 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python 3 found: $PYTHON_VERSION"
    
    # Check pip
    if ! python3 -m pip --version > /dev/null 2>&1; then
        print_error "pip is required but not available"
        print_info "Install it with: sudo apt install python3-pip"
        return 1
    fi
    print_success "pip is available"
    
    # Check if python3-venv is available
    print_info "Checking for python3-venv package..."
    if ! python3 -m venv --help > /dev/null 2>&1; then
        print_warning "python3-venv package not found"
        PYTHON_MINOR=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
        print_info "Installing python${PYTHON_MINOR}-venv..."
        if ! sudo apt-get update > /dev/null 2>&1; then
            print_error "Failed to update apt cache"
            return 1
        fi
        if ! sudo apt-get install -y python${PYTHON_MINOR}-venv > /dev/null 2>&1; then
            print_error "Failed to install python${PYTHON_MINOR}-venv"
            return 1
        fi
        print_success "python3-venv installed"
    else
        print_success "python3-venv is available"
    fi
    
    # Check git (optional but recommended)
    if command -v git &> /dev/null; then
        print_success "git is available"
    else
        print_warning "git is not installed (optional)"
    fi

    print_divider

    steps=(
        "Create Virtual Environment"
        "Install Dependencies"
        "Clean Database (optional)"
        "Make Migrations"
        "Run Migrations"
        "Collect Static Files"
        "Create Superuser Account"
    )

    echo "This complete setup will perform the following steps:"
    print_divider
    for i in "${!steps[@]}"; do
        printf '%b\n' "  $((i+1)). ${steps[$i]}"
    done
    print_divider

    read -p "Continue with full setup? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Setup cancelled"
        return 0
    fi

    echo ""

    # ========== STEP 1: Virtual Environment ==========
    if ! create_venv; then
        print_error "Failed to create virtual environment"
        return 1
    fi
    echo ""

    # ========== STEP 2: Dependencies ==========
    if ! setup_dependencies; then
        print_error "Failed to install dependencies"
        print_warning "Attempting fallback installation method..."
        if ! activate_venv; then
            print_error "Cannot activate venv for fallback"
            return 1
        fi
        if ! pip install --no-cache-dir --disable-pip-version-check -r "$PROJECT_DIR/requirements.txt"; then
            print_error "Fallback installation also failed"
            return 1
        fi
    fi
    echo ""

    # ========== STEP 3: Clean Database (Optional) ==========
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        print_info "Existing database found at $PROJECT_DIR/db.sqlite3"
        read -p "Do you want to reset the database? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Removing old database..."
            rm -f "$PROJECT_DIR/db.sqlite3"
            # Also remove migration cache
            find "$PROJECT_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
            print_success "Database reset"
        fi
    fi
    echo ""

    # ========== STEP 4: Migrations ==========
    if ! make_migrations "auto"; then
        print_error "Failed to create migrations"
        return 1
    fi
    echo ""

    # ========== STEP 5: Database Migration ==========
    if ! migrate_database; then
        print_error "Failed to run migrations"
        return 1
    fi
    echo ""

    # ========== STEP 6: Static Files ==========
    if ! collect_static; then
        print_error "Failed to collect static files"
        return 1
    fi
    echo ""

    # ========== STEP 7: Superuser ==========
    print_header "Create Admin Account"
    print_info "You'll now create a superuser account for admin access"
    if ! createsuperuser_interactive; then
        print_warning "Superuser creation skipped or failed"
    fi
    echo ""

    # ========== FINAL VALIDATION ==========
    print_divider
    print_header "Validating Setup"
    
    # Check database exists
    if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
        print_success "✓ Database created"
    else
        print_warning "⚠ Database not found"
    fi
    
    # Check static files
    if [ -d "$PROJECT_DIR/staticfiles" ] && [ "$(ls -A "$PROJECT_DIR/staticfiles" 2>/dev/null)" ]; then
        STATIC_COUNT=$(find "$PROJECT_DIR/staticfiles" -type f 2>/dev/null | wc -l)
        print_success "✓ Static files collected ($STATIC_COUNT files)"
    else
        print_warning "⚠ Static files directory empty"
    fi
    
    # Check venv
    if [ -d "$VENV_DIR/bin" ]; then
        print_success "✓ Virtual environment ready"
    fi
    
    # Verify critical packages one more time
    if activate_venv; then
        if python3 -c "import django; import rest_framework" 2>/dev/null; then
            print_success "✓ Critical packages verified"
        else
            print_warning "⚠ Critical packages verification failed"
        fi
    fi

    print_divider
    print_success "✅ Setup complete!"
    print_divider
    printf '%b\n' "${BOLD}Next steps:${NC}"
    printf '%b\n' "  1. Start server:   ${CYAN}./manage.sh start${NC} or ${CYAN}./manage.sh 8${NC}"
    printf '%b\n' "  2. Open browser:   ${CYAN}http://localhost:8000${NC}"
    printf '%b\n' "  3. Admin panel:    ${CYAN}http://localhost:8000/admin${NC}"
    printf '%b\n' "  4. View accounts:  ${CYAN}./manage.sh accounts${NC} or ${CYAN}./manage.sh 15${NC}"
    print_divider
}

# ============================================================================
# Quick Commands (CLI interface)
# ============================================================================

show_usage() {
    cat << EOF
${BOLD}╔════════════════════════════════════════════════════════════════╗${NC}
${BOLD}║   WorkTrack Pro - Django Management Script (GUI Edition)       ║${NC}
${BOLD}║                                                                ║${NC}
${BOLD}║   Full-Featured Web Application with Bootstrap 5 UI            ║${NC}
${BOLD}╚════════════════════════════════════════════════════════════════╝${NC}

${BOLD}Usage:${NC}
  ./manage.sh [COMMAND]

${BOLD}Setup Commands:${NC}
  ${CYAN}setup${NC}              Full setup: venv, deps, migrations, superuser
  ${CYAN}venv${NC}               Create/setup virtual environment
  ${CYAN}install${NC}            Install project dependencies

${BOLD}Database Commands:${NC}
  ${CYAN}makemig${NC}            Create migrations (interactive app selection)
  ${CYAN}migrate${NC}            Run pending migrations
  ${CYAN}static${NC}             Collect static files for production
  ${CYAN}update${NC}             Quick update (Migrations + Static)
  ${CYAN}superuser${NC}          Create new admin account

${BOLD}Server Commands:${NC}
  ${CYAN}start${NC}              Start Django development server
  ${CYAN}stop${NC}               Stop the running server
  ${CYAN}stopall${NC}            Stop all running Django servers (with confirmation)
  ${CYAN}stopall -f${NC}         Stop all running servers (no confirmation)
  ${CYAN}restart${NC}            Restart the server
  ${CYAN}status${NC}             Show server status
  ${CYAN}logs${NC}               View real-time server logs

${BOLD}Utilities:${NC}
  ${CYAN}shell${NC}              Open Django interactive shell
  ${CYAN}dbinfo${NC}             Show database information
  ${CYAN}healthcheck${NC}        Run system health diagnostic
  ${CYAN}accounts${NC}           Show test account credentials
  ${CYAN}backup${NC}             Create a complete system backup archive
  ${CYAN}smtp${NC}               Configure Gmail SMTP settings
  ${CYAN}menu${NC}               Interactive menu (default)
  ${CYAN}help${NC}               Show this help message

${BOLD}Examples:${NC}
  ./manage.sh setup              # First-time setup
  ./manage.sh start              # Start development server
  ./manage.sh status             # Check if server is running
  ./manage.sh stop               # Stop the server
  ./manage.sh stopall            # Stop all servers
  ./manage.sh logs               # View server logs
  ./manage.sh accounts           # Show test logins
  ./manage.sh backup             # Create a project backup
  ./manage.sh menu               # Interactive menu

${BOLD}Application URLs:${NC}
  🌐 Home Page:          http://localhost:8000
  🏠 Dashboard:          http://localhost:8000/dashboard
  ✅ Tasks:             http://localhost:8000/tasks
  📥 Submissions:        http://localhost:8000/submissions
  🔔 Notifications:      http://localhost:8000/notifications
  👤 Profile:            http://localhost:8000/profile
  ⚙️  Admin Panel:        http://localhost:8000/admin
  📊 API Endpoints:      http://localhost:8000/api

EOF
}

# ============================================================================
# Interactive Menu
# ============================================================================

show_menu() {
    clear
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║              🌟 WorkTrack Pro - Management Menu (v1) 🌟                    ║
║                                                                            ║
║         Full-Featured Web Application with Bootstrap 5 UI                  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
    echo ""
    echo "  📦 Setup & Installation:"
    printf '%b\n' "    ${CYAN}1${NC}  ✨ Full Setup"
    printf '%b\n' "    ${CYAN}2${NC}  🐍 Create Virtual Environment"
    printf '%b\n' "    ${CYAN}3${NC}  📥 Install Dependencies"
    echo ""
    echo "  💾 Database Management:"
    printf '%b\n' "    ${CYAN}4${NC}  🏗️  Make Migrations"
    printf '%b\n' "    ${CYAN}5${NC}  🏃 Run Migrations"
    printf '%b\n' "    ${CYAN}6${NC}  📁 Collect Static Files"
    printf '%b\n' "    ${CYAN}7${NC}  👤 Create Superuser"
    echo ""
    echo "  🚀 Server Management:"
    printf '%b\n' "    ${CYAN}8${NC}  ▶️  Start Server"
    printf '%b\n' "    ${CYAN}9${NC}  ⏹️  Stop Server"
    printf '%b\n' "    ${CYAN}10${NC} 🛑 Stop All Servers"
    printf '%b\n' "    ${CYAN}11${NC} 📊 Server Status"
    printf '%b\n' "    ${CYAN}12${NC} 🔄 Restart Server"
    printf '%b\n' "    ${CYAN}13${NC} 📜 View Server Logs"
    echo ""
    echo "  🔧 Utilities:"
    printf '%b\n' "    ${CYAN}14${NC}  🗄️  Database Info"
    printf '%b\n' "    ${CYAN}15${NC}  🔑 Test Accounts"
    printf '%b\n' "    ${CYAN}16${NC}  💻 Django Shell"
    printf '%b\n' "    ${CYAN}17${NC}  🏥 Health Check"
    printf '%b\n' "    ${CYAN}18${NC}  🛡️  System Backup"
    printf '%b\n' "    ${CYAN}19${NC}  ⚡ Quick Update (Migrations + Static)"
    printf '%b\n' "    ${CYAN}20${NC}  📧 Configure SMTP (Gmail)"
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
            1) full_setup; read -p "Press Enter to continue..." ;;
            2) create_venv; read -p "Press Enter to continue..." ;;
            3) setup_dependencies; read -p "Press Enter to continue..." ;;
            4) make_migrations; read -p "Press Enter to continue..." ;;
            5) migrate_database; read -p "Press Enter to continue..." ;;
            6) collect_static; read -p "Press Enter to continue..." ;;
            7) createsuperuser_interactive; read -p "Press Enter to continue..." ;;
            8) start_server; read -p "Press Enter to continue..." ;;
            9) stop_server; read -p "Press Enter to continue..." ;;
            10) stop_all_servers; read -p "Press Enter to continue..." ;;
            11) server_status; read -p "Press Enter to continue..." ;;
            12) stop_server; sleep 2; start_server; read -p "Press Enter to continue..." ;;
            13) tail_logs ;;
            14) show_db_info; read -p "Press Enter to continue..." ;;
            15) show_test_accounts; read -p "Press Enter to continue..." ;;
            16)
                if activate_venv; then
                    cd "$PROJECT_DIR" || exit 1
                    python3 manage.py shell
                fi
                read -p "Press Enter to continue..." ;;
            17) health_check; read -p "Press Enter to continue..." ;;
            18) backup_system; read -p "Press Enter to continue..." ;;
            19) quick_update; read -p "Press Enter to continue..." ;;
            20) setup_smtp; read -p "Press Enter to continue..." ;;
            0)
                clear
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                read -p "Press Enter to continue..." ;;
        esac

        echo ""
    done
}

# ============================================================================
# Main Entry Point
# ============================================================================

main() {
    case "${1:-menu}" in
        setup)
            full_setup
            ;;
        venv)
            create_venv
            ;;
        install)
            setup_dependencies
            ;;
        makemig)
            make_migrations
            ;;
        migrate)
            migrate_database
            ;;
        static)
            collect_static
            ;;
        superuser)
            createsuperuser_interactive
            ;;
        update)
            quick_update
            ;;
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        stopall)
            if [ "$2" = "-f" ] || [ "$2" = "--force" ]; then
                stop_all_servers true
            else
                stop_all_servers false
            fi
            ;;
        status)
            server_status
            ;;
        restart)
            stop_server
            sleep 2
            start_server
            ;;
        logs)
            tail_logs
            ;;
        shell)
            if activate_venv; then
                cd "$PROJECT_DIR" || exit 1
                python3 manage.py shell
            fi
            ;;
        dbinfo)
            show_db_info
            ;;
        healthcheck)
            health_check
            ;;
        accounts)
            show_test_accounts
            ;;
        backup)
            backup_system
            ;;
        smtp)
            setup_smtp
            ;;
        menu)
            interactive_menu
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
