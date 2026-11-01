"""descargar_lofi.py - Buscador incansable de Lofi en YouTube con fallback a Bandcamp."""
import subprocess, pathlib, sys, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

def buscar_y_descargar_youtube():
    """Buscador incansable: si falla una query, prueba otra. Si falla un video, prueba otro."""
    busquedas = [
        "lofi hip hop mix 1 hour",
        "chillhop music mix",
        "lofi beats to study",
        "jazz hop cafe mix",
        "lofi chill instrumental",
        "lofi sleep music",
        "lofi study beats mix"
    ]
    random.shuffle(busquedas)
    
    for query in busquedas:
        print(f"[Lofi] YouTube buscando: '{query}'...", flush=True)
        try:
            r = subprocess.run([
                "yt-dlp", f"ytsearch10:{query}",
                "--match-filter", "duration > 900",  # solo videos >15 min
                "--get-id", "--get-title", "--get-duration",
                "--flat-playlist", "--no-warnings"
            ], capture_output=True, text=True, timeout=60)
            
            lineas = [l.strip() for l in r.stdout.strip().split("\n") if l.strip()]
            videos = []
            # Con --get-id --get-title --get-duration son 3 lineas por video
            i = 0
            while i + 2 < len(lineas):
                try:
                    videos.append({"titulo": lineas[i], "id": lineas[i+1], "duracion": lineas[i+2]})
                    i += 3
                except:
                    i += 1
                
            if not videos:
                print("[Lofi] YouTube: No se encontraron videos para esta búsqueda.", flush=True)
                continue
                
            random.shuffle(videos)
            
            for v in videos[:3]:
                url = f"https://www.youtube.com/watch?v={v['id']}"
                print(f"[Lofi] YouTube intentando: {v['titulo'][:40]}...", flush=True)
                try:
                    subprocess.run([
                        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                        "--download-sections", "*0-900", "--socket-timeout", "15",
                        "-o", str(destino), url, 
                        "--no-warnings", "--force-overwrites"
                    ], check=True, capture_output=True, timeout=600)
                    
                    if destino.exists() and destino.stat().st_size > 100000:
                        print(f"[Lofi] ✅ YouTube OK: {destino.stat().st_size//1024//1024}MB", flush=True)
                        return True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                    print("[Lofi] Fallo en este video (posible directo/bloqueo), probando siguiente...", flush=True)
                    continue
        except Exception as e:
            print(f"[Lofi] Error general en YouTube: {e}", flush=True)
            continue
            
    return False

# SIEMPRE descargar (nunca reutilizar del dia anterior)
if destino.exists():
    size_mb = destino.stat().st_size // 1024 // 1024
    print(f"[Lofi] Borrando musica anterior ({size_mb}MB) para descargar nueva...", flush=True)
    destino.unlink()

if not buscar_y_descargar_youtube():
    print("[Lofi] ❌ YouTube agotó todas las opciones. Activando fallback a Bandcamp (CC0)...", flush=True)
    subprocess.run(["python3", "scripts/descargar_lofi_bandcamp.py"], check=False)
