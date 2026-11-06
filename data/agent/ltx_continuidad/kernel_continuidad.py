"""Kernel LTX continuidad — 3 segmentos de 2s encadenados por último frame.
Reutiliza el patrón del v6.2 (runtime + server). Aislado (no toca colas).
Resultado: output/videos/test_continuidad/{seg1,seg2,seg3,test_continuidad_6s}.mp4
"""
import sys, subprocess, os, json, time, pathlib, urllib.request, base64, glob, shutil
import requests

GITHUB_TOKEN = "REEMPLAZAR_TOKEN_AQUI"
GITHUB_REPO = "keizdespania/LofiProducer-Limpio"
IMG_URL = "https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/data/agent/ltx_assets/hacker_base_832x480.jpg"
PROMPT = "hacker encapuchado de espaldas tecleando en teclado mecánico, múltiples pantallas con código y noticias, iluminación neón azul, cámara estática, movimiento sutil de dedos y hombros, sin cambios de plano"
NEG = "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark"

def log(msg): print(msg, flush=True)

log("=== TEST CONTINUIDAD LTX ===")

# ═══ 1. RUNTIME (copia exacta v6.2, NO TOCAR) ═══
log("[1/8] Buscando runtime...")
RT = "/kaggle/working/rt"
os.makedirs(RT, exist_ok=True)
SRC = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "sd_bin" in dirs or "nvidia_libs" in dirs:
        SRC = root; break
if not SRC: raise RuntimeError("Dataset runtime NO encontrado")
log("  SRC: " + SRC)
shutil.copytree(SRC, RT, dirs_exist_ok=True)

log("[2/8] LD_LIBRARY_PATH...")
cuda_dirs = glob.glob(RT + "/nvidia_libs/nvidia/*/lib")
os.environ["LD_LIBRARY_PATH"] = ":".join(cuda_dirs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
cudart = glob.glob(RT + "/nvidia_libs/**/libcudart.so.12", recursive=True)
log("  dirs: " + str(len(cuda_dirs)) + " | libcudart: " + str(len(cudart)))
if not cudart: raise RuntimeError("libcudart.so.12 NO encontrada")

log("[3/8] sd-server...")
os.makedirs("/tmp/sd_bin/bin", exist_ok=True)
shutil.copy(RT + "/sd_bin/bin/sd-server", "/tmp/sd_bin/bin/sd-server")
os.chmod("/tmp/sd_bin/bin/sd-server", 0o755)

log("[4/8] free-aistudio...")
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.append(WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

log("[5/8] Modelos Q3...")
from src.downloader import download_models
download_models(preset="LTX-Video-2.3-Q3")

log("[6/8] Arrancando server...")
from src.server import start_server
server_process = start_server(load_audio_vae=True)
log("  esperando 90s...")
time.sleep(90)

# ═══ 2. LÓGICA CONTINUIDAD ═══
OUT = "/kaggle/working/out"
os.makedirs(OUT, exist_ok=True)
SERVER_URL = "http://127.0.0.1:1234"

def to_b64_uri(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

def run_job(init_path, tag, frames=49, w=832, h=480):
    log("[JOB " + tag + "] init=" + pathlib.Path(init_path).name + " " + str(frames) + "f " + str(w) + "x" + str(h))
    payload = {
        "prompt": PROMPT,
        "negative_prompt": NEG,
        "init_image": to_b64_uri(init_path),
        "vae_decode_only": False,
        "video_frames": frames,
        "fps": 24,
        "width": w,
        "height": h,
        "sample_params": {"sample_steps": 12, "cfg_scale": 3.0,
                          "sample_method": "euler", "scheduler": "discrete"},
    }
    r = requests.post(SERVER_URL + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
    log("  POST: " + str(r.status_code))
    if r.status_code not in (200, 201, 202):
        log("  body: " + r.text[:300]); return None
    job = r.json(); job_id = job.get("id") or job.get("job_id")
    log("  job_id: " + str(job_id))
    if not job_id: return None
    deadline = time.time() + 900
    while time.time() < deadline:
        time.sleep(5)
        jd = requests.get(SERVER_URL + "/sdcpp/v1/jobs/" + job_id, timeout=30).json()
        st = jd.get("status", "?")
        if int(time.time()) % 30 < 5: log("  poll: " + st)
        if st in ("completed", "succeeded", "done"):
            vdata = (jd.get("result") or {}).get("b64_json")
            if not vdata:
                log("  sin b64_json"); return None
            out = OUT + "/" + tag + ".mp4"
            with open(out, "wb") as f:
                f.write(base64.b64decode(vdata))
            log("  OK " + str(os.path.getsize(out)//1024) + " KB")
            return out
        if st in ("failed", "error", "cancelled"):
            log("  FAILED: " + str(jd)[:400]); return None
    log("  TIMEOUT"); return None

def last_frame(video):
    """Último frame real del MP4 (-sseof -0.1, no -sseof 0)."""
    out = video.replace(".mp4", "_last.png")
    subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", video,
                    "-vframes", "1", out], check=True, capture_output=True)
    return out

def concat_videos(videos, out_path):
    lista = OUT + "/lista.txt"
    with open(lista, "w") as f:
        for v in videos:
            f.write("file '" + v + "'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                    "-i", lista, "-c", "copy", out_path],
                   check=True, capture_output=True)

def gh_upload(local, remote):
    with open(local, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/" + remote
    h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=h, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    data = {"message": "test: " + pathlib.Path(local).name,
            "content": content, "branch": "main"}
    if sha: data["sha"] = sha
    r = requests.put(url, headers=h, json=data, timeout=120)
    return r.status_code in (200, 201)

# ═══ 3. EJECUCIÓN ═══
log("[7/8] Descargando imagen base...")
IMG = "/kaggle/working/base.jpg"
urllib.request.urlretrieve(IMG_URL, IMG)
log("  " + str(os.path.getsize(IMG)//1024) + " KB")

log("[8/8] Generando 3 segmentos encadenados...")
seg1 = run_job(IMG, "seg1", 49, 832, 480)
if not seg1: sys.exit(1)
f_last_1 = last_frame(seg1)
log("  Frame 1 extraído: " + f_last_1)
seg2 = run_job(f_last_1, "seg2", 49, 832, 480)
if not seg2: sys.exit(1)
f_last_2 = last_frame(seg2)
log("  Frame 2 extraído: " + f_last_2)
seg3 = run_job(f_last_2, "seg3", 49, 832, 480)
if not seg3: sys.exit(1)

log("Concatenando 3 segmentos...")
concat = OUT + "/test_continuidad_6s.mp4"
concat_videos([seg1, seg2, seg3], concat)
log("  concat: " + str(os.path.getsize(concat)//1024) + " KB")

log("Subiendo a GitHub...")
ups = [
    (seg1, "output/videos/test_continuidad/seg1.mp4"),
    (seg2, "output/videos/test_continuidad/seg2.mp4"),
    (seg3, "output/videos/test_continuidad/seg3.mp4"),
    (concat, "output/videos/test_continuidad/test_continuidad_6s.mp4"),
]
for local, remote in ups:
    ok = gh_upload(local, remote)
    log("  " + ("OK " if ok else "FAIL ") + remote)

log("=== FIN ===")
