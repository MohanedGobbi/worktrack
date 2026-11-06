#!/bin/bash

# WorkTrack Pro - Docker Management Script v2
# Streamlined for Docker + PostgreSQL

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$PROJECT_DIR/backup"

# ============================================================================
# ANSI Color Codes
# ============================================================================
RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[1;33m'
CYAN=$'\033[0;36m'
BOLD=$'\033[1m'
NC=$'\033[0m'

# ============================================================================
# Utility Functions
# ============================================================================

print_success() { printf '%b\n' "${GREEN}✓ $1${NC}"; }
print_error() { printf '%b\n' "${RED}✗ $1${NC}"; }
print_info() { printf '%b\n' "${CYAN}ℹ $1${NC}"; }
print_warning() { printf '%b\n' "${YELLOW}⚠ $1${NC}"; }
print_header() { printf '%b\n' "${BOLD}${CYAN}╭─ $1${NC}"; }
print_divider() { echo ""; }

# ============================================================================
# Core Commands
# ============================================================================

check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

install_app() {
    print_header "Installing WorkTrack Pro (Docker)"
    check_docker
    
    print_info "Building images and starting services..."
    docker compose up -d --build
    
    print_info "Waiting for database to be ready (approx 10-15s)..."
    sleep 15
    
    print_info "Applying database migrations..."
    docker compose exec web python manage.py migrate
    
    print_info "Collecting static files..."
    docker compose exec web python manage.py collectstatic --noinput
    
    print_info "Creating superuser..."
    print_info "Follow the prompts to create an admin account:"
    docker compose exec web python manage.py createsuperuser || print_error "Superuser creation skipped or failed."
    
    print_success "Installation complete!"
    print_info "App is running at http://localhost:8000"
}

quick_update() {
    print_header "Quick Update (Migrations + Static Files)"
    check_docker
    
    print_info "Creating database migrations..."
    if ! docker compose exec web python manage.py makemigrations; then
        print_error "Failed to create migrations"
        return 1
    fi

    print_info "Applying database migrations..."
    if ! docker compose exec web python manage.py migrate; then
        print_error "Failed to run migrations"
        return 1
    fi
    
    print_info "Collecting static files..."
    if ! docker compose exec web python manage.py collectstatic --noinput; then
        print_error "Failed to collect static files"
        return 1
    fi
    
    print_success "Update complete!"
}

create_superuser() {
    print_header "Create Super Admin User"
    check_docker

    echo ""
    printf '%b\n' "${BOLD}  This will create a new super_admin account in WorkTrack Pro.${NC}"
    echo ""

    # Gather input
    read -p "  Email address : " SU_EMAIL
    if [ -z "$SU_EMAIL" ]; then
        print_error "Email cannot be empty."
        return 1
    fi

    read -p "  First name    : " SU_FIRST
    read -p "  Last name     : " SU_LAST

    # Password prompt (hidden input)
    while true; do
        read -s -p "  Password      : " SU_PASS; echo ""
        read -s -p "  Confirm pass  : " SU_PASS2; echo ""
        if [ "$SU_PASS" = "$SU_PASS2" ]; then
            break
        fi
        print_error "Passwords do not match. Try again."
    done

    echo ""
    print_info "Creating user in the database..."

    # Single Python command — creates the user with role=super_admin and is_staff/is_superuser flags
    docker compose exec web python manage.py shell -c "
import sys
from django.contrib.auth import get_user_model
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
    check_docker
    
    print_info "Creating database migrations..."
    if ! docker compose exec web python manage.py makemigrations; then
        print_error "Failed to create migrations"
        return 1
    fi
    print_success "Migrations created!"
}

run_migrations() {
    print_header "Run Migrations"
    check_docker
    
    print_info "Applying database migrations..."
    if ! docker compose exec web python manage.py migrate; then
        print_error "Failed to run migrations"
        return 1
    fi
    print_success "Migrations applied!"
}

collect_static() {
    print_header "Collect Static Files"
    check_docker
    
    print_info "Collecting static files..."
    if ! docker compose exec web python manage.py collectstatic --noinput; then
        print_error "Failed to collect static files"
        return 1
    fi
    print_success "Static files collected!"
}

start_app() {
    print_header "Starting WorkTrack Pro (Docker)"
    check_docker
    docker compose up -d
    print_success "Services started!"
    print_info "App is running at http://localhost:8000"
}

stop_app() {
    print_header "Stopping WorkTrack Pro (Docker)"
    check_docker
    docker compose down
    print_success "Services stopped!"
}

cleanup_app() {
    print_header "Full Cleanup (Removing Containers & Networks)"
    check_docker
    
    print_warning "This will stop and remove ALL containers and networks for this project."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Cleanup cancelled."
        exit 0
    fi

    print_info "Stopping services and removing volumes..."
    docker compose down -v || true
    
    print_info "Explicitly removing specific containers to resolve conflicts..."
    docker stop worktrack_db worktrack_redis worktrack_web worktrack_celery worktrack_celery_beat 2>/dev/null || true
    docker rm worktrack_db worktrack_redis worktrack_web worktrack_celery worktrack_celery_beat 2>/dev/null || true
    
    print_info "Removing project network..."
    docker network rm worktrack_network 2>/dev/null || true
    
    print_success "Full cleanup completed!"
}

logs_app() {
    print_header "WorkTrack Pro Logs"
    check_docker
    docker compose logs -f
}

backup_app() {
    print_header "Database Backup"
    check_docker
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/worktrack_db_$TIMESTAMP.sql"
    
    print_info "Creating backup at $BACKUP_FILE..."
    # Execute pg_dump inside the db container
    docker compose exec -T db pg_dump -U postgres -d worktrack_pro > "$BACKUP_FILE"
    
    if [ -s "$BACKUP_FILE" ]; then
        print_success "Backup completed successfully!"
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        print_info "Size: $SIZE"
    else
        print_error "Backup failed or generated an empty file."
        rm -f "$BACKUP_FILE"
    fi
}

restore_app() {
    print_header "Database Restore"
    check_docker
    
    if [ -z "$2" ]; then
        print_error "Please provide the backup file path."
        print_info "Usage: ./manage_v2.sh restore backup/your_backup_file.sql"
        exit 1
    fi
    
    BACKUP_FILE="$2"
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Backup file not found: $BACKUP_FILE"
        exit 1
    fi
    
    print_info "WARNING: This will overwrite the current database."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled."
        exit 0
    fi
    
    print_info "Restoring database from $BACKUP_FILE..."
    # Recreate the database to ensure a clean restore
    docker compose exec -T db dropdb -U postgres --if-exists worktrack_pro
    docker compose exec -T db createdb -U postgres worktrack_pro
    cat "$BACKUP_FILE" | docker compose exec -T db psql -U postgres -d worktrack_pro
    
    print_success "Restore completed!"
}

access_container() {
    print_header "Container Access"
    check_docker
    
    CONTAINER=${2:-web}
    if [[ ! "$CONTAINER" =~ ^(web|db|redis|celery|celery-beat)$ ]]; then
        print_error "Invalid container: $CONTAINER"
        print_info "Valid options: web, db, redis, celery, celery-beat"
        exit 1
    fi
    
    print_info "Opening shell in $CONTAINER..."
    if [ "$CONTAINER" = "db" ] || [ "$CONTAINER" = "redis" ]; then
        docker compose exec "$CONTAINER" sh
    else
        docker compose exec "$CONTAINER" bash
    fi
}

backup_full_app() {
    print_header "Full Application Backup"
    check_docker
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
    # 1. Backup the database first
    print_info "Step 1: Backing up database..."
    DB_BACKUP_FILE="$BACKUP_DIR/db_temp_$TIMESTAMP.sql"
    docker compose exec -T db pg_dump -U postgres -d worktrack_pro > "$DB_BACKUP_FILE"
    
    # 2. Package everything
    print_info "Step 2: Creating full portable archive..."
    FULL_BACKUP_FILE="$BACKUP_DIR/worktrack_pro_full_$TIMESTAMP.tar.gz"
    
    # Create the archive including the temporary sql dump, but excluding unwanted dirs
    tar -czf "$FULL_BACKUP_FILE" \
        --transform="s|^$BACKUP_DIR/db_temp_$TIMESTAMP\.sql$|database_backup.sql|" \
        --exclude="backup/worktrack_pro_full_*.tar.gz" \
        --exclude="backup/worktrack_db_*.sql" \
        --exclude="venv" \
        --exclude="__pycache__" \
        --exclude=".git" \
        --exclude="*.pyc" \
        --exclude=".pytest_cache" \
        . "$DB_BACKUP_FILE"
        
    # Clean up the temporary db dump
    rm -f "$DB_BACKUP_FILE"
    
    if [ -s "$FULL_BACKUP_FILE" ]; then
        print_success "Full portable backup completed successfully!"
        SIZE=$(du -h "$FULL_BACKUP_FILE" | cut -f1)
        print_info "Size: $SIZE"
        print_info "Saved to: $FULL_BACKUP_FILE"
        print_divider
        print_info "To restore on a new machine:"
        print_info "1. Extract this archive: tar -xzf worktrack_pro_full_${TIMESTAMP}.tar.gz"
        print_info "2. Run: ./manage_v2.sh restore_full"
    else
        print_error "Backup failed or generated an empty file."
        rm -f "$FULL_BACKUP_FILE"
    fi
}

restore_full_app() {
    print_header "Full Application Restore"
    check_docker
    
    if grep -q "database_backup.sql" <<< $(tar -tf "backup/worktrack_pro_full_*.tar.gz" 2>/dev/null || echo ""); then
        print_error "This feature requires extracting the archive first."
        print_info "Please extract the full backup archive in a new directory, then run this command."
        exit 1
    fi

    if [ ! -f "database_backup.sql" ]; then
        print_error "database_backup.sql not found in the current directory."
        print_info "Did you extract a full backup archive here?"
        exit 1
    fi
    
    print_info "WARNING: This will overwrite the current Docker database if it exists."
    read -p "Are you sure you want to proceed? (y/n): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Restore cancelled."
        exit 0
    fi
    
    print_info "Step 1: Starting database service..."
    docker compose up -d db
    print_info "Waiting for database to be ready (approx 10s)..."
    sleep 10
    
    print_info "Step 2: Restoring database..."
    docker compose exec -T db dropdb -U postgres --if-exists worktrack_pro
    docker compose exec -T db createdb -U postgres worktrack_pro
    cat "database_backup.sql" | docker compose exec -T db psql -U postgres -d worktrack_pro
    
    print_info "Step 3: Starting remaining services..."
    docker compose up -d
    
    print_success "Full restore completed!"
    print_info "You can delete database_backup.sql if everything is working fine."
}

setup_smtp() {
    print_header "SMTP Configuration (Gmail)"
    print_divider
    
    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        print_error ".env file not found."
        return 1
    fi
    
    print_info "This utility will help you configure Gmail for notifications."
    print_warning "Note: For Gmail, you MUST use an 'App Password', not your regular login password."
    print_info "Instructions: https://support.google.com/accounts/answer/185833"
    print_divider
    
    read -p "  Gmail Address (e.g., user@gmail.com): " gmail_addr
    if [ -z "$gmail_addr" ]; then
        print_error "Gmail address cannot be empty."
        return 1
    fi
    
    read -p "  Google App Password: " app_pass
    if [ -z "$app_pass" ]; then
        print_error "App password cannot be empty."
        return 1
    fi
    
    print_divider
    print_info "Updating .env configuration..."
    
    # Use temporary file for safety
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
    print_info "Note: You may need to restart the containers for changes to take effect."
    print_divider
    
    read -p "Would you like to run the diagnostic test now? (y/n): " confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        print_info "Attempting to run diagnostic test inside the 'web' container..."
        if docker compose ps web | grep -q "Up"; then
            docker compose exec -T web python3 manage.py shell < test_email.py
        else
            print_error "Web container is not running. Please start the app first."
        fi
    fi
}

setup_vscode_env() {
    print_header "VS Code Local Environment Setup"
    print_divider
    
    # 1. Check for python3
    if ! command -v python3 &> /dev/null; then
        print_error "python3 is not installed. Please install it first."
        return 1
    fi

    # 2. Create virtual environment
    if [ -d ".venv" ]; then
        print_warning "Existing .venv directory found."
        read -p "  Recreate virtual environment? (y/n): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            print_info "Removing existing .venv..."
            rm -rf .venv
        else
            print_info "Using existing .venv..."
        fi
    fi

    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment in .venv..."
        if ! python3 -m venv .venv; then
            print_error "Failed to create virtual environment."
            return 1
        fi
    fi
    
    # 3. Install requirements
    if [ -f "requirements.txt" ]; then
        print_info "Installing/Updating requirements..."
        .venv/bin/pip install --upgrade pip
        if ! .venv/bin/pip install -r requirements.txt; then
            print_error "Failed to install requirements."
            return 1
        fi
    else
        print_warning "requirements.txt not found. Skipping dependency installation."
    fi

    # 4. Configure VS Code
    print_info "Configuring VS Code settings..."
    mkdir -p .vscode
    
    # Create or update settings.json
    # Overwriting to ensure a clean environment configuration as requested
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
    print_info "1. Virtual environment created in '.venv'"
    print_info "2. Dependencies installed from requirements.txt"
    print_info "3. VS Code configured to use the local interpreter"
    print_divider
    print_warning "Please restart VS Code or 'Reload Window' for changes to take effect."
}

setup_stitch_mcp() {
    print_header "Stitch MCP Server & IDE Setup"
    print_divider

    # 1. Check/Install/Upgrade Node.js & npm
    local NEEDS_UPGRADE=false
    if ! command -v node &> /dev/null || ! command -v npx &> /dev/null; then
        print_warning "Node.js or npx not found (Required for Stitch MCP)."
        NEEDS_UPGRADE=true
    else
        NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VER" -lt 20 ]; then
            print_warning "Found Node.js v$(node -v | tr -d 'v'). Node.js 20+ is recommended for compatibility."
            NEEDS_UPGRADE=true
        fi
    fi

    if [ "$NEEDS_UPGRADE" = true ]; then
        read -p "  Would you like to install/upgrade to Node.js 20? (y/n): " install_node
        if [[ $install_node =~ ^[Yy]$ ]]; then
            print_info "Adding NodeSource repository for Node.js 20..."
            if ! command -v curl &> /dev/null; then
                sudo apt update && sudo apt install -y curl
            fi
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            print_info "Installing Node.js 20 via apt..."
            sudo apt-get install -y nodejs
            print_success "Node.js 20 installation completed! Current version: $(node -v)"
        else
            if ! command -v node &> /dev/null; then
                print_error "Node.js is required for Stitch MCP. Setup aborted."
                return 1
            fi
            print_warning "Continuing with existing Node.js... (Compat polyfill will be applied)"
        fi
    fi

    # 2. Verify connection & sync
    print_info "Syncing with @_davideast/stitch-mcp..."
    
    # 3. Initialization
    echo ""
    print_info "Starting Stitch MCP Initialization..."
    print_warning "Follow the prompts to authenticate with Google Cloud."
    echo ""
    
    # Recalculate Node version in case it was upgraded during Step 1
    NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    
    if [ "$NODE_VER" -lt 20 ]; then
        # Create polyfill for Node.js 18 compatibility with undici/fetch
        # Using relative path to avoid issues with spaces in $PROJECT_DIR
        POLYFILL_JS="./.stitch_polyfill.js"
        cat > "$POLYFILL_JS" <<EOF
try {
    const { File } = require('node:buffer');
    if (typeof global.File === 'undefined' && typeof File !== 'undefined') {
        global.File = File;
    }
} catch (e) {}
EOF
        export NODE_OPTIONS="--require $POLYFILL_JS"
    fi

    if npx @_davideast/stitch-mcp init; then
        print_divider
        print_info "Running system health check..."
        npx @_davideast/stitch-mcp doctor
        
        print_divider
        print_success "Stitch MCP is now fully configured for your platform!"
        print_info "Next: Select Option 19 to integrate with this IDE (Antigravity)."
        if [ -f "./.stitch_polyfill.js" ]; then rm -f "./.stitch_polyfill.js"; fi
        unset NODE_OPTIONS
    else
        print_error "Stitch MCP initialization failed."
        if [ -f "./.stitch_polyfill.js" ]; then rm -f "./.stitch_polyfill.js"; fi
        unset NODE_OPTIONS
    fi
}

integrate_stitch_ide() {
    print_header "Integrate Stitch with Antigravity IDE"
    print_divider
    
    CONFIG_FILE="/home/pc-2026-1/.gemini/antigravity/mcp_config.json"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Antigravity config file not found at $CONFIG_FILE"
        print_info "Please ensure Antigravity is installed and initialized."
        return 1
    fi

    echo "This will update your IDE configuration with your Stitch API Key."
    read -p "  Paste your Stitch API Key: " api_key
    
    if [ -z "$api_key" ]; then
        print_error "API Key cannot be empty."
        return 1
    fi

    print_info "Updating $CONFIG_FILE..."
    
    # Use python to safely update the JSON file to preserve other servers
    python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
except Exception:
    config = {'mcpServers': {}}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

config['mcpServers']['StitchMCP'] = {
    '\$typeName': 'exa.cascade_plugins_pb.CascadePluginCommandTemplate',
    'command': 'npx',
    'args': [
        '-y',
        'mcp-remote',
        'https://stitch.googleapis.com/mcp',
        '--header',
        f'X-Goog-Api-Key: $api_key'
    ],
    'env': {}
}

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)
print('SUCCESS')
" | grep -q "SUCCESS" && print_success "IDE integration updated!" || print_error "Failed to update config."

    print_divider
    print_warning "IMPORTANT: Please 'Restart Agent' or 'Reload IDE' to load the new config."
}


