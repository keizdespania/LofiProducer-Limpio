"""generar_thumbnail.py - Genera miniaturas con texto para YouTube."""
import subprocess, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"

def crear_thumb(titulo, fecha, tipo="short"):
    img_fondo = MEDIA / "encuadre_01.png"
    if not img_fondo.exists(): return None
    
    salida = OUT / f"thumb_{tipo}_{fecha}.jpg"
    size = "1080x1920" if tipo == "short" else "1280x720"
    fontsize = 60 if tipo == "short" else 40
    titulo_ffmpeg = titulo.replace("'", "\\'")[:40]
    
    cmd = [
        "ffmpeg", "-y", "-i", str(img_fondo),
        "-vf", f"scale={size}:force_original_aspect_ratio=increase,crop={size},drawtext=text='{titulo_ffmpeg}':fontcolor=white:fontsize={fontsize}:box=1:boxcolor=black@0.7:boxborderw=20:x=(w-text_w)/2:y=h-th-100",
        "-frames:v", "1", str(salida)
    ]
    subprocess.run(cmd, capture_output=True)
    return str(salida) if salida.exists() else None

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else "2026-10-28"
    print(crear_thumb("El truco de la manipulacion", fecha, "short"))
