#!/data/data/com.termux/files/usr/bin/bash
# Bucle infinito que comprueba los videos cada 60s
cd ~/LofiProducer || exit 1
while true; do
    python scripts/kaggle_video_checker.py >> data/logs/checker.log 2>&1
    sleep 60
done
