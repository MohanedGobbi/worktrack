#!/usr/bin/env bash
# Build the self-contained release package: worktrack-<version>.tar.gz + SHA256SUMS.
#   bash deploy/build_package.sh <version> <output dir>
# Needs the project's Python requirements installed (to run collectstatic). The package carries prebuilt static
# files and version.json (version, commit, build date), so the server needs no build tools.
set -euo pipefail

VERSION="${1:?usage: build_package.sh <version> <output dir>}"
OUT="${2:?usage: build_package.sh <version> <output dir>}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="${PYTHON:-python3}"

if [ "$(tr -d '[:space:]' < "$ROOT/VERSION")" != "$VERSION" ]; then
    echo "VERSION file says $(cat "$ROOT/VERSION"), asked to build $VERSION" >&2
    exit 1
fi

BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT
mkdir -p "$OUT"

# Tracked files only (no local database, uploads, .env or virtualenv).
git -C "$ROOT" archive --format=tar --prefix=worktrack/ HEAD | tar -x -C "$BUILD"
PKG="$BUILD/worktrack"

cat > "$PKG/version.json" <<EOF
{"version": "$VERSION", "commit": "$(git -C "$ROOT" rev-parse HEAD)", "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
EOF

# Prebuilt static files (compressed + manifest), built in production mode with throwaway paths.
( cd "$PKG" && DEBUG=False SECRET_KEY=package-build-only DB_NAME="$BUILD/build.sqlite3" LOG_DIR="$BUILD/logs" \
  CACHE_DIR="$BUILD/cache" "$PYTHON" manage.py collectstatic --noinput >/dev/null )
rm -rf "$PKG/logs" "$PKG/.translation_cache"

NAME="worktrack-$VERSION.tar.gz"
tar -czf "$OUT/$NAME" -C "$BUILD" worktrack
( cd "$OUT" && sha256sum "$NAME" > SHA256SUMS )
echo "Built $OUT/$NAME"
cat "$OUT/SHA256SUMS"
