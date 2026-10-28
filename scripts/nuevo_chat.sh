#!/data/data/com.termux/files/usr/bin/bash
# Cajon 101.D - Copia al portapapeles el paquete de arranque para un chat nuevo.
# Uso: ./scripts/nuevo_chat.sh

set -eu

REPO="$HOME/LofiProducer"
cd "$REPO"

OUT=$(
  cat BOOT_PROMPT.md
  echo
  echo "═══ ULTIMOS COMMITS ═══"
  git log --oneline -5 2>/dev/null || echo "(sin commits)"
  echo
  echo "═══ ESTADO ACTUAL ═══"
  git status --short 2>/dev/null | head -15 || true
  echo
  echo "═══ ULTIMOS CAMBIOS AUTO (AUTO_CHANGELOG.md, ultimos 2 bloques) ═══"
  if [ -f AUTO_CHANGELOG.md ]; then
    awk 'BEGIN{RS="### "; ORS=""} NR>2 {print "### "$0}' AUTO_CHANGELOG.md | tail -40
  else
    echo "(AUTO_CHANGELOG.md aún no generado)"
  fi
)

# Imprimir en stdout
printf '%s\n' "$OUT"

# Intentar copiar al portapapeles si termux-api esta disponible
if command -v termux-clipboard-set >/dev/null 2>&1; then
  printf '%s' "$OUT" | termux-clipboard-set
  echo
  echo "─────────────────────────────────────────────"
  echo "✅ Copiado al portapapeles. Pega en el chat nuevo."
else
  echo
  echo "─────────────────────────────────────────────"
  echo "ℹ️  termux-api no instalado. Instala Termux:API desde F-Droid y"
  echo "    ejecuta 'pkg install termux-api' para copiar automáticamente."
fi
