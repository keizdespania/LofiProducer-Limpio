"""render_shorts_batch.py - Genera 4 shorts de El Encuadre (manipulacion, sin sensacionalismo)."""
import sys, json, pathlib, subprocess, datetime, asyncio, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from render_short_rot import generar_short
from especialistas import pedir_a_especialista
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MUSICA = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Lista negra de palabras sensacionalistas
PROHIBIDAS = ["muert", "muerte", "sangre", "tragedia", "saqueo", "víctima", "asesin", "fallecid"]

async def _gen_voz(texto, salida):
    c = edge_tts.Communicate(texto, "es-ES-AlvaroNeural", rate="-5%")
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _guion_short(hook_original, tipo):
    """Genera guion de ~45s (50-60 palabras) sin sensacionalismo, con foco en manipulación."""
    prompt = (
        f"Eres el guionista de shorts de 'El Encuadre'. Tu misión es desmontar la manipulación mediática. "
        f"NO hables de la tragedia en sí. Habla de CÓMO el medio usó la noticia para manipular. "
        f"Tipo: {tipo}. Hook original: '{hook_original}'. "
        "Escribe 50-60 palabras para un short de 40 segundos. "
        "Empieza con una pregunta que despierte curiosidad. "
        "Menciona el medio y la técnica de manipulación. "
        "TERMINA EXACTAMENTE con: 'Somos El Encuadre, analistas de la manipulación. Suscríbete para más'. "
        "PROHIBIDO: hablar de muertos, víctimas, tragedias o violencia. Sin markdown."
    )
    return pedir_a_especialista("guionista_retencion_v2", prompt, contexto=hook_original, proveedor="auto")

def _limpiar_texto(texto, hook):
    """Si el LLM mete palabras prohibidas, usa el hook limpio."""
    if not texto: return hook
    if any(p in texto.lower() for p in PROHIBIDAS):
        print("  ⚠️ Texto con palabras prohibidas, usando hook original limpio", flush=True)
        return hook
    # Truncar a 60 palabras
    palabras = texto.split()
    if len(palabras) > 60:
        texto = " ".join(palabras[:60]) + "... Somos El Encuadre, analistas de la manipulación. Suscríbete."
    return texto

def _descargar_musica_intriga():
    """Descarga música de intriga con bajos (cinematic dark tension)."""
    destino = MUSICA / "intriga_bass.mp3"
    if destino.exists() and destino.stat().st_size > 100000:
        return destino
    
    print("[shorts] Descargando música de intriga (cinematic dark tension)...", flush=True)
    # Buscar en Bandcamp o YouTube
    busquedas = ["cinematic dark tension bass", "terminator theme dark", "dark thriller bass"]
    for q in busquedas:
        try:
            r = subprocess.run([
                "yt-dlp", f"ytsearch3:{q}", "--get-id", "--flat-playlist", "--no-warnings"
            ], capture_output=True, text=True, timeout=45)
            ids = r.stdout.strip().split("\n")
            for vid in ids[:2]:
                url = f"https://www.youtube.com/watch?v={vid}"
                try:
                    subprocess.run([
                        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                        "--download-sections", "*0-60", "-o", str(destino), url, 
                        "--no-warnings", "--force-overwrites"
                    ], check=True, capture_output=True, timeout=300)
                    if destino.exists() and destino.stat().st_size > 100000:
                        print(f"[shorts] ✅ Música de intriga: {destino.name}", flush=True)
                        return destino
                except: continue
        except: continue
    return None

def main():
    prod = OUT / f"produccion_{FECHA}.json"
    dos = OUT / f"dossier_{FECHA}.json"
    if not prod.exists() or not dos.exists():
        print("❌ Faltan produccion o dossier"); return

    dossier = json.loads(dos.read_text())
    hooks = dossier.get("guiones", {}).get("hooks_totales", [])[:4]
    if not hooks:
        print("❌ No hay hooks"); return

    img_vertical = ROOT / "web" / "media" / "imagenes" / "short_bg_01.png"
    musica_intriga = _descargar_musica_intriga() or (MUSICA / "lofi_base.mp3")

    for i, h in enumerate(hooks):
        num = i + 1
        tipo = h.get("tipo", "dato")
        hook = h.get("hook", "")
        
        print(f"[{num}/4] Generando guion ({tipo})...", flush=True)
        texto = _guion_short(hook, tipo)
        texto = _limpiar_texto(texto, hook)
        
        voz_path = OUT / f"short_{num}_voz_{FECHA}.mp3"
        print(f"[{num}/4] Generando voz...", flush=True)
        asyncio.run(_gen_voz(texto, voz_path))
        
        salida = OUT / f"short_{num}_{FECHA}.mp4"
        print(f"[{num}/4] Renderizando short...", flush=True)
        try:
            generar_short(str(img_vertical), texto, str(voz_path), str(musica_intriga), str(salida))
            print(f"  ✅ {salida.name}", flush=True)
        except Exception as e:
            print(f"  ❌ Fallo: {e}", flush=True)

if __name__ == "__main__":
    main()