repair_ide_environment() {
    print_header "Repair System & Environment (Option 20)"
    print_divider
    
    # 1. IDE Settings
    print_info "Syncing VS Code settings..."
    mkdir -p .vscode
    cat > .vscode/settings.json <<EOF
{
    "python.defaultInterpreterPath": "\${workspaceFolder}/.venv/bin/python",
    "python.analysis.venvPath": "\${workspaceFolder}",
    "python.analysis.venv": ".venv",
    "python.analysis.extraPaths": [
        "\${workspaceFolder}",
        "\${workspaceFolder}/worktrack_pro"
    ],
    "python.envFile": "\${workspaceFolder}/.env",
    "python.languageServer": "Pylance",
    "python.analysis.diagnosticMode": "workspace",
    "python.analysis.typeCheckingMode": "basic",
    "python.terminal.activateEnvInCurrentTerminal": true,
    "editor.formatOnSave": true,
    "python.analysis.autoImportCompletions": true
}
EOF
    print_success "IDE settings updated."

    # 2. Virtual Environment
    if [ ! -d ".venv" ]; then
        print_warning ".venv missing. Creating..."
        python3 -m venv .venv
    fi
    
    # 3. Virtual Environment Dependencies
    print_info "Verifying core dependencies..."
    if [ -f "requirements.txt" ]; then
        .venv/bin/pip install --upgrade pip &> /dev/null
        .venv/bin/pip install -r requirements.txt &> /dev/null
    fi
    print_success "Dependencies verified."

    # 4. Docker & Database Integrity
    if docker compose ps | grep -q "web"; then
        print_info "Running database integrity check (migrations)..."
        docker compose exec -T web python manage.py makemigrations &> /dev/null || true
        docker compose exec -T web python manage.py migrate
        print_success "Database migrations synced."
        
        print_info "Refreshing static assets..."
        docker compose exec -T web python manage.py collectstatic --noinput &> /dev/null
        print_success "Static files refreshed."
    else
        print_warning "Docker services not running. Skipping database repair."
    fi

    # 5. Fix common data issues (e.g. empty slugs)
    if docker compose ps | grep -q "web"; then
        print_info "Fixing common data issues (e.g. empty slugs)..."
        docker compose exec -T web python manage.py shell -c "
from django.utils.text import slugify
from work_modules.models import WorkModule, WorkGroup
# Fix WorkModule slugs
for m in WorkModule.objects.filter(slug=''):
    m.slug = slugify(m.name) or f'module-{m.id}'
    m.save()
# Fix WorkGroup slugs
for g in WorkGroup.objects.filter(slug=''):
    g.slug = slugify(g.name) or f'group-{g.id}'
    g.save()
print('SUCCESS')
" | grep -q "SUCCESS" && print_success "Data integrity fixed." || print_error "Data repair failed."
    fi

    print_divider
    print_success "System Repair Complete!"
    print_info "Please 'Reload Window' in VS Code for IDE changes."
}

