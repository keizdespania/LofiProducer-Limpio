#!/data/data/com.termux/files/usr/bin/bash
# Monitoriza el kernel worker-real-v10 y notifica cuando termine.
cd ~/LofiProducer

python3 -c "
import sys, json, urllib.request, urllib.parse
sys.path.insert(0, 'scripts')
from kaggle_light import _leer_token

token = _leer_token()
params = urllib.parse.urlencode({'userName': 'keizproductions', 'kernelSlug': 'worker-real-v10'})
url = f'https://www.kaggle.com/api/v1/kernels/status?{params}'
req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Accept', 'application/json')

try:
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
        print(data.get('status'))
except Exception:
    print('error')
" > data/kaggle_estado.txt 2>/dev/null

ESTADO=$(cat data/kaggle_estado.txt)

if [ "$ESTADO" = "complete" ]; then
    termux-notification -t "🎵 Canción lista" -c "El pipeline de Kaggle ha terminado. Haz git pull para traerla." --id kaggle_done
    exit 0
elif [ "$ESTADO" = "error" ]; then
    termux-notification -t "❌ Pipeline falló" -c "El kernel de Kaggle ha dado error. Revisa el log." --id kaggle_error
    exit 0
fi
