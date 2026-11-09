#!/usr/bin/env bash
# WorkTrack Pro - the normal steps after new code is in place (used by install.sh and worktrack-update.sh):
# Python dependencies, database migrations (as the app user, who owns the database), static files.
# Needs: APP_DIR, VENV_DIR, ENV_FILE, APP_USER.
set -euo pipefail
: "${APP_DIR:?}" "${VENV_DIR:?}" "${ENV_FILE:?}" "${APP_USER:?}"

set -a
# shellcheck source=/dev/null
. "$ENV_FILE"
set +a

"$VENV_DIR/bin/pip" install --quiet --disable-pip-version-check -r "$APP_DIR/requirements.txt"
cd "$APP_DIR"
runuser -u "$APP_USER" -- env PATH="$VENV_DIR/bin:$PATH" "$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py collectstatic --noinput >/dev/null
chmod -R a+rX "$APP_DIR"
