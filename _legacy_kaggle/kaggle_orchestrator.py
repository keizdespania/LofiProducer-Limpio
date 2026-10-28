"""
Orquestador de Kaggle: Sube el notebook de PyTorch (audio) o LTX (vídeo) según el tipo.
"""
import sys
import json
import os
from pathlib import Path
sys.path.insert(0, "scripts")
from kaggle_light import crear_kernel, activar_kernel

def lanzar_pipeline(ordenes: dict, github_token: str):
    tipo = ordenes.get("tipo", "musica")
    
    # 1. Elegir el notebook según el tipo
    if tipo == "video":
        notebook_path = Path("worker_definitivo_v10.ipynb")  # En un futuro, uno específico de vídeo
        kernel_name = "keizproductions/worker-video-v1"
    else:
        notebook_path = Path("worker_definitivo_v10.ipynb")
        kernel_name = "keizproductions/worker-real-v10"

    if not notebook_path.exists():
        print(f"ERROR: No existe {notebook_path}")
        return False

    # 2. Extraer el código Python de las celdas
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    codigo_worker = ""
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            codigo_worker += "".join(cell.get("source", [])) + "\n\n"

    if not codigo_worker.strip():
        print("ERROR: El notebook no tiene código Python.")
        return False

    # 3. Inyectar variables de entorno
    user = "keizdespania"
    repo = "LofiProducer-backup"
    
    cabecera = "import os\n"
    cabecera += f"os.environ['GITHUB_TOKEN'] = '{github_token}'\n"
    cabecera += f"os.environ['GITHUB_USER'] = '{user}'\n"
    cabecera += f"os.environ['GITHUB_REPO'] = '{repo}'\n"
    cabecera += f"os.environ['TEMA'] = '{ordenes.get('tema', 'lofi')}'\n\n"
    
    codigo_final = cabecera + codigo_worker

    # 4. Subir y activar
    print(f"[Orquestador] Subiendo Worker de {tipo} a Kaggle...")
    try:
        crear_kernel(kernel_name, codigo_final, gpu=True)
        print("Kernel subido. Activando ejecución...")
        activar_kernel("keizproductions", kernel_name.split("/")[1])
        print("OK: Kernel activado. Esperando a que Kaggle arranque y procese...")
        return True
    except Exception as e:
        print(f"ERROR al subir el kernel: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/kaggle_orchestrator.py '{\"tema\": \"lofi\", \"tipo\": \"musica\"}'")
        sys.exit(1)
        
    ordenes = json.loads(sys.argv[1])
    github_token = ""
    env = Path(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                github_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    
    if not github_token:
        print("ERROR: Falta GITHUB_TOKEN en .env")
        sys.exit(1)
        
    exito = lanzar_pipeline(ordenes, github_token)
    if exito:
        print("Pipeline lanzado con éxito.")
    else:
        print("Fallo al lanzar el pipeline.")
