"""
Extrae o inyecta Audio Codes (tokens semánticos) de ACE-Step.
"""
import sys
import json
import requests
from pathlib import Path

def extraer_codigos(url_gradio: str, ruta_audio_local: str):
    """Sube un audio local a Gradio y extrae sus audio codes."""
    print(f"Extrayendo audio codes de {ruta_audio_local}...")
    
    # 1. Subir el audio a Gradio
    with open(ruta_audio_local, 'rb') as f:
        files = {'files': f}
        r = requests.post(f"{url_gradio}/upload", files=files, timeout=60)
    
    if r.status_code != 200:
        return f"ERROR subiendo audio: {r.status_code} {r.text[:200]}"
    
    ruta_remota = r.json()[0]
    print(f"Audio subido a: {ruta_remota}")
    
    # 2. Llamar al endpoint de extracción de códigos
    # (El endpoint exacto depende de la versión de ACE-Step, probamos con /audio2code)
    payload = {"data": [ruta_remota]}
    r2 = requests.post(f"{url_gradio}/gradio_api/call/audio2code", json=payload, timeout=120)
    
    if r2.status_code != 200:
        return f"ERROR extrayendo códigos: {r2.status_code} {r2.text[:200]}"
    
    event_id = r2.json().get("event_id")
    print(f"Esperando resultado (Event ID: {event_id})...")
    
    # 3. Leer el stream de resultados
    stream_url = f"{url_gradio}/gradio_api/call/audio2code/{event_id}"
    with requests.get(stream_url, stream=True, timeout=300) as stream:
        for line in stream.iter_lines():
            if not line: continue
            texto = line.decode('utf-8')
            if texto.startswith("data: "):
                data = texto[6:]
                try:
                    resultado = json.loads(data)
                    # Buscar los códigos en el resultado
                    if "audio_codes" in str(resultado):
                        return f"OK: Codigos extraidos: {str(resultado)[:500]}"
                except:
                    pass
    return "ERROR: No se obtuvieron codigos."

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/audio_codes.py 'URL_GRADIO' 'ruta/audio.mp3'")
        sys.exit(1)
    print(extraer_codigos(sys.argv[1], sys.argv[2]))
