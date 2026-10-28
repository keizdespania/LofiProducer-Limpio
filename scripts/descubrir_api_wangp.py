"""Descubre los endpoints disponibles en el Gradio de WanGP."""
import sys, requests, json

def descubrir(url):
    base = url.rstrip('/')
    print(f"Consultando {base}/gradio_api/openapi.json ...")
    
    try:
        r = requests.get(f"{base}/gradio_api/openapi.json", timeout=30)
        if r.status_code != 200:
            print(f"ERROR: HTTP {r.status_code}")
            return
        
        data = r.json()
        paths = data.get("paths", {})
        
        print(f"\nEndpoints encontrados ({len(paths)}):")
        for path in paths:
            if "/call/" in path:
                print(f"  · {path}")
                # Mostrar parametros si existen
                post = paths[path].get("post", {})
                if "requestBody" in post:
                    print(f"      (tiene requestBody)")
                    
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python descubrir_api_wangp.py 'https://tu-url.gradio.live'")
        sys.exit(1)
    descubrir(sys.argv[1])
