#!/usr/bin/env bash
# WorkTrack Pro - nightly updater (runs as root from worktrack-update.service; started by the timer or by the
# "Check for updates now" button through worktrack-update.path).
#
# Installs the latest published GitHub release when it is newer than the installed version:
#   check -> download + verify SHA256 -> version inside package must match the tag -> backup (db + uploads)
#   -> swap folders (APP.new -> APP, old APP -> APP.previous) -> pip/migrate/static -> restart -> health check
#   -> on failure: restore code AND database, restart, keep APP.failed, remember the version so it is skipped.
# Settings: /etc/worktrack/updater.conf (root only). Progress: STATUS_DIR/status.json (read by the admin panel).
#
# The whole body sits in main(), called on the last line: bash reads the file while running and this script moves
# its own folder, so nothing may run before the full file has been read.

CONFIG_FILE="${WORKTRACK_UPDATER_CONFIG:-/etc/worktrack/updater.conf}"

log() { echo "[worktrack-update] $*"; }

json_get() {  # json_get FILE KEY  -> value of a top-level key ('' if missing)
    python3 - "$1" "$2" <<'PY'
import json, sys
try:
    data = json.load(open(sys.argv[1], encoding='utf-8'))
    value = data.get(sys.argv[2], '') if isinstance(data, dict) else ''
    print(value if isinstance(value, (str, int, float)) else '')
except Exception:
    print('')
PY
}

asset_id() {  # asset_id RELEASE_JSON NAME -> numeric id of that release asset ('' if missing)
    python3 - "$1" "$2" <<'PY'
import json, sys
try:
    for a in json.load(open(sys.argv[1], encoding='utf-8')).get('assets', []):
        if a.get('name') == sys.argv[2]:
            print(a.get('id', ''))
            break
except Exception:
    pass
PY
}

write_status() {  # write_status STATE INSTALLED LATEST MESSAGE  (atomic: temp file then mv; 644)
    local tmp
    tmp="$(mktemp "$STATUS_DIR/.status.XXXXXX")" || return 0
    python3 - "$1" "$2" "$3" "$4" > "$tmp" <<'PY'
import json, sys, datetime
state, installed, latest, message = sys.argv[1:5]
print(json.dumps({'state': state, 'installed': installed, 'latest': latest, 'message': message,
                  'timestamp': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}))
PY
    chmod 644 "$tmp"
    mv -f "$tmp" "$STATUS_DIR/status.json"
    log "$1: $4"
}

history() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" >> "$HISTORY_FILE"; }

installed_version() {
    local v=""
    [ -f "$APP_DIR/version.json" ] && v="$(json_get "$APP_DIR/version.json" version)"
    [ -z "$v" ] && [ -f "$APP_DIR/VERSION" ] && v="$(tr -d '[:space:]' < "$APP_DIR/VERSION")"
    echo "${v:-0.0.0}"
}

is_newer() {  # is_newer A B -> true when A > B
    [ "$1" != "$2" ] && [ "$(printf '%s\n%s\n' "$1" "$2" | sort -V | tail -n1)" = "$1" ]
}

api_get() {  # api_get URL OUTFILE [ACCEPT]
    local accept="${3:-application/vnd.github+json}"
    local auth=()
    [ -n "$TOKEN" ] && auth=(-H "Authorization: Bearer $TOKEN")
    curl -fsSL --retry 2 --connect-timeout 20 --max-time 600 -H "Accept: $accept" \
        -H "X-GitHub-Api-Version: 2022-11-28" "${auth[@]}" -o "$2" "$1"
}

health_ok() {  # the new code answers on HEALTH_URL with the expected version
    local body
    body="$(curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null)" || return 1
    python3 - "$1" "$body" <<'PY'
import json, sys
try:
    data = json.loads(sys.argv[2])
    sys.exit(0 if data.get('status') == 'ok' and (not sys.argv[1] or data.get('version') == sys.argv[1]) else 1)
except Exception:
    sys.exit(1)
PY
}

wait_healthy() {  # wait_healthy VERSION -> up to HEALTH_TIMEOUT seconds
    local waited=0
    while [ "$waited" -lt "$HEALTH_TIMEOUT" ]; do
        health_ok "$1" && return 0
        sleep 2
        waited=$((waited + 2))
    done
    return 1
}

