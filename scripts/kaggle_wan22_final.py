"""Wan 2.2 - Batch mode: N prompts en 1 kernel, timeout 55 min."""
import sys, subprocess, time, pathlib

PROMPTS_LIST = __PROMPTS_LIST__
CANAL = "__CANAL__"
RESOLUTION = "__RESOLUTION__"  # "640x384" horizontal | "384x640" vertical
NUM_FRAMES = __NUM_FRAMES__
NUM_STEPS = __NUM_STEPS__
GITHUB_TOKEN = "__GITHUB_TOKEN__"
GITHUB_REPO = "keizdespania/LofiProducer-backup"
T_MAX = 55 * 60  # 55 min max

print(f"=== WAN 2.2 BATCH ({len(PROMPTS_LIST)} clips) ===", flush=True)
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "-q", "torchao"], check=False)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "diffusers>=0.35.0", "transformers", "accelerate", "imageio", "imageio-ffmpeg"], check=True)

import torch
from diffusers import WanPipeline, AutoencoderKLWan
from diffusers.utils import export_to_video

model_id = "Wan-AI/Wan2.2-TI2V-5B-Diffusers"

print("Cargando VAE...", flush=True)
vae = AutoencoderKLWan.from_pretrained(model_id, subfolder="vae", torch_dtype=torch.float16)
print("Cargando pipeline...", flush=True)
pipe = WanPipeline.from_pretrained(model_id, vae=vae, torch_dtype=torch.float16)
pipe.text_encoder.to("cpu")
pipe.transformer.enable_gradient_checkpointing()
pipe.enable_model_cpu_offload()
pipe.scheduler.shift = 3.0

try:
    h, w = [int(x) for x in RESOLUTION.split("x")]
except Exception:
    h, w = 384, 640

T_START = time.time()
for i, prompt in enumerate(PROMPTS_LIST):
    if time.time() - T_START > T_MAX:
        print(f"TIMEOUT a {int((time.time()-T_START)/60)}min. Generados {i}/{len(PROMPTS_LIST)}.", flush=True)
        break
    print(f"\n─── Clip {i+1}/{len(PROMPTS_LIST)}: {prompt[:60]} ───", flush=True)
    try:
        generator = torch.Generator(device="cpu").manual_seed(42 + i)
        output = pipe(
            prompt=prompt,
            negative_prompt="low quality, blurry, static, watermark",
            height=h, width=w,
            num_frames=NUM_FRAMES,
            guidance_scale=1.0,
            num_inference_steps=NUM_STEPS,
            generator=generator,
        ).frames[0]
        ts = int(time.time())
        # Naming consistente
        try:
            titulo_slug = (prompt[:40] or "clip").strip()
            nombre, _ = generar_nombre(CANAL, "video", titulo_slug, "mp4")
        except Exception:
            nombre = f"clip_{ts}_{i}.mp4"
        local = pathlib.Path(f"/kaggle/working/{nombre}")
        export_to_video(output, str(local), fps=8)
        print(f"OK local: {local} ({local.stat().st_size} bytes)", flush=True)
        
        # Subir a GitHub
        if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("__"):
            try:
                import base64, requests as _rq
                dest_path = f"output/videos/clip_{ts}_{i}.mp4"
                with open(str(local), "rb") as f:
                    content = base64.b64encode(f.read()).decode()
                url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{dest_path}"
                headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
                r = _rq.get(url, headers=headers)
                sha = r.json().get("sha") if r.status_code == 200 else None
                payload = {"message": f"Add clip {ts}_{i}", "content": content, "branch": "main"}
                if sha: payload["sha"] = sha
                r = _rq.put(url, headers=headers, json=payload)
                print(f"GitHub {dest_path}: {r.status_code}", flush=True)
            except Exception as e:
                print(f"Error GitHub: {e}", flush=True)
    except Exception as e:
        print(f"ERROR clip {i+1}: {e}", flush=True)
        continue

print(f"\n=== FIN: {len(PROMPTS_LIST)} clips en {int(time.time()-T_START)}s ===", flush=True)
