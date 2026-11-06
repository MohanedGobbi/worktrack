#!/bin/bash

# WorkTrack Pro - cPanel Online Management Script
# Designed specifically for CloudLinux/Passenger Python Apps
# Make sure to run the `source /home/user/virtualenv/...` command given by cPanel before using!

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ANSI Color Codes
CYAN=$'\033[0;36m'
GREEN=$'\033[0;32m'
RED=$'\033[0;31m'
NC=$'\033[0m'

print_header() { echo -e "${CYAN}╭─ $1${NC}"; }
print_info() { echo -e "${CYAN}ℹ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }

check_env() {
    if [ -z "$VIRTUAL_ENV" ]; then
        echo -e "${RED}⚠ WARNING: You don't seem to be in a cPanel Python virtual environment!${NC}"
        echo -e "Did you run the 'source /home/username/virtualenv/...' command cPanel gave you in the Setup Python App page?"
        read -p "Press Enter to try anyway or Ctrl+C to exit..."
    fi
}

install_deps() {
    print_header "Installing Dependencies (Production)"
    check_env
    pip install --upgrade pip
    pip install -r requirements.txt
    print_success "Dependencies installed!"
}

update_db() {
    print_header "Applying Database Migrations"
    check_env
    python manage.py makemigrations
    python manage.py migrate
    print_success "Database is up to date!"
}

collect_static() {
    print_header "Collecting Static Files"
    check_env
    python manage.py collectstatic --noinput
    print_success "Static files cached!"
}

restart_passenger() {
    print_header "Restarting Online Server (cPanel Passenger)"
    # Passenger monitors the tmp/restart.txt file. Touching it reloads the app.
    mkdir -p "$PROJECT_DIR/tmp"
    touch "$PROJECT_DIR/tmp/restart.txt"
    print_success "Server restart triggered! passenger_wsgi.py will reload."
    print_success "You can now refresh dhetasks.com in your browser."
}

create_superuser() {
    print_header "Create Super Admin User"
    check_env
    python manage.py createsuperuser
}

create_default_admin() {
    print_header "Create Default Admin User"
    check_env
    print_info "Creating admin@admin.com with password '0'..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'admin@admin.com'
password = '0'
user, created = User.objects.get_or_create(email=email)
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.role = 'super_admin'
user.first_name = 'Default'
user.last_name = 'Admin'
user.save()
print('SUCCESS: default admin user created/updated successfully!')
"
    print_success "Default Admin User created! Email: admin@admin.com | Password: 0"
}

allow_host() {
    print_header "Allow Host Domain"
    check_env
    read -p "Enter domain to allow (e.g. dhetasks.com, or * for all): " DOMAIN
    if [ -n "$DOMAIN" ]; then
        python manage.py shell -c "from core.models import AllowedHost; AllowedHost.objects.update_or_create(hostname='$DOMAIN', defaults={'is_active': True}); print('Host added successfully!'); from django.core.cache import cache; cache.clear()"
        print_success "Host $DOMAIN is now allowed!"
    else
        print_error "Domain cannot be empty."
    fi
}

start_all_servers() {
    print_header "Starting All Servers (Web + Background Workers)"
    check_env
    
    restart_passenger
    
    print_info "Starting Celery Worker in background..."
    pkill -f "celery -A worktrack_pro worker" || true
    nohup celery -A worktrack_pro worker -l info > "$PROJECT_DIR/tmp/celery_worker.log" 2>&1 &
    
    print_info "Starting Celery Beat in background..."
    pkill -f "celery -A worktrack_pro beat" || true
    nohup celery -A worktrack_pro beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler > "$PROJECT_DIR/tmp/celery_beat.log" 2>&1 &
    
    print_success "All servers started successfully in background!"
}

full_deploy() {
    install_deps
    update_db
    collect_static
    restart_passenger
    print_success "Full Production Deployment Completed!"
}

full_backup() {
    print_header "Creating Full Application Backup"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$PROJECT_DIR/backups"
    BACKUP_FILE="worktrack_pro_cpanel_backup_$TIMESTAMP.tar.gz"
    
    mkdir -p "$BACKUP_DIR"
    
    print_info "Compressing files (excluding virtual environments and caches)..."
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
        --exclude="venv" \
        --exclude=".venv" \
        --exclude="virtualenv" \
        --exclude=".git" \
        --exclude="__pycache__" \
        --exclude="node_modules" \
        --exclude="backups" \
        --exclude="*.log" \
        --exclude="tmp" \
        -C "$PROJECT_DIR" .
        
    print_success "Backup completed successfully!"
    print_info "Backup saved to: backups/$BACKUP_FILE"
}

view_logs() {
    print_header "View Application Logs"
    echo "1) View Django App Log (worktrack_pro.log)"
    echo "2) View Server Error Log (stderr.log)"
    echo "3) View Background Tasks Log (celery_worker.log)"
    read -p "Select log to view: " log_choice
    case $log_choice in
        1) if [ -f "$PROJECT_DIR/logs/worktrack_pro.log" ]; then tail -n 50 "$PROJECT_DIR/logs/worktrack_pro.log"; else print_error "Log not found."; fi ;;
        2) if [ -f "$PROJECT_DIR/stderr.log" ]; then tail -n 50 "$PROJECT_DIR/stderr.log"; else print_error "Log not found."; fi ;;
        3) if [ -f "$PROJECT_DIR/tmp/celery_worker.log" ]; then tail -n 50 "$PROJECT_DIR/tmp/celery_worker.log"; else print_error "Log not found."; fi ;;
        *) print_error "Invalid option" ;;
    esac
}

