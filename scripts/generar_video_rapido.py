"""Motor rápido: Texto -> Vídeo (Pexels + Edge-TTS + FFmpeg). Sin GPU."""
import sys, os, json, pathlib, subprocess, asyncio, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

async def _generar_voz(texto, salida):
    import edge_tts
    await edge_tts.Communicate(texto, "es-ES-AlvaroNeural").save(salida)

def _buscar_video_pixabay(query, cantidad=3):
    key = _env("PIXABAY_API_KEY")
    if not key: return []
    url = f"https://pixabay.com/api/videos/?key={key}&q={urllib.parse.quote(query)}&per_page={cantidad}&video_type=film"
    try:
        from curl_cffi import requests as cffi_req
        r = cffi_req.get(url, impersonate="chrome", timeout=30)
        data = r.json()
        return [v["videos"]["medium"]["url"] for v in data.get("hits", []) if v.get("videos")]
    except ImportError:
        print("  ⚠️  curl_cffi no instalado, usando urllib (puede fallar)")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return [v["videos"]["medium"]["url"] for v in r.get("hits", []) if v.get("videos")]

def generar(texto, titulo="video_rapido"):
    out_dir = ROOT / "output" / "rapidos"
    out_dir.mkdir(parents=True, exist_ok=True)
    audio = out_dir / f"{titulo}.mp3"
    video_final = out_dir / f"{titulo}.mp4"
    
    # 1. Voz
    print("[1/4] Generando voz...")
    asyncio.run(_generar_voz(texto, str(audio)))
    if not audio.exists(): return "ERROR: fallo la voz"
    
    # 2. Buscar clips
    print("[2/4] Buscando clips en Pexels...")
    clips = _buscar_video_pixabay("technology", 3)  # Búsqueda fija de clips para el test
    if not clips:
        return "ERROR: sin clips (¿falta PEXELS_API_KEY?)"
    
    # 3. Descargar clips (usando curl_cffi para evitar Cloudflare)
    print("[3/4] Descargando clips...")
    clips_path = []
    from curl_cffi import requests as cffi_req
    for i, url in enumerate(clips):
        p = out_dir / f"clip_{i}.mp4"
        try:
            r = cffi_req.get(url, impersonate="chrome", timeout=60)
            if r.status_code == 200:
                p.write_bytes(r.content)
                clips_path.append(p)
            else:
                print(f"  ⚠️ clip {i}: HTTP {r.status_code}")
        except Exception as e: print(f"  ⚠️ clip {i}: {e}")
    if not clips_path: return "ERROR: no se descargaron clips"
    
    # 4. Montar (bucle de clips hasta cubrir el audio, sin audio original)
    print("[4/4] Montando con FFmpeg...")
    concat = out_dir / "concat.txt"
    with open(concat, "w") as f:
        for i, p in enumerate(clips_path):
            f.write(f"file '{p}'\n")
            if i < len(clips_path) - 1:
                f.write(f"file '{p}'\n") # repetir para alargar
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(audio),
           "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video_final)]
    subprocess.run(cmd, capture_output=True, check=True)
    # Limpiar clips temporales del taller
    for c in clips_path:
        try: c.unlink()
        except: pass
    try: (out_dir / "concat.txt").unlink()
    except: pass

    # Notificar al móvil
    try:
        import subprocess as _sp
        _sp.run(["termux-notification", "-t", "🎬 Vídeo listo", "-c", f"{titulo}.mp4 ({video_final.stat().st_size // 1024} KB) - Revisar antes de subir"], check=False, timeout=5)
    except Exception: pass
    return f"OK: {video_final} ({video_final.stat().st_size // 1024} KB)"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/generar_video_rapido.py 'texto' 'titulo'")
        sys.exit(1)
    print(generar(sys.argv[1], sys.argv[2]))