apply_templates() {  # apply_templates APP_FOLDER: systemd units and the nginx site, from that version of the code
    local src="$1/deploy/linux" changed=0 f name
    for f in "$src"/systemd/*.service "$src"/systemd/*.timer "$src"/systemd/*.path; do
        [ -f "$f" ] || continue
        name="$(basename "$f")"
        if ! cmp -s "$f" "$SYSTEMD_DIR/$name"; then
            install -m 644 "$f" "$SYSTEMD_DIR/$name"
            changed=1
        fi
    done
    [ "$changed" = 1 ] && systemctl daemon-reload 9>&-
    if [ -f "$src/nginx/worktrack.conf" ] && [ -f "$INSTALL_CONF" ] && command -v nginx >/dev/null 2>&1; then
        local domain rendered
        domain="$(grep -E '^DOMAIN=' "$INSTALL_CONF" | head -n1 | cut -d= -f2-)"
        rendered="$(mktemp)"
        sed "s|__DOMAIN__|${domain:-_}|g" "$src/nginx/worktrack.conf" > "$rendered"
        if ! cmp -s "$rendered" "$NGINX_SITE"; then
            cp -f "$NGINX_SITE" "$NGINX_SITE.bak" 2>/dev/null || true
            install -m 644 "$rendered" "$NGINX_SITE"
            if nginx -t >/dev/null 2>&1; then
                systemctl reload nginx 9>&-
            else
                log "New nginx template does not pass nginx -t; keeping the previous one"
                [ -f "$NGINX_SITE.bak" ] && mv -f "$NGINX_SITE.bak" "$NGINX_SITE"
            fi
        fi
        rm -f "$rendered"
    fi
}

run_update_steps() {  # the project's normal update steps, from the new code
    APP_DIR="$APP_DIR" VENV_DIR="$VENV_DIR" ENV_FILE="$ENV_FILE" APP_USER="$APP_USER" \
        bash "$APP_DIR/deploy/linux/update_steps.sh"
}

rollback() {  # rollback BACKUP_PATH LATEST INSTALLED REASON
    local backup="$1" latest="$2" installed="$3" reason="$4"
    log "Rolling back: $reason"
    systemctl stop "$SERVICE" 9>&- || true
    rm -rf "$APP_DIR.failed"
    mv "$APP_DIR" "$APP_DIR.failed"
    mv "$APP_DIR.previous" "$APP_DIR"
    # Migrations may already have changed the database: restore the copy taken just before.
    DATA_DIR="$DATA_DIR" BACKUP_DIR="$BACKUP_DIR" APP_USER="$APP_USER" \
        bash "$APP_DIR/deploy/linux/backup.sh" --restore "$backup" || log "Database restore reported a problem"
    apply_templates "$APP_DIR"
    systemctl restart "$SERVICE" 9>&- || true
    if wait_healthy "$installed"; then reason="$reason; back on $installed"; else reason="$reason; previous version restored but not answering yet"; fi
    echo "$latest" > "$FAILED_FILE"
    write_status failed "$installed" "$latest" "$reason"
    history "failed $installed -> $latest ($reason)"
}

main() {
    REPO=""; TOKEN=""; API_BASE="https://api.github.com"
    APP_DIR=/opt/worktrack/app; VENV_DIR=/opt/worktrack/venv; DATA_DIR=/var/lib/worktrack
    BACKUP_DIR=/var/backups/worktrack; STATUS_DIR=/var/lib/worktrack/update; REQUEST_DIR=/var/lib/worktrack/update-request
    HISTORY_FILE=/var/log/worktrack/update-history.log; ENV_FILE=/etc/worktrack/worktrack.env; APP_USER=worktrack
    SERVICE=worktrack; HEALTH_URL=http://127.0.0.1:8000/healthz/; HEALTH_TIMEOUT=60
    LOCK_FILE=/run/lock/worktrack-update.lock; SYSTEMD_DIR=/etc/systemd/system
    NGINX_SITE=/etc/nginx/sites-available/worktrack; INSTALL_CONF=/etc/worktrack/install.conf
    HTTPS_PROXY="${HTTPS_PROXY:-}"

    if [ ! -r "$CONFIG_FILE" ]; then log "No config at $CONFIG_FILE; automatic updates are not set up."; return 1; fi
    # shellcheck source=/dev/null
    . "$CONFIG_FILE"
    [ -n "$HTTPS_PROXY" ] && export HTTPS_PROXY HTTP_PROXY="${HTTP_PROXY:-$HTTPS_PROXY}"
    FAILED_FILE="$STATUS_DIR/failed_version"
    mkdir -p "$STATUS_DIR" "$(dirname "$HISTORY_FILE")" "$BACKUP_DIR" "$(dirname "$LOCK_FILE")"
    chmod 755 "$STATUS_DIR"

    exec 9>"$LOCK_FILE"
    if ! flock -n 9; then
        log "Another update run is in progress; stepping aside."
        return 0
    fi
    rm -f "$REQUEST_DIR/request"

    local installed latest tag pkg work backup reason
    installed="$(installed_version)"
    write_status checking "$installed" "" "Looking for a new release"
    if [ -z "$REPO" ]; then write_status error "$installed" "" "REPO is not set in $CONFIG_FILE"; return 1; fi

    work="$(mktemp -d)"
    trap 'rm -rf "$work"' RETURN

    if ! api_get "$API_BASE/repos/$REPO/releases/latest" "$work/release.json"; then
        write_status error "$installed" "" "Could not read the latest release from GitHub (no release published yet, or network, token or repository name)"
        return 1
    fi
    tag="$(json_get "$work/release.json" tag_name)"
    latest="${tag#v}"
    if ! [[ "$latest" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        write_status error "$installed" "" "The latest release tag '$tag' is not vX.Y.Z"
        return 1
    fi
    if [ -f "$FAILED_FILE" ] && [ "$(cat "$FAILED_FILE")" = "$latest" ]; then
        write_status skipped "$installed" "$latest" "Version $latest failed before; waiting for a newer release"
        return 0
    fi
    if ! is_newer "$latest" "$installed"; then
        write_status up_to_date "$installed" "$latest" "Already on the latest release"
        return 0
    fi

    write_status downloading "$installed" "$latest" "Downloading $latest"
    pkg="worktrack-$latest.tar.gz"
    local pkg_id sums_id
    pkg_id="$(asset_id "$work/release.json" "$pkg")"
    sums_id="$(asset_id "$work/release.json" SHA256SUMS)"
    if [ -z "$pkg_id" ] || [ -z "$sums_id" ]; then
        write_status error "$installed" "$latest" "Release $tag is missing $pkg or SHA256SUMS"
        return 1
    fi
    if ! api_get "$API_BASE/repos/$REPO/releases/assets/$pkg_id" "$work/$pkg" application/octet-stream \
       || ! api_get "$API_BASE/repos/$REPO/releases/assets/$sums_id" "$work/SHA256SUMS" application/octet-stream; then
        write_status error "$installed" "$latest" "Download of $tag failed"
        return 1
    fi
    if ! ( cd "$work" && grep -E "  $pkg\$" SHA256SUMS > sums.one && sha256sum -c --status sums.one ); then
        write_status error "$installed" "$latest" "Checksum mismatch for $pkg: package refused"
        history "refused $latest (checksum mismatch)"
        return 1
    fi
    rm -rf "$APP_DIR.new" "$work/unpack"
    mkdir -p "$work/unpack"
    if ! tar -xzf "$work/$pkg" -C "$work/unpack" || [ ! -d "$work/unpack/worktrack" ]; then
        write_status error "$installed" "$latest" "Package $pkg could not be unpacked"
        return 1
    fi
    if [ "$(json_get "$work/unpack/worktrack/version.json" version)" != "$latest" ]; then
        write_status error "$installed" "$latest" "Package version does not match the release tag $tag: refused"
        return 1
    fi
    mv "$work/unpack/worktrack" "$APP_DIR.new"

    write_status installing "$installed" "$latest" "Backing up and installing $latest"
    if ! backup="$(DATA_DIR="$DATA_DIR" BACKUP_DIR="$BACKUP_DIR" APP_USER="$APP_USER" \
                   bash "$APP_DIR/deploy/linux/backup.sh" --label "pre-update-$latest")"; then
        rm -rf "$APP_DIR.new"
        write_status error "$installed" "$latest" "Backup failed; nothing was changed"
        return 1
    fi
    log "Backup: $backup"

    rm -rf "$APP_DIR.previous"
    mv "$APP_DIR" "$APP_DIR.previous"
    mv "$APP_DIR.new" "$APP_DIR"
    chmod -R a+rX "$APP_DIR"

    if ! run_update_steps; then
        rollback "$backup" "$latest" "$installed" "Update steps (dependencies, migrations, static files) failed"
        return 1
    fi
    apply_templates "$APP_DIR"
    systemctl restart "$SERVICE" 9>&- || true
    if ! wait_healthy "$latest"; then
        rollback "$backup" "$latest" "$installed" "Version $latest did not answer the health check within ${HEALTH_TIMEOUT}s"
        return 1
    fi
    rm -f "$FAILED_FILE"
    write_status updated "$latest" "$latest" "Updated from $installed"
    history "updated $installed -> $latest (backup $backup)"
    return 0
}

main "$@"
