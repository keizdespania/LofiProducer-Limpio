"""Kernel LTX v6.2 FUNCIONAL — patrón base que se debe replicar.
Este es el código de referencia probado en producción (capibara_4 + capibara_5).
Cualquier kernel nuevo (continuidad, hook, short largo) debe copiar este patrón.
NO modificar la sección de runtime. Adaptar solo la parte de "Procesando cola".
"""
import sys, subprocess, os, json, time, pathlib, urllib.request, base64, glob, shutil

COLA_PENDIENTE_URL = "https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/data/agent/ltx_cola_pendiente.json"
COLA_COMPLETADOS_URL = "https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/data/agent/ltx_cola_completados.json"
GITHUB_TOKEN = "REEMPLAZAR_TOKEN_AQUI"
GITHUB_REPO = "keizdespania/LofiProducer-Limpio"
DATASET_ID = "keizproductions/ltx-free-runtime"

def log(msg):
    print(msg, flush=True)

def _gh_get(path):
    import base64 as _b
    import requests as _rq
    url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/" + path
    h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    r = _rq.get(url, headers=h)
    if r.status_code == 200:
        d = r.json()
        return _b.b64decode(d["content"]), d["sha"]
    return None, str(r.status_code)

def _gh_put(path, content_bytes, message, sha):
    import base64 as _b
    import requests as _rq
    url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/" + path
    h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    data = {"message": message, "content": _b.b64encode(content_bytes).decode(), "branch": "main"}
    if sha:
        data["sha"] = sha
    r = _rq.put(url, headers=h, json=data)
    if r.status_code in (200, 201):
        return True, r.json().get("content", {}).get("sha")
    return False, r.text[:200]

def mover_a_completados(nombre):
    log("  cola: moviendo " + nombre + " a completados...")
    comp_bytes, comp_sha = _gh_get("data/agent/ltx_cola_completados.json")
    if comp_bytes is None:
        log("  cola ERROR get completados: " + str(comp_sha)); return False
    pend_bytes, pend_sha = _gh_get("data/agent/ltx_cola_pendiente.json")
    if pend_bytes is None:
        log("  cola ERROR get pendiente: " + str(pend_sha)); return False
    comp = json.loads(comp_bytes); pend = json.loads(pend_bytes)
    item = None; pend_rest = []
    for x in pend:
        if x.get("nombre") == nombre:
            item = x; item["completado"] = True
        else:
            pend_rest.append(x)
    if item is None:
        log("  cola WARN: " + nombre + " no está en pendiente"); return False
    comp.append(item)
    ok, e = _gh_put("data/agent/ltx_cola_completados.json",
                    json.dumps(comp, indent=2, ensure_ascii=False).encode(),
                    "chore(ltx): " + nombre + " completado", comp_sha)
    if not ok:
        log("  cola ERROR put completados: " + str(e)); return False
    ok, e = _gh_put("data/agent/ltx_cola_pendiente.json",
                    json.dumps(pend_rest, indent=2, ensure_ascii=False).encode(),
                    "chore(ltx): quitar " + nombre + " de pendiente", pend_sha)
    if not ok:
        log("  cola ERROR put pendiente: " + str(e)); return False
    log("  cola OK: " + nombre + " movido")
    return True

log("=== LTX v6.2 (steps:12 + auto-cola) ===")

# ═══ RUNTIME — NO TOCAR. Funciona. ═══
log("[1/7] Buscando runtime...")
RT = "/kaggle/working/rt"
os.makedirs(RT, exist_ok=True)
SRC = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "sd_bin" in dirs or "nvidia_libs" in dirs:
        SRC = root; break
if not SRC:
    raise RuntimeError("Dataset runtime NO encontrado. Añadir dataset_sources=['keizproductions/ltx-free-runtime']")
log("  SRC: " + SRC)
shutil.copytree(SRC, RT, dirs_exist_ok=True)

