"""agente_wan_encuadre.py - Wan Factory (Turbo + Batch).
Lee una cola de imágenes de GitHub, las anima con Wan 2.2 Turbo (4 pasos)
y sube los resultados a GitHub. NO TOCA el pipeline principal.
"""
import sys, json, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel, salida_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "wan-factory-encuadre"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_URL = f"https://raw.githubusercontent.com/{REPO}/main/data/agent/wan_cola.json"
COLA_LOCAL = ROOT / "data" / "agent" / "wan_cola.json"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _construir_kernel():
    github_token = _leer_env("GITHUB_TOKEN")

    codigo = f'''"""Wan Factory - Turbo (4 pasos) + Batch."""
import sys, subprocess, time, pathlib, base64, urllib.request, json

COLA_URL = "{COLA_URL}"
GITHUB_TOKEN = "{github_token}"
GITHUB_REPO = "{REPO}"
T_MAX = 55 * 60  # 55 min max por sesion

print("=== WAN FACTORY (Turbo Batch) ===", flush=True)
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg", "ftfy", "sentencepiece", "protobuf"], check=True)

import torch
from diffusers import WanImageToVideoPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video, load_image
import requests

# 1. Leer cola de GitHub
print(f"Descargando cola: {{COLA_URL}}", flush=True)
try:
    with urllib.request.urlopen(COLA_URL) as r:
        cola = json.loads(r.read())
except Exception as e:
    print(f"❌ Error cola: {{e}}", flush=True)
    sys.exit(1)

# Filtrar pendientes
pendientes = [item for item in cola if not item.get("completado", False)]
print(f"Cola: {{len(cola)}} total, {{len(pendientes)}} pendientes", flush=True)

if not pendientes:
    print("✅ Nada que hacer.", flush=True)
    sys.exit(0)

# 2. Cargar modelo Turbo
model_id = "cbensimon/Wan2.2-TI2V-5B-Turbo-Diffusers"
print(f"Cargando VAE ({{model_id}})...", flush=True)
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.bfloat16)
print("Cargando pipeline I2V Turbo...", flush=True)
pipe = WanImageToVideoPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.bfloat16)
pipe.text_encoder.to("cpu")
pipe.transformer.enable_gradient_checkpointing()
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

T_START = time.time()
for i, item in enumerate(pendientes):
    if time.time() - T_START > T_MAX:
        print(f"TIMEOUT a {{int((time.time()-T_START)/60)}}min. Procesados {{i}}/{{len(pendientes)}}.", flush=True)
        break

    img_url = item["imagen_url"]
    prompt = item["prompt"]
    filename = item["nombre"]
    res = item.get("resolution", "832x480")
    frames = item.get("num_frames", 49)
    steps = item.get("num_steps", 4)

    print(f"\\n[{{i+1}}/{{len(pendientes)}}] {{filename}}", flush=True)
    print(f"  Imagen: {{img_url}}", flush=True)
    print(f"  Prompt: {{prompt[:60]}}...", flush=True)

    # Descargar imagen
    img_path = f"/kaggle/working/{{filename}}_in.png"
    try:
        urllib.request.urlretrieve(img_url, img_path)
        image = load_image(img_path)
    except Exception as e:
        print(f"  ❌ Error imagen: {{e}}", flush=True)
        continue

    # Generar
    h, w = [int(x) for x in res.split("x")]
    try:
        T0 = time.time()
        video = pipe(
            image=image, prompt=prompt,
            negative_prompt="text, letters, words, writing, subtitles, watermark, logo, signature",
            height=h, width=w,
            num_frames=frames, num_inference_steps=steps, guidance_scale=1.0
        ).frames[0]
        print(f"  ✅ Generado en {{time.time()-T0:.1f}}s", flush=True)
    except Exception as e:
        print(f"  ❌ Error generacion: {{e}}", flush=True)
        continue

    # Guardar
    out_path = f"/kaggle/working/{{filename}}.mp4"
    export_to_video(video, out_path, fps=16)
    size_kb = pathlib.Path(out_path).stat().st_size // 1024
    print(f"  📁 {{filename}}.mp4 ({{size_kb}}KB)", flush=True)

    # Subir a GitHub
    if GITHUB_TOKEN:
        url = f"https://api.github.com/repos/{{GITHUB_REPO}}/contents/output/videos/{{filename}}.mp4"
        headers = {{"Authorization": f"token {{GITHUB_TOKEN}}", "Accept": "application/vnd.github.v3+json"}}
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None
        data = {{
            "message": f"Add {{filename}}.mp4",
            "content": base64.b64encode(pathlib.Path(out_path).read_bytes()).decode(),
            "branch": "main"
        }}
        if sha: data["sha"] = sha
        r = requests.put(url, headers=headers, json=data)
        if r.status_code in (200, 201):
            print(f"  ✅ Subido a GitHub", flush=True)
            item["completado"] = True
        else:
            print(f"  ⚠️ GitHub upload: {{r.status_code}} {{r.text[:100]}}", flush=True)

# 3. Actualizar cola en GitHub
if GITHUB_TOKEN:
    print("\\nActualizando cola...", flush=True)
    url = f"https://api.github.com/repos/{{GITHUB_REPO}}/contents/data/agent/wan_cola.json"
    headers = {{"Authorization": f"token {{GITHUB_TOKEN}}", "Accept": "application/vnd.github.v3+json"}}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")
        data = {{
            "message": "Update cola (Wan Factory)",
            "content": base64.b64encode(json.dumps(cola, indent=2).encode()).decode(),
            "branch": "main",
            "sha": sha
        }}
        r = requests.put(url, headers=headers, json=data)
        print("Cola actualizada" if r.status_code in (200, 201) else f"Error cola: {{r.text[:100]}}", flush=True)

print("=== FIN ===", flush=True)
'''
    return codigo


def lanzar():
    print("🚀 Wan Factory - Lanzando a Kaggle...")
    codigo = _construir_kernel()
    print(f"   Código: {len(codigo)} chars")

    slug = f"{KAGGLE_USER}/{KERNEL_SLUG}"
    res = push_kernel(slug, codigo, enable_gpu=True, enable_internet=True)
    print(f"   Push: {res}")

    if isinstance(res, dict) and res.get("hasError"):
        print(f"❌ Error: {res.get('error')}")
        return False
    return True


def estado():
    return estado_kernel(f"{KAGGLE_USER}/{KERNEL_SLUG}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado(), indent=2))
