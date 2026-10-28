"""Sube un archivo a GitHub usando la API REST."""
import os, sys, json, base64, requests, pathlib

# Leer GITHUB_TOKEN del entorno o del .env
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    # Fallback: leer del .env del proyecto (si estamos en Termux)
    env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                GITHUB_TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not GITHUB_TOKEN:
    print("ERROR: Falta GITHUB_TOKEN")
    sys.exit(1)

REPO = "keizdespania/LofiProducer-backup"
BRANCH = "main"

def subir_archivo(file_path, dest_path=None):
    if dest_path is None:
        dest_path = f"output/videos/{pathlib.Path(file_path).name}"
    
    # Leer el archivo y codificar en base64
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    
    url = f"https://api.github.com/repos/{REPO}/contents/{dest_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    # Comprobar si ya existe (para obtener el SHA)
    sha = None
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")
    
    payload = {
        "message": f"Add video {pathlib.Path(file_path).name}",
        "content": content,
        "branch": BRANCH,
    }
    if sha:
        payload["sha"] = sha
    
    r = requests.put(url, headers=headers, json=payload)
    if r.status_code in (200, 201):
        print(f"OK: {dest_path} subido a GitHub")
        return True
    else:
        print(f"ERROR: {r.status_code} - {r.text[:200]}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python upload_to_github.py 'ruta/al/video.mp4'")
        sys.exit(1)
    subir_archivo(sys.argv[1])
