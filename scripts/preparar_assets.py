"""preparar_assets.py - Asegura que las imágenes existen antes de renderizar."""
import sys, json, pathlib, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MEDIA.mkdir(parents=True, exist_ok=True)

def preparar(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    print("[assets] Verificando imágenes...", flush=True)
    
    imagenes = list(MEDIA.glob("*.jpg")) + list(MEDIA.glob("*.png"))
    if len(imagenes) < 3:
        print(f"  ⚠️ Solo hay {len(imagenes)} imágenes. Generando placeholders...", flush=True)
        for i in range(3):
            img_path = MEDIA / f"placeholder_{fecha}_{i}.jpg"
            if not img_path.exists():
                subprocess.run(["ffmpeg", "-f", "lavfi", "-i", f"color=c=0x1a1a24:s=1920x1080:d=1", "-frames:v", "1", str(img_path), "-y"], capture_output=True)
                print(f"  ✅ Placeholder: {img_path.name}", flush=True)
    else:
        print(f"  ✅ {len(imagenes)} imágenes disponibles", flush=True)
    
    print(f"\n[assets] ✅ Imágenes listas. (La voz y los subtítulos los genera voz_edge.py)", flush=True)
    return True

if __name__ == "__main__":
    preparar(sys.argv[1] if len(sys.argv) > 1 else None)
