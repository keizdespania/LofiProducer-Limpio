"""preparar_assets.py - Asegura que todas las imágenes, voz y subtítulos existen antes de renderizar."""
import sys, json, pathlib, re, subprocess, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MEDIA.mkdir(parents=True, exist_ok=True)

def _srt_basico(texto, salida, duracion=60):
    """Genera un SRT básico troceando el texto cada 4 segundos."""
    palabras = texto.split()
    lineas = []
    tiempo = 0
    idx = 1
    while palabras:
        bloque = palabras[:10]
        palabras = palabras[10:]
        start = f"00:00:{tiempo:02d},000"
        fin = f"00:00:{min(tiempo+4, duracion):02d},000"
        lineas.append(f"{idx}\n{start} --> {fin}\n{' '.join(bloque)}\n")
        idx += 1
        tiempo += 4
    salida.write_text("\n".join(lineas))
    return salida

def _generar_voz(texto, salida, preset="noticias"):
    """Genera voz con voice_studio."""
    try:
        from voice_studio import generar_audio
        r = generar_audio(texto, voz="es_ES-davefx-medium", preset=preset, formato="mp3", nombre=salida.stem)
        if r.get("status") == "ok":
            mp3 = ROOT / "output" / "audios" / (r["audio_id"] + ".mp3")
            if mp3.exists():
                import shutil
                shutil.copy2(mp3, salida)
                return salida
    except Exception as e:
        print(f"  ⚠️ Error voz: {e}")
    return None

def preparar(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists():
        print(f"[assets] No existe {prod_file}")
        return None
    
    datos = json.loads(prod_file.read_text())
    escenas = datos.get("guion_cinematografico", {}).get("guion", [])
    shorts = datos.get("shorts_finales", [])
    
    # 1. IMÁGENES (usar las que ya existen o generar nuevas)
    print("[assets] 1/4 Verificando imágenes...", flush=True)
    imagenes = list(MEDIA.glob("*.jpg")) + list(MEDIA.glob("*.png"))
    if len(imagenes) < 3:
        print(f"  ⚠️ Solo hay {len(imagenes)} imágenes. Generando placeholders...", flush=True)
        for i in range(3):
            img_path = MEDIA / f"placeholder_{fecha}_{i}.jpg"
            if not img_path.exists():
                # Generar imagen con FFmpeg (color sólido)
                subprocess.run(["ffmpeg", "-f", "lavfi", "-i", f"color=c=0x1a1a24:s=1920x1080:d=1", "-frames:v", "1", str(img_path), "-y"], capture_output=True)
                print(f"  ✅ Placeholder: {img_path.name}", flush=True)
    else:
        print(f"  ✅ {len(imagenes)} imágenes disponibles", flush=True)
    
    # 2. VOZ EN OFF (Se delega a voz_edge.py)
    print("[assets] 2/4 Voz en off se generará con Edge-TTS después...", flush=True)
    
    # 3. VOZ DE LOS SHORTS
    print("[assets] 3/4 Verificando voz de los shorts...", flush=True)
    for i, short in enumerate(shorts[:4]):
        voz_short = OUT / f"short_{i+1}_voz_{fecha}.mp3"
        if not voz_short.exists():
            texto = short.get("guion", short.get("hook", ""))
            v = _generar_voz(texto, voz_short, preset="noticias")
            if v:
                print(f"  ✅ Short {i+1} voz: {v.name}", flush=True)
    
    # 4. SUBTÍTULOS (SRT para el largo y los shorts)
    print("[assets] 4/4 Generando subtítulos...", flush=True)
    srt_largo = OUT / f"voz_largo_{fecha}.srt"
    if not srt_largo.exists() and voz_largo and voz_largo.exists():
        texto_guion = " ".join([e.get("texto", "") for e in escenas])
        _srt_basico(texto_guion, srt_largo, 300)
        print(f"  ✅ SRT largo generado", flush=True)
    
    for i, short in enumerate(shorts[:4]):
        srt_short = OUT / f"short_{i+1}_{fecha}.srt"
        if not srt_short.exists():
            texto = short.get("guion", short.get("hook", ""))
            _srt_basico(texto, srt_short, 60)
            print(f"  ✅ SRT short {i+1} generado", flush=True)
    
    # 5. RESUMEN
    print(f"\n[assets] ✅ Resumen:", flush=True)
    print(f"  Imágenes: {len(list(MEDIA.glob('*.jpg'))) + len(list(MEDIA.glob('*.png')))}")
    print(f"  Audios voz: {len(list(OUT.glob('voz_*.mp3')))}")
    print(f"  SRTs: {len(list(OUT.glob('*.srt')))}")
    print(f"  Música: {len(list((ROOT / 'output' / 'musica_temp').glob('*.mp3')))}")
    
    return True

if __name__ == "__main__":
    preparar(sys.argv[1] if len(sys.argv) > 1 else None)
