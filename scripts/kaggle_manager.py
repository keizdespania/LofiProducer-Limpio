"""Gestor unificado de Kaggle para el Dios: lanza notebooks con task_id."""
import sys, pathlib, json, time
sys.path.insert(0, "scripts")
from kaggle_bearer import _req

ROOT = pathlib.Path(__file__).resolve().parent.parent

def lanzar_y_descargar(prompt, task_id, tipo="video"):
    print(f"[Kaggle] Iniciando tarea tipo '{tipo}' con prompt: {prompt}")
    print(f"[Kaggle] Task ID: {task_id}")
    
    nb_path = ROOT / "wangp_nb.json"
    if not nb_path.exists():
        return "ERROR: No se encuentra el notebook base (wangp_nb.json)."
    
    nb = json.loads(nb_path.read_text())
    
    # Inyectar prompt en la celda de generacion
    for cell in nb["cells"]:
        if cell["cell_type"] == "code" and "settings =" in "".join(cell["source"]):
            source = "".join(cell["source"])
            source = source.replace('"A cat riding a bicycle in a sunny park, cinematic, 4k"', f'"{prompt}"')
            cell["source"] = source.splitlines(keepends=True)
            print("[Kaggle] Prompt inyectado.")
            break
    
    # Usar task_id en el slug para que el checker lo encuentre
    slug = f"keizproductions/kaggle-auto-{task_id}"
    payload = {
        "slug": slug,
        "newTitle": f"Kaggle Auto {tipo} {task_id}",
        "text": json.dumps(nb),
        "language": "python",
        "kernelType": "notebook",
        "isPrivate": True,
        "enableGpu": True,
        "enableTpu": False,
        "enableInternet": True,
        "datasetDataSources": [],
        "competitionDataSources": [],
        "kernelDataSources": [],
    }
    print(f"[Kaggle] Subiendo {slug}...")
    res = _req("/kernels/push", method="POST", data=payload, cuenta=1)
    if res.get("hasError"):
        return f"ERROR al subir: {res.get('error')}"
    
    url = res.get("url")
    print(f"[Kaggle] Notebook subido: {url}")
    print(f"[Kaggle] El checker lo descargara automaticamente cuando termine.")
    return f"OK: Tarea lanzada en {url}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python kaggle_manager.py 'tu prompt' 'task_id'")
        sys.exit(1)
    print(lanzar_y_descargar(sys.argv[1], sys.argv[2]))
