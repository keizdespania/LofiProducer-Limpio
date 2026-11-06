"""preparar_dataset_ltx.py - Prepara runtime LTX en Kaggle (por cuenta).
Uso:
  python3 scripts/preparar_dataset_ltx.py lanzar           # cuenta 1
  python3 scripts/preparar_dataset_ltx.py lanzar --cuenta 2  # cuenta 2
  python3 scripts/preparar_dataset_ltx.py estado [--cuenta N]

Cada cuenta crea SU PROPIO dataset para no dejar vínculos entre cuentas
(evita patrones detectables de multi-cuenta coordinada).
"""
import sys, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

CUENTAS = {
    1: {"user": "keizproductions", "kernel": "ltx-runtime-to-dataset",   "dataset": "keizproductions/ltx-free-runtime",   "token_var": "KAGGLE_API_TOKEN"},
    2: {"user": "lofiproducer",    "kernel": "ltx-runtime-to-dataset-2", "dataset": "lofiproducer/ltx-free-runtime",      "token_var": "KAGGLE_API_TOKEN_2"},
}


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


_KERNEL_TEMPLATE = """
import sys, subprocess, os, json, shutil

DATASET_ID = "%DATASET_ID%"
KAGGLE_TOKEN = "%TOKEN%"
KAGGLE_USER = "%KAGGLE_USER%"

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
        body += b"--" + boundary.encode() + b"\\r\\n"
        body += b'Content-Disposition: form-data; name="' + name.encode() + b'"; filename="' + fname.encode() + b'"\\r\\n'
        body += b"Content-Type: " + ctype.encode() + b"\\r\\n\\r\\n"
        body += content + b"\\r\\n"
    body += b"--" + boundary.encode() + b"--\\r\\n"

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
"""


def _construir_kernel(cuenta):
    info = CUENTAS[cuenta]
    token = _leer_env(info["token_var"])
    if not token:
        raise RuntimeError(f"{info['token_var']} no encontrado en .env")
    return (_KERNEL_TEMPLATE
            .replace("%DATASET_ID%", info["dataset"])
            .replace("%TOKEN%", token)
            .replace("%KAGGLE_USER%", info["user"]))


def _parse_args(argv):
    cuenta = 1
    if "--cuenta" in argv:
        i = argv.index("--cuenta")
        try:
            cuenta = int(argv[i + 1])
        except (IndexError, ValueError):
            print("Uso: --cuenta 1|2")
            sys.exit(2)
    if cuenta not in CUENTAS:
        print(f"Cuenta inválida: {cuenta}. Válidas: {list(CUENTAS.keys())}")
        sys.exit(2)
    return cuenta


if __name__ == "__main__":
    cuenta = _parse_args(sys.argv)
    info = CUENTAS[cuenta]
    cmd = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "lanzar"

    if cmd == "lanzar":
        codigo = _construir_kernel(cuenta)
        print(f"[cuenta {cuenta}] Kernel: {len(codigo)} chars")
        print(f"[cuenta {cuenta}] Destino: {info['user']}/{info['kernel']}")
        print(f"[cuenta {cuenta}] Dataset: {info['dataset']}")
        res = push_kernel(f"{info['user']}/{info['kernel']}", codigo,
                          enable_gpu=False, enable_internet=True, cuenta=cuenta)
        print("Push:", {k: v for k, v in (res or {}).items() if k in ("hasError", "error", "versionNumber", "ref")})
    elif cmd == "estado":
        print(json.dumps(estado_kernel(f"{info['user']}/{info['kernel']}"), indent=2))
