#!/data/data/com.termux/files/usr/bin/bash
cd ~/LofiProducer || exit 1
python scripts/conserje.py >> data/logs/conserje_cron.log 2>&1
