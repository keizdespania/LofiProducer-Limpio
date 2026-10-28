"""Wan 2.2 v11 - Ruta directa al Kaggle Input."""
import sys, subprocess, os, pathlib

PROMPT = "A cat riding a bicycle in a sunny park, cinematic, 4k, masterpiece"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v11 (Ruta Directa Input) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

# 1. Ruta directa que Kaggle asigna al dataset
base_path = pathlib.Path("/kaggle/input/wan2-2-ti2v-5b")

# 2. Fallback: buscar model_index.json por si está en una subcarpeta
if not (base_path / "model_index.json").exists():
    print("Buscando model_index.json en /kaggle/input...")
    for f in pathlib.Path("/kaggle/input").rglob("model_index.json"):
        base_path = f.parent
        break

print(f"Cargando modelo desde: {base_path}")
vae = AutoencoderKLWan.from_pretrained(str(base_path), subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(str(base_path), vae=vae, torch_dtype=torch.float16)
pipe.enable_model_cpu_offload()

print("Generando video...")
output = pipe(
    prompt=PROMPT,
    height=480,
    width=832,
    num_frames=24,
    guidance_scale=5.0,
    num_inference_steps=20,
).frames[0]

export_to_video(output, OUTPUT, fps=8)
print("=== FINALIZADO ===")
