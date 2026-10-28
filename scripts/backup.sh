#!/data/data/com.termux/files/usr/bin/bash
# Backup automatico LofiProducer -> GitHub privado
cd ~/LofiProducer || exit 1
TIMESTAMP=$(date +"%Y-%m-%d_%H:%M")

# 1. Regenerar PROYECTO.md (raiz)
python scripts/generar_docs.py > /dev/null 2>&1

# 2. Regenerar colab/README.md (bloque dinamico)
python scripts/generar_readme_colab.py > /dev/null 2>&1

# 3. Git add + commit + push
git add -A
if git diff --cached --quiet; then
    echo "[$(date)] Sin cambios"
    exit 0
fi
git commit -m "Auto-backup $TIMESTAMP" -q
if git push origin main -q 2>&1; then
    echo "[$(date)] Backup OK -> $TIMESTAMP"
else
    echo "[$(date)] ERROR push fallido"
    exit 1
fi
