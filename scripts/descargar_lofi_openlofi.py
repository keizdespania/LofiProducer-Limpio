"""descargar_lofi_openlofi.py - Descarga 1 track CC0 de Open-LoFi desde Internet Archive."""
import json, pathlib, random, subprocess, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

# Identificador del item en Internet Archive (OpenLo-Fi de btahir)
IA_ITEM = "openlofi"
IA_META_URL = f"https://archive.org/metadata/{IA_ITEM}"

def elegir_track():
    print("[OpenLoFi] Leyendo metadatos de Internet Archive...", flush=True)
    try:
        data = json.loads(urllib.request.urlopen(IA_META_URL, timeout=30).read())
        files = data.get("files", [])
        # Filtrar solo MP3s
        mp3s = [f for f in files if f.get("name", "").endswith(".mp3")]
        if not mp3s:
            print("[OpenLoFi] ❌ No hay MP3s en el item"); sys.exit(1)
        
        elegido = random.choice(mp3s)
        nombre = elegido["name"]
        print(f"[OpenLoFi] Elegido: {nombre}", flush=True)
        # URL de descarga directa
        return f"https://archive.org/download/{IA_ITEM}/{urllib.parse.quote(nombre)}"
    except Exception as e:
        print(f"[OpenLoFi] Error leyendo metadatos: {e}", flush=True)
        sys.exit(1)

def descargar_y_recortar(url):
    print(f"[OpenLoFi] Descargando: {url[:80]}...", flush=True)
    raw = OUT / "lofi_raw.mp3"
    try:
        urllib.request.urlretrieve(url, raw)
    except Exception as e:
        print(f"[OpenLoFi] ❌ Fallo descarga: {e}", flush=True); sys.exit(1)
    
    if not raw.exists() or raw.stat().st_size < 100000:
        print("[OpenLoFi] ❌ Archivo vacío o corrupto"); sys.exit(1)
    
    print(f"[OpenLoFi] Recortando a 15 min...", flush=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(raw), "-t", "900", "-c:a", "libmp3lame", "-b:a", "192k", str(destino)], check=True)
    raw.unlink(missing_ok=True)
    print(f"[OpenLoFi] ✅ Guardado en {destino} ({destino.stat().st_size//1024//1024}MB)", flush=True)

if __name__ == "__main__":
    if destino.exists() and destino.stat().st_size > 1024*1024:
        print("[OpenLoFi] Ya existe lofi_base.mp3, saltando."); sys.exit(0)
    url = elegir_track()
    descargar_y_recortar(url)
