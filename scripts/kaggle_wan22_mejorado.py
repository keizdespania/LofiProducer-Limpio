"""Wan 2.2 v26 - Parametros afinados para evitar el croma verde."""
import sys, subprocess, pathlib

PROMPT = "A fluffy orange cat riding a small red bicycle in a green park, sunny day, highly detailed, cinematic lighting"
NEGATIVE_PROMPT = "blurry, low quality, distorted, green screen, croma, extra limbs, deformed, wheels cut off, watermark, text"
OUTPUT = "/kaggle/working/Wan2GP-outputs/video_mejorado.mp4"

print("=== WAN 2.2 MEJORADO ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg", "safetensors"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

print("Cargando VAE...")
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float16)
print("Cargando pipeline...")
pipe = WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.float16)

pipe.text_encoder.to("cpu")
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

print("Generando video (esto tarda 8-15 min)...")
generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt=NEGATIVE_PROMPT,
    height=480,
    width=832,
    num_frames=81,
    guidance_scale=5.0,
    num_inference_steps=25,
    generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=16)
print(f"✅ Video guardado en {OUTPUT}")
