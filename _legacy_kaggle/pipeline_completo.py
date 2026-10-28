"""
Pipeline completo: Lanza Kaggle, espera la URL en GitHub y genera la música.
"""
import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_FILE = ROOT / "data" / "kaggle_url.txt"

def git_pull():
    """Actualiza el repo local para ver si hay URL nueva."""
    subprocess.run(["git", "pull", "origin", "main"], cwd=str(ROOT), capture_output=True, text=True)

def main():
    tema = sys.argv[1] if len(sys.argv) > 1 else "lofi jazz"
    print(f"🚀 Lanzando pipeline para: {tema}")

    # 1. Borrar la URL vieja (para no confundirnos)
    if URL_FILE.exists():
        URL_FILE.unlink()

    # 2. Lanzar el notebook en Kaggle (a través del Orquestador)
    print("📤 Subiendo notebook a Kaggle...")
    proc = subprocess.run(
        ["python", "scripts/kaggle_orchestrator.py", f'{{"tema": "{tema}"}}'],
        cwd=str(ROOT), capture_output=True, text=True, timeout=600
    )
    if "Kernel creado" not in proc.stdout and "Kernel activado" not in proc.stdout:
        print(f"❌ Error lanzando el pipeline: {proc.stdout[-500:]}")
        return 1

    print("✅ Notebook lanzado. Esperando URL de Kaggle (esto puede tardar 5-10 min)...")

    # 3. Bucle esperando la URL en GitHub
    for intento in range(40):  # 40 x 15s = 10 minutos
        time.sleep(15)
        git_pull()
        if URL_FILE.exists():
            url = URL_FILE.read_text().strip()
            if url.startswith("https://") and ".gradio.live" in url:
                print(f"✅ URL encontrada: {url}")
                break
        print(f"   [{(intento+1)*15}s] Esperando URL...")
    else:
        print("❌ Timeout: No se encontró la URL en 10 minutos.")
        return 1

    # 4. Generar la música con el script que ya funciona
    print("🎵 Generando música con la URL de Kaggle...")
    proc_gen = subprocess.run(
        ["python", "scripts/generar_musica.py", url, tema],
        cwd=str(ROOT), capture_output=True, text=True, timeout=1200
    )
    if "descargada" in proc_gen.stdout:
        print("✅ ¡Canción generada y descargada a output/!")
        return 0
    else:
        print(f"❌ Error generando música: {proc_gen.stdout[-500:]}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
