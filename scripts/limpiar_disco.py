"""limpiar_disco.py - Borra archivos generados de más de 7 días (excepto logo y shorts)."""
import os, time, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIAS_RETENCION = 7
SEGUNDOS = DIAS_RETENCION * 86400

CARPETAS_A_LIMPIAR = [
    ROOT / "output" / "encuadre",
    ROOT / "output" / "musica_temp",
    ROOT / "output" / "audios",
    ROOT / "output" / "imagenes",
    ROOT / "web" / "media" / "imagenes",
]

EXTENSIONES = {".mp4", ".mp3", ".wav", ".png", ".jpg", ".jpeg", ".webm", ".ass", ".srt"}

def limpiar():
    ahora = time.time()
    borrados = 0
    liberados_mb = 0

    print(f"🧹 Limpiando archivos con más de {DIAS_RETENCION} días...")
    
    for carpeta in CARPETAS_A_LIMPIAR:
        if not carpeta.exists(): continue
        for archivo in carpeta.rglob("*"):
            if not archivo.is_file(): continue
            if archivo.suffix.lower() not in EXTENSIONES: continue
            if "logo_encuadre" in archivo.name: continue
            if "short_" in archivo.name: continue  # Protegemos los shorts

            if (ahora - archivo.stat().st_mtime) > SEGUNDOS:
                try:
                    tamano = archivo.stat().st_size
                    archivo.unlink()
                    borrados += 1
                    liberados_mb += tamano / (1024 * 1024)
                    print(f"  🗑️ Borrado: {archivo.name}")
                except Exception as e:
                    print(f"  ❌ Error: {e}")

    print(f"\n✅ Limpieza completada: {borrados} archivos. Liberados: {liberados_mb:.1f} MB")

if __name__ == "__main__":
    limpiar()
