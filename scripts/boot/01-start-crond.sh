#!/data/data/com.termux/files/usr/bin/sh
# 1. CPU despierta (crítico)
termux-wake-lock

# 2. Crond (si no está ya)
pgrep crond > /dev/null || crond

# 3. Ecosistema completo (OmniRoute + Worker + Flask) en background
cd ~/LofiProducer || exit 1
nohup python3 scripts/start_all.py >> data/logs/boot.log 2>&1 &

# 4. Log de arranque
echo "[$(date)] BOOT: wake-lock + crond + start_all lanzado" >> data/logs/boot.log
