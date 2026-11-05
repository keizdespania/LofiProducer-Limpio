"""agente_ltx_kaggle_free.py - LTX 2.3 en Kaggle T4 (Q3, sin limite).
Replica el notebook de free-aistudio y procesa la cola de pendientes.
"""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-free-t4"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_PENDIENTE_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola_pendiente.json"
COLA_COMPLETADOS_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola_completados.json"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _construir_kernel():
    github_token = _leer_env("GITHUB_TOKEN")

    codigo = '''"""LTX 2.3 Free en Kaggle T4 (Q3, sin limite)."""
import sys, subprocess, os, json, time, pathlib, urllib.request, base64

COLA_PENDIENTE_URL = "''' + COLA_PENDIENTE_URL + '''"
COLA_COMPLETADOS_URL = "''' + COLA_COMPLETADOS_URL + '''"
GITHUB_TOKEN = "''' + github_token + '''"
GITHUB_REPO = "''' + REPO + '''"

print("=== LTX 2.3 Free T4 ===", flush=True)

# 1. Clonar repo free-aistudio
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    print("Clonando free-aistudio...", flush=True)
    subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
else:
    print("Actualizando free-aistudio...", flush=True)
    subprocess.run(["git", "-C", WORK, "pull"], check=True)

# 2. Instalar requirements
print("Instalando dependencias...", flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)
sys.path.append(WORK)

# 3.5 Fix CUDA runtime 12 (Kaggle T4 tiene CUDA 13, sd-server busca libcudart.so.12)
# Instalamos a /tmp/cuda12_libs (--target) y seteamos LD_LIBRARY_PATH global
# ANTES del import start_server (que hace env=os.environ.copy()).
# Bypass del bug de find_cuda_library_paths() en src/server.py: filtra por
# "site-packages" pero Kaggle usa /usr/local/lib/python3.13/dist-packages.
print("Instalando CUDA 12 runtime en /tmp/cuda12_libs...", flush=True)
r = subprocess.run([sys.executable, "-m", "pip", "install",
                    "--target", "/tmp/cuda12_libs",
                    "nvidia-cuda-runtime-cu12==12.4.127",
                    "nvidia-cublas-cu12==12.4.5.8",
                    "nvidia-cudnn-cu12==9.1.0.70"],
                   capture_output=True, text=True)
print("  pip rc:", r.returncode, flush=True)
if r.returncode != 0:
    print("  pip stderr (tail):", r.stderr[-500:], flush=True)

# Buscar libcudart.so.12 y demas libs CUDA 12 en /tmp/cuda12_libs
import glob as _glob
cuda_lib_dirs = sorted(_glob.glob("/tmp/cuda12_libs/nvidia/*/lib"))
cudart = _glob.glob("/tmp/cuda12_libs/**/libcudart.so.12", recursive=True)
cublas = _glob.glob("/tmp/cuda12_libs/**/libcublas.so.12", recursive=True)
cudnn  = _glob.glob("/tmp/cuda12_libs/**/libcudnn.so*", recursive=True)
print("  dirs CUDA:", cuda_lib_dirs, flush=True)
print("  libcudart.so.12:", cudart, flush=True)
print("  libcublas.so.12:", cublas, flush=True)
print("  libcudnn:", cudnn, flush=True)

if cudart:
    ld = ":".join(cuda_lib_dirs)
    os.environ["LD_LIBRARY_PATH"] = ld + ":" + os.environ.get("LD_LIBRARY_PATH", "")
    print("  LD_LIBRARY_PATH =", os.environ["LD_LIBRARY_PATH"][:300], flush=True)
    print("  ✅ libcudart encontrada — start_server deberia arrancar", flush=True)
else:
    print("  ❌ libcudart.so.12 NO se descargo — via_c sigue bloqueada", flush=True)
    raise RuntimeError("libcudart.so.12 no disponible tras pip install --target")

# 3. Descargar binario + pesos
print("Descargando binario y pesos (Q3)...", flush=True)
from src.downloader import restore_binary, download_models
restore_binary(repo="airesearch-official/free-aistudio", tag="v1.0.0")
download_models(preset="LTX-Video-2.3-Q3")

# 4. Levantar servidor C++
print("Arrancando servidor C++...", flush=True)
from src.server import start_server, tail_logs
server_process = start_server(load_audio_vae=True)
print("Esperando 90s a que cargue el modelo...", flush=True)
time.sleep(90)
print("Server logs:", flush=True)
print(tail_logs(), flush=True)

# 5. Descargar colas
print("Descargando colas...", flush=True)
with urllib.request.urlopen(COLA_PENDIENTE_URL) as r:
    pendientes = json.loads(r.read())
try:
    with urllib.request.urlopen(COLA_COMPLETADOS_URL) as r:
        completados = json.loads(r.read())
except Exception:
    completados = []

print("Pendientes:", len(pendientes), "| Completados:", len(completados), flush=True)

if not pendientes:
    print("Nada que hacer.", flush=True)
    sys.exit(0)

# 6. Procesar cada item llamando al servidor local
# El servidor sd-server expone un endpoint HTTP en localhost (puerto por defecto 8080)
SERVER_URL = "http://127.0.0.1:1234"

for i, item in enumerate(pendientes):
    nombre = item["nombre"]
    prompt = item["prompt"]
    img_url = item["imagen_url"]

    print("", flush=True)
    print("[" + str(i+1) + "/" + str(len(pendientes)) + "] " + nombre, flush=True)

    # Descargar imagen
    img_path = "/kaggle/working/" + nombre + "_in.png"
    urllib.request.urlretrieve(img_url, img_path)
    print("Imagen:", os.path.getsize(img_path) // 1024, "KB", flush=True)

    # Llamar al servidor sdcpp (API nativa asincrona)
    import requests, base64 as _b64
    try:
        # 1) Codificar imagen como data URI base64
        with open(img_path, "rb") as f:
            img_b64 = _b64.b64encode(f.read()).decode()
        img_data_uri = "data:image/png;base64," + img_b64

        # 2) POST a /sdcpp/v1/vid_gen (endpoint real de sd-server)
        payload = {
            "prompt": prompt,
            "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark",
            "init_image": img_data_uri,
            "vae_decode_only": False,
            "video_frames": 97,
            "fps": 24,
            "width": 832,
            "height": 480,
        }
        r = requests.post(SERVER_URL + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
        if r.status_code not in (200, 201, 202):
            print("POST fallo:", r.status_code, r.text[:300], flush=True)
            continue
        job = r.json()
        job_id = job.get("id") or job.get("job_id") or job.get("task_id")
        print("Job lanzado:", job_id, "| status:", job.get("status"), flush=True)
        if not job_id:
            print("Sin job_id en respuesta:", job, flush=True)
            continue

        # 3) Polling a /sdcpp/v1/jobs/{id} hasta completar (max 15 min)
        import time as _time
        deadline = _time.time() + 900
        result = None
        while _time.time() < deadline:
            _time.sleep(5)
            jr = requests.get(SERVER_URL + "/sdcpp/v1/jobs/" + job_id, timeout=30)
            if jr.status_code != 200:
                print("Poll fallo:", jr.status_code, flush=True); continue
            jd = jr.json()
            st = jd.get("status", "?")
            print("  poll:", st, flush=True)
            if st in ("completed", "succeeded", "done"):
                result = jd; break
            if st in ("failed", "error", "cancelled"):
                print("Job fallido:", jd, flush=True); break
        if not result:
            print("Timeout o fallo de job", flush=True); continue

        # 4) Extraer b64 del video
        video_data = None
        if isinstance(result, dict):
            r2 = result.get("result") or {}
            if isinstance(r2, dict):
                video_data = r2.get("b64_json") or r2.get("video")
            if not video_data:
                video_data = result.get("b64_json") or result.get("video")

        if video_data:
            out_path = "/kaggle/working/" + nombre + ".mp4"
            with open(out_path, "wb") as f:
                f.write(_b64.b64decode(video_data))
            print("Video:", os.path.getsize(out_path) // 1024, "KB", flush=True)

            # 5) Subir a GitHub
            if GITHUB_TOKEN:
                url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/videos/" + nombre + ".mp4"
                headers = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
                rr = requests.get(url, headers=headers)
                sha = rr.json().get("sha") if rr.status_code == 200 else None
                data = {
                    "message": "Add " + nombre + ".mp4",
                    "content": _b64.b64encode(pathlib.Path(out_path).read_bytes()).decode(),
                    "branch": "main"
                }
                if sha: data["sha"] = sha
                rr = requests.put(url, headers=headers, json=data)
                print("GitHub:", "OK" if rr.status_code in (200, 201) else rr.text[:100], flush=True)
                if rr.status_code in (200, 201):
                    item["completado"] = True
        else:
            print("Sin video en respuesta:", str(result)[:300], flush=True)
    except Exception as e:
        print("Error:", type(e).__name__, ":", e, flush=True)

print("=== FIN ===", flush=True)
'''
    return codigo


def lanzar():
    print("Lanzando LTX Free T4 a Kaggle (sin limite)...")
    codigo = _construir_kernel()
    print("   Código:", len(codigo), "chars")
    res = push_kernel(KAGGLE_USER + "/" + KERNEL_SLUG, codigo, enable_gpu=True, enable_internet=True)
    print("   Push:", res)
    return not (isinstance(res, dict) and res.get("hasError"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(KAGGLE_USER + "/" + KERNEL_SLUG), indent=2))
