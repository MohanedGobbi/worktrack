#!/usr/bin/env bash
# End-to-end test of deploy/linux/worktrack-update.sh in a throwaway Ubuntu container:
#   docker run --rm -v "$PWD":/src:ro ubuntu:24.04 bash /src/deploy/linux/tests/run_updater_tests.sh
# The project's own updater, backup and update-steps scripts run for real. Stubbed: systemctl (it starts a fake app
# that answers /healthz/ with the version in APP/version.json, or HTTP 500 when the package contains BROKEN),
# the virtualenv (pip is a no-op; "manage.py migrate" writes a row into the SQLite database, so a rollback must
# restore it), and GitHub (deploy/linux/tests/fake_github.py on 127.0.0.1:9999).
set -uo pipefail
SRC=/src
PASS=0; FAIL=0
ok()   { echo "PASS  $*"; PASS=$((PASS + 1)); }
bad()  { echo "FAIL  $*"; FAIL=$((FAIL + 1)); sed 's/^/      | /' /tmp/run.log | tail -n 8; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

echo "== setting up the container"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq >/dev/null && apt-get install -y -qq python3 curl util-linux ca-certificates >/dev/null || { echo "apt failed"; exit 1; }
useradd --system worktrack 2>/dev/null || true

APP=/opt/worktrack/app; VENV=/opt/worktrack/venv; DATA=/var/lib/worktrack; GH=/tmp/gh
mkdir -p /opt/worktrack "$DATA" /etc/worktrack /var/log/worktrack "$GH/releases" /run/lock /etc/systemd/system
install -d -o worktrack -g worktrack "$DATA/update-request" "$DATA/media"
echo "photo" > "$DATA/media/upload.txt"

# Database the fake migrations write into.
python3 - <<'PY'
import sqlite3
c = sqlite3.connect('/var/lib/worktrack/db.sqlite3')
c.execute('create table migrations_log (version text)')
c.execute("insert into migrations_log values ('1.0.0')")
c.commit()
PY
chown worktrack:worktrack "$DATA" "$DATA/db.sqlite3"

# Stub virtualenv.
mkdir -p "$VENV/bin"
printf '#!/bin/sh\nexit 0\n' > "$VENV/bin/pip"
cat > "$VENV/bin/python" <<'PY'
#!/usr/bin/env python3
import json, sqlite3, sys, os
args = sys.argv[1:]
if 'migrate' in args:
    v = json.load(open('version.json'))['version']
    c = sqlite3.connect('/var/lib/worktrack/db.sqlite3'); c.execute('insert into migrations_log values (?)', (v,)); c.commit()
sys.exit(0)
PY
chmod +x "$VENV/bin/pip" "$VENV/bin/python"
touch "$VENV/KEEP_ME"
echo "ENV_MARKER=1" > /etc/worktrack/worktrack.env

# Stub systemctl: restart/start of the app runs a fake app server; everything else is logged.
cat > /usr/local/bin/systemctl <<'SH'
#!/bin/bash
echo "systemctl $*" >> /tmp/systemctl.log
case "$1 $2" in
  "restart worktrack"|"start worktrack")
    pkill -f fake_app.py 2>/dev/null; sleep 0.3
    nohup python3 /tmp/fake_app.py >/dev/null 2>&1 &
    ;;
  "stop worktrack") pkill -f fake_app.py 2>/dev/null ;;
esac
exit 0
SH
chmod +x /usr/local/bin/systemctl
cat > /tmp/fake_app.py <<'PY'
import json, os
from http.server import BaseHTTPRequestHandler, HTTPServer
APP = '/opt/worktrack/app'
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        broken = os.path.exists(f'{APP}/BROKEN')
        v = json.load(open(f'{APP}/version.json'))['version']
        body = json.dumps({'status': 'ok', 'version': v}).encode()
        self.send_response(500 if broken else 200); self.end_headers(); self.wfile.write(b'{}' if broken else body)
HTTPServer(('127.0.0.1', 8000), H).serve_forever()
PY

# Package builder: real deploy scripts + version.json (+ BROKEN marker for a release that fails its health check).
make_pkg() {  # make_pkg VERSION [broken|badsum]
    local v="$1" mode="${2:-}" b; b="$(mktemp -d)"
    mkdir -p "$b/worktrack/deploy"
    cp -r "$SRC/deploy/linux" "$b/worktrack/deploy/linux"
    echo "{\"version\": \"$v\", \"commit\": \"test\", \"build_date\": \"now\"}" > "$b/worktrack/version.json"
    echo "Django" > "$b/worktrack/requirements.txt"
    echo "print('manage')" > "$b/worktrack/manage.py"
    [ "$mode" = broken ] && touch "$b/worktrack/BROKEN"
    mkdir -p "$GH/releases/v$v"
    tar -czf "$GH/releases/v$v/worktrack-$v.tar.gz" -C "$b" worktrack
    ( cd "$GH/releases/v$v" && sha256sum "worktrack-$v.tar.gz" > SHA256SUMS )
    [ "$mode" = badsum ] && sed -i 's/^./0/' "$GH/releases/v$v/SHA256SUMS"
    rm -rf "$b"
}
release() { echo "v$1" > "$GH/latest"; }

# Installed version 1.0.0.
make_pkg 1.0.0
tar -xzf "$GH/releases/v1.0.0/worktrack-1.0.0.tar.gz" -C /opt/worktrack && mv /opt/worktrack/worktrack "$APP"
systemctl start worktrack

