"""descargar_lofi_openlofi.py - Descarga 1 track CC0 de Open-LoFi (sin bajar el ZIP entero)."""
import json, pathlib, random, subprocess, sys, urllib.request
from remotezip import RemoteZip

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"
ZIP_URL = "https://github.com/btahir/open-lofi/releases/latest/download/openlofi.zip"
CATALOG_URL = "https://raw.githubusercontent.com/btahir/open-lofi/main/catalog.json"

def elegir_track():
    print("[OpenLoFi] Leyendo catálogo...", flush=True)
    data = json.loads(urllib.request.urlopen(CATALOG_URL, timeout=30).read())
    
    # Buscar la lista de tracks (puede estar en 'tracks' o en las categorías)
    tracks = data.get("tracks", [])
    if not tracks:
        # Si no hay lista plana, sacar de las categorías
        for cat in data.get("categories", []):
            tracks.extend(cat.get("tracks", []))
    
    if not tracks:
        print("[OpenLoFi] ❌ No hay tracks en el catálogo"); sys.exit(1)
    
    # Elegir uno que sea de 'chillhop' o 'jazzhop' (los más neutros)
    neutros = [t for t in tracks if t.get("category") in ("chillhop", "jazzhop", "ambient-lofi")]
    elegido = random.choice(neutros if neutros else tracks)
    print(f"[OpenLoFi] Elegido: {elegido.get('title', '?')} ({elegido.get('file', '?')})", flush=True)
    return elegido.get("file") or elegido.get("path")

def descargar_y_recortar(archivo):
    print(f"[OpenLoFi] Abriendo ZIP remoto (solo se descarga {archivo})...", flush=True)
    raw = OUT / "lofi_raw.mp3"
    for intento in range(3):
        try:
            print(f"[OpenLoFi] Intento {intento+1}/3...", flush=True)
            with RemoteZip(ZIP_URL, timeout=300) as z:
                with z.open(archivo) as f:
                    raw.write_bytes(f.read())
            if raw.exists() and raw.stat().st_size > 100000:
                break
        except Exception as e:
            print(f"[OpenLoFi] Fallo intento {intento+1}: {e}", flush=True)
    if not raw.exists() or raw.stat().st_size < 100000:
        print("[OpenLoFi] ❌ Todos los intentos fallaron.", flush=True); sys.exit(1)
    
    print(f"[OpenLoFi] Recortando a 15 min...", flush=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw), "-t", "900", "-c:a", "libmp3lame", "-b:a", "192k", str(destino)], check=True)
    raw.unlink(missing_ok=True)
    print(f"[OpenLoFi] ✅ Guardado en {destino} ({destino.stat().st_size//1024//1024}MB)", flush=True)

if __name__ == "__main__":
    if destino.exists() and destino.stat().st_size > 1024*1024:
        print("[OpenLoFi] Ya existe lofi_base.mp3, saltando."); sys.exit(0)
    archivo = elegir_track()
    descargar_y_recortar(archivo)
