"""render_shorts_batch.py - Genera 4 shorts con guion de 45s, musica viral y cierre pactado."""
import sys, json, pathlib, subprocess, datetime, asyncio
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from render_short_rot import generar_short
from especialistas import pedir_a_especialista
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MUSICA = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

async def _gen_voz(texto, salida):
    c = edge_tts.Communicate(texto, "es-ES-AlvaroNeural", rate="-5%")
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _guion_short(hook_original, tipo):
    """Genera guion de ~45s (70-80 palabras) con intriga y cierre pactado."""
    prompt = (
        f"Eres guionista de shorts virales. Reescribe este hook en 70-80 palabras para un short de 45 segundos. "
        f"Hook original: '{hook_original}'. "
        "Empieza con una pregunta incómoda o dato bomba. "
        "Crea intriga (no lo resuelvas del todo). "
        "TERMINA EXACTAMENTE con: 'Somos El Encuadre, analistas de la manipulación. Suscríbete para no perderte el siguiente análisis'. "
        "Sin markdown, sin acotaciones, solo texto plano para TTS."
    )
    return pedir_a_especialista("guionista_retencion_v2", prompt, contexto=hook_original, proveedor="auto")

def _descargar_musica_viral():
    """Descarga un audio viral del momento de YouTube."""
    destino = MUSICA / "viral_hit.mp3"
    if destino.exists() and destino.stat().st_size > 100000:
        return destino
    
    busquedas = [
        "viral hits 2026",
        "trending songs 2026 tiktok",
        "top hits 2026 short version"
    ]
    for q in busquedas:
        try:
            r = subprocess.run([
                "yt-dlp", f"ytsearch3:{q}", "--get-id", "--flat-playlist", "--no-warnings"
            ], capture_output=True, text=True, timeout=45)
            ids = r.stdout.strip().split("\n")
            if not ids: continue
            for vid in ids[:2]:
                url = f"https://www.youtube.com/watch?v={vid}"
                try:
                    subprocess.run([
                        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                        "--download-sections", "*0-60", "-o", str(destino), url, "--no-warnings", "--force-overwrites"
                    ], check=True, capture_output=True, timeout=120)
                    if destino.exists() and destino.stat().st_size > 100000:
                        return destino
                except: continue
        except: continue
    return None

def main():
    prod = OUT / f"produccion_{FECHA}.json"
    dos = OUT / f"dossier_{FECHA}.json"
    if not prod.exists() or not dos.exists():
        print(f"❌ Faltan produccion o dossier"); return

    dossier = json.loads(dos.read_text())
    hooks = dossier.get("guiones", {}).get("hooks_totales", [])[:4]
    if not hooks:
        print("❌ No hay hooks"); return

    img_vertical = ROOT / "web" / "media" / "imagenes" / "short_bg_01.png"

    print("[shorts] Descargando música viral del momento...", flush=True)
    musica_viral = _descargar_musica_viral()
    if musica_viral:
        print(f"[shorts] ✅ Música viral: {musica_viral.name}", flush=True)
    else:
        print("[shorts] ⚠️ No se pudo descargar música viral, usando Lofi", flush=True)
        musica_viral = MUSICA / "lofi_base.mp3"

    for i, h in enumerate(hooks):
        num = i + 1
        tipo = h.get("tipo", "dato")
        hook = h.get("hook", "")
        
        print(f"[{num}/4] Generando guion ({tipo})...", flush=True)
        texto = _guion_short(hook, tipo)
        if not texto or len(texto.split()) < 30:
            texto = hook + " Somos El Encuadre, analistas de la manipulación. Suscríbete para más."
        
        voz_path = OUT / f"short_{num}_voz_{FECHA}.mp3"
        print(f"[{num}/4] Generando voz...", flush=True)
        asyncio.run(_gen_voz(texto, voz_path))
        
        salida = OUT / f"short_{num}_{FECHA}.mp4"
        print(f"[{num}/4] Renderizando short...", flush=True)
        try:
            generar_short(str(img_vertical), texto, str(voz_path), str(musica_viral), str(salida))
            print(f"  ✅ {salida.name}", flush=True)
        except Exception as e:
            print(f"  ❌ Fallo: {e}", flush=True)

if __name__ == "__main__":
    main()
