#!/data/data/com.termux/files/usr/bin/bash
cd ~/LofiProducer || exit 1

PENDIENTES="data/accesos_pendientes.json"

if [ -f "$PENDIENTES" ]; then
    IPS=$(python3 -c "
import json
try:
    data = json.load(open('$PENDIENTES'))
    for ip in data.get('ips', []):
        print(ip)
except:
    pass
")
    
    if [ -n "$IPS" ]; then
        echo "$IPS" | while read -r IP; do
            termux-notification \
                -t "🚨 Intento de acceso a la web" \
                -c "IP: $IP. ¿Permitir acceso?" \
                --button1 "Aprobar" \
                --button1-action "termux-open-url http://127.0.0.1:8001/aprobar/$IP" \
                --id "acceso_$IP"
        done
    fi
fi
