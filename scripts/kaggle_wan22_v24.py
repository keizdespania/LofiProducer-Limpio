"""Wan 2.2 v24 - Group Offloading (sin VAE tiling roto)."""
import sys, subprocess, pathlib

PROMPT = "A cat riding a bicycle in a sunny park"
OUTPUT = "/kaggle/working/video_generado.mp4"

print("=== WAN 2.2 v24 (Group Offload) ===")
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg", "safetensors"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan, WanTransformer3DModel
from diffusers.utils import export_to_video
from diffusers.hooks import apply_group_offloading

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"
base = pathlib.Path("/kaggle/input/datasets/rangith/video-generation-dataset")
transformer_path = base / "wan2.2_ti2v_5B_fp16.safetensors"
vae_path = base / "wan2.2_vae.safetensors"

print("Cargando Transformer...")
transformer = WanTransformer3DModel.from_single_file(str(transformer_path), torch_dtype=torch.float16)

print("Cargando VAE...")
vae = AutoencoderKLWan.from_single_file(str(vae_path), torch_dtype=torch.float16)

print("Cargando pipeline...")
pipe = WanPipeline.from_pretrained(model_id, transformer=transformer, vae=vae, torch_dtype=torch.float16)

# GROUP OFFLOADING (la tecnica de Unsloth para T4)
pipe.transformer.enable_group_offload(
    onload_device=torch.device("cuda"),
    offload_device=torch.device("cpu"),
    offload_type="leaf_level",
    use_stream=True,
)
pipe.text_encoder.to("cpu")
pipe.scheduler.shift = 3.0

generator = torch.Generator(device="cpu").manual_seed(42)
output = pipe(
    prompt=PROMPT,
    negative_prompt="low quality, blurry",
    height=384, width=640, # Minimo para asegurar
    num_frames=17, # 2 segundos
    guidance_scale=5.0, num_inference_steps=15, generator=generator,
).frames[0]

export_to_video(output, OUTPUT, fps=8)
print("=== FINALIZADO ===")
