#!/usr/bin/env bash
set -euo pipefail
SRC_WEB="$HOME/LofiProducer/web"
CLEAN_REPO="$HOME/lofiproducer-limpio"
ENV_FILE="$HOME/LofiProducer/.env"
TMP_SITE="$HOME/temp/site_build"
[ -f "$ENV_FILE" ] && { set -a; source "$ENV_FILE"; set +a; }
cd "$SRC_WEB" && python3 -u scripts/sync_langs.py --only-missing-or-fallback
rsync -a --delete --exclude '.git' --exclude 'site' "$SRC_WEB/" "$CLEAN_REPO/"
mkdocs build -f "$CLEAN_REPO/mkdocs.yml" -d "$TMP_SITE" && rm -rf "$TMP_SITE"
git -C "$CLEAN_REPO" add -A
git -C "$CLEAN_REPO" diff --cached --quiet || { git -C "$CLEAN_REPO" commit -m "Auto sync y build web" && git -C "$CLEAN_REPO" push; }
