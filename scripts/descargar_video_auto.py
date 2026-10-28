"""Descarga el video generado en Kaggle (version + ruta interna)."""
import sys, pathlib, shutil, kagglehub

def descargar(slug, version, ruta_interna, destino):
    handle = f"{slug}/versions/{version}"
    print(f"Descargando {ruta_interna} de {handle}...")
    try:
        path = kagglehub.notebook_output_download(handle, path=ruta_interna)
        dest = pathlib.Path(destino)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        print(f"✅ Video descargado: {dest} ({dest.stat().st_size // 1024} KB)")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Uso: python descargar_video_auto.py 'user/slug' 'version' 'ruta/interna.mp4' 'ruta/destino.mp4'")
        sys.exit(1)
    descargar(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
