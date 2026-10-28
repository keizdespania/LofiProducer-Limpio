#!/data/data/com.termux/files/usr/bin/bash
PORT=8001
echo "🔪 Buscando y matando procesos en el puerto $PORT..."

# Matar con fuser (el más agresivo)
pkg install psmisc -y > /dev/null 2>&1
fuser -k $PORT/tcp 2>/dev/null

# Matar con lsof por si acaso
if command -v lsof >/dev/null; then
    PIDS=$(lsof -t -i:$PORT)
    if [ -n "$PIDS" ]; then
        kill -9 $PIDS 2>/dev/null
    fi
fi

# Matar cualquier proceso de Flask que se haya quedado huérfano
pkill -9 -f "web_dashboard.py" 2>/dev/null
pkill -9 -f "flask" 2>/dev/null

# Esperar a que Android libere el socket
echo "⏳ Esperando 6 segundos para que Android libere el puerto..."
sleep 6

# Arrancar el servidor
echo "🚀 Arrancando KeiZ Command Center en el puerto $PORT..."
cd /data/data/com.termux/files/home/LofiProducer
python web_dashboard.py
