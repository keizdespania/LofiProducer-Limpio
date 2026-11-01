"""descargar_musica_diaria.py - Descarga musica CC0 NUEVA cada dia (Tunetank -> Bandcamp). Sin reutilizar."""
import sys, pathlib, subprocess, random, datetime, urllib.request, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)
DESTINO = OUT / "lofi_base.mp3"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# ============ FUENTE 1: TUNETANK (CC0, moods) ============
MOODS_TUNETANK = ["dark", "epic", "calm", "mysterious", "inspiring", "electronic"]
MCP_URL = "https://mcp.tunetank.com"

def _tunetank(mood):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "search_music", "arguments": {"mood": mood, "duration": 180, "tolerance": 30, "limit": 5}}}
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    try:
        req = urllib.request.Request(MCP_URL, data=data, headers=headers, method="POST")
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        result = r.get("result", {}).get("content", [])
        if not result: return None
        data_obj = json.loads(result[0].get("text", "{}"))
        tracks = data_obj.get("results", [])
        if not tracks: return None
        random.shuffle(tracks)
        for track in tracks[:3]:
            url = track.get("preview_url") or track.get("download_url") or track.get("url")
            if not url: continue
            print(f"  Tunetank {mood}: {track.get("title", "?")[:50]}")
            subprocess.run(["curl", "-L", "-s", "-o", str(DESTINO), url], check=True, timeout=120)
            if DESTINO.exists() and DESTINO.stat().st_size > 500000:
                return DESTINO
    except Exception as e:
        print(f"  Tunetank error: {e}")
    return None

# ============ FUENTE 2: BANDCAMP CC0 (HoliznaCC0) ============
TRACKS_BANDCAMP = [
    "https://holiznacc0.bandcamp.com/track/tokyo-sunset",
    "https://holiznacc0.bandcamp.com/track/lofi-dreams",
    "https://holiznacc0.bandcamp.com/track/chill-vibes",
    "https://holiznacc0.bandcamp.com/track/rainy-day",
    "https://holiznacc0.bandcamp.com/track/sunset-drive",
    "https://holiznacc0.bandcamp.com/track/late-night-study",
    "https://holiznacc0.bandcamp.com/track/tranquil-mindset",
    "https://holiznacc0.bandcamp.com/track/midnight-coffee",
]

def _bandcamp():
    tracks = TRACKS_BANDCAMP.copy()
    random.shuffle(tracks)
    for url in tracks:
        print(f"  Bandcamp: {url.split(chr(47))[-1]}")
        tmp = OUT / "bc_tmp.mp3"
        try:
            subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                "--download-sections", "*0-900", "-o", str(tmp), url, "--no-warnings", "--force-overwrites"],
                check=True, capture_output=True, timeout=180)
            if tmp.exists() and tmp.stat().st_size > 500000:
                # Buclear a 15 min
                lista = OUT / "bc_concat.txt"
                with open(lista, "w") as f:
                    for _ in range(15):
                        f.write(f"file {chr(39)}{tmp.absolute()}{chr(39)}\n")
                subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "concat", "-safe", "0", "-i", str(lista),
                    "-t", "900", "-c:a", "libmp3lame", "-b:a", "192k", str(DESTINO)],
                    check=True, timeout=120)
                tmp.unlink(missing_ok=True)
                lista.unlink(missing_ok=True)
                if DESTINO.exists() and DESTINO.stat().st_size > 1000000:
                    return DESTINO
        except Exception as e:
            print(f"  Bandcamp error: {e}")
    return None

# ============ FUENTE 3: SILENCIO (fallback ultimo) ============
def _silencio():
    print("  Fallback: silencio 15 min")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-t", "900", "-c:a", "libmp3lame", "-b:a", "128k", str(DESTINO)], check=True, timeout=60)
    return DESTINO if DESTINO.exists() else None

def main(fecha=None):
    fecha = fecha or FECHA
    print(f"Descargando musica nueva para {fecha}...")
    print("=" * 60)
    
    # SIEMPRE borrar la anterior
    if DESTINO.exists():
        size_old = DESTINO.stat().st_size // 1024 // 1024
        DESTINO.unlink()
        print(f"  Borrada musica anterior ({size_old}MB)")
    
    # Limpiar temporales viejos
    for tmp in OUT.glob("*.part"): tmp.unlink(missing_ok=True)
    
    # Intentar Tunetank con 3 moods aleatorios
    moods = MOODS_TUNETANK.copy()
    random.shuffle(moods)
    print(f"[1/2] Probando Tunetank (moods: {moods[:3]})...")
    for mood in moods[:3]:
        result = _tunetank(mood)
        if result:
            print(f"  OK Tunetank ({result.stat().st_size//1024//1024}MB)")
            return True
    
    print("[2/2] Fallback a Bandcamp CC0...")
    result = _bandcamp()
    if result:
        print(f"  OK Bandcamp ({result.stat().st_size//1024//1024}MB)")
        return True
    
    print("⚠️ Sin musica, generando silencio")
    result = _silencio()
    return result is not None

if __name__ == "__main__":
    ok = main(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)