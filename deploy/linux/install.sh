#!/usr/bin/env bash
# WorkTrack Pro - install or upgrade on Ubuntu/Debian from an unpacked release package (no git needed).
#   sudo bash deploy/linux/install.sh --domain tasks.example.edu [--auto-update OWNER/REPO [--token-file FILE]]
#   sudo bash deploy/linux/install.sh --no-auto-update
# Re-running is safe: existing config (/etc/worktrack/*.env, updater.conf, install.conf) and data are kept.
# Layout: code /opt/worktrack/app, virtualenv /opt/worktrack/venv, data /var/lib/worktrack (db.sqlite3, media,
# update status), config /etc/worktrack, logs /var/log/worktrack, backups /var/backups/worktrack.
set -euo pipefail

APP_USER=worktrack
BASE=/opt/worktrack
APP_DIR=$BASE/app
VENV_DIR=$BASE/venv
DATA_DIR=/var/lib/worktrack
ETC=/etc/worktrack
LOG_DIR=/var/log/worktrack
CACHE_DIR=/var/cache/worktrack
BACKUP_DIR=/var/backups/worktrack
STATUS_DIR=$DATA_DIR/update
REQUEST_DIR=$DATA_DIR/update-request
ENV_FILE=$ETC/worktrack.env
UPDATER_CONF=$ETC/updater.conf
INSTALL_CONF=$ETC/install.conf
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

DOMAIN=""; AUTO=""; REPO=""; TOKEN_FILE=""; ASSUME_YES=0
while [ $# -gt 0 ]; do
    case "$1" in
        --domain) DOMAIN="$2"; shift 2 ;;
        --auto-update) AUTO=on; REPO="$2"; shift 2 ;;
        --token-file) TOKEN_FILE="$2"; shift 2 ;;
        --no-auto-update) AUTO=off; shift ;;
        --yes|-y) ASSUME_YES=1; shift ;;
        -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

say() { echo "==> $*"; }
[ "$(id -u)" = 0 ] || { echo "Run as root (sudo)." >&2; exit 1; }
[ -f "$SRC/manage.py" ] && [ -f "$SRC/requirements.txt" ] || { echo "Run this from an unpacked WorkTrack package." >&2; exit 1; }

say "System packages"
if command -v apt-get >/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq python3 python3-venv python3-pip nginx curl ca-certificates util-linux >/dev/null
fi

say "User and folders"
id "$APP_USER" >/dev/null 2>&1 || useradd --system --home "$DATA_DIR" --shell /usr/sbin/nologin "$APP_USER"
install -d -m 755 "$BASE"
install -d -m 750 -o "$APP_USER" -g "$APP_USER" "$DATA_DIR" "$DATA_DIR/media" "$CACHE_DIR"
install -d -m 755 -o "$APP_USER" -g "$APP_USER" "$LOG_DIR"
install -d -m 750 -o root -g "$APP_USER" "$ETC"
install -d -m 700 "$BACKUP_DIR"
install -d -m 755 "$STATUS_DIR"
chmod 751 "$DATA_DIR"   # the app user owns it; others may only reach update/status.json

# Domain: flag, else what an earlier install recorded, else ask.
[ -z "$DOMAIN" ] && [ -f "$INSTALL_CONF" ] && DOMAIN="$(grep -E '^DOMAIN=' "$INSTALL_CONF" | cut -d= -f2-)"
if [ -z "$DOMAIN" ] && [ -t 0 ] && [ "$ASSUME_YES" = 0 ]; then read -r -p "Domain name for this install (e.g. tasks.example.edu): " DOMAIN; fi
DOMAIN="${DOMAIN:-localhost}"
[ -f "$INSTALL_CONF" ] || printf 'DOMAIN=%s\n' "$DOMAIN" > "$INSTALL_CONF"

say "Code in $APP_DIR"
if [ "$SRC" != "$APP_DIR" ]; then
    rm -rf "$APP_DIR.new"
    cp -a "$SRC" "$APP_DIR.new"
    if [ -d "$APP_DIR" ]; then rm -rf "$APP_DIR.previous"; mv "$APP_DIR" "$APP_DIR.previous"; fi
    mv "$APP_DIR.new" "$APP_DIR"
fi
chown -R root:root "$APP_DIR"
chmod -R a+rX "$APP_DIR"

say "Python environment"
[ -x "$VENV_DIR/bin/python" ] || python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --quiet --upgrade pip

if [ ! -f "$ENV_FILE" ]; then
    say "Writing $ENV_FILE"
    SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
    cat > "$ENV_FILE" <<EOF
