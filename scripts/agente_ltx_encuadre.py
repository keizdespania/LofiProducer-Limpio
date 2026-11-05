"""agente_ltx_encuadre.py - LTX 2.3 I2V via stable-diffusion.cpp CLI en Kaggle."""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-i2v-encuadre"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_URL = f"https://raw.githubusercontent.com/{REPO}/main/data/agent/ltx_cola.json"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _construir_kernel():
    github_token = _leer_env("GITHUB_TOKEN")

    codigo = f'''"""LTX 2.3 I2V - stable-diffusion.cpp CLI."""
import sys, subprocess, time, pathlib, urllib.request, json, os, base64

COLA_URL = "{COLA_URL}"
GITHUB_TOKEN = "{github_token}"
GITHUB_REPO = "{REPO}"
T_MAX = 55 * 60

print("=== LTX 2.3 I2V (CLI) ===", flush=True)

# 1. Instalar dependencias
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"], check=True)

# 2. Descargar binario sd-cli (dinámico vía API de GitHub)
print("Consultando última release de sd-cli...", flush=True)
import urllib.request, json
API_URL = "https://api.github.com/repos/leejet/stable-diffusion.cpp/releases/latest"
req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "LofiProducer"})
with urllib.request.urlopen(req, timeout=30) as r:
    release = json.loads(r.read())

# Buscar asset Linux x64 (preferir CUDA, fallback Vulkan/CPU)
assets = release.get("assets", [])
candidatos = [a for a in assets if "linux" in a["name"].lower() and ("x86_64" in a["name"].lower() or "x64" in a["name"].lower())]
elegido = None
for pref in ["cuda", "vulkan", "cpu"]:
    for a in candidatos:
        if pref in a["name"].lower():
            elegido = a
            break
    if elegido:
        break
if not elegido and candidatos:
    elegido = candidatos[0]

if not elegido:
    print(f"No hay asset Linux x64. Assets: {[a['name'] for a in assets]}", flush=True)
    sys.exit(1)

print(f"Descargando: {elegido['name']} ({elegido['size']//1024//1024}MB)", flush=True)
BIN_ZIP = "/kaggle/working/sd-cli.zip"
urllib.request.urlretrieve(elegido["browser_download_url"], BIN_ZIP)
subprocess.run(["unzip", "-o", BIN_ZIP, "-d", "/kaggle/working/sd-cli"], check=True)

# Buscar el binario sd-cli en la carpeta extraída (puede estar en subcarpeta)
import glob
binarios = glob.glob("/kaggle/working/sd-cli/**/sd-cli", recursive=True)
if not binarios:
    binarios = glob.glob("/kaggle/working/sd-cli/sd-cli")
if not binarios:
    print("No se encontró sd-cli en el zip", flush=True)
    sys.exit(1)
SD_CLI = binarios[0]
subprocess.run(["chmod", "+x", SD_CLI], check=True)
print(f"sd-cli listo: {SD_CLI}", flush=True)

# 3. Descargar pesos GGUF
print("Descargando pesos GGUF (Q4_K_M)...", flush=True)
from huggingface_hub import hf_hub_download
MODEL_DIR = "/kaggle/working/models"
os.makedirs(MODEL_DIR, exist_ok=True)

diffusion = hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev-UD-Q4_K_M.gguf", local_dir=MODEL_DIR)
vae = hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev_video_vae.safetensors", local_dir=MODEL_DIR)
audio_vae = hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev_audio_vae.safetensors", local_dir=MODEL_DIR)
llm = hf_hub_download("unsloth/LTX-2.3-GGUF", "gemma-3-12b-it-qat-UD-Q4_K_XL.gguf", local_dir=MODEL_DIR)
connectors = hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev_embeddings_connectors.safetensors", local_dir=MODEL_DIR)
print("Pesos listos", flush=True)

# 4. Descargar cola
print(f"Descargando cola: {{COLA_URL}}", flush=True)
with urllib.request.urlopen(COLA_URL) as r:
    cola = json.loads(r.read())

pendientes = [item for item in cola if not item.get("completado", False)]
print(f"Cola: {{len(cola)}} total, {{len(pendientes)}} pendientes", flush=True)

if not pendientes:
    print("Nada que hacer.", flush=True)
    sys.exit(0)

# 5. Procesar cada item
for i, item in enumerate(pendientes):
    img_url = item["imagen_url"]
    prompt = item["prompt"]
    filename = item["nombre"]
    frames = item.get("num_frames", 33)

    print(f"\\n[{{i+1}}/{{len(pendientes)}}] {{filename}}", flush=True)
    img_path = f"/kaggle/working/{{filename}}_in.png"
    urllib.request.urlretrieve(img_url, img_path)

    out_path = f"/kaggle/working/{{filename}}.webm"
    cmd = [
        SD_CLI, "-M", "vid_gen",
        "--diffusion-model", diffusion,
        "--vae", vae,
        "--audio-vae", audio_vae,
        "--llm", llm,
        "--embeddings-connectors", connectors,
        "-p", prompt,
        "--cfg-scale", "6.0", "--sampling-method", "euler",
        "-W", "480", "-H", "832",
        "--offload-to-cpu",
        "--video-frames", str(frames), "--fps", "24",
        "-i", img_path,
        "-o", out_path
    ]
    print(f"Ejecutando sd-cli...", flush=True)
    T0 = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=T_MAX)
    if result.returncode != 0:
        print(f"Error sd-cli: {{result.stderr[-500:]}}", flush=True)
        continue

    print(f"Generado en {{time.time()-T0:.1f}}s", flush=True)
    size_kb = pathlib.Path(out_path).stat().st_size // 1024
    print(f"Archivo: {{size_kb}}KB", flush=True)

    # 6. Subir a GitHub
    if GITHUB_TOKEN:
        import requests
        url = f"https://api.github.com/repos/{{GITHUB_REPO}}/contents/output/videos/{{filename}}.webm"
        headers = {{"Authorization": f"token {{GITHUB_TOKEN}}", "Accept": "application/vnd.github.v3+json"}}
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        data = {{
            "message": f"Add {{filename}}.webm",
            "content": base64.b64encode(pathlib.Path(out_path).read_bytes()).decode(),
            "branch": "main"
        }}
        if sha: data["sha"] = sha
        r = requests.put(url, headers=headers, json=data)
        print("GitHub upload:", "OK" if r.status_code in (200, 201) else r.text[:100], flush=True)
        if r.status_code in (200, 201):
            item["completado"] = True

# 7. Actualizar cola
if GITHUB_TOKEN:
    import requests
    url = f"https://api.github.com/repos/{{GITHUB_REPO}}/contents/data/agent/ltx_cola.json"
    headers = {{"Authorization": f"token {{GITHUB_TOKEN}}", "Accept": "application/vnd.github.v3+json"}}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")
        data = {{
            "message": "Update ltx_cola",
            "content": base64.b64encode(json.dumps(cola, indent=2).encode()).decode(),
            "branch": "main",
            "sha": sha
        }}
        requests.put(url, headers=headers, json=data)

print("=== FIN ===", flush=True)
'''
    return codigo


def lanzar():
    print("🚀 LTX I2V - Lanzando a Kaggle...")
    codigo = _construir_kernel()
    print(f"   Código: {len(codigo)} chars")
    res = push_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}", codigo, enable_gpu=True, enable_internet=True)
    print(f"   Push: {res}")
    if isinstance(res, dict) and res.get("hasError"):
        print(f"❌ Error: {res.get('error')}")
        return False
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
