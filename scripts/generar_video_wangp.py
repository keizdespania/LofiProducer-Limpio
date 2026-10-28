"""Genera un video usando WanGP en Kaggle desde Termux."""
import sys, requests, time

def generar(gradio_url, prompt):
    # Eliminamos la barra final si existe
    base_url = gradio_url.rstrip('/')
    print(f"Conectando con {base_url}...")
    
    # 1. Enviar el prompt a la API de WanGP
    # Nota: WanGP usa un endpoint especifico para generar. Asumimos el formato estandar.
    endpoint = f"{base_url}/gradio_api/call/generate"
    payload = {"data": [prompt, None, None, 121, 4, 480, 832, 42, 5.0, 1]}
    
    try:
        r = requests.post(endpoint, json=payload, timeout=30)
        if r.status_code != 200:
            return f"ERROR: {r.status_code} - {r.text[:200]}"
        
        # 2. Obtener el enlace del video generado
        data = r.json()
        if "data" in data:
            return f"OK: Video generado en {data['data'][0]}"
        return f"Respuesta inesperada: {str(data)[:200]}"
        
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python generar_video_wangp.py 'URL_GRADIO' 'tu prompt'")
        sys.exit(1)
    
    url = sys.argv[1]
    prompt = sys.argv[2]
    print(generar(url, prompt))
