"""Busca datasets publicos en Kaggle que contengan Wan 2.2."""
import sys, pathlib
sys.path.insert(0, "scripts")
from kaggle_bearer import _req

def buscar(query):
    print(f"Buscando datasets: '{query}'...")
    # La API de Kaggle usa /datasets/list con search
    r = _req(f"/datasets/list?search={query}&page=1")
    if isinstance(r, dict) and "error" in r:
        print("ERROR:", r["error"])
        return
    if not isinstance(r, list):
        print("Respuesta inesperada:", str(r)[:200])
        return
    print(f"Encontrados {len(r)} datasets:")
    for d in r[:10]:
        print(f"  · {d.get('ref')} | {d.get('title')} | {d.get('totalBytes', '?')} bytes")

if __name__ == "__main__":
    buscar("wan 2.2")
    print()
    buscar("wan2.2")
    print()
    buscar("wan-ai")
