#!/usr/bin/env bash
set -euo pipefail

WEB_DIR="/data/data/com.termux/files/home/LofiProducer/web"
ENV_FILE="/data/data/com.termux/files/home/LofiProducer/.env"
OUT_DIR="${1:-$WEB_DIR/site}"

if [ -f "$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

cd "$WEB_DIR"
python3 -u scripts/sync_langs.py --only-missing-or-fallback
mkdocs build -d "$OUT_DIR"