show_help() {
    echo "WorkTrack Pro - Docker Management Script v2"
    echo "Usage: ./manage_v2.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install        Build images, start services, migrate, collect static, create superuser"
    echo "  start          Start the Docker containers"
    echo "  stop           Stop the Docker containers"
    echo "  logs           View streaming logs for all containers"
    echo "  backup         Create a PostgreSQL database dump in the backup/ directory"
    echo "  restore [file] Restore a database dump from a file"
    echo "  backup_full    Create a full portable tar.gz backup (code + database)"
    echo "  restore_full   Restore from an extracted full backup in the current directory"
    echo "  access [name]  Open an interactive shell in a container (default: web, options: web, db, redis, celery, celery-beat)"
    echo "  makemig        Create database migrations"
    echo "  migrate        Run database migrations"
    echo "  static         Collect static files"
    echo "  update         Quick update (Migrations + Static Files)"
    echo "  superuser      Create a new super admin user interactively"
    echo "  smtp           Configure Gmail SMTP settings"
    echo "  vscode         Setup local VS Code environment (.venv + settings)"
    echo "  stitch         Install & Configure Stitch MCP Server (Node.js/npx)"
    echo "  stitch_ide     Integrate Stitch MCP with Antigravity IDE settings"
    echo "  help           Show this help message"
    echo ""
}