SECRET_KEY=$SECRET
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://$DOMAIN,http://$DOMAIN
SITE_URL=https://$DOMAIN
DB_NAME=$DATA_DIR/db.sqlite3
MEDIA_ROOT=$DATA_DIR/media
LOG_DIR=$LOG_DIR
CACHE_DIR=$CACHE_DIR
UPDATE_STATUS_FILE=$STATUS_DIR/status.json
UPDATE_REQUEST_DIR=$REQUEST_DIR
SECURE_COOKIES=False
EOF
fi
chown root:"$APP_USER" "$ENV_FILE"; chmod 640 "$ENV_FILE"
touch "$LOG_DIR/worktrack_pro.log"; chown "$APP_USER":"$APP_USER" "$LOG_DIR/worktrack_pro.log"

say "Dependencies, database, static files"
APP_DIR="$APP_DIR" VENV_DIR="$VENV_DIR" ENV_FILE="$ENV_FILE" APP_USER="$APP_USER" bash "$APP_DIR/deploy/linux/update_steps.sh"
chown "$APP_USER":"$APP_USER" "$DATA_DIR/db.sqlite3" 2>/dev/null || true
# The app checks Host headers against its own table too: allow this domain.
( set -a; . "$ENV_FILE"; set +a; cd "$APP_DIR"
  runuser -u "$APP_USER" -- env PATH="$VENV_DIR/bin:$PATH" "$VENV_DIR/bin/python" manage.py shell -c \
  "from core.models import AllowedHost; AllowedHost.objects.get_or_create(hostname='$DOMAIN')" >/dev/null )

say "Services"
for f in "$APP_DIR"/deploy/linux/systemd/*; do install -m 644 "$f" /etc/systemd/system/; done
sed "s|__DOMAIN__|$DOMAIN|g" "$APP_DIR/deploy/linux/nginx/worktrack.conf" > /etc/nginx/sites-available/worktrack
ln -sf /etc/nginx/sites-available/worktrack /etc/nginx/sites-enabled/worktrack
rm -f /etc/nginx/sites-enabled/default
systemctl daemon-reload
systemctl enable --now worktrack.service worktrack-backup.timer
systemctl restart worktrack.service
nginx -t && systemctl reload nginx

# ── Automatic updates ──
if [ -z "$AUTO" ]; then
    if [ -f "$UPDATER_CONF" ]; then
        AUTO=keep
    elif [ -t 0 ] && [ "$ASSUME_YES" = 0 ]; then
        read -r -p "Install new versions automatically every night from GitHub? [Y/n] " ans
        case "${ans:-y}" in [Nn]*) AUTO=off ;; *) AUTO=on ;; esac
        if [ "$AUTO" = on ] && [ -z "$REPO" ]; then read -r -p "GitHub repository (owner/name): " REPO; fi
        if [ "$AUTO" = on ] && [ -z "$TOKEN_FILE" ]; then
            read -r -s -p "Read-only token for a private repository (leave empty for a public one): " TOKEN_IN; echo
        fi
    else
        AUTO=keep
    fi
fi

if [ "$AUTO" = on ]; then
    [ -n "$REPO" ] || { echo "--auto-update needs OWNER/REPO" >&2; exit 2; }
    if [ ! -f "$UPDATER_CONF" ]; then
        TOKEN=""
        [ -n "$TOKEN_FILE" ] && TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
        [ -n "${TOKEN_IN:-}" ] && TOKEN="$TOKEN_IN"
        umask 077
        cat > "$UPDATER_CONF" <<EOF
# WorkTrack Pro updater settings (root only). See docs/guides/INSTALL_LINUX.md.
REPO=$REPO
TOKEN=$TOKEN
API_BASE=https://api.github.com
APP_DIR=$APP_DIR
VENV_DIR=$VENV_DIR
DATA_DIR=$DATA_DIR
BACKUP_DIR=$BACKUP_DIR
STATUS_DIR=$STATUS_DIR
REQUEST_DIR=$REQUEST_DIR
HISTORY_FILE=$LOG_DIR/update-history.log
ENV_FILE=$ENV_FILE
APP_USER=$APP_USER
SERVICE=worktrack
HEALTH_URL=http://127.0.0.1:8000/healthz/
HEALTH_TIMEOUT=60
# HTTPS_PROXY=http://proxy.example:3128
EOF
        umask 022
    fi
    chmod 600 "$UPDATER_CONF"
    install -d -m 750 -o "$APP_USER" -g "$APP_USER" "$REQUEST_DIR"
    systemctl enable --now worktrack-update.timer worktrack-update.path
    say "Automatic updates: on (every night ~03:00 from $(grep -E '^REPO=' "$UPDATER_CONF" | cut -d= -f2))"
elif [ "$AUTO" = off ]; then
    systemctl disable --now worktrack-update.timer worktrack-update.path 2>/dev/null || true
    rm -rf "$REQUEST_DIR"
    rm -f "$UPDATER_CONF"
    say "Automatic updates: off"
fi

say "Done. Open http://$DOMAIN/ ; create the first institution with:"
echo "    cd $APP_DIR && sudo -u $APP_USER env \$(cat $ENV_FILE | xargs) $VENV_DIR/bin/python manage.py new_institution --config FILE.json"
