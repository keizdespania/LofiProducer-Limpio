"""Vídeo personalizado: SpaceX 30s + intro logo + cierre 'ay mi madre' + lofi piano."""
import sys, os, json, pathlib, subprocess, asyncio, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "rapidos"
OUT.mkdir(parents=True, exist_ok=True)

LOGO = ROOT / "assets" / "logo.png"
MUSICA = None  # Buscar en output/musica

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

async def _voz(texto, salida):
    import edge_tts
    await edge_tts.Communicate(texto, "es-ES-AlvaroNeural").save(str(salida))

def _clips_pixabay(query, cantidad=3):
    from curl_cffi import requests
    key = _env("PIXABAY_API_KEY")
    url = f"https://pixabay.com/api/videos/?key={key}&q={urllib.parse.quote(query)}&per_page={cantidad}&video_type=film"
    r = requests.get(url, impersonate="chrome", timeout=30)
    data = r.json()
    return [v["videos"]["medium"]["url"] for v in data.get("hits", []) if v.get("videos")]

def generar(texto, titulo):
    audio = OUT / f"{titulo}.mp3"
    video = OUT / f"{titulo}.mp4"
    
    # 1. Voz principal
    print("[1/5] Voz principal...")
    asyncio.run(_voz(texto, audio))
    
    # 2. Voz cierre "ay mi madre"
    print("[2/5] Cierre...")
    cierre = OUT / f"{titulo}_cierre.mp3"
    asyncio.run(_voz("¡Ay mi madre!", cierre))
    
    # 3. Clips SpaceX
    print("[3/5] Clips SpaceX...")
    clips = _clips_pixabay("spacex rocket launch", 3)
    if not clips: return "ERROR: sin clips"
    
    from curl_cffi import requests as cffi
    clips_path = []
    for i, url in enumerate(clips):
        p = OUT / f"clip_sp_{i}.mp4"
        r = cffi.get(url, impersonate="chrome", timeout=60)
        if r.status_code == 200:
            p.write_bytes(r.content)
            clips_path.append(p)
    
    # 4. Montar vídeo base (clips + audio principal)
    print("[4/5] Montando vídeo base...")
    concat = OUT / "concat_sp.txt"
    with open(concat, "w") as f:
        for p in clips_path:
            f.write(f"file '{p}'\n")
    
    base = OUT / f"{titulo}_base.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(audio), "-c:v", "libx264", "-c:a", "aac", "-shortest", str(base)],
                   capture_output=True, check=True)
    
    # 5. Añadir intro con logo + cierre + música
    print("[5/5] Intro + cierre...")
    # Crear intro (2s logo sobre negro)
    intro = OUT / "intro.mp4"
    if LOGO.exists():
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(LOGO), "-t", "2",
                        "-vf", "scale=720:-1,pad=720:1280:(ow-iw)/2:(oh-ih)/2:black",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(intro)], capture_output=True)
        # Concatenar intro + base + cierre
        concat2 = OUT / "concat_final.txt"
        with open(concat2, "w") as f:
            f.write(f"file '{intro}'\n")
            f.write(f"file '{base}'\n")
        # (El cierre se puede añadir como texto al final o audio)
    
    # Copiar base al final (simplificado para este test)
    final = OUT / f"{titulo}_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat2),
                    "-i", str(cierre), "-c:v", "libx264", "-c:a", "aac", "-shortest", str(final)],
                   capture_output=True) if 'concat2' in dir() else subprocess.run(["cp", str(base), str(final)])
    
    # Notificar
    try:
        subprocess.run(["termux-notification", "-t", "🚀 SpaceX listo", "-c", f"{titulo}_final.mp4"], check=False, timeout=5)
    except Exception: pass
    
    return f"OK: {final} ({final.stat().st_size // 1024} KB)"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/video_spacex.py 'texto' 'titulo'")
        sys.exit(1)
    print(generar(sys.argv[1], sys.argv[2]))