show_menu() {
    clear
    cat << "EOF"
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🐳 WorkTrack Pro - Docker Management Menu (v2) 🐳                  ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
    echo ""
    echo "  🚀 Container Setup & Execution:"
    printf '%b\n' "    ${CYAN}1${NC}  ✨ Install & Build All Services"
    printf '%b\n' "    ${CYAN}2${NC}  ▶️  Start App (Docker Compose Up)"
    printf '%b\n' "    ${CYAN}3${NC}  ⏹️  Stop App (Docker Compose Down)"
    printf '%b\n' "    ${CYAN}4${NC}  📜 View Logs"
    echo ""
    echo "  💾 Database & Backup:"
    printf '%b\n' "    ${CYAN}5${NC}  📦 Backup Database Only"
    printf '%b\n' "    ${CYAN}6${NC}  🔄 Restore Database Only"
    printf '%b\n' "    ${CYAN}7${NC}  🧳 Full Portable Backup (DB + Code)"
    printf '%b\n' "    ${CYAN}8${NC}  🌐 Restore Full Portable Backup"
    echo ""
    echo "  🔧 Utilities:"
    printf '%b\n' "    ${CYAN}9${NC}  💻 Access Container Shell"
    printf '%b\n' "    ${CYAN}10${NC} 🏗️  Make Migrations"
    printf '%b\n' "    ${CYAN}11${NC} 🏃 Run Migrations"
    printf '%b\n' "    ${CYAN}12${NC} 📁 Collect Static Files"
    printf '%b\n' "    ${CYAN}13${NC} ⚡ Quick Update (Migrations + Static)"
    printf '%b\n' "    ${CYAN}14${NC} 👤 Create Super Admin User"
    printf '%b\n' "    ${CYAN}15${NC} 📧 Configure SMTP (Gmail)"
    printf '%b\n' "    ${CYAN}16${NC} 🧹 Full Cleanup (Remove Containers & Networks)"
    printf '%b\n' "    ${CYAN}17${NC} 💻 Setup VS Code Environment (.venv)"
    printf '%b\n' "    ${CYAN}18${NC} 🧩 Setup Stitch MCP Server (Node.js)"
    printf '%b\n' "    ${CYAN}19${NC} 🔗 Integrate Stitch with IDE (Antigravity)"
    echo ""
    echo "  🚀 Repair & Verify:"
    printf '%b\n' "    ${CYAN}20${NC} 🔧 Repair IDE & Environment (Fix Red Flags)"
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
            6) 
                read -p "Enter backup file path: " backup_file
                if [ -n "$backup_file" ]; then
                    restore_app "" "$backup_file"
                else
                    print_error "No backup file provided."
                fi
                read -p "Press Enter to continue..."
                ;;
            7) backup_full_app; read -p "Press Enter to continue..." ;;
            8) restore_full_app; read -p "Press Enter to continue..." ;;
            9)
                read -p "Enter container name (web/db/redis/celery/celery-beat) [web]: " container_name
                if [ -z "$container_name" ]; then
                    container_name="web"
                fi
                access_container "" "$container_name"
                read -p "Press Enter to continue..."
                ;;
            10) make_migrations; read -p "Press Enter to continue..." ;;
            11) run_migrations; read -p "Press Enter to continue..." ;;
            12) collect_static; read -p "Press Enter to continue..." ;;
            13) quick_update; read -p "Press Enter to continue..." ;;
            14) create_superuser; read -p "Press Enter to continue..." ;;
            15) setup_smtp; read -p "Press Enter to continue..." ;;
            16) cleanup_app; read -p "Press Enter to continue..." ;;
            17) setup_vscode_env; read -p "Press Enter to continue..." ;;
            18) setup_stitch_mcp; read -p "Press Enter to continue..." ;;
            19) integrate_stitch_ide; read -p "Press Enter to continue..." ;;
            20) repair_ide_environment; read -p "Press Enter to continue..." ;;
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

# ============================================================================
# Main Execution
# ============================================================================

cd "$PROJECT_DIR"

if [ $# -eq 0 ]; then
    interactive_menu
else
    case "$1" in
        install)
            install_app
            ;;
        start)
            start_app
            ;;
        stop)
            stop_app
            ;;
        logs)
            logs_app
            ;;
        backup)
            backup_app
            ;;
        restore)
            restore_app "$@"
            ;;
        backup_full)
            backup_full_app
            ;;
        restore_full)
            restore_full_app
            ;;
        access)
            access_container "$@"
            ;;
        makemig)
            make_migrations
            ;;
        migrate)
            run_migrations
            ;;
        static)
            collect_static
            ;;
        update)
            quick_update
            ;;
        superuser)
            create_superuser
            ;;
        smtp)
            setup_smtp
            ;;
        vscode)
            setup_vscode_env
            ;;
        stitch)
            setup_stitch_mcp
            ;;
        stitch_ide)
            integrate_stitch_ide
            ;;
        repair|fix)
            repair_ide_environment
            ;;
        cleanup)
            cleanup_app
            ;;
        help|*)
            show_help
            ;;
    esac
fi
