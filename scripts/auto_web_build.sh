#!/usr/bin/env bash
set -euo pipefail
LOCK_FILE="$HOME/temp/auto_web_build.lock"
SRC_WEB="$HOME/LofiProducer/web"
CLEAN_REPO="$HOME/lofiproducer-limpio"
ENV_FILE="$HOME/LofiProducer/.env"
TMP_SITE="$HOME/temp/site_build"
LOG_FILE="$HOME/temp/auto_web_build.log"
mkdir -p "$HOME/temp"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0
trap 'rm -rf "$TMP_SITE"' EXIT
[ -f "$ENV_FILE" ] && { set -a; source "$ENV_FILE"; set +a; }
{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  cd "$SRC_WEB" && timeout -k 10 180 python3 -u scripts/sync_langs.py --only-missing-or-fallback || true
  rsync -a --delete --exclude '.git' --exclude 'site' "$SRC_WEB/" "$CLEAN_REPO/"
  mkdocs build -f "$CLEAN_REPO/mkdocs.yml" -d "$TMP_SITE"
  git -C "$CLEAN_REPO" add -A
  git -C "$CLEAN_REPO" diff --cached --quiet || { git -C "$CLEAN_REPO" commit -m "Auto sync y build web" && git -C "$CLEAN_REPO" push; }
} >> "$LOG_FILE" 2>&1
