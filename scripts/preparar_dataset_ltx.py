"""preparar_dataset_ltx.py - Kernel que prepara runtime LTX y crea Dataset Kaggle.
Evita descarga manual: el kernel hace pip install CUDA 12 + restore_binary
y publica /kaggle/working/ltx_runtime como Dataset keizproductions/ltx-free-runtime.

Regla #20: reescrito limpio 2026-11-06 tras 3 parches fallidos.
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-runtime-to-dataset"
DATASET_ID = "keizproductions/ltx-free-runtime"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# Template del kernel: comillas simples triples exteriores, dentro SIN triples
# comillas (comentarios # y strings normales). Placeholders %TOKEN% y %DATASET_ID%
_KERNEL_TEMPLATE = r'''"""Kernel: prepara runtime LTX + crea Dataset Kaggle."""
import sys, subprocess, os, json, shutil

DATASET_ID = "%DATASET_ID%"
KAGGLE_TOKEN = "%TOKEN%"
KAGGLE_USER = "keizproductions"

print("=== PREPARANDO RUNTIME LTX ===", flush=True)

rt = "/kaggle/working/ltx_runtime"
os.makedirs(rt, exist_ok=True)

# [1/4] CUDA 12
print("[1/4] pip install CUDA 12...", flush=True)
if not os.path.exists(rt + "/nvidia_libs/nvidia"):
    subprocess.run([sys.executable, "-m", "pip", "install", "--target", rt + "/nvidia_libs",
                    "nvidia-cuda-runtime-cu12==12.4.127",
                    "nvidia-cublas-cu12==12.4.5.8",
                    "nvidia-cudnn-cu12==9.1.0.70"], check=True)
else:
    print("  ya existe nvidia_libs, skip", flush=True)

# [2/4] Binario
print("[2/4] Restaurando binario...", flush=True)
WORK = "/kaggle/working/free-aistudio"
if not os.path.exists(WORK):
    subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.append(WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)
from src.downloader import restore_binary
restore_binary(repo="airesearch-official/free-aistudio", tag="v1.0.0")
if os.path.exists(rt + "/sd_bin"):
    shutil.rmtree(rt + "/sd_bin")
shutil.copytree("/tmp/sd_bin", rt + "/sd_bin")

# [3/4] Metadata
print("[3/4] Metadata...", flush=True)
meta = {"title": "LTX Free Runtime", "id": DATASET_ID, "licenses": [{"name": "CC0-1.0"}]}
with open(rt + "/dataset-metadata.json", "w") as f:
    json.dump(meta, f, indent=2)

# [4/4] Crear dataset
print("[4/4] Creando Dataset con --dir-mode zip...", flush=True)
os.environ["KAGGLE_USERNAME"] = KAGGLE_USER
os.environ["KAGGLE_KEY"] = KAGGLE_TOKEN
r = subprocess.run(["kaggle", "datasets", "create", "-p", rt, "--dir-mode", "zip"],
                   capture_output=True, text=True, timeout=900)
out = (r.stdout or "") + (r.stderr or "")
print("CLI rc:", r.returncode, flush=True)
print("CLI out (tail):", out[-2000:], flush=True)

errores = ("error", "failed", "please upload", "skipping folder")
cli_ok = r.returncode == 0 and not any(e in out.lower() for e in errores)

if not cli_ok:
    print("CLI fallo, intentando REST multipart...", flush=True)
    import urllib.request, zipfile
    zip_path = "/kaggle/working/ltx_runtime_full.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for root, dirs, files in os.walk(rt):
            for f in files:
                if f == "dataset-metadata.json":
                    continue
                fp = os.path.join(root, f)
                z.write(fp, os.path.relpath(fp, rt))
    print("ZIP:", os.path.getsize(zip_path) // 1024 // 1024, "MB", flush=True)

    boundary = "----kaggleBoundary"
    body = b""
    for name, fname, content, ctype in [
        ("metadata", "dataset-metadata.json", json.dumps(meta).encode(), "application/json"),
        ("file", "ltx_runtime_full.zip", open(zip_path, "rb").read(), "application/zip"),
    ]:
        body += b"--" + boundary.encode() + b"\r\n"
        body += b'Content-Disposition: form-data; name="' + name.encode() + b'"; filename="' + fname.encode() + b'"\r\n'
        body += b"Content-Type: " + ctype.encode() + b"\r\n\r\n"
        body += content + b"\r\n"
    body += b"--" + boundary.encode() + b"--\r\n"

    req = urllib.request.Request(
        "https://www.kaggle.com/api/v1/datasets/create/new",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + KAGGLE_TOKEN,
                 "Content-Type": "multipart/form-data; boundary=" + boundary},
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            print("REST OK:", resp.read().decode()[:500], flush=True)
    except Exception as e:
        body_err = e.read()[:500].decode(errors="replace") if hasattr(e, "read") else str(e)[:500]
        print("REST fallo:", type(e).__name__, body_err, flush=True)
else:
    print("CLI creo el dataset OK", flush=True)

print("=== FIN ===", flush=True)
'''


def _construir_kernel():
    token = _leer_env("KAGGLE_API_TOKEN")
    if not token:
        raise RuntimeError("KAGGLE_API_TOKEN no encontrado en .env")
    codigo = _KERNEL_TEMPLATE.replace("%TOKEN%", token).replace("%DATASET_ID%", DATASET_ID)
    return codigo


def lanzar():
    print(f"Lanzando kernel {KAGGLE_USER}/{KERNEL_SLUG}...")
    codigo = _construir_kernel()
    print("  Codigo:", len(codigo), "chars")
    res = push_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}", codigo, enable_gpu=False, enable_internet=True)
    print("  Push:", {k: v for k, v in (res or {}).items() if k in ("hasError", "error", "ref", "versionNumber")})
    return not (isinstance(res, dict) and res.get("hasError"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
