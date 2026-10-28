"""Wan 2.2 v8 - Mínimo, T4 optimizado, rápido."""
import sys, subprocess

PROMPT = "A cat riding a bicycle in a sunny park, cinematic, 4k, masterpiece"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v8 ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float32)
pipe = WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.float16)
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
