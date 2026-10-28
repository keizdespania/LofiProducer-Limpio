"""Wan 2.2 v23 - Anti-OOM definitivo: VAE Tiling + T5 CPU + Pocos pasos."""
import sys, subprocess, pathlib

PROMPT = "A cat riding a bicycle in a sunny park, cinematic, 4k"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v23 (Anti-OOM) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg", "safetensors"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan, WanTransformer3DModel
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
base = pathlib.Path("/kaggle/input/datasets/rangith/video-generation-dataset")
transformer_path = base / "wan2.2_ti2v_5B_fp16.safetensors"
vae_path = base / "wan2.2_vae.safetensors"

print(f"Transformer local: {transformer_path.exists()}")
print(f"VAE local: {vae_path.exists()}")

# 1. Cargar Transformer desde Input (rapido)
transformer = WanTransformer3DModel.from_single_file(str(transformer_path), torch_dtype=torch.float16)

# 2. Cargar VAE desde Input (float16 para ahorrar)
vae = AutoencoderKLWan.from_single_file(str(vae_path), torch_dtype=torch.float16)

# 3. Pipeline base desde HF (descarga T5 y scheduler)
print("Cargando pipeline (T5 desde HF)...")
pipe = WanPipeline.from_pretrained(model_id, transformer=transformer, vae=vae, torch_dtype=torch.float16)

# 4. TRUCO ANTI-OOM: T5 a CPU + VAE Tiling + Offload
pipe.text_encoder.to("cpu")
pipe.vae.enable_tiling()
pipe.vae.enable_slicing()
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

# 5. Menos pasos (20) y frames justos (25 = ~3s a 8fps)
generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt="low quality, blurry, distorted",
    height=480, width=832, num_frames=25,
    guidance_scale=5.0, num_inference_steps=20, generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=8)
print("=== FINALIZADO ===")