setup_email_settings() {
    print_header "System Email Settings (SMTP) Setup"
    check_env
    
    DOTENV_FILE="$PROJECT_DIR/.env"
    if [ ! -f "$DOTENV_FILE" ]; then
        touch "$DOTENV_FILE"
    fi

    echo "Configure SMTP credentials to allow the system to send emails (notifications, password resets, etc.)."
    echo ""

    read -p "SMTP Host Server [default: smtp.gmail.com]: " host_input
    SMTP_HOST="${host_input:-smtp.gmail.com}"

    read -p "SMTP Port [default: 587]: " port_input
    SMTP_PORT="${port_input:-587}"

    read -p "Use TLS (y/n) [default: y]: " tls_input
    if [[ "$tls_input" =~ ^[Nn]$ ]]; then
        SMTP_TLS="False"
    else
        SMTP_TLS="True"
    fi

    read -p "SMTP Email Username (e.g. sender@gmail.com): " SMTP_USER
    if [ -z "$SMTP_USER" ]; then
        print_error "SMTP Username cannot be empty."
        return 1
    fi

    read -s -p "SMTP Password / App Password: " SMTP_PASS
    echo ""
    if [ -z "$SMTP_PASS" ]; then
        print_error "SMTP Password cannot be empty."
        return 1
    fi

    read -p "Default From Email [default: $SMTP_USER]: " from_input
    DEFAULT_FROM="${from_input:-$SMTP_USER}"

    read -p "Site URL [default: https://dhetasks.com]: " site_input
    SITE_URL_VAL="${site_input:-https://dhetasks.com}"

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
    check_env
    if [ -f "$PROJECT_DIR/test_email.py" ]; then
        python "$PROJECT_DIR/test_email.py"
    else
        print_error "test_email.py not found in $PROJECT_DIR."
    fi
}

setup_db_settings() {
    print_header "Database Setup & Configuration"
    check_env

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

    echo "Configure the database for your WorkTrack Pro / cPanel setup."
    echo "  1) SQLite (default embedded file database)"
    echo "  2) MySQL / MariaDB (recommended for cPanel production)"
    echo "  3) PostgreSQL"
    echo ""
    read -p "Select database engine [default 2]: " db_choice
    db_choice="${db_choice:-2}"

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
            read -p "Database Name (e.g., username_worktrack): " DB_NAME
            read -p "Database User (e.g., username_dbuser): " DB_USER
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
    if python manage.py check --database default > /tmp/db_test.log 2>&1; then
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
    print_info "Applying next automated configuration steps..."
    update_db
    collect_static
    restart_passenger

    print_success "Database configuration and all automated next steps completed successfully!"
}

