import modal
import subprocess
import time
import re

# 1. Definir la imagen (entorno) con CUDA, Git y FFmpeg
image = (
    modal.Image.from_registry("nvidia/cuda:13.0.0-cudnn-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "ffmpeg")
    .run_commands(
        "git clone --branch v0.1.6 --depth 1 https://github.com/ace-step/ACE-Step-1.5.git /opt/ace-step",
    )
    .uv_pip_install(
        "/opt/ace-step", "hf_transfer==0.1.9", "torchcodec==0.10.0", "torch~=2.10.0"
    )
    .env({"ACESTEP_PROJECT_ROOT": "/opt/ace-step", "HF_HUB_ENABLE_HF_TRANSFER": "1"})
)

# 2. Volumen para cachear los pesos (para no descargarlos cada vez)
model_cache = modal.Volume.from_name("ACE-Step-v15-model-cache", create_if_missing=True)

app = modal.App("ace-step-music")

@app.function(
    image=image,
    gpu="T4",
    volumes={"/opt/ace-step/checkpoints": model_cache},
    timeout=1800,
)
def generar_musica(prompt: str, duracion: int = 30):
    # 1. Arrancar el servidor de ACE-Step en segundo plano
    proc = subprocess.Popen(
        ["uv", "run", "acestep", "--share", "--init_service", "true"],
        cwd="/opt/ace-step",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
    )
    
    # 2. Capturar la URL de Gradio
    url = None
    inicio = time.time()
    while time.time() - inicio < 300:
        line = proc.stdout.readline()
        if not line: break
        m = re.search(r'https://([a-z0-9]+)\.gradio\.live', line)
        if m:
            url = m.group(0)
            break
    
    if not url:
        proc.kill()
        return {"status": "error", "mensaje": "No se capturó la URL"}
    
    # 3. Aquí iría la lógica para generar la música con la URL
    # (Por ahora, devolvemos la URL para probar)
    return {"status": "ok", "url": url}

@app.local_entrypoint()
def main(prompt: str = "lofi jazz, piano suave"):
    print(f"Lanzando generación en Modal...")
    resultado = generar_musica.remote(prompt)
    print(f"Resultado: {resultado}")
