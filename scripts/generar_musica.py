import requests
import json
import sys
import re

def main():
    if len(sys.argv) < 3:
        print("Uso: python scripts/generar_musica.py 'URL' 'Prompt' ['Letra'] [Duracion_seg]")
        return

    url_base = sys.argv[1].rstrip("/")
    prompt = sys.argv[2]
    letra = sys.argv[3] if len(sys.argv) > 3 else ""
    duracion = int(sys.argv[4]) if len(sys.argv) > 4 else 30

    print(f"Conectando a {url_base}...")
    try:
        r_config = requests.get(f"{url_base}/config", timeout=30)
        config = r_config.json()
    except Exception as e:
        print(f"❌ Error al leer config: {e}")
        return

    defaults = {}
    for comp in config.get("components", []):
        defaults[comp.get("id")] = comp.get("props", {}).get("value", None)

    inputs_ids = []
    for dep in config.get("dependencies", []):
        if dep.get("api_name") == "generation_wrapper":
            inputs_ids = dep.get("inputs", [])
            break

    data = [defaults.get(comp_id, None) for comp_id in inputs_ids]
    
    if len(data) > 0: data[0] = prompt
    if len(data) > 1: data[1] = letra
    if len(data) > 11: data[11] = duracion
    if len(data) > 6: data[6] = 12 # Aumentamos pasos para mejor calidad

    endpoint = f"{url_base}/gradio_api/call/generation_wrapper"
    print("Enviando petición a la GPU...")
    r = requests.post(endpoint, json={"data": data}, timeout=30)
    if r.status_code != 200:
        print(f"❌ Error HTTP {r.status_code}")
        return

    event_id = r.json().get("event_id")
    print(f"✅ Aceptada. Esperando generación (esto puede tardar varios minutos)...")
    
    stream_url = f"{url_base}/gradio_api/call/generation_wrapper/{event_id}"
    evento_actual = None

    with requests.get(stream_url, stream=True, timeout=900) as stream:
        for line in stream.iter_lines():
            if not line: continue
            texto = line.decode('utf-8')
            if texto.startswith("event: "):
                evento_actual = texto[7:]
            elif texto.startswith("data: ") and evento_actual != "heartbeat":
                payload_str = texto[6:]
                if evento_actual == "complete":
                    match = re.search(r'([a-zA-Z0-9_/.-]+\.(mp3|wav))', payload_str)
                    if match:
                        ruta_kaggle = match.group(1)
                        url_archivo = f"{url_base}/gradio_api/file={ruta_kaggle}"
                        r_file = requests.get(url_archivo, timeout=60)
                        if r_file.status_code == 200:
                            with open("output/cancion_generada.mp3", "wb") as f:
                                f.write(r_file.content)
                            print("✅ ¡Canción descargada en output/cancion_generada.mp3!")
                        else:
                            print(f"❌ Error al descargar: HTTP {r_file.status_code}")
                    break

if __name__ == "__main__":
    main()
