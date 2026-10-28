import sys
import json
import requests
import re
from pathlib import Path

def generar_video(url_base, prompt):
    url_base = url_base.rstrip("/")
    endpoint = f"{url_base}/gradio_api/call/handle_generation"
    
    # Construimos los 15 parámetros con valores seguros para una T4
    payload = {
        "data": [
            prompt,                                                     # 1. Text Prompt
            "blurry, worst quality, low quality, glitch, distortion",   # 2. Negative Prompt
            8,                                                          # 3. Sampling Steps
            "360p (480x360) - Fastest Testing Baseline",                # 4. Dimensions (Exact)
            False,                                                      # 5. Use Custom Resolution
            640,                                                        # 6. Custom Width
            384,                                                        # 7. Custom Height
            3,                                                          # 8. Duration Seconds (3s)
            None,                                                       # 9. Input Image
            False,                                                      # 10. Enable Hi-Res Upscaling
            6.0,                                                        # 11. CFG Scale
            3.5,                                                        # 12. Distilled Guidance Scale
            "default",                                                  # 13. Inference Scheduler (Exact)
            0.0,                                                        # 14. Flow Shift
            True                                                        # 15. Enable VAE Tiling
        ]
    }

    print(f"Enviando petición a Kaggle... (esto puede tardar 2-5 min)")
    try:
        r = requests.post(endpoint, json=payload, timeout=30)
        if r.status_code != 200:
            print(f"❌ Error HTTP {r.status_code}: {r.text[:300]}")
            return

        event_id = r.json().get("event_id")
        print(f"✅ Aceptada. Event ID: {event_id}")
        
        stream_url = f"{url_base}/gradio_api/call/handle_generation/{event_id}"
        print("Esperando a que la T4 genere el vídeo...")
        
        evento_actual = None
        with requests.get(stream_url, stream=True, timeout=900) as stream:
            for line in stream.iter_lines():
                if not line: continue
                texto = line.decode('utf-8')
                
                if texto.startswith("event: "):
                    evento_actual = texto[7:]
                    if evento_actual != "heartbeat":
                        print(f"[{evento_actual.upper()}]")
                        
                elif texto.startswith("data: ") and evento_actual != "heartbeat":
                    payload_str = texto[6:]
                    
                    if evento_actual == "complete":
                        print("✅ ¡Generación completada! Buscando el archivo...")
                        # Buscamos la ruta del mp4 en el JSON
                        match = re.search(r'([a-zA-Z0-9_/.-]+\.(mp4|gif|webm))', payload_str)
                        if match:
                            ruta_kaggle = match.group(1)
                            print(f"🎬 Archivo detectado: {ruta_kaggle}")
                            
                            url_archivo = f"{url_base}/gradio_api/file={ruta_kaggle}"
                            print(f"Descargando desde {url_archivo}...")
                            
                            r_file = requests.get(url_archivo, timeout=60)
                            if r_file.status_code == 200:
                                with open("output/video_generado.mp4", "wb") as f:
                                    f.write(r_file.content)
                                print("✅ ¡Vídeo descargado en output/video_generado.mp4!")
                            else:
                                print(f"❌ Error al descargar: HTTP {r_file.status_code}")
                        else:
                            print("⚠️ No se encontró la ruta del archivo en el JSON.")
                        break
                    else:
                        print(payload_str[:150] + "...")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/generar_video.py 'URL_GRADIO' 'tu prompt'")
        sys.exit(1)
    generar_video(sys.argv[1], sys.argv[2])
