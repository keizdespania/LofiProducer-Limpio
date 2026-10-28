#!/data/data/com.termux/files/usr/bin/bash
cd ~/LofiProducer || exit 1
# Añadir cambios, commit y push
git add -A
git commit -m "backup(auto): $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
git push origin main 2>/dev/null
