"""Genera clips LTX desde las 120 imágenes de biblioteca_src.
Modo: batch por lotes de 40 (3 kernels totales).
Lote 1 = imágenes 1-40, Lote 2 = 41-80, Lote 3 = 81-120."""
import sys, json, pathlib, base64, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
REPO = "keizdespania/LofiProducer-Limpio"
DATASET_ID = "keizproductions/ltx-free-runtime"
BIBLIO_RAW = f"https://raw.githubusercontent.com/{REPO}/main/data/agent/ltx_assets/biblioteca_src/"

# Las 120 imágenes listadas (el kernel solo procesará el lote que le toque)
def _img_list():
    p = ROOT / "data/agent/ltx_assets/biblioteca_src"
    return sorted([f.name for f in p.glob("*.jpg")])

def _token():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("GITHUB_TOKEN="): return line.split("=", 1)[1].strip()
    return ""

KERNEL_CODE = r'''
import sys, subprocess, os, json, time, pathlib, urllib.request, base64, glob, shutil
import requests

GITHUB_TOKEN = "__TOKEN__"
REPO = "keizdespania/LofiProducer-Limpio"
BIBLIO_RAW = "https://raw.githubusercontent.com/__REPO__/main/data/agent/ltx_assets/biblioteca_src/"
IMGS = __IMGS__
PROMPT = "subtle movement, breathing, typing fingers, blinking screens, camera static, no camera movement"
NEG = "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark"

def log(m): print(m, flush=True)
log(f"=== LTX BIBLIOTECA ({len(IMGS)} clips) ===")

# 1. Runtime
log("[1/6] Runtime...")
RT = "/kaggle/working/rt"; os.makedirs(RT, exist_ok=True)
SRC = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "sd_bin" in dirs or "nvidia_libs" in dirs: SRC = root; break
if not SRC: raise RuntimeError("Dataset runtime NO encontrado")
shutil.copytree(SRC, RT, dirs_exist_ok=True)

log("[2/6] LD_LIBRARY_PATH...")
cuda_dirs = glob.glob(RT + "/nvidia_libs/nvidia/*/lib")
os.environ["LD_LIBRARY_PATH"] = ":".join(cuda_dirs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
if not glob.glob(RT + "/nvidia_libs/**/libcudart.so.12", recursive=True):
    raise RuntimeError("libcudart.so.12 NO encontrada")

log("[3/6] sd-server...")
os.makedirs("/tmp/sd_bin/bin", exist_ok=True)
shutil.copy(RT + "/sd_bin/bin/sd-server", "/tmp/sd_bin/bin/sd-server")
os.chmod("/tmp/sd_bin/bin/sd-server", 0o755)

log("[4/6] free-aistudio...")
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "--depth", "1",
                    "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.insert(0, WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

log("[5/6] Modelos + server...")
from src.downloader import download_models
download_models(preset="LTX-Video-2.3-Q3")
from src.server import start_server
start_server(load_audio_vae=True)
log("  esperando 90s...")
time.sleep(90)

# 6. Generar cada clip
OUT = "/kaggle/working/clips"; os.makedirs(OUT, exist_ok=True)
SERVER = "http://127.0.0.1:1234"

def gen_clip(img_path, img_name, idx, total):
    log(f"[{idx}/{total}] {img_name}")
    out = os.path.join(OUT, img_name.replace(".jpg", ".mp4"))
    if os.path.exists(out): log("  ya existe"); return out
    with open(img_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = {
        "prompt": PROMPT,
        "negative_prompt": NEG,
        "init_image": "data:image/jpeg;base64," + b64,
        "vae_decode_only": False,
        "video_frames": 49,
        "fps": 24,
        "width": 832,
        "height": 480,
        "sample_params": {"sample_steps": 12, "cfg_scale": 3.0,
                          "sample_method": "euler", "scheduler": "discrete"},
    }
    try:
        r = requests.post(SERVER + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
        if r.status_code not in (200, 201, 202):
            log(f"  POST {r.status_code}: {r.text[:200]}"); return None
        job = r.json(); job_id = job.get("id") or job.get("job_id")
        if not job_id: log("  sin job_id"); return None
        t0 = time.time()
        while time.time() - t0 < 900:
            time.sleep(5)
            jd = requests.get(SERVER + "/sdcpp/v1/jobs/" + job_id, timeout=30).json()
            st = jd.get("status", "?")
            if int(time.time() - t0) % 60 < 5:
                log(f"  poll: {st} ({int(time.time()-t0)}s)")
            if st in ("completed", "succeeded", "done"):
                vd = (jd.get("result") or {}).get("b64_json")
                if not vd: log("  sin b64"); return None
                with open(out, "wb") as f:
                    f.write(base64.b64decode(vd))
                log(f"  OK {os.path.getsize(out)//1024} KB en {int(time.time()-t0)}s")
                return out
            if st in ("failed", "error", "cancelled"):
                log(f"  FAILED: {str(jd)[:300]}"); return None
        log("  TIMEOUT"); return None
    except Exception as e:
        log(f"  ERROR: {type(e).__name__}: {str(e)[:100]}"); return None

def gh_upload(local, remote):
    with open(local, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    url = f"https://api.github.com/repos/{REPO}/contents/{remote}"
    h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=h, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    data = {"message": f"clip: {pathlib.Path(local).name}", "content": content, "branch": "main"}
    if sha: data["sha"] = sha
    r = requests.put(url, headers=h, json=data, timeout=120)
    return r.status_code in (200, 201)

IMGDIR = "/kaggle/working/imgs"; os.makedirs(IMGDIR, exist_ok=True)
ok_count = 0
for i, img_name in enumerate(IMGS, 1):
    img_url = BIBLIO_RAW + img_name
    img_path = os.path.join(IMGDIR, img_name)
    if not os.path.exists(img_path):
        try:
            urllib.request.urlretrieve(img_url, img_path)
        except Exception as e:
            log(f"[{i}] DESC FAIL {img_name}: {e}"); continue
    clip = gen_clip(img_path, img_name, i, len(IMGS))
    if clip:
        # Subir a GitHub en output/videos/biblioteca/{categoria}/nombre.mp4
        cat = img_name.rsplit("_", 2)[0].replace("16x9", "").replace("9x16", "").strip("_")
        # category es todo menos "NN_aspect.jpg"
        parts = img_name.rsplit("_", 2)
        cat = parts[0]
        remote = f"output/videos/biblioteca/{cat}/{os.path.basename(clip)}"
        if gh_upload(clip, remote):
            ok_count += 1
            log(f"  GitHub OK: {remote}")

log(f"=== FIN: {ok_count}/{len(IMGS)} clips generados y subidos ===")
'''

def _construir(lote):
    imgs = _img_list()
    if lote == 1: sel = imgs[0:40]
    elif lote == 2: sel = imgs[40:80]
    elif lote == 3: sel = imgs[80:120]
    else: raise ValueError(f"lote {lote} no válido (1,2,3)")
    code = KERNEL_CODE.replace("__TOKEN__", _token())
    code = code.replace("__REPO__", REPO)
    code = code.replace("__IMGS__", json.dumps(sel))
    return code, sel

def lanzar(lote):
    code, sel = _construir(lote)
    slug = f"{KAGGLE_USER}/ltx-biblioteca-v1-lote{lote}"
    print(f"Lanzando lote {lote}: {len(sel)} clips → {slug}")
    print(f"   Código: {len(code)} chars")
    res = push_kernel(slug, code, enable_gpu=True, enable_internet=True,
                      dataset_sources=[DATASET_ID])
    print(f"   Push: {res}")
    return not (isinstance(res, dict) and res.get("hasError"))

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lote1"
    if cmd.startswith("lote"):
        n = int(cmd[4:])
        sys.exit(0 if lanzar(n) else 1)
    elif cmd == "estado":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/ltx-biblioteca-v1-lote{n}"), indent=2))
