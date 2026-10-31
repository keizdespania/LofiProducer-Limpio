"""crear_fondo_short.py - Genera el fondo futurista 9:16 para los shorts (una sola vez)."""
import sys, pathlib, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from generar_imagen import generar

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "web" / "media" / "imagenes"
LOGO = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
DESTINO = MEDIA / "short_bg_futurista.png"

PROMPT = (
    "Futuristic newsroom desk at night, multiple holographic screens floating with "
    "Spanish newspaper headlines, dark neon blue and red lighting, dramatic shadows, "
    "cinematic, moody, 35mm film, black and gold color palette, no people, no text"
)

def crear_con_sdxl():
    print("[fondo] Generando con SDXL (9:16)...", flush=True)
    try:
        r = generar(PROMPT, preset="cinematic", aspect="9:16", canal="encuadre")
        if "OK: " in r:
            ruta = r.split("OK: ")[1].split(" ")[0]
            src = pathlib.Path(ruta)
            if src.exists():
                return src
    except Exception as e:
        print(f"[fondo] SDXL fallo: {e}", flush=True)
    return None

def crear_con_ffmpeg():
    print("[fondo] Fallback: generando fondo con FFmpeg...", flush=True)
    tmp = MEDIA / "_fondo_tmp.png"
    # Fondo negro 1080x1920 con degradado radial azul oscuro
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        "color=c=0x0a0a14:s=1080x1920:d=1",
        "-vf", "drawbox=x=0:y=0:w=1080:h=1920:color=0x1a1a3a@0.3:t=fill",
        "-frames:v", "1", str(tmp)
    ], check=True, capture_output=True)
    return tmp

def main():
    if DESTINO.exists():
        print(f"[fondo] Ya existe {DESTINO.name}, saltando.", flush=True)
        return
    
    MEDIA.mkdir(parents=True, exist_ok=True)
    
    # 1. Intentar SDXL
    src = crear_con_sdxl()
    
    # 2. Fallback FFmpeg
    if not src:
        src = crear_con_ffmpeg()
    
    # 3. Superponer el logo en el centro
    print("[fondo] Superponiendo logo en el centro...", flush=True)
    if LOGO.exists():
        # Logo escalado a 250px de ancho, centrado, con halo
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-i", str(src), "-i", str(LOGO),
            "-filter_complex",
            "[1:v]scale=250:-1,format=rgba,colorchannelmixer=aa=0.9[logo];"
            "[0:v][logo]overlay=(W-w)/2:(H-h)/2",
            "-frames:v", "1", str(DESTINO)
        ], check=True, capture_output=True)
    else:
        import shutil
        shutil.copy2(src, DESTINO)
    
    # Limpiar tmp
    if src and src.name.startswith("_"):
        src.unlink(missing_ok=True)
    
    print(f"[fondo] ✅ Guardado en {DESTINO} ({DESTINO.stat().st_size//1024}KB)", flush=True)

if __name__ == "__main__":
    main()
