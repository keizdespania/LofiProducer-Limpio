"""agente_ltx_kaggle_v6.py - LTX 2.3 productor (dataset runtime cacheado).
Arranque ~81s vs 412s v5: descarga dataset (5-10s) en vez de pip install (325s).
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-free-t4-v6"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_PENDIENTE_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola_pendiente.json"
COLA_COMPLETADOS_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola_completados.json"
DATASET_ID = "keizproductions/ltx-free-runtime"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


_KERNEL = r'''"""LTX 2.3 productor (dataset runtime cacheado)."""
import sys, subprocess, os, json, time, pathlib, urllib.request, base64, glob, shutil

COLA_PENDIENTE_URL = "%COLA_P%"
COLA_COMPLETADOS_URL = "%COLA_C%"
GITHUB_TOKEN = "%GH%"
GITHUB_REPO = "%REPO%"
DATASET_ID = "%DS%"

print("=== LTX v6 (runtime cacheado) ===", flush=True)

# 1. Dataset runtime ya montado en /kaggle/input/ por dataset_sources
# (no necesita kaggle CLI ni credenciales — Kaggle lo monta read-only automaticamente)
print("[1/6] Copiando dataset runtime de /kaggle/input/...", flush=True)
RT = "/kaggle/working/rt"
os.makedirs(RT, exist_ok=True)
# Kaggle monta como /kaggle/input/<slug-sin-user>/ donde slug = "ltx-free-runtime"
SRC = "/kaggle/input/ltx-free-runtime"
if not os.path.exists(SRC):
    # Fallback: buscar cualquier dir que contenga nvidia_libs o sd_bin
    for cand in glob.glob("/kaggle/input/*"):
        if os.path.exists(cand + "/nvidia_libs") or os.path.exists(cand + "/sd_bin"):
            SRC = cand; break
if not os.path.exists(SRC):
    raise RuntimeError("Dataset runtime no encontrado. Revisar dataset_sources en push_kernel.")
print("  SRC:", SRC, flush=True)
shutil.copytree(SRC, RT, dirs_exist_ok=True)
print("  RT listo:", len(os.listdir(RT)), "entradas", flush=True)

# 2. Montar LD_LIBRARY_PATH
print("[2/6] Montando LD_LIBRARY_PATH...", flush=True)
cuda_dirs = glob.glob(RT + "/nvidia_libs/nvidia/*/lib")
os.environ["LD_LIBRARY_PATH"] = ":".join(cuda_dirs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
print("  dirs:", cuda_dirs, flush=True)
print("  libcudart:", glob.glob(RT + "/nvidia_libs/**/libcudart.so.12", recursive=True), flush=True)

# 3. Symlink binario
print("[3/6] Instalando binario...", flush=True)
os.makedirs("/tmp/sd_bin/bin", exist_ok=True)
shutil.copy(RT + "/sd_bin/bin/sd-server", "/tmp/sd_bin/bin/sd-server")
os.chmod("/tmp/sd_bin/bin/sd-server", 0o755)

# 4. Clonar repo (necesario para src.server)
print("[4/6] Clonando free-aistudio...", flush=True)
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.append(WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

# 5. Descargar modelos Q3 (no cacheados, ~7s a 300MB/s)
print("[5/6] Descargando modelos Q3...", flush=True)
from src.downloader import download_models
download_models(preset="LTX-Video-2.3-Q3")

# 6. Arrancar servidor
print("[6/6] Arrancando servidor...", flush=True)
from src.server import start_server, tail_logs
server_process = start_server(load_audio_vae=True)
print("Esperando 90s...", flush=True)
time.sleep(90)

# Procesar cola
SERVER_URL = "http://127.0.0.1:1234"
with urllib.request.urlopen(COLA_PENDIENTE_URL) as r:
    pendientes = json.loads(r.read())
print("Pendientes:", len(pendientes), flush=True)

import requests
for i, item in enumerate(pendientes):
    nombre = item["nombre"]; prompt = item["prompt"]; img_url = item["imagen_url"]
    print("[" + str(i+1) + "/" + str(len(pendientes)) + "] " + nombre, flush=True)
    img_path = "/kaggle/working/" + nombre + "_in.png"
    urllib.request.urlretrieve(img_url, img_path)
    with open(img_path, "rb") as f:
        img_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode()

    payload = {
        "prompt": prompt,
        "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark",
        "init_image": img_uri,
        "video_frames": 97,
        "fps": 24,
        "width": 832, "height": 480,
        "sample_params": {"sample_steps": 20, "cfg_scale": 3.0, "sample_method": "euler", "scheduler": "discrete"},
    }
    try:
        r = requests.post(SERVER_URL + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
        job = r.json(); job_id = job.get("id")
        deadline = time.time() + 900
        result = None
        while time.time() < deadline:
            time.sleep(5)
            jd = requests.get(SERVER_URL + "/sdcpp/v1/jobs/" + job_id, timeout=30).json()
            if jd.get("status") in ("completed","succeeded","done"): result = jd; break
            if jd.get("status") in ("failed","error"): break
        if result:
            vdata = (result.get("result") or {}).get("b64_json")
            if vdata:
                out = "/kaggle/working/" + nombre + ".mp4"
                with open(out, "wb") as f: f.write(base64.b64decode(vdata))
                print("Video:", os.path.getsize(out)//1024, "KB", flush=True)
                # Upload
                url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/videos/" + nombre + ".mp4"
                h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
                sha = requests.get(url, headers=h).json().get("sha")
                data = {"message": "Add " + nombre, "content": base64.b64encode(open(out,"rb").read()).decode(), "branch": "main"}
                if sha: data["sha"] = sha
                rr = requests.put(url, headers=h, json=data)
                print("GitHub:", "OK" if rr.status_code in (200,201) else rr.text[:100], flush=True)
    except Exception as e:
        print("Error:", type(e).__name__, ":", e, flush=True)

print("=== FIN ===", flush=True)
'''


def _construir_kernel():
    return (_KERNEL
            .replace("%COLA_P%", COLA_PENDIENTE_URL)
            .replace("%COLA_C%", COLA_COMPLETADOS_URL)
            .replace("%GH%", _leer_env("GITHUB_TOKEN"))
            .replace("%REPO%", REPO)
            .replace("%DS%", DATASET_ID))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        codigo = _construir_kernel()
        print("Kernel:", len(codigo), "chars")
        res = push_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}", codigo, enable_gpu=True, enable_internet=True,
                          dataset_sources=[DATASET_ID])
        print("Push:", {k:v for k,v in (res or {}).items() if k in ("hasError","error","versionNumber")})
    elif cmd == "estado":
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
