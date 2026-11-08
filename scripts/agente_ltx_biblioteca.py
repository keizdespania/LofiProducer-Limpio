"""Agente LTX Biblioteca - Genera clips de 6s Top-1 con crossfade, en lotes de 20."""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
REPO = "keizdespania/LofiProducer-Limpio"
DATASET_ID = "keizproductions/ltx-free-runtime"


def _img_list():
    p = ROOT / "data/agent/ltx_assets/biblioteca_src"
    return sorted([f.name for f in p.glob("*.jpg")])


def _token():
    p = ROOT / ".env"
    if not p.exists(): return ""
    for line in p.read_text().splitlines():
        if line.startswith("GITHUB_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


KERNEL_CODE = r'''
import sys, subprocess, os, json, time, pathlib, urllib.request, base64, glob, shutil, requests

def log(m): print(m, flush=True)
log("=== LTX BIBLIOTECA TOP-1 v3 ===")

# Config inyectada por orquestador
GITHUB_TOKEN = "__TOKEN__"
REPO = "__REPO__"
BIBLIO_RAW = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_assets/biblioteca_src/"
IMGS = __IMGS__
NEG = "worst quality, inconsistent motion, blurry, jittery, text, letters, words, writing, subtitles, watermark"

PROMPTS = [
    "Cinematic close-up, subject motion subtle, camera pushes in slowly, deep blue neon lighting, highly detailed",
    "The subject continues their action, screen glow pulses, subtle camera pan right, cyberpunk atmosphere",
    "The subject pauses, staring intently at the screen, slow camera zoom out, dramatic side lighting",
]

# 1. Runtime
RT = "/kaggle/working/rt"; os.makedirs(RT, exist_ok=True)
SRC = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "sd_bin" in dirs or "nvidia_libs" in dirs:
        SRC = root; break
if not SRC: raise RuntimeError("Dataset runtime NO encontrado")
shutil.copytree(SRC, RT, dirs_exist_ok=True)

# 2. LD_LIBRARY_PATH
cuda_dirs = glob.glob(RT + "/nvidia_libs/nvidia/*/lib")
os.environ["LD_LIBRARY_PATH"] = ":".join(cuda_dirs) + ":" + os.environ.get("LD_LIBRARY_PATH", "")
if not glob.glob(RT + "/nvidia_libs/**/libcudart.so.12", recursive=True):
    raise RuntimeError("libcudart.so.12 NO encontrada")

# 3. Server bin
os.makedirs("/tmp/sd_bin/bin", exist_ok=True)
shutil.copy(RT + "/sd_bin/bin/sd-server", "/tmp/sd_bin/bin/sd-server")
os.chmod("/tmp/sd_bin/bin/sd-server", 0o755)

# 4. free-aistudio
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "--depth", "1", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.insert(0, WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

# 5. Modelos + server
from src.downloader import download_models
download_models(preset="LTX-Video-2.3-Q3")
from src.server import start_server
start_server(load_audio_vae=True)
time.sleep(90)

OUT = "/kaggle/working/clips"; os.makedirs(OUT, exist_ok=True)
SERVER = "http://127.0.0.1:1234"

def _gen_seg(init_path, tag, prompt, is_vertical=False):
    with open(init_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
    w, h = (480, 832) if is_vertical else (832, 480)
    payload = {
        "prompt": prompt, "negative_prompt": NEG,
        "init_image": "data:image/jpeg;base64," + b64,
        "vae_decode_only": False, "video_frames": 49, "fps": 24,
        "width": w, "height": h,
        "sample_params": {"sample_steps": 16, "cfg_scale": 3.5, "sample_method": "euler", "scheduler": "discrete"},
    }
    r = requests.post(SERVER + "/sdcpp/v1/vid_gen", json=payload, timeout=600)
    if r.status_code not in (200, 201, 202): return None
    job_id = r.json().get("id") or r.json().get("job_id")
    t0 = time.time()
    while time.time() - t0 < 900:
        time.sleep(5)
        jd = requests.get(SERVER + "/sdcpp/v1/jobs/" + job_id, timeout=30).json()
        if jd.get("status") in ("completed", "succeeded", "done"):
            out = f"{OUT}/{tag}.mp4"
            vd = (jd.get("result") or {}).get("b64_json")
            if vd:
                with open(out, "wb") as f: f.write(base64.b64decode(vd))
                return out
            return None
        if jd.get("status") in ("failed", "error"): return None
    return None

def _last_frame(video):
    out = video.replace(".mp4", "_last.png")
    subprocess.run(["ffmpeg", "-y", "-sseof", "-0.1", "-i", video, "-vframes", "1", out], check=True, capture_output=True)
    return out

def _concat_crossfade(videos, out_path):
    fc = (
        "[0:v][1:v]xfade=transition=fade:duration=0.4:offset=1.64[v01];"
        "[v01][2:v]xfade=transition=fade:duration=0.4:offset=3.28[v02];"
        "[v02]eq=contrast=1.08:saturation=1.15:brightness=-0.02,"
        "curves=preset=medium_contrast,"
        "noise=alls=5:allf=t+u,"
        "format=yuv420p[vfinal]"
    )
    cmd = [
        "ffmpeg", "-y", "-i", videos[0], "-i", videos[1], "-i", videos[2],
        "-filter_complex", fc, "-map", "[vfinal]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-r", "24",
        out_path,
    ]
    return subprocess.run(cmd, capture_output=True, text=True).returncode == 0

def gh_upload(local, remote):
    with open(local, "rb") as f: content = base64.b64encode(f.read()).decode()
    url = "https://api.github.com/repos/" + REPO + "/contents/" + remote
    h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=h, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    data = {"message": "clip top-1: " + pathlib.Path(local).name, "content": content, "branch": "main"}
    if sha: data["sha"] = sha
    return requests.put(url, headers=h, json=data, timeout=120).status_code in (200, 201)

IMGDIR = "/kaggle/working/imgs"; os.makedirs(IMGDIR, exist_ok=True)
ok_count = 0
for i, img_name in enumerate(IMGS, 1):
    log("[" + str(i) + "/" + str(len(IMGS)) + "] " + img_name)
    img_path = os.path.join(IMGDIR, img_name)
    if not os.path.exists(img_path):
        try:
            urllib.request.urlretrieve(BIBLIO_RAW + img_name, img_path)
        except Exception as e:
            log("  DESC FAIL: " + str(e)); continue

    is_vertical = "9x16" in img_name
    out_name = img_name.replace(".jpg", ".mp4")
    cat = img_name.rsplit("_", 2)[0]
    remote = "output/videos/biblioteca/" + cat + "/" + out_name

    s1_local = os.path.join(OUT, "s1_" + out_name)
    r = requests.get("https://raw.githubusercontent.com/" + REPO + "/main/" + remote, timeout=60)
    if r.status_code == 200:
        log("  Seg1 de GitHub (ahorro)")
        with open(s1_local, "wb") as f: f.write(r.content)
    else:
        log("  Generando Seg1...")
        s1_local = _gen_seg(img_path, img_name.replace(".jpg", "_s1"), PROMPTS[0], is_vertical)
        if not s1_local: continue

    log("  Generando Seg2...")
    s2 = _gen_seg(_last_frame(s1_local), img_name.replace(".jpg", "_s2"), PROMPTS[1], is_vertical)
    if not s2: continue

    log("  Generando Seg3...")
    s3 = _gen_seg(_last_frame(s2), img_name.replace(".jpg", "_s3"), PROMPTS[2], is_vertical)
    if not s3: continue

    log("  Concat + crossfade + grading...")
    out = os.path.join(OUT, out_name)
    if not _concat_crossfade([s1_local, s2, s3], out):
        log("  FFMPEG crossfade FAIL, fallback concat simple")
        lista = OUT + "/lista_" + str(i) + ".txt"
        with open(lista, "w") as f:
            for v in [s1_local, s2, s3]: f.write("file '" + v + "'\n")
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista,
                        "-c:v", "libx264", "-preset", "ultrafast", out],
                       check=True, capture_output=True)

    for v in [s1_local, s2, s3]:
        if os.path.exists(v): os.remove(v)

    log("  CLIP 6s OK: " + str(os.path.getsize(out) // 1024) + " KB")
    if gh_upload(out, remote):
        ok_count += 1
        log("  GitHub OK")

log("=== FIN: " + str(ok_count) + "/" + str(len(IMGS)) + " clips ===")
'''


def _construir(lote):
    imgs = _img_list()
    sel = imgs[(lote-1)*20 : lote*20]
    if not sel:
        raise ValueError(f"Lote {lote} sin imágenes")
    code = (KERNEL_CODE
            .replace("__TOKEN__", _token())
            .replace("__REPO__", REPO)
            .replace("__IMGS__", json.dumps(sel)))
    return code, sel


def lanzar(lote):
    code, sel = _construir(lote)
    slug = f"{KAGGLE_USER}/ltx-biblioteca-v1-lote{lote}"
    print(f"Lanzando lote {lote}: {len(sel)} clips -> {slug}")
    res = push_kernel(slug, code, enable_gpu=True, enable_internet=True, dataset_sources=[DATASET_ID])
    print(f"Push: {res}")
    return not (isinstance(res, dict) and res.get("hasError"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lote1"
    if cmd.startswith("lote"):
        sys.exit(0 if lanzar(int(cmd[4:])) else 1)
