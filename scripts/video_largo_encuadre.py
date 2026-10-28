"""video_largo_encuadre.py - Ensamblador cinematográfico 16:9"""
import os, json, re, subprocess, pathlib, random
from pathlib import Path
from subir_youtube import subir

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
OUT.mkdir(parents=True, exist_ok=True)

def _voz(texto, salida, parte=1):
    """Genera voz con Sherpa."""
    from voice_studio import generar_audio
    r = generar_audio(texto, voz="es_ES-davefx-medium", preset="narracion_relajada", formato="mp3", nombre="video_" + salida.stem)
    if r.get("status") == "ok":
        mp3 = Path.home() / "LofiProducer" / "media" / "audios" / (r["audio_id"] + ".mp3")
        if mp3.exists():
            import shutil
            shutil.copy2(mp3, salida)
            return salida
    return None


def _elegir_musica():
    """Elige música de la carpeta libre."""
    musica_dir = ROOT / "output" / "musica_libre"
    tracks = list(musica_dir.rglob("*.mp3"))
    return random.choice(tracks) if tracks else None

def _generar_srt(texto, salida, duracion):
    """Genera un SRT básico (trocea el texto cada 4 segundos)."""
    palabras = texto.split()
    lineas = []
    tiempo = 0
    idx = 1
    while palabras:
        bloque = palabras[:15] # 15 palabras por bloque aprox
        palabras = palabras[15:]
        start = f"00:00:{tiempo:02d},000"
        fin = f"00:00:{min(tiempo+4, duracion):02d},000"
        lineas.append(f"{idx}\n{start} --> {fin}\n{' '.join(bloque)}\n")
        idx += 1
        tiempo += 4
    salida.write_text("\n".join(lineas))
    return salida

def generar_video_largo(fecha=None):
    fecha = fecha or pathlib.Path.today().isoformat()
    html_file = ROOT / "web" / "docs" / "posts" / f"{fecha}.html"
    if not html_file.exists():
        print("[video_largo] No hay post")
        return None
    
    html = html_file.read_text()
    # 1. Leer guion audiovisual (o fallback al HTML si no existe)
    guion_file = OUT / f"guiones_{fecha}.json"
    if guion_file.exists():
        guiones = json.loads(guion_file.read_text())
        texto_plano = guiones.get("video_largo", "")
        if not texto_plano:
            texto_plano = re.sub(r'<[^>]+>', ' ', html)
            texto_plano = re.sub(r'\s+', ' ', texto_plano).strip()
    else:
        texto_plano = re.sub(r'<[^>]+>', ' ', html)
        texto_plano = re.sub(r'\s+', ' ', texto_plano).strip()
    
    # 2. Generar voz
    voz_path = OUT / f"video_voz_{fecha}.mp3"
    v = _voz(texto_plano[:4000], voz_path) # Limitamos para no petar
    if not v:
        print("[video_largo] Voz fallida")
        return None
        
    # 3. Generar SRT
    srt_path = OUT / f"video_sub_{fecha}.srt"
    _generar_srt(texto_plano, srt_path, 60) # Dummy duration

    # 4. Seleccionar fondo (Imagen destacada o clip stock)
    # Por ahora usamos la imagen del post
    imgs = re.findall(r'<img src="(/media/imagenes/[^"]+)"', html)
    if not imgs:
        print("[video_largo] Sin imágenes")
        return None
    img = ROOT / imgs[0].lstrip("/")
    
    # 5. Ensamblar
    print("[video_largo] Ensamblando vídeo cinematográfico...")
    out = OUT / f"video_largo_{fecha}.mp4"
    
    # Filtro: Zoom lento + subtítulos
    # Usamos subtitles=... para quemar los subtítulos en el vídeo
    filtro = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,zoompan=z='min(zoom+0.0015,1.5)':d=1:s=1920x1080,subtitles={srt_path}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,Outline=2'"
    
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(v)]
    if _elegir_musica():
        cmd += ["-i", str(_elegir_musica())]
    
    # Mezcla de audio
    cmd += ["-filter_complex", f"[0:v]{filtro}[v];[1:a]loudnorm=I=-14:LRA=11:TP=-1.5[voz];[2:a]volume=0.15[mus];[voz][mus]amix=inputs=2:duration=first[aout]"]
    cmd += ["-map", "[v]", "-map", "[aout]", "-t", "60", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", str(out)]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode == 0 and out.exists():
        print(f"[video_largo] OK: {out}")
        return str(out)
    print(f"[video_largo] FFmpeg error: {r.stderr[-300:]}")
    return None

if __name__ == "__main__":
    import sys
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    print(generar_video_largo(fecha))
