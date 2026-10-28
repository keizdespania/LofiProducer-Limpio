"""
Cajon 18 - Generador de musica con ACE-Step 1.5 en Colab GPU.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from core.logger import get_logger


log = get_logger("fases.musica_ace")

BROWSER = "/data/data/com.termux/files/home/bin/xdg-open"


def _audio_dir() -> Path:
    from core.config import OUTPUT_DIR
    canal = OUTPUT_DIR.name
    project = OUTPUT_DIR.parent.parent
    d = project / "assets" / canal / "audio" / "local"
    d.mkdir(parents=True, exist_ok=True)
    return d


ACE_STEP_CODE = """import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["PATH"] += ":/root/.local/bin"

os.system("curl -LsSf https://astral.sh/uv/install.sh | sh 2>&1 | tail -2")

if not os.path.exists("/content/ACE-Step-1.5"):
    os.system("cd /content && git clone https://github.com/ace-step/ACE-Step-1.5.git 2>&1 | tail -3")

os.chdir("/content/ACE-Step-1.5")

print("uv sync...")
os.system("uv sync 2>&1 | tail -5")

print("descargando modelo...")
os.system("uv run acestep-download 2>&1 | tail -5")

import subprocess
import shlex

PROMPTS = __PROMPTS__
DURACION = __DURACION__

os.makedirs("/content/outputs", exist_ok=True)

for i, prompt in enumerate(PROMPTS, 1):
    path = f"/content/outputs/track_{i:02d}.wav"
    print(f"[{i}/{len(PROMPTS)}] {prompt[:60]}...")
    cmd = (
        f"uv run acestep "
        f"--prompt {shlex.quote(prompt)} "
        f"--audio_duration {DURACION} "
        f"--output_path {path} "
        f"--infer_step 15 "
        f"--guidance_scale 7.5 "
        f"--cpu_offload true"
    )
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=600)
        if os.path.exists(path):
            print(f"  OK -> {path} ({os.path.getsize(path)} bytes)")
        else:
            print(f"  ERROR: {r.stderr[-300:]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("DONE")
"""


async def _generar_remoto(prompts: list[str], duracion: int) -> Path:
    code = (ACE_STEP_CODE
            .replace("__PROMPTS__", json.dumps(prompts, ensure_ascii=False))
            .replace("__DURACION__", str(duracion)))

    out_dir = _audio_dir()
    log.info("Destino local: %s", out_dir)

    params = StdioServerParameters(
        command="mcp-server-kaggle-exec", args=[],
        env={"BROWSER": BROWSER},
    )

    log.info("Conectando a Colab GPU...")
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            log.info("Ejecutando ACE-Step (5-15 min la primera vez)...")
            result = await s.call_tool("kaggle_execute_notebook", {
                "code": code,
                "output_dir": str(out_dir),
                "enable_gpu": True,
                "timeout": 2400,
            })
            for c in result.content:
                if hasattr(c, "text"):
                    for linea in c.text.strip().split("\n")[-30:]:
                        log.info("  %s", linea)

    return out_dir


def generar_musica(prompts: list[str], duracion: int = 90) -> Path:
    return asyncio.run(_generar_remoto(prompts, duracion))


if __name__ == "__main__":
    log.info("=== Test fases.musica_ace (v2) ===")
    prompts = [
        "lofi hip hop, 80 BPM, warm Rhodes piano, vinyl crackle, no vocals",
        
    ]
    out = generar_musica(prompts, duracion=30)
    print()
    print("=" * 60)
    wavs = sorted(out.glob("*.wav")) + sorted(out.glob("*.mp3"))
    print(f"[OK] {len(wavs)} tracks en {out}:")
    for w in wavs:
        print(f"  {w.name} ({w.stat().st_size/1024:.1f} KB)")
    print("=" * 60)

