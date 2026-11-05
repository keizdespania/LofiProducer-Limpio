"""crear_dataset_ltx.py - Crea un Dataset de Kaggle con los pesos de LTX 2.3.
Se ejecuta UNA VEZ. Sube los pesos a Kaggle para que los kernels los monten.
"""
import sys, subprocess, pathlib, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel, salida_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-weights-downloader"


def _construir_kernel():
    codigo = '''"""Descarga los pesos de LTX 2.3 a /kaggle/working/ltx_weights."""
import subprocess, sys, pathlib, os

print("Instalando huggingface_hub...", flush=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "huggingface_hub"], check=True)

from huggingface_hub import hf_hub_download

OUT = pathlib.Path("/kaggle/working/ltx_weights")
OUT.mkdir(parents=True, exist_ok=True)

# 1. Transformer GGUF (Q4_K_M)
print("Descargando transformer...", flush=True)
hf_hub_download("unsloth/LTX-2.3-GGUF", "ltx-2.3-22b-dev-UD-Q4_K_M.gguf", local_dir=str(OUT))

# 2. VAE video y audio
print("Descargando VAE...", flush=True)
hf_hub_download("unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_video_vae.safetensors", local_dir=str(OUT))
hf_hub_download("unsloth/LTX-2.3-GGUF", "vae/ltx-2.3-22b-dev_audio_vae.safetensors", local_dir=str(OUT))

# 3. LLM Gemma 3 12B
print("Descargando LLM...", flush=True)
hf_hub_download("unsloth/gemma-3-12b-it-qat-GGUF", "gemma-3-12b-it-qat-UD-Q4_K_XL.gguf", local_dir=str(OUT))

# 4. Embeddings connectors
print("Descargando connectors...", flush=True)
hf_hub_download("unsloth/LTX-2.3-GGUF", "text_encoders/ltx-2.3-22b-dev_embeddings_connectors.safetensors", local_dir=str(OUT))

print("=== DESCARGAS COMPLETADAS ===", flush=True)
for f in sorted(OUT.rglob("*")):
    if f.is_file():
        print(f"{f.name}: {f.stat().st_size//1024//1024}MB", flush=True)
'''
    return codigo


def lanzar():
    print("📦 Creando Dataset de LTX (descarga de pesos)...")
    codigo = _construir_kernel()
    res = push_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}", codigo, enable_gpu=False, enable_internet=True)
    print(f"Push: {res}")
    if isinstance(res, dict) and res.get("hasError"):
        print(f"❌ {res.get('error')}")
        return False
    print("✅ Kernel lanzado. Espera a que termine y luego descarga los ficheros.")
    return True


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
    elif cmd == "salida":
        print(json.dumps(salida_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}"), indent=2))
