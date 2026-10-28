#!/data/data/com.termux/files/usr/bin/sh
# Vigilante: si la web no responde, la arranca en segundo plano.
cd /data/data/com.termux/files/home/LofiProducer

# Comprobar si el puerto 8080 está escuchando
if ! curl -s http://localhost:8080 > /dev/null; then
    # Si no está vivo, lo arrancamos de forma invisible
    nohup python web_dashboard.py > data/logs/web_daemon.log 2>&1 &
fi