fix_messaging_platform() {
    print_header "🩺 Messaging Platform Doctor — Fix & Verify All Issues"
    check_env

    DOTENV_FILE="$PROJECT_DIR/.env"
    ERRORS=0
    FIXES=0

    # ── Shared helper to upsert a key in .env ──────────────────────────────
    update_env_key() {
        local key=$1 val=$2
        if grep -q "^${key}=" "$DOTENV_FILE" 2>/dev/null; then
            sed -i "s|^${key}=.*|${key}=${val}|" "$DOTENV_FILE"
        else
            echo "${key}=${val}" >> "$DOTENV_FILE"
        fi
    }

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 1 — Checking .env configuration for HTTPS/cPanel"
    echo "════════════════════════════════════════════════════════"

    if [ ! -f "$DOTENV_FILE" ]; then
        print_error ".env file not found! Creating a minimal one..."
        touch "$DOTENV_FILE"
    fi

    # 1a. SECURE_COOKIES — required for CSRF POST to work over HTTPS
    SECURE_COOKIES_VAL=$(grep -oP '^SECURE_COOKIES=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [ "$SECURE_COOKIES_VAL" != "True" ]; then
        print_error "SECURE_COOKIES is '${SECURE_COOKIES_VAL:-not set}' → CSRF POST requests will fail over HTTPS!"
        update_env_key "SECURE_COOKIES" "True"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set SECURE_COOKIES=True"
    else
        print_success "OK: SECURE_COOKIES=True"
    fi

    # 1b. CSRF_COOKIE_SAMESITE — ensure it is Lax not Strict (blocks cross-tab POSTs)
    SAMESITE_VAL=$(grep -oP '^CSRF_COOKIE_SAMESITE=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [ -z "$SAMESITE_VAL" ]; then
        update_env_key "CSRF_COOKIE_SAMESITE" "Lax"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set CSRF_COOKIE_SAMESITE=Lax"
    else
        print_success "OK: CSRF_COOKIE_SAMESITE=${SAMESITE_VAL}"
    fi

    # 1c. ALLOWED_HOSTS — must include the live domain
    HOSTS_VAL=$(grep -oP '^ALLOWED_HOSTS=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [ -z "$HOSTS_VAL" ]; then
        update_env_key "ALLOWED_HOSTS" "dhetasks.com,www.dhetasks.com,localhost,127.0.0.1"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set default ALLOWED_HOSTS"
    else
        print_success "OK: ALLOWED_HOSTS=${HOSTS_VAL}"
    fi

    # 1d. CSRF_TRUSTED_ORIGINS — must list the https:// domain
    TRUSTED_VAL=$(grep -oP '^CSRF_TRUSTED_ORIGINS=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [[ -z "$TRUSTED_VAL" ]] || [[ "$TRUSTED_VAL" != *"https://"* ]]; then
        update_env_key "CSRF_TRUSTED_ORIGINS" "https://dhetasks.com,https://www.dhetasks.com"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set CSRF_TRUSTED_ORIGINS with https:// origins"
    else
        print_success "OK: CSRF_TRUSTED_ORIGINS=${TRUSTED_VAL}"
    fi

    # 1e. CORS_ALLOWED_ORIGINS — must include https:// origins
    CORS_VAL=$(grep -oP '^CORS_ALLOWED_ORIGINS=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [[ -z "$CORS_VAL" ]] || [[ "$CORS_VAL" != *"https://"* ]]; then
        update_env_key "CORS_ALLOWED_ORIGINS" "https://dhetasks.com,https://www.dhetasks.com,http://localhost:3000,http://localhost:8000"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set CORS_ALLOWED_ORIGINS with https:// origins"
    else
        print_success "OK: CORS_ALLOWED_ORIGINS=${CORS_VAL}"
    fi

    # 1f. SITE_URL — must use https://
    SITE_URL_VAL=$(grep -oP '^SITE_URL=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [[ -z "$SITE_URL_VAL" ]] || [[ "$SITE_URL_VAL" == *"http://localhost"* ]]; then
        update_env_key "SITE_URL" "https://dhetasks.com"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set SITE_URL=https://dhetasks.com"
    else
        print_success "OK: SITE_URL=${SITE_URL_VAL}"
    fi

    # 1g. DEBUG must be False on production
    DEBUG_VAL=$(grep -oP '^DEBUG=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "")
    if [ "$DEBUG_VAL" = "True" ]; then
        print_error "DEBUG=True in production — security risk and can hide real errors!"
        update_env_key "DEBUG" "False"
        FIXES=$((FIXES+1))
        print_success "FIXED: Set DEBUG=False"
    else
        print_success "OK: DEBUG=${DEBUG_VAL:-False}"
    fi

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 2 — Installing / Verifying Python Dependencies"
    echo "════════════════════════════════════════════════════════"

    print_info "Upgrading pip..."
    pip install --upgrade pip --quiet

    print_info "Installing requirements.txt..."
    if pip install -r requirements.txt --quiet; then
        print_success "All Python packages installed / verified!"
    else
        print_error "pip install failed! Check requirements.txt and your Python environment."
        ERRORS=$((ERRORS+1))
    fi

    # Check critical packages explicitly
    for PKG in django djangorestframework whitenoise python-decouple pillow; do
        if python -c "import $(echo $PKG | tr '-' '_' | sed 's/djangorestframework/rest_framework/;s/python_decouple/decouple/')" 2>/dev/null; then
            print_success "OK: $PKG is available"
        else
            print_error "MISSING: $PKG — trying to install..."
            pip install "$PKG" --quiet && print_success "FIXED: $PKG installed!" || ERRORS=$((ERRORS+1))
        fi
    done

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 3 — Database Migrations (messaging tables)"
    echo "════════════════════════════════════════════════════════"

    print_info "Running makemigrations for messaging app..."
    python manage.py makemigrations messaging --no-input 2>/dev/null || true
    python manage.py makemigrations --no-input 2>/dev/null || true

    print_info "Applying all pending migrations..."
    if python manage.py migrate --no-input; then
        print_success "All migrations applied! Messaging tables are ready."
    else
        print_error "Migration failed! Check database credentials in .env."
        ERRORS=$((ERRORS+1))
    fi

    # Verify messaging tables exist
    print_info "Verifying messaging tables in database..."
    TABLE_CHECK=$(python manage.py shell -c "
try:
    from messaging.models import Message, Conversation, ConversationMember
    mc = Message.objects.count()
    cc = Conversation.objects.count()
    print(f'OK: Message={mc}, Conversations={cc}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    if echo "$TABLE_CHECK" | grep -q "^OK:"; then
        print_success "$TABLE_CHECK"
    else
        print_error "Messaging tables check: $TABLE_CHECK"
        ERRORS=$((ERRORS+1))
    fi

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 4 — Collecting Static Files"
    echo "════════════════════════════════════════════════════════"

    if python manage.py collectstatic --noinput --clear 2>/dev/null; then
        print_success "Static files collected! CSS/JS/vendor files are live."
    else
        print_error "collectstatic failed!"
        ERRORS=$((ERRORS+1))
    fi

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 5 — File Permissions (DB + Media)"
    echo "════════════════════════════════════════════════════════"

    # Fix SQLite permissions if used
    DB_ENGINE_VAL=$(grep -oP '^DB_ENGINE=\K.*' "$DOTENV_FILE" 2>/dev/null || echo "sqlite3")
    if [[ "$DB_ENGINE_VAL" == *"sqlite3"* ]]; then
        if [ -f "$PROJECT_DIR/db.sqlite3" ]; then
            chmod 664 "$PROJECT_DIR/db.sqlite3" && print_success "OK: db.sqlite3 permissions fixed (664)"
        fi
    fi
    chmod 755 "$PROJECT_DIR" 2>/dev/null && print_success "OK: Project directory permissions set (755)"

    # Fix media directory
    mkdir -p "$PROJECT_DIR/media"
    chmod 755 "$PROJECT_DIR/media" 2>/dev/null && print_success "OK: media/ directory permissions set (755)"

    # Fix logs directory
    mkdir -p "$PROJECT_DIR/logs"
    chmod 755 "$PROJECT_DIR/logs" 2>/dev/null && print_success "OK: logs/ directory permissions set (755)"

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 6 — Verifying Messaging API URLs"
    echo "════════════════════════════════════════════════════════"

    URL_CHECK=$(python manage.py shell -c "
try:
    from django.urls import reverse
    urls = [
        ('messaging:api-get-conversations', reverse('messaging:api-get-conversations')),
        ('messaging:api-send-message',      reverse('messaging:api-send-message')),
        ('messaging:api-search-users',      reverse('messaging:api-search-users')),
        ('messaging:api-unread-count',      reverse('messaging:api-unread-count')),
    ]
    for name, url in urls:
        print(f'OK: {name} → {url}')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
    while IFS= read -r line; do
        if echo "$line" | grep -q "^OK:"; then
            print_success "$line"
        elif echo "$line" | grep -q "^ERROR:"; then
            print_error "$line"
            ERRORS=$((ERRORS+1))
        fi
    done <<< "$URL_CHECK"

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 7 — Django System Check"
    echo "════════════════════════════════════════════════════════"

    if python manage.py check --deploy 2>/tmp/django_check.log; then
        print_success "Django system check passed with no issues!"
    else
        print_warning "Django check warnings (non-fatal):"
        grep -v "^$" /tmp/django_check.log | head -20 || true
    fi

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  STEP 8 — Restarting cPanel Passenger Server"
    echo "════════════════════════════════════════════════════════"
    restart_passenger

    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "           📋 MESSAGING DOCTOR — SUMMARY REPORT"
    echo "════════════════════════════════════════════════════════"
    print_success "Fixes applied  : $FIXES"
    if [ "$ERRORS" -gt 0 ]; then
        print_error  "Errors found   : $ERRORS (check output above)"
    else
        print_success "Errors found   : 0 — All clear!"
    fi
    echo ""
    print_info "✅ What was verified and fixed:"
    echo "   • SECURE_COOKIES, CSRF_TRUSTED_ORIGINS, CORS_ALLOWED_ORIGINS for HTTPS"
    echo "   • All Python packages from requirements.txt installed"
    echo "   • All database migrations applied (messaging tables exist)"
    echo "   • Static files collected (CSS/JS files are live on server)"
    echo "   • File permissions fixed (db, media, logs)"
    echo "   • Messaging API URL routes verified"
    echo "   • Server restarted"
    echo ""
    print_info "🔍 Next: Open browser DevTools → Network tab on https://dhetasks.com/messaging/"
    print_info "   Look for any /messaging/api/ calls returning 403, 404, or 500."
    print_info "   If 403 → CSRF issue. If 404 → URL config. If 500 → DB/code error."
    echo ""
}

auto_config_online() {
    print_header "⚡ Auto-Configure Production Environment & Deploy ⚡"
    check_env

    DOTENV_FILE="$PROJECT_DIR/.env"
    
    print_info "Writing production environment settings to .env..."
    cat > "$DOTENV_FILE" << 'EOF'
# Django Settings
SECRET_KEY=django-insecure-your-secret-key-here-change-in-production
DEBUG=False
ALLOWED_HOSTS=dhetasks.com,www.dhetasks.com,localhost,127.0.0.1,*

# Database Configuration (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=dhetas95_worktrack
DB_USER=dhetas95_admin
DB_PASSWORD=vgF5J:T-k*!xk~a
DB_HOST=127.0.0.1
DB_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=dr.houssem.degha.contact@gmail.com
EMAIL_HOST_PASSWORD=tvvt jqgu aowq blun
DEFAULT_FROM_EMAIL=dr.houssem.degha.contact@gmail.com

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TASK_ALWAYS_EAGER=True

# CORS Configuration
CORS_ALLOWED_ORIGINS=https://dhetasks.com,https://www.dhetasks.com,http://localhost:3000,http://localhost:8000

# Django Log Level
DJANGO_LOG_LEVEL=INFO

# Django Environment
DJANGO_SETTINGS_MODULE=worktrack_pro.settings
PYTHONPATH=.
EOF

    print_success ".env updated with production settings successfully!"

    echo ""
    print_info "Step 1: Installing / verifying dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    echo ""
    print_info "Step 2: Checking database connection..."
    if python manage.py check --database default > /tmp/db_test.log 2>&1; then
        print_success "Database system check passed!"
    else
        print_warning "Database check produced output or warnings. Details:"
        cat /tmp/db_test.log
    fi

    echo ""
    print_info "Step 3: Running database migrations (makemigrations & migrate)..."
    python manage.py makemigrations || true
    python manage.py migrate

    echo ""
    print_info "Step 4: Collecting static files..."
    python manage.py collectstatic --noinput

    echo ""
    print_info "Step 5: Creating default admin user (admin@admin.com)..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'admin@admin.com'
password = '0'
user, created = User.objects.get_or_create(email=email)
user.set_password(password)
user.is_staff = True
user.is_superuser = True
user.role = 'super_admin'
user.first_name = 'Default'
user.last_name = 'Admin'
user.save()
print('SUCCESS: default admin user created/updated successfully!')
" || true

    echo ""
    print_info "Step 6: Restarting cPanel Passenger Server..."
    restart_passenger

    print_success "✨ Complete online setup and deployment finished successfully! ✨"
    print_info "Your system is ready and running at: https://dhetasks.com"
}

show_menu() {
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          ☁️  WorkTrack Pro - cPanel Cloud Manager ☁️          ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "  1  🚀 Full Deploy (Install + Migrate + Static + Restart)"
    echo "  2  📦 Install/Update Requirements"
    echo "  3  🏃 Run Migrations (Fix missing tables)"
    echo "  4  📁 Collect Static Files"
    echo "  5  🔄 Restart Online Server (Touch restart.txt)"
    echo "  6  👤 Create Super Admin User"
    echo "  7  🟢 Start All Servers (Web + Background Workers)"
    echo "  8  🌐 Allow Host Domain (Fix 403 Forbidden)"
    echo "  9  🔑 Create Default Admin (admin@admin.com)"
    echo "  10 🗄️  Full Application Backup"
    echo "  11 🛡️  Fix Database Write Permissions (Fix 500 Error)"
    echo "  12 📜 View System Logs (Diagnose 500 Errors)"
    echo "  13 ✉️  Configure System Email Settings (SMTP)"
    echo "  14 🧪 Test Email Sending"
    echo "  15 🗃️  Configure Database (SQLite / MySQL / MariaDB / PostgreSQL)"
    echo "  16 ⚡ Auto-Setup Production Environment & Deploy (.env + DB + Static + Server Restart)"
    echo ""
    echo "  ─────────────────────────────────────────────────────────────"
    echo "  17 🩺 Messaging Platform Doctor (Fix Messenger on cPanel)"
    echo "  ─────────────────────────────────────────────────────────────"
    echo ""
    echo "  0  ❌ Exit"
    echo ""
}

# Ensure execution context
cd "$PROJECT_DIR"

if [ $# -eq 0 ]; then
    while true; do
        show_menu
        read -p "Select option: " choice
        echo ""
        case $choice in
            1) full_deploy; read -p "Press Enter to continue..." ;;
            2) install_deps; read -p "Press Enter to continue..." ;;
            3) update_db; read -p "Press Enter to continue..." ;;
            4) collect_static; read -p "Press Enter to continue..." ;;
            5) restart_passenger; read -p "Press Enter to continue..." ;;
            6) create_superuser; read -p "Press Enter to continue..." ;;
            7) start_all_servers; read -p "Press Enter to continue..." ;;
            8) allow_host; read -p "Press Enter to continue..." ;;
            9) create_default_admin; read -p "Press Enter to continue..." ;;
            10) full_backup; read -p "Press Enter to continue..." ;;
            11) chmod 775 "$PROJECT_DIR" && chmod 664 "$PROJECT_DIR/db.sqlite3" && print_success "Permissions fixed!"; restart_passenger; read -p "Press Enter to continue..." ;;
            12) view_logs; read -p "Press Enter to continue..." ;;
            13) setup_email_settings; read -p "Press Enter to continue..." ;;
            14) test_email_settings; read -p "Press Enter to continue..." ;;
            15) setup_db_settings; read -p "Press Enter to continue..." ;;
            16) auto_config_online; read -p "Press Enter to continue..." ;;
            17) fix_messaging_platform; read -p "Press Enter to continue..." ;;
            0) echo "Goodbye!"; exit 0 ;;
            *) print_error "Invalid option"; read -p "Press Enter..." ;;
        esac
    done
else
    case "$1" in
        deploy) full_deploy ;;
        install) install_deps ;;
        migrate) update_db ;;
        static) collect_static ;;
        restart) restart_passenger ;;
        start_servers) start_all_servers ;;
        allow_host) allow_host ;;
        superuser) create_superuser ;;
        default_admin) create_default_admin ;;
        backup) full_backup ;;
        fix_perms) chmod 775 "$PROJECT_DIR" && chmod 664 "$PROJECT_DIR/db.sqlite3" && restart_passenger ;;
        logs) view_logs ;;
        email_config|smtp) setup_email_settings ;;
        test_email) test_email_settings ;;
        db_config|database) setup_db_settings ;;
        auto_config|online_config|auto_setup) auto_config_online ;;
        fix_messaging|messaging_doctor|messenger_fix) fix_messaging_platform ;;
        *) echo "Usage: ./manage_cpanel.sh [deploy|install|migrate|static|restart|start_servers|allow_host|superuser|default_admin|backup|fix_perms|logs|email_config|test_email|db_config|auto_config|fix_messaging]" ;;
    esac
fi