cat > /etc/worktrack/updater.conf <<EOF
REPO=owner/worktrack
TOKEN=test-token
API_BASE=http://127.0.0.1:9999
APP_DIR=$APP
VENV_DIR=$VENV
DATA_DIR=$DATA
BACKUP_DIR=/var/backups/worktrack
STATUS_DIR=$DATA/update
REQUEST_DIR=$DATA/update-request
HISTORY_FILE=/var/log/worktrack/update-history.log
ENV_FILE=/etc/worktrack/worktrack.env
APP_USER=worktrack
SERVICE=worktrack
HEALTH_URL=http://127.0.0.1:8000/healthz/
HEALTH_TIMEOUT=10
EOF
chmod 600 /etc/worktrack/updater.conf
python3 "$SRC/deploy/linux/tests/fake_github.py" "$GH" 9999 &
sleep 1

UPDATER="$APP/deploy/linux/worktrack-update.sh"
state()     { python3 -c "import json;print(json.load(open('$DATA/update/status.json'))['state'])"; }
installed() { python3 -c "import json;print(json.load(open('$APP/version.json'))['version'])"; }
dbrows()    { python3 -c "import sqlite3;print(','.join(r[0] for r in sqlite3.connect('$DATA/db.sqlite3').execute('select version from migrations_log')))"; }
run() { bash "$APP/deploy/linux/worktrack-update.sh" > /tmp/run.log 2>&1; echo $? > /tmp/run.rc; }

echo "== 1. same version is a no-op"
release 1.0.0; run
check "same version: state up_to_date" '[ "$(state)" = up_to_date ]'
check "same version: still 1.0.0, no previous copy" '[ "$(installed)" = 1.0.0 ] && [ ! -d $APP.previous ]'
check "status file is 644 and dir 755" '[ "$(stat -c %a $DATA/update/status.json)" = 644 ] && [ "$(stat -c %a $DATA/update)" = 755 ]'

echo "== 2. newer version installs"
make_pkg 1.1.0; release 1.1.0
touch "$DATA/update-request/request"
run
check "newer: state updated" '[ "$(state)" = updated ]'
check "newer: 1.1.0 installed" '[ "$(installed)" = 1.1.0 ]'
check "newer: previous version kept in APP.previous" '[ "$(python3 -c "import json;print(json.load(open(\"$APP.previous/version.json\"))[\"version\"])")" = 1.0.0 ]'
check "newer: virtualenv kept" '[ -f $VENV/KEEP_ME ] && [ -x $VENV/bin/python ]'
check "newer: migrations ran" '[ "$(dbrows)" = 1.0.0,1.1.0 ]'
check "newer: history line written" 'grep -q "updated 1.0.0 -> 1.1.0" /var/log/worktrack/update-history.log'
check "newer: request file consumed" '[ ! -e $DATA/update-request/request ]'
check "newer: uploads untouched" '[ -f $DATA/media/upload.txt ]'
check "newer: a backup was taken" 'ls /var/backups/worktrack/*pre-update-1.1.0/db.sqlite3 >/dev/null 2>&1'
check "newer: systemd templates re-applied" '[ -f /etc/systemd/system/worktrack-update.path ]'

echo "== 3. broken release rolls back code AND database"
make_pkg 1.2.0 broken; release 1.2.0; run
check "broken: state failed" '[ "$(state)" = failed ]'
check "broken: code back on 1.1.0" '[ "$(installed)" = 1.1.0 ]'
check "broken: database restored (no 1.2.0 migration row)" '[ "$(dbrows)" = 1.0.0,1.1.0 ]'
check "broken: broken copy kept in APP.failed" '[ -f $APP.failed/BROKEN ]'
check "broken: version recorded as failed" '[ "$(cat $DATA/update/failed_version)" = 1.2.0 ]'
check "broken: app answering again on 1.1.0" 'curl -fsS http://127.0.0.1:8000/healthz/ | grep -q 1.1.0'

echo "== 4. failed version is skipped, no retry loop"
run
check "skip: state skipped" '[ "$(state)" = skipped ]'
check "skip: nothing changed" '[ "$(installed)" = 1.1.0 ] && [ "$(dbrows)" = 1.0.0,1.1.0 ]'

echo "== 5. damaged checksum is refused"
make_pkg 1.3.0 badsum; release 1.3.0; run
check "checksum: state error" '[ "$(state)" = error ]'
check "checksum: message says so" 'grep -q "Checksum mismatch" $DATA/update/status.json'
check "checksum: still on 1.1.0" '[ "$(installed)" = 1.1.0 ]'

echo "== 6. a second concurrent run steps aside"
make_pkg 1.4.0; release 1.4.0
( exec 8>/run/lock/worktrack-update.lock; flock 8; sleep 4 ) &
HOLDER=$!
sleep 1
before="$(cat $DATA/update/status.json)"
run
check "concurrent: exits cleanly" '[ "$(cat /tmp/run.rc)" = 0 ]'
check "concurrent: says it steps aside" 'grep -q "stepping aside" /tmp/run.log'
check "concurrent: did nothing" '[ "$(cat $DATA/update/status.json)" = "$before" ] && [ "$(installed)" = 1.1.0 ]'
wait "$HOLDER"

echo "== 7. a later good release installs"
run
check "later: state updated" '[ "$(state)" = updated ]'
check "later: 1.4.0 installed" '[ "$(installed)" = 1.4.0 ]'
check "later: failed-version marker cleared" '[ ! -f $DATA/update/failed_version ]'
check "later: migrations ran once more" '[ "$(dbrows)" = 1.0.0,1.1.0,1.4.0 ]'

echo
echo "RESULT: $PASS passed, $FAIL failed"
[ "$FAIL" = 0 ]
