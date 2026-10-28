"""Filtra los endpoints de WanGP para encontrar el de generar video."""
import sys, requests

def filtrar(url, palabras):
    base = url.rstrip('/')
    r = requests.get(f"{base}/gradio_api/openapi.json", timeout=30)
    if r.status_code != 200:
        print(f"ERROR: HTTP {r.status_code}")
        return
    
    data = r.json()
    paths = data.get("paths", {})
    
    print(f"Buscando endpoints que contengan: {palabras}")
    encontrados = []
    for path in paths:
        if "/call/" in path and any(p in path.lower() for p in palabras):
            encontrados.append(path)
    
    if encontrados:
        print(f"\nEncontrados {len(encontrados)} endpoints:")
        for e in encontrados[:20]:
            print(f"  · {e}")
    else:
        print("\nNo se encontraron endpoints con esas palabras.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python filtrar_api_wangp.py 'https://tu-url.gradio.live' [palabras]")
        sys.exit(1)
    url = sys.argv[1]
    palabras = sys.argv[2:] if len(sys.argv) > 2 else ["generate", "run", "video", "predict", "process"]
    filtrar(url, palabras)
