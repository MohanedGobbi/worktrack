#!/usr/bin/env bash
# WorkTrack Pro - backup and restore of the database and uploaded files.
#   backup.sh [--label NAME]      -> makes BACKUP_DIR/<date>-<label>/ (db.sqlite3 + media.tar.gz), prints its path
#   backup.sh --restore DIR       -> puts DIR/db.sqlite3 back (stop the app first; the updater does)
# Settings come from the environment, else /etc/worktrack/updater.conf: DATA_DIR, BACKUP_DIR, APP_USER, KEEP.
# The SQLite copy uses SQLite's online backup, so it is consistent even while the app is running.
set -euo pipefail

CONF="${WORKTRACK_UPDATER_CONFIG:-/etc/worktrack/updater.conf}"
_DATA="${DATA_DIR:-}"; _BACKUP="${BACKUP_DIR:-}"; _USER="${APP_USER:-}"
# shellcheck source=/dev/null
[ -r "$CONF" ] && . "$CONF"
DATA_DIR="${_DATA:-${DATA_DIR:-/var/lib/worktrack}}"
BACKUP_DIR="${_BACKUP:-${BACKUP_DIR:-/var/backups/worktrack}}"
APP_USER="${_USER:-${APP_USER:-worktrack}}"
KEEP="${KEEP:-14}"
DB="$DATA_DIR/db.sqlite3"

copy_sqlite() {  # copy_sqlite FROM TO
    python3 - "$1" "$2" <<'PY'
import sqlite3, sys
src = sqlite3.connect(sys.argv[1])
dst = sqlite3.connect(sys.argv[2])
with dst:
    src.backup(dst)
dst.close(); src.close()
PY
}

if [ "${1:-}" = "--restore" ]; then
    DIR="${2:?usage: backup.sh --restore DIR}"
    [ -f "$DIR/db.sqlite3" ] || { echo "No db.sqlite3 in $DIR" >&2; exit 1; }
    tmp="$DB.restore.$$"
    cp -f "$DIR/db.sqlite3" "$tmp"
    rm -f "$DB-wal" "$DB-shm" "$DB-journal"
    mv -f "$tmp" "$DB"
    chown "$APP_USER":"$APP_USER" "$DB" 2>/dev/null || true
    chmod 660 "$DB" 2>/dev/null || true
    echo "Restored $DB from $DIR" >&2
    exit 0
fi

LABEL="nightly"
[ "${1:-}" = "--label" ] && LABEL="${2:?usage: backup.sh --label NAME}"
LABEL="$(printf '%s' "$LABEL" | tr -c 'A-Za-z0-9._-' '-')"
OUT="$BACKUP_DIR/$(date -u +%Y%m%d-%H%M%S)-$LABEL"
mkdir -p "$OUT"
chmod 700 "$BACKUP_DIR" "$OUT"
if [ -f "$DB" ]; then
    copy_sqlite "$DB" "$OUT/db.sqlite3"
fi
if [ -d "$DATA_DIR/media" ]; then
    tar -czf "$OUT/media.tar.gz" -C "$DATA_DIR" media
fi
# Keep the newest KEEP backups.
ls -1dt "$BACKUP_DIR"/*/ 2>/dev/null | tail -n +"$((KEEP + 1))" | xargs -r rm -rf
echo "$OUT"
