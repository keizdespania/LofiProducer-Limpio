"""render_shorts_batch.py - Shorts Top 1: fondo negro+logo, musica en el drop, guion blindado."""
import sys, json, pathlib, subprocess, datetime, asyncio, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from render_short_rot import generar_short
from especialistas import pedir_a_especialista
from analista_audio import analizar_pista
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MUSICA = ROOT / "output" / "musica_temp"
MEDIA = ROOT / "web" / "media" / "imagenes"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

PROHIBIDAS = ["muert", "muerte", "sangre", "tragedia", "saqueo", "víctima", "asesin", "fallecid"]

async def _gen_voz(texto, salida):
    c = edge_tts.Communicate(texto, "es-ES-AlvaroNeural", rate="-5%")
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _guion_short(hook_original, tipo):
    prompt = (
        f"Eres guionista de shorts de 'El Encuadre'. Tu misión es desmontar la manipulación mediática. "
        f"NO hables de la tragedia, habla de CÓMO el medio manipuló la noticia. "
        f"Tipo: {tipo}. Hook original: '{hook_original}'. "
        "Escribe 50-60 palabras para un short de 40 segundos. "
        "Empieza con pregunta que despierte curiosidad. "
        "Menciona el medio y la técnica de manipulación. "
        "TERMINA EXACTAMENTE con: 'Somos El Encuadre, analistas de la manipulación. Suscríbete para más'. "
        "Sin markdown, sin acotaciones."
    )
    return pedir_a_especialista("guionista_retencion_v2", prompt, contexto=hook_original, proveedor="auto")

def _limpiar_texto(texto, hook):
    if not texto: return hook
    if any(p in texto.lower() for p in PROHIBIDAS):
        print("  ⚠️ Texto con palabras prohibidas, forzando reescritura...", flush=True)
        return None  # Fuerza el fallback
    palabras = texto.split()
    if len(palabras) < 40:
        print(f"  ⚠️ Texto demasiado corto ({len(palabras)} palabras). Fallback...", flush=True)
        return None
    if len(palabras) > 65:
        texto = " ".join(palabras[:65]) + "... Somos El Encuadre. Suscríbete."
    return texto

def _crear_fondo_negro_logo():
    """Crea una imagen 1080x1920 con fondo negro y el logo en la parte superior."""
    destino = MEDIA / "short_bg_negro_logo.png"
    if destino.exists():
        return destino
    
    logo = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
    if not logo.exists():
        # Fallback: fondo negro sin logo
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x0a0a0f:s=1080x1920:d=1", "-frames:v", "1", str(destino)], check=True)
        return destino
    
    # Fondo negro 1080x1920 con logo arriba (centrado)
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x0a0a0f:s=1080x1920:d=1",
        "-i", str(logo),
        "-filter_complex", "[1:v]scale=300:-1[logo];[0:v][logo]overlay=(W-w)/2:80",
        "-frames:v", "1", str(destino)
    ], check=True, capture_output=True)
    return destino

def _cortar_musica_en_peak(musica_path):
    """Analiza la energía de la musica y corta 45s desde el peak."""
    if not musica_path or not pathlib.Path(musica_path).exists():
        return musica_path
    
    info = analizar_pista(str(musica_path))
    peak = info.get("peak_energy_time", 0)
    if peak <= 0: peak = 5
    
    salida = MUSICA / "short_musica_peak.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(max(0, peak - 2)), "-i", str(musica_path),
        "-t", "45", "-c:a", "libmp3lame", "-b:a", "192k", str(salida)
    ], check=True)
    return salida

def _descargar_musica_intriga():
    destino = MUSICA / "intriga_bass.mp3"
    if destino.exists() and destino.stat().st_size > 100000:
        return destino
    
    print("[shorts] Descargando música de intriga...", flush=True)
    for q in ["cinematic dark tension bass", "dark thriller bass", "epic dark trailer"]:
        try:
            r = subprocess.run(["yt-dlp", f"ytsearch3:{q}", "--get-id", "--flat-playlist", "--no-warnings"],
                capture_output=True, text=True, timeout=45)
            for vid in r.stdout.strip().split("\n")[:2]:
                if not vid: continue
                try:
                    subprocess.run([
                        "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "5",
                        "--download-sections", "*0-180", "-o", str(destino),
                        f"https://www.youtube.com/watch?v={vid}", "--no-warnings", "--force-overwrites"
                    ], check=True, capture_output=True, timeout=300)
                    if destino.exists() and destino.stat().st_size > 100000:
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

    # Fondo negro + logo
    print("[shorts] Creando fondo negro con logo...", flush=True)
    img_fondo = _crear_fondo_negro_logo()
    print(f"[shorts] ✅ Fondo: {img_fondo.name}", flush=True)

    # Música de intriga cortada en el peak
    musica_base = _descargar_musica_intriga() or (MUSICA / "lofi_base.mp3")
    print(f"[shorts] Analizando energía de la música...", flush=True)
    musica = _cortar_musica_en_peak(musica_base)
    print(f"[shorts] ✅ Música cortada en el drop", flush=True)

    for i, h in enumerate(hooks):
        num = i + 1
        tipo = h.get("tipo", "dato")
        hook = h.get("hook", "")
        
        print(f"[{num}/4] Generando guion ({tipo})...", flush=True)
        texto = _guion_short(hook, tipo)
        texto = _limpiar_texto(texto, hook)
        
        # Fallback si el LLM falla o no cumple
        if not texto:
            texto = (
                f"{hook}. ¿Te has parado a pensar cómo los medios usan esta noticia para manipularte? "
                "Es la técnica del hombre de paja. Somos El Encuadre, analistas de la manipulación. Suscríbete para más."
            )
        
        voz_path = OUT / f"short_{num}_voz_{FECHA}.mp3"
        print(f"[{num}/4] Generando voz...", flush=True)
        asyncio.run(_gen_voz(texto, voz_path))
        
        salida = OUT / f"short_{num}_{FECHA}.mp4"
        print(f"[{num}/4] Renderizando short...", flush=True)
        try:
            generar_short(str(img_fondo), texto, str(voz_path), str(musica), str(salida))
            print(f"  ✅ {salida.name}", flush=True)
        except Exception as e:
            print(f"  ❌ Fallo: {e}", flush=True)

if __name__ == "__main__":
    main()
