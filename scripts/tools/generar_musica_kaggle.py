import os, json, subprocess
from pathlib import Path

def generar_musica_kaggle(estilo_prompt: str, cantidad: int = 1, duracion: int = 120):
    if cantidad > 10: return "❌ Máximo 10 pistas."
    base_tmp = Path(os.path.expanduser("~")) / "tmp" / "acestep_kernel"
    base_tmp.mkdir(parents=True, exist_ok=True)

    nb = """CAPTIONS_LIST = __CAPTIONS__
DURATION = __DURACION__
GITHUB_TOKEN = "@@TOKEN@@"
GITHUB_REPO = "keizdespania/LofiProducer-Limpio"

import subprocess, pathlib, json, shutil, sys, time, os

def sh(cmd, cwd=None, env=None):
    print("$ " + cmd, flush=True)
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, env=env)
    if r.stdout: print(r.stdout[-2000:], flush=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], flush=True)
        sys.exit("FAIL: " + cmd)

WORK = pathlib.Path("/kaggle/working")

print("== 1. EXTRAER DATASET ==", flush=True)
tgz = None
for root, dirs, files in os.walk("/kaggle/input"):
    if "acestep-runtime.tgz" in files:
        tgz = os.path.join(root, "acestep-runtime.tgz"); break
if not tgz: sys.exit("dataset tgz no encontrado")
sh("tar -xzf " + tgz + " -C /kaggle/working/")

print("== 2. VERIFICAR LIBRERIAS ==", flush=True)
BUILD = WORK / "build"
if not (BUILD / "libggml.so.0").exists():
    sys.exit("libggml.so.0 no encontrado en build/")
if not (BUILD / "ace-lm").exists():
    sys.exit("ace-lm no encontrado")
print("✅ build/ OK", flush=True)

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = str(BUILD) + ":" + env.get("LD_LIBRARY_PATH", "")

print("== 3. GENERAR ==", flush=True)
request = {
    "lm_model": "acestep-5Hz-lm-1.7B-Q8_0.gguf",
    "synth_model": "acestep-v15-xl-turbo-Q4_K_M.gguf",
    "caption": "", "task_type": "text2music", "lyrics": "",
    "instrumental": True, "vocal_language": "unknown",
    "duration": DURATION, "bpm": 90, "keyscale": "", "timesignature": "4/4",
    "inference_steps": 6, "guidance_scale": 1.0, "shift": 3.0,
    "lm_temperature": 0.85, "lm_cfg_scale": 2.0, "lm_top_p": 0.9,
    "seed": -1, "output_format": "mp3", "mp3_bitrate": 128,
}
T0 = time.time()

for i, caption in enumerate(CAPTIONS_LIST):
    if time.time() - T0 > 55*60: break
    print(f"--- Cancion {i+1}/{len(CAPTIONS_LIST)} ---", flush=True)
    request["caption"] = caption
    request["seed"] = request.get("seed", -1) + i if request.get("seed", -1) != -1 else -1
    pathlib.Path("/tmp/request.json").write_text(json.dumps(request))
    
    try:
        sh(str(BUILD / "ace-lm") + " --models models --request /tmp/request.json", cwd=str(WORK), env=env)
        sh(str(BUILD / "ace-synth") + " --models models --request /tmp/request0.json", cwd=str(WORK), env=env)
    except SystemExit as e:
        print(f"ERROR: {e}", flush=True); continue
    
    cands = list(pathlib.Path("/tmp").glob("request00*.mp3")) + list(WORK.glob("request00*.mp3")) + list(BUILD.glob("request00*.mp3"))
    if not cands:
        print("Sin MP3", flush=True); continue
    mp3 = cands[0]
    ts = int(time.time())
    name = f"musica_{ts}_{i}.mp3"
    dst = WORK / name
    shutil.copy2(mp3, dst)
    print(f"OK: {dst} ({dst.stat().st_size} bytes)", flush=True)
    
    if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("__"):
        try:
            import base64, requests as _rq
            content = base64.b64encode(dst.read_bytes()).decode()
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/output/musica/{name}"
            h = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
            r = _rq.get(url, headers=h)
            sha = r.json().get("sha") if r.status_code == 200 else None
            payload = {"message": f"Add music {name}", "content": content, "branch": "main"}
            if sha: payload["sha"] = sha
            r = _rq.put(url, headers=h, json=payload)
            print(f"GitHub: {r.status_code}", flush=True)
        except Exception as e:
            print(f"GitHub err: {e}", flush=True)

print(f"=== FIN {int(time.time()-T0)}s ===", flush=True)
"""
    
    token_path = os.path.expanduser("~/.acestep_token")
    try:
        token = open(token_path).read().strip()
    except Exception:
        token = ""
    nb = nb.replace("@@TOKEN@@", token)
    nb = nb.replace("__CAPTIONS__", json.dumps([estilo_prompt] * cantidad)).replace("__DURACION__", str(duracion))

    (base_tmp / "acestep_generator.ipynb").write_text(json.dumps({
        "cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": nb.splitlines(True)}],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5
    }))
    (base_tmp / "kernel-metadata.json").write_text(json.dumps({
        "id": "lofiproducer/acestep-generator",
        "title": "ACEStep Generator",
        "code_file": "acestep_generator.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": "true",
        "enable_gpu": "true",
        "enable_internet": "true",
        "dataset_sources": ["lofiproducer/acestep-runtime"],
        "competition_sources": [],
        "kernel_sources": []
    }))
    print("Push a Kaggle...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", str(base_tmp)], capture_output=True, text=True)
    print(res.stdout); print(res.stderr)
    if res.returncode != 0: return f"❌ {res.stderr}"
    return f"✅ Kernel lanzado. {cantidad} pistas de {duracion}s."
