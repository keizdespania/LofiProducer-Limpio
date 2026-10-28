"""Wan 2.2 v18 - Pipeline completo con Transformer/VAE desde Input y T5 desde HF."""
import sys, subprocess, pathlib

PROMPT = "A cat riding a bicycle in a sunny park, cinematic, 4k, masterpiece"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v18 (Input + HF para T5) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg", "safetensors"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan, WanTransformer3DModel
from diffusers.utils import export_to_video

# Rutas locales al dataset
base = pathlib.Path("/kaggle/input/datasets/rangith/video-generation-dataset")
transformer_path = base / "wan2.2_ti2v_5B_fp16.safetensors"
vae_path = base / "wan2.2_vae.safetensors"

print(f"Transformer: {transformer_path.exists()}")
print(f"VAE: {vae_path.exists()}")

print("Cargando Transformer desde Input...")
transformer = WanTransformer3DModel.from_single_file(str(transformer_path), torch_dtype=torch.float16)

print("Cargando VAE desde Input...")
vae = AutoencoderKLWan.from_single_file(str(vae_path), torch_dtype=torch.float32)

print("Cargando pipeline base (T5 desde HF)...")
pipe = WanPipeline.from_pretrained(
    "Wan-AI/Wan2.2-TI2V-5B-Diffusers",
    transformer=transformer,
    vae=vae,
    torch_dtype=torch.float16
)

pipe.text_encoder.to("cpu")
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt="low quality, blurry, distorted, watermark, text",
    height=480, width=832, num_frames=49,
    guidance_scale=5.0, num_inference_steps=30, generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=16)
print("=== FINALIZADO ===")