log("[2/7] LD_LIBRARY_PATH...")
cuda_dirs = glob.glob(RT + "/nvidia_libs/nvidia/*/lib")
os.environ["LD_LIBRARY_PATH"] = ":".join(cuda_dirs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
cudart = glob.glob(RT + "/nvidia_libs/**/libcudart.so.12", recursive=True)
log("  dirs: " + str(len(cuda_dirs)) + " | libcudart: " + str(len(cudart)))
if not cudart:
    raise RuntimeError("libcudart.so.12 NO encontrada en dataset")

log("[3/7] sd-server...")
os.makedirs("/tmp/sd_bin/bin", exist_ok=True)
shutil.copy(RT + "/sd_bin/bin/sd-server", "/tmp/sd_bin/bin/sd-server")
os.chmod("/tmp/sd_bin/bin/sd-server", 0o755)

log("[4/7] free-aistudio...")
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.append(WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

log("[5/7] Modelos Q3...")
from src.downloader import download_models
download_models(preset="LTX-Video-2.3-Q3")

log("[6/7] Arrancando server...")
from src.server import start_server
server_process = start_server(load_audio_vae=True)
log("  esperando 90s...")
time.sleep(90)

# ═══ LÓGICA DE NEGOCIO — aquí se cambia por continuidad, cola, o lo que sea ═══
log("[7/7] Procesando cola...")
SERVER_URL = "http://127.0.0.1:1234"
with urllib.request.urlopen(COLA_PENDIENTE_URL) as r:
    pendientes = json.loads(r.read())
log("  pendientes: " + str(len(pendientes)))

import requests
for i, item in enumerate(pendientes):
    nombre = item["nombre"]; prompt = item["prompt"]; img_url = item["imagen_url"]
    log("[" + str(i+1) + "/" + str(len(pendientes)) + "] " + nombre)

    img_path = "/kaggle/working/" + nombre + "_in.png"
    try:
        data = requests.get(img_url, timeout=30).content
        with open(img_path, "wb") as f: f.write(data)
        log("  img: " + str(len(data)//1024) + " KB")
    except Exception as e:
        log("  ERROR imagen: " + str(e)); continue

    with open(img_path, "rb") as f:
        img_uri = "data:image/png;base64," + base64.b64encode(f.read()).decode()

    payload = {
        "prompt": prompt,
        "negative_prompt": "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark",
        "init_image": img_uri,
        "vae_decode_only": False,
        "video_frames": item.get("video_frames", 25),
        "fps": 24,
        "width": item.get("width", 832),
        "height": item.get("height", 480),
        "sample_params": {"sample_steps": 12, "cfg_scale": 3.0, "sample_method": "euler", "scheduler": "discrete"},
    }

    try:
        r = requests.post(SERVER_URL + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
        log("  POST: " + str(r.status_code))
        if r.status_code not in (200, 201, 202):
            log("  POST body: " + r.text[:300]); continue
        job = r.json(); job_id = job.get("id") or job.get("job_id")
        log("  job_id: " + str(job_id))
        if not job_id:
            log("  sin job_id: " + str(job)[:300]); continue

        deadline = time.time() + 900
        result = None; poll_n = 0
        while time.time() < deadline:
            time.sleep(5); poll_n += 1
            jd = requests.get(SERVER_URL + "/sdcpp/v1/jobs/" + job_id, timeout=30).json()
            st = jd.get("status", "?")
            log("  poll " + str(poll_n) + ": " + st)
            if st in ("completed", "succeeded", "done"): result = jd; break
            if st in ("failed", "error", "cancelled"):
                log("  JOB FAILED: " + str(jd)[:400]); break

        if not result:
            log("  sin resultado"); continue

        vdata = (result.get("result") or {}).get("b64_json")
        if not vdata:
            log("  sin b64_json: " + str(result)[:300]); continue

        out = "/kaggle/working/" + nombre + ".mp4"
        with open(out, "wb") as f: f.write(base64.b64decode(vdata))
        log("  Video: " + str(os.path.getsize(out)//1024) + " KB")

        url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/videos/" + nombre + ".mp4"
        h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
        sha = requests.get(url, headers=h).json().get("sha")
        data_up = {"message": "Add " + nombre, "content": base64.b64encode(open(out,"rb").read()).decode(), "branch": "main"}
        if sha: data_up["sha"] = sha
        rr = requests.put(url, headers=h, json=data_up)
        if rr.status_code in (200, 201):
            log("  GitHub: OK")
            mover_a_completados(nombre)
        else:
            log("  GitHub FAIL: " + rr.text[:100])
    except Exception as e:
        log("  ERROR: " + type(e).__name__ + ": " + str(e))

log("=== FIN ===")
