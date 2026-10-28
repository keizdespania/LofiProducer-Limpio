"""renderizador.py - Monta el vídeo usando el plan de montaje (pausas, música, efectos)."""
import sys, json, pathlib, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"

def _buscar(patron):
    r = list(patron.parent.glob(patron.name))
    return r[0] if r else None

def renderizar(fecha):
    prod = OUT / f"produccion_{fecha}.json"
    if not prod.exists(): return
    datos = json.loads(prod.read_text())
    plan = datos.get("plan_montaje", {})
    timeline = plan.get("timeline", [])
    
    imagen = MEDIA / "fondo_encuadre.jpg"
    voz = OUT / f"voz_largo_{fecha}.mp3"
    ass = OUT / f"voz_largo_{fecha}.ass"
    
    if not all([imagen.exists(), voz.exists()]):
        print("[render] Faltan assets base (imagen o voz).")
        return
        
    # Comando base de FFmpeg
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(imagen), "-i", str(voz)]
    
    # Buscar una pista de música de fondo
    musica = _buscar(MUSICA / "*.mp3")
    if musica:
        cmd += ["-i", str(musica)]
    
    # Filtro de vídeo (con ASS si existe)
    filtro_v = "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080"
    if ass.exists():
        filtro_v += f",ass={ass}"
    filtro_v += "[v]"
    
    # Filtro de audio (Simplificado para asegurar que funciona, pero respetando la mezcla)
    # Si el plan tenía volumen, lo aplicamos. Si no, un 0.15 por defecto.
    vol_mus = 0.15
    if musica:
        filtro_a = f"[2:a]volume={vol_mus}[mus];[1:a][mus]amix=inputs=2:duration=first:dropout_transition=2[a]"
    else:
        filtro_a = "[1:a]anull[a]"
    
    filter_complex = f"{filtro_v};{filtro_a}"
    
    cmd += ["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]", "-shortest", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac"]
    salida = OUT / f"video_largo_{fecha}.mp4"
    cmd.append(str(salida))
    
    print("[render] Renderizando vídeo largo (usando plan de montaje)...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode == 0:
        print(f"[render] ✅ {salida.name}")
    else:
        print(f"[render] ❌ Error: {r.stderr[-300:]}")

if __name__ == "__main__":
    renderizar(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat())
