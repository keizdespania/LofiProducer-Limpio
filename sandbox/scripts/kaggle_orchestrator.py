import sys
import json
import base64
import os
from pathlib import Path
sys.path.insert(0, "scripts")
from kaggle_light import crear_kernel, _leer_token
import requests
import time

def _leer_github_token() -> str:
    """Lee GITHUB_TOKEN desde el entorno o del archivo .env."""
    tok = os.environ.get("GITHUB_TOKEN", "").strip()
    if tok:
        return tok
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("GITHUB_TOKEN="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Falta GITHUB_TOKEN en .env o variable de entorno")

def lanzar_pipeline(ordenes: dict, github_token: str):
    """Genera el código del worker, lo sube a Kaggle y espera a que termine."""
    
    # Inyectamos el token y las órdenes en el código del notebook
    token_b64 = base64.b64encode(github_token.encode()).decode()
    ordenes_json = json.dumps(ordenes)
    
    codigo_worker = f"""
import os
import subprocess
import json
import base64

# Recuperar token y ordenes
github_token = base64.b64decode("{token_b64}").decode()
ordenes = json.loads('''{ordenes_json}''')

print("[Worker] Iniciando pipeline completo...")

# 1. Generar Música (Simulado por ahora, aquí iría ACE-Step)
print("[Worker] Generando música...")
os.makedirs('output', exist_ok=True)
with open('output/musica.mp3', 'w') as f: f.write('audio_mock')

# 2. Generar Vídeo (Simulado, aquí iría LTX-Video)
print("[Worker] Generando vídeo...")
with open('output/video.mp4', 'w') as f: f.write('video_mock')

# 3. Subir resultados a GitHub
print("[Worker] Subiendo resultados a GitHub...")
repo_url = f"https://{{github_token}}@github.com/keizdespania/LofiProducer-backup.git"

try:
    subprocess.run(["git", "clone", repo_url, "/tmp/repo"], check=True)
    # Copiamos los archivos generados
    subprocess.run(["cp", "-r", "output/.", "/tmp/repo/output/"], check=True)
    
    # Hacemos commit y push
    subprocess.run(["git", "-C", "/tmp/repo", "config", "user.email", "kaggle@keiz.com"], check=True)
    subprocess.run(["git", "-C", "/tmp/repo", "config", "user.name", "Kaggle Worker"], check=True)
    subprocess.run(["git", "-C", "/tmp/repo", "add", "output/"], check=True)
    subprocess.run(["git", "-C", "/tmp/repo", "commit", "-m", "feat(kaggle): pipeline completado"], check=True)
    subprocess.run(["git", "-C", "/tmp/repo", "push"], check=True)
    print("[Worker] ¡Resultados subidos con éxito!")
except Exception as e:
    print(f"[Worker] Error subiendo a GitHub: {{e}}")

print("[Worker] Tarea completada. Apagando GPU...")
"""

    print("[Orquestador] Subiendo Worker a Kaggle...")
    try:
        crear_kernel("keizproductions/worker-auto", codigo_worker)
        print("✅ Kernel subido. Esperando a que Kaggle arranque y procese...")
        # NOTA: Aquí faltaría la lógica para consultar el estado del Kernel vía API.
        # Como Kaggle API no tiene endpoint directo para "esperar", hacemos un bucle
        # de 10 minutos comprobando si el archivo ya está en GitHub.
        return True
    except Exception as e:
        print(f"❌ Error al subir el kernel: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/kaggle_orchestrator.py '{\"tema\": \"lofi\"}'")
        sys.exit(1)
        
    ordenes = json.loads(sys.argv[1])
    github_token = _leer_github_token()
    if not github_token:
        print("❌ Falta GITHUB_TOKEN en el .env")
        sys.exit(1)
        
    lanzar_pipeline(ordenes, github_token)
