"""descargar_lofi.py - Busca y descarga 15 min de Lofi aleatorio de YouTube."""
import subprocess, pathlib, sys, random, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
destino = OUT / "lofi_base.mp3"

def buscar_y_descargar():
    # Busca 10 videos de lofi chill en YouTube
    busquedas = ["lofi hip hop radio", "chillhop music", "lofi chill beats", "jazz hop cafe"]
    query = random.choice(busquedas)
    
    print(f"[Lofi] Buscando en YouTube: '{query}'...", flush=True)
    try:
        r = subprocess.run([
            "yt-dlp", f"ytsearch10:{query}", "--get-id", "--get-title", "--flat-playlist", "--no-warnings"
        ], capture_output=True, text=True, timeout=60)
        
        lineas = r.stdout.strip().split("\n")
        videos = []
        # yt-dlp devuelve título e ID en líneas separadas
        for i in range(0, len(lineas)-1, 2):
            videos.append({"titulo": lineas[i], "id": lineas[i+1]})
            
        if not videos:
            print("[Lofi] No se encontraron videos.", flush=True)
            return False
            
        random.shuffle(videos)
        
        for v in videos[:5]: # Intenta con los primeros 5 aleatorios
            url = f"https://www.youtube.com/watch?v={v['id']}"
            print(f"[Lofi] Intentando descargar: {v['titulo'][:40]}... ({url})", flush=True)
            try:
                subprocess.run([
                    "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                    "--download-sections", "*0-900",
                    "-o", str(destino), url, "--no-warnings", "--force-overwrites"
                ], check=True, capture_output=True, timeout=60)
                
                if destino.exists() and destino.stat().st_size > 100000:
                    print(f"[Lofi] ✅ Descargado: {destino.stat().st_size//1024//1024}MB", flush=True)
                    return True
            except subprocess.CalledProcessError:
                print("[Lofi] Fallo en este video, probando el siguiente...", flush=True)
                continue
    except Exception as e:
        print(f"[Lofi] Error buscando: {e}", flush=True)
    return False

if not destino.exists() or destino.stat().st_size < 1024*1024:
    if not buscar_y_descargar():
        print("[Lofi] ❌ Todos los intentos fallaron. Generando 15 min de silencio.", flush=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "900", "-c:a", "libmp3lame", str(destino)], check=True)
else:
    print("[Lofi] Ya existe lofi_base.mp3, saltando.", flush=True)
