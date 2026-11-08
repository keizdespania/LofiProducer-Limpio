import sys, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
ANGULOS = ["dato", "contradiccion", "prediccion", "tutorial"]

def run_new(angulo):
    print(f"\n🚀 [NUEVO x4] Lanzando short: {angulo}")
    r = subprocess.run([sys.executable, str(ROOT/"scripts/pipeline_short_definitivo.py"), angulo])
    return r.returncode == 0

def run_old(angulo):
    print(f"\n⚠️ [FALLBACK] Fallo el nuevo. Usando short_engine.py para: {angulo}")
    r = subprocess.run([sys.executable, str(ROOT/"scripts/short_engine.py"), "Tema del día", "ia_news", angulo])
    return r.returncode == 0

if __name__ == "__main__":
    print("=== DRY RUN: GENERANDO 4 SHORTS ===")
    for angulo in ANGULOS:
        exito = run_new(angulo)
        if not exito:
            run_old(angulo)
    print("\n✅ DRY RUN COMPLETADO. Revisa output/shorts/")
