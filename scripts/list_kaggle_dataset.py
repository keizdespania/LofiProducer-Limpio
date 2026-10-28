"""Lista los archivos de un dataset de Kaggle para ver su estructura."""
import sys, pathlib
sys.path.insert(0, "scripts")
from kaggle_bearer import _req

def listar(ref):
    # La API de Kaggle para listar archivos de un dataset
    r = _req(f"/datasets/list/{ref}/files")
    if isinstance(r, dict) and "error" in r:
        print("ERROR:", r["error"])
        return
    if not isinstance(r, list):
        print("Respuesta:", str(r)[:300])
        return
    print(f"Dataset {ref}: {len(r)} archivos (mostrando los primeros 20):")
    for f in r[:20]:
        print(f"  · {f.get('name')} ({f.get('totalBytes', '?')} bytes)")

if __name__ == "__main__":
    listar("ihsannika/wan2-2-ti2v-5b")
