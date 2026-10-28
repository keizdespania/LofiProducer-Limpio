"""Wan 2.2 v25 - HF oficial, configuracion minima para T4."""
import sys, subprocess

PROMPT = "A cat riding a bicycle"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v25 (HF Oficial, Minimo) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

print("Cargando VAE...")
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float16)

print("Cargando pipeline (descarga HF)...")
pipe = WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.float16)

pipe.text_encoder.to("cpu")
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt="low quality, blurry",
    height=320, width=512,
    num_frames=17,
    guidance_scale=5.0, num_inference_steps=15, generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=8)
print("=== FINALIZADO ===")
