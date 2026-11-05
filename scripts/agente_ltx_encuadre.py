"""agente_ltx_encuadre.py - LTX 2.3 I2V via dangkhoa2016 runtime (flujo oficial)."""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-i2v-v2"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola.json"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _construir_kernel():
    github_token = _leer_env("GITHUB_TOKEN")

    codigo = '''"""LTX 2.3 I2V - dangkhoa2016 runtime (flujo oficial)."""
import sys, subprocess, time, pathlib, urllib.request, json, os, base64, glob, shutil

COLA_URL = "''' + COLA_URL + '''"
GITHUB_TOKEN = "''' + github_token + '''"
GITHUB_REPO = "''' + REPO + '''"
T_MAX = 55 * 60

print("=== LTX 2.3 I2V (dangkhoa runtime oficial) ===", flush=True)

# 1. Instalar dependencias Python
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub", "requests"], check=True)

# 2. Copiar runtime de dangkhoa2016 a /kaggle/tmp (escribible)
SRC_DIR = "/kaggle/input/stable-diffusion-cpp-6b3edaa-cuda-t4-runtime"
if not os.path.exists(SRC_DIR):
    print("ERROR: No existe el dataset en", SRC_DIR, flush=True)
    sys.exit(1)

# El dataset contiene un .tar.gz que hay que extraer (según documentación oficial)
tars = glob.glob(SRC_DIR + "/**/*.tar.gz", recursive=True)
if not tars:
    print("ERROR: No se encontró el .tar.gz en el dataset", flush=True)
    print("Contenido:", os.listdir(SRC_DIR), flush=True)
    sys.exit(1)

tar_path = tars[0]
print("Extrayendo:", tar_path, flush=True)

DST_DIR = "/kaggle/tmp/sd-runtime"
if os.path.exists(DST_DIR):
    shutil.rmtree(DST_DIR)
os.makedirs(DST_DIR, exist_ok=True)

with tarfile.open(tar_path, "r:gz") as tar:
    tar.extractall(DST_DIR)

# Buscar run-sd-cli.sh en la carpeta extraída
RUNTIME_DIR = None
for root, dirs, files in os.walk(DST_DIR):
    if "run-sd-cli.sh" in files:
        RUNTIME_DIR = root
        break
if not RUNTIME_DIR:
    print("ERROR: No se encontró run-sd-cli.sh tras extraer", flush=True)
    for root, dirs, files in os.walk(DST_DIR):
        print("  ", root, "->", files[:10], flush=True)
    sys.exit(1)

print("runtime dir:", RUNTIME_DIR, flush=True)
# Dar permisos a todo
for root, dirs, files in os.walk(RUNTIME_DIR):
    for f in files:
        try: os.chmod(os.path.join(root, f), 0o755)
        except: pass


print("LD_LIBRARY_PATH configurado:", CUDA_LIB, flush=True)

# 5. Configurar LD_LIBRARY_PATH con la ruta EXACTA de libcudart.so.12
CUDA_LIB = "/usr/local/lib/python3.13/dist-packages/nvidia/cuda_runtime/lib"
if not os.path.isdir(CUDA_LIB):
    print("ERROR: no existe", CUDA_LIB, flush=True)
    sys.exit(1)

env_vars = os.environ.copy()
env_vars["CUDA_VISIBLE_DEVICES"] = "0"
env_vars["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
env_vars["LD_LIBRARY_PATH"] = CUDA_LIB + ":" + env_vars.get("LD_LIBRARY_PATH", "")
print("LD_LIBRARY_PATH configurado:", CUDA_LIB, flush=True)

print("Verificando ./run-sd-cli.sh --list-devices...", flush=True)
try:
    verify = subprocess.run(
        ["./run-sd-cli.sh", "--list-devices"],
        cwd=RUNTIME_DIR, env=env_vars,
        capture_output=True, text=True, timeout=120
    )
    print("Verify stdout:", verify.stdout[:400], flush=True)
    print("Verify stderr:", verify.stderr[:400], flush=True)
    print("Verify returncode:", verify.returncode, flush=True)
    if verify.returncode != 0:
        print("WARN: sd-cli --list-devices falló", flush=True)
except Exception as e:
    print("ERROR en verify:", e, flush=True)

# 6. Descargar pesos GGUF
print("Descargando pesos GGUF...", flush=True)
from huggingface_hub import hf_hub_download
MODEL_DIR = "/kaggle/tmp/models"
os.makedirs(MODEL_DIR, exist_ok=True)

try:
    diffusion = hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev-Q2_K.gguf", local_dir=MODEL_DIR)
    vae = hf_hub_download("unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_video_vae.safetensors", local_dir=MODEL_DIR)
    audio_vae = hf_hub_download("unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_audio_vae.safetensors", local_dir=MODEL_DIR)
    connectors = hf_hub_download("unsloth/LTX-2.3-GGUF", "text_encoders/ltx-2.3-22b-dev_embeddings_connectors.safetensors", local_dir=MODEL_DIR)
    llm = hf_hub_download("unsloth/gemma-3-12b-it-qat-GGUF", "gemma-3-12b-it-qat-UD-Q4_K_XL.gguf", local_dir=MODEL_DIR)
    print("Pesos listos", flush=True)
except Exception as e:
    print("ERROR descargando pesos:", e, flush=True)
    sys.exit(1)

# 7. Descargar cola
print("Descargando cola:", COLA_URL, flush=True)
try:
    with urllib.request.urlopen(COLA_URL) as r:
        cola = json.loads(r.read())
except Exception as e:
    print("ERROR cola:", e, flush=True)
    sys.exit(1)

pendientes = [item for item in cola if not item.get("completado", False)]
print("Cola:", len(cola), "total,", len(pendientes), "pendientes", flush=True)

if not pendientes:
    print("Nada que hacer.", flush=True)
    sys.exit(0)

# 8. Procesar cada item
for i, item in enumerate(pendientes):
    img_url = item["imagen_url"]
    prompt = item["prompt"]
    filename = item["nombre"]
    frames = item.get("num_frames", 33)

    print("[" + str(i+1) + "/" + str(len(pendientes)) + "] " + filename, flush=True)
    img_path = "/kaggle/tmp/" + filename + "_in.png"
    urllib.request.urlretrieve(img_url, img_path)

    out_path = "/kaggle/tmp/" + filename + ".webm"
    cmd = [
        "./run-sd-cli.sh", "-M", "vid_gen",
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
    print("Ejecutando sd-cli desde", RUNTIME_DIR, flush=True)
    T0 = time.time()
    try:
        result = subprocess.run(cmd, cwd=RUNTIME_DIR, env=env_vars, capture_output=True, text=True, timeout=T_MAX)
        if result.returncode != 0:
            print("ERROR sd-cli (code " + str(result.returncode) + "):", flush=True)
            print("STDOUT:", result.stdout[-500:], flush=True)
            print("STDERR:", result.stderr[-1000:], flush=True)
            continue
    except Exception as e:
        print("ERROR ejecutando sd-cli:", e, flush=True)
        continue

    print("Generado en", round(time.time()-T0, 1), "s", flush=True)
    if not os.path.exists(out_path):
        print("ERROR: no se generó el vídeo", flush=True)
        continue
    size_kb = pathlib.Path(out_path).stat().st_size // 1024
    print("Archivo:", size_kb, "KB", flush=True)

    # 9. Subir a GitHub
    if GITHUB_TOKEN:
        import requests
        url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/videos/" + filename + ".webm"
        headers = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        data = {
            "message": "Add " + filename + ".webm",
            "content": base64.b64encode(pathlib.Path(out_path).read_bytes()).decode(),
            "branch": "main"
        }
        if sha: data["sha"] = sha
        r = requests.put(url, headers=headers, json=data)
        print("GitHub upload:", "OK" if r.status_code in (200, 201) else r.text[:100], flush=True)
        if r.status_code in (200, 201):
            item["completado"] = True

# 10. Actualizar cola
if GITHUB_TOKEN:
    import requests
    url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/data/agent/ltx_cola.json"
    headers = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")
        data = {
            "message": "Update ltx_cola",
            "content": base64.b64encode(json.dumps(cola, indent=2).encode()).decode(),
            "branch": "main",
            "sha": sha
        }
        requests.put(url, headers=headers, json=data)

print("=== FIN ===", flush=True)
'''
    return codigo


def lanzar():
    print("Lanzando LTX I2V a Kaggle...")
    codigo = _construir_kernel()
    print("   Código:", len(codigo), "chars")
    res = push_kernel(KAGGLE_USER + "/" + KERNEL_SLUG, codigo, enable_gpu=True, enable_internet=True, dataset_sources=["dangkhoa2016/stable-diffusion-cpp-6b3edaa-cuda-t4-runtime"])
    print("   Push:", res)
    if isinstance(res, dict) and res.get("hasError"):
        print("ERROR:", res.get("error"))
        return False
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(KAGGLE_USER + "/" + KERNEL_SLUG), indent=2))
