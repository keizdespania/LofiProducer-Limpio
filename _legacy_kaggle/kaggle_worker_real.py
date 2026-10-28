"""
Worker Real de Kaggle: Levanta ACE-Step, genera la música con la GPU,
sube el MP3 a GitHub y termina (apagando la GPU).
"""
import os
import sys
import json
import base64
import subprocess
import re
import time
from pathlib import Path

# ── CONFIGURACIÓN RECIBIDA POR VARIABLES DE ENTORNO ──
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_USER = os.environ.get("GITHUB_USER", "keizdespania")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "LofiProducer-backup")

if not GITHUB_TOKEN:
    print("❌ Falta GITHUB_TOKEN")
    sys.exit(1)

REPO_URL = f"https://{GITHUB_TOKEN}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"

# ── 1. INSTALAR Y PREPARAR ACE-STEP ──
print("[Worker] Instalando ACE-Step...")
subprocess.run(["pip", "install", "-q", "uv", "huggingface_hub"], check=True)
if not Path("ACE-Step-1.5").exists():
    subprocess.run(["git", "clone", "https://github.com/ace-step/ACE-Step-1.5.git"], check=True)
os.chdir("ACE-Step-1.5")
subprocess.run(["uv", "sync"], check=True)

# ── 2. COPIAR EL MODELO DESDE EL DATASET DE KAGGLE ──
print("[Worker] Copiando modelo desde el dataset de Kaggle...")
import shutil
dataset_path = Path("/kaggle/input/acestep-15-models")
if dataset_path.exists():
    print(f"[Worker] Dataset encontrado en {dataset_path}")
    # Buscar la carpeta del modelo turbo en el dataset
    for candidate in dataset_path.rglob("acestep-v15-turbo"):
        if candidate.is_dir():
            os.makedirs("checkpoints", exist_ok=True)
            shutil.copytree(candidate, "checkpoints/acestep-v15-turbo", dirs_exist_ok=True)
            print(f"[Worker] Modelo copiado desde {candidate}")
            break
    # Buscar la carpeta VAE
    for candidate in dataset_path.rglob("vae"):
        if candidate.is_dir():
            shutil.copytree(candidate, "checkpoints/vae", dirs_exist_ok=True)
            print(f"[Worker] VAE copiado desde {candidate}")
            break
else:
    print("[Worker] Dataset no encontrado, descargando de HuggingFace...")
    os.makedirs("checkpoints", exist_ok=True)
    subprocess.run([
        "hf", "download", "ACE-Step/Ace-Step1.5",
        "--local-dir", "checkpoints",
        "--include", "acestep-v15-turbo/*",
        "--include", "vae/*"
    ], check=True)

# ── 3. LANZAR ACE-STEP (con fix de float32 para T4) ──
print("[Worker] Arreglando float16 → float32 (fix NaN)...")
orchestrator = Path("acestep/core/generation/handler/init_service_orchestrator.py")
if orchestrator.exists():
    contenido = orchestrator.read_text(encoding="utf-8")
    contenido = contenido.replace("torch.float16", "torch.float32")
    orchestrator.write_text(contenido, encoding="utf-8")

print("[Worker] Arrancando ACE-Step...")
proc = subprocess.Popen(
    ["uv", "run", "acestep", "--share", "--init_service", "true"],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
)

url_capturada = None
for line in iter(proc.stdout.readline, ''):
    print(line, end='')
    match = re.search(r'https://([a-z0-9]+)\.gradio\.live', line)
    if match and not url_capturada:
        url_capturada = match.group(0)
        print(f"\n[Worker] URL capturada: {url_capturada}")
        break

if not url_capturada:
    print("❌ No se pudo capturar la URL de ACE-Step")
    proc.kill()
    sys.exit(1)

# ── 4. GENERAR MÚSICA CON LA URL ──
print("[Worker] Generando música con la URL...")
musica_script = Path("../scripts/generar_musica.py")
if musica_script.exists():
    resultado = subprocess.run(
        ["python", str(musica_script), url_capturada,
         "lofi jazz, smooth jazz, saxophone, piano, rain"],
        capture_output=True, text=True, timeout=900
    )
    print(resultado.stdout[-500:])
    if resultado.returncode != 0:
        print(resultado.stderr[-500:])

# ── 4.5. CONVERTIR VÍDEOS A MP4 ──
print("[Worker] Convirtiendo vídeos a MP4...")
video_dir = Path("output")
if video_dir.exists():
    for video in list(video_dir.glob("*.mov")) + list(video_dir.glob("*.webm")) + list(video_dir.glob("*.mkv")):
        print(f"[Worker] Convirtiendo {video.name}...")
        subprocess.run(["python", "../scripts/procesar_video.py", str(video)], check=False)

# ── 5. SUBIR EL MP3 (Y VÍDEOS) A GITHUB ──
print("[Worker] Subiendo archivos a GitHub...")
try:
    subprocess.run(["git", "clone", REPO_URL, "/tmp/repo"], check=True)
    mp3_path = Path("output/cancion_generada.mp3")
    if mp3_path.exists():
        target = Path("/tmp/repo/output/cancion_generada.mp3")
        target.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy(mp3_path, target)
        
        subprocess.run(["git", "-C", "/tmp/repo", "config", "user.email", "kaggle@keiz.com"], check=True)
        subprocess.run(["git", "-C", "/tmp/repo", "config", "user.name", "Kaggle Worker"], check=True)
        subprocess.run(["git", "-C", "/tmp/repo", "add", "output/"], check=True)
        subprocess.run(["git", "-C", "/tmp/repo", "commit", "-m", "feat(kaggle): musica generada por ACE-Step"], check=True)
        subprocess.run(["git", "-C", "/tmp/repo", "push"], check=True)
        print("✅ Música subida a GitHub.")
    else:
        print("❌ No se generó el MP3 (revisa el log de arriba).")
except Exception as e:
    print(f"❌ Error subiendo a GitHub: {e}")

print("[Worker] Tarea completada. Apagando GPU...")
proc.kill()
