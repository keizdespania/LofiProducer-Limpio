"""Wan 2.2 v21 - Pipeline oficial HF (público, sin token)."""
import sys, subprocess

PROMPT = "A cat riding a bicycle in a sunny park, cinematic, 4k, masterpiece"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v21 (HF oficial) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

print("Cargando VAE...")
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float16)

print("Cargando pipeline (descarga desde HF)...")
pipe = WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.float16)

pipe.text_encoder.to("cpu")
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt="low quality, blurry, distorted, watermark, text",
    height=480, width=832, num_frames=25,
    guidance_scale=5.0, num_inference_steps=20, generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=8)
print("=== FINALIZADO ===")
