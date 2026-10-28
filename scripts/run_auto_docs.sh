#!/data/data/com.termux/files/usr/bin/bash
# Wrapper para termux-job-scheduler. Ejecuta auto_docs.py cada 15 min.
# Lock para evitar solapamientos. Log rotativo basico.

set -u

REPO="$HOME/LofiProducer"
LOG="$REPO/data/logs/auto_docs.log"
LOCK="$REPO/data/.auto_docs.lock"
MAX_LOG_LINES=2000

mkdir -p "$(dirname "$LOG")"
cd "$REPO" || exit 1

# Lock: si ya hay otro proceso corriendo, salir silenciosamente
if [ -f "$LOCK" ]; then
    if kill -0 "$(cat "$LOCK" 2>/dev/null)" 2>/dev/null; then
        echo "$(date -Iseconds) [skip] ya hay otro auto_docs corriendo (PID $(cat "$LOCK"))" >> "$LOG"
        exit 0
    fi
fi
echo $$ > "$LOCK"
trap 'rm -f "$LOCK"' EXIT

# Timestamp de inicio
echo "=== $(date -Iseconds) auto_docs start ===" >> "$LOG"

# Ejecutar
python scripts/auto_docs.py >> "$LOG" 2>&1
RC=$?

echo "=== $(date -Iseconds) auto_docs end (rc=$RC) ===" >> "$LOG"

# Rotacion simple: si el log supera MAX_LOG_LINES, dejar las ultimas 500
LINES=$(wc -l < "$LOG")
if [ "$LINES" -gt "$MAX_LOG_LINES" ]; then
    tail -n 500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

exit $RC
