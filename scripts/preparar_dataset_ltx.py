"""preparar_dataset_ltx.py - Kernel que prepara runtime LTX y crea Dataset Kaggle.
Evita descarga manual: el kernel hace pip install CUDA 12 + restore_binary
y publica /kaggle/working/ltx_runtime como Dataset keizproductions/ltx-free-runtime.
"""
import sys, pathlib

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


def _construir_kernel():
    token = _leer_env("KAGGLE_API_TOKEN")  # KGAT de keizproductions
    if not token:
        raise RuntimeError("KAGGLE_API_TOKEN no encontrado en .env")

    codigo = '''"""Prepara runtime LTX + crea Dataset Kaggle (sin descarga manual)."""
import sys, subprocess, os, json, pathlib, shutil

DATASET_ID = "''' + DATASET_ID + '''"
KAGGLE_TOKEN = "''' + token + '''"
KAGGLE_USER = "keizproductions"

print("=== PREPARANDO RUNTIME LTX ===", flush=True)

# 1. Instalar CUDA 12 en /kaggle/working/ltx_runtime/nvidia_libs
print("[1/4] pip install CUDA 12...", flush=True)
rt = "/kaggle/working/ltx_runtime"
os.makedirs(rt, exist_ok=True)
subprocess.run([sys.executable, "-m", "pip", "install", "--target", rt + "/nvidia_libs",
                "nvidia-cuda-runtime-cu12==12.4.127",
                "nvidia-cublas-cu12==12.4.5.8",
                "nvidia-cudnn-cu12==9.1.0.70"], check=True)

# 2. Clonar repo + restaurar binario
print("[2/4] Clonando free-aistudio...", flush=True)
WORK = "/kaggle/working/free-aistudio"
subprocess.run(["git", "clone", "https://github.com/airesearch-official/free-aistudio.git", WORK], check=True)
sys.path.append(WORK)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", WORK + "/requirements.txt"], check=True)

print("[3/4] Restaurando binario sd-server...", flush=True)
from src.downloader import restore_binary
restore_binary(repo="airesearch-official/free-aistudio", tag="v1.0.0")
shutil.copytree("/tmp/sd_bin", rt + "/sd_bin", dirs_exist_ok=True)

# 3. Metadata del dataset
print("[4/4] Creando Dataset...", flush=True)
meta = {
    "title": "LTX Free Runtime",
    "id": DATASET_ID,
    "licenses": [{"name": "CC0-1.0"}]
}
with open(rt + "/dataset-metadata.json", "w") as f:
    json.dump(meta, f, indent=2)

# 4. Intentar CLI primero
os.environ["KAGGLE_USERNAME"] = KAGGLE_USER
os.environ["KAGGLE_KEY"] = KAGGLE_TOKEN
r = subprocess.run(["kaggle", "datasets", "create", "-p", rt],
                   capture_output=True, text=True, timeout=600)
print("CLI rc:", r.returncode, flush=True)
print("CLI stdout:", r.stdout[-1500:], flush=True)
print("CLI stderr:", r.stderr[-1500:], flush=True)

# 5. Fallback REST multipart si CLI falla
if r.returncode != 0:
    print("CLI fallo, probando REST multipart...", flush=True)
    import urllib.request, zipfile, tempfile
    # Comprimir solo lo necesario (excluye dataset-metadata.json y cosas gordas)
    zip_path = "/kaggle/working/ltx_runtime.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(rt):
            for f in files:
                if f == "dataset-metadata.json":
                    continue
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, rt)
                z.write(fp, rel)
    print("ZIP:", os.path.getsize(zip_path) // 1024 // 1024, "MB", flush=True)

    # POST multipart a /api/v1/datasets/create/new
    boundary = "----kaggleBoundary"
    meta_json = json.dumps(meta)
    body = b""
    for name, filename, content, ctype in [
        ("metadata", "dataset-metadata.json", meta_json.encode(), "application/json"),
        ("file", "ltx_runtime.zip", open(zip_path, "rb").read(), "application/zip"),
    ]:
        body += b"--" + boundary.encode() + b"\\r\\n"
        body += b'Content-Disposition: form-data; name="' + name.encode() + b'"; filename="' + filename.encode() + b'"\\r\\n'
        body += b"Content-Type: " + ctype.encode() + b"\\r\\n\\r\\n"
        body += content + b"\\r\\n"
    body += b"--" + boundary.encode() + b"--\\r\\n"

    req = urllib.request.Request(
        "https://www.kaggle.com/api/v1/datasets/create/new",
        data=body, method="POST",
        headers={
            "Authorization": "Bearer " + KAGGLE_TOKEN,
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            print("REST OK:", resp.read().decode()[:500], flush=True)
    except Exception as e:
        print("REST fallo:", type(e).__name__, str(e)[:500], flush=True)

print("=== FIN ===", flush=True)
'''
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
        import json
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
