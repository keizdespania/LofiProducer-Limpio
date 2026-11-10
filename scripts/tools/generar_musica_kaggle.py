import os, json, subprocess
from pathlib import Path

def generar_musica_kaggle(estilo_prompt, cantidad=1, duracion=240, lyrics="", vocal_language="unknown", bpm=0, keyscale="", timesignature="4", lm_batch_size=1, synth_batch_size=1):
    if cantidad > 10: return "Error: Maximo 10 pistas."
    base_tmp = Path(os.path.expanduser("~")) / "tmp" / "acestep_kernel"
    base_tmp.mkdir(parents=True, exist_ok=True)
    lyrics_efectiva = lyrics if lyrics.strip() else "[Instrumental]"
    req = {
        "task_type": "text2music", "solver": "euler",
        "inference_steps": 8, "shift": 3.0, "use_cot_caption": True,
        "lm_temperature": 0.85, "lm_cfg_scale": 2.0, "lm_top_p": 0.9,
        "output_format": "mp3", "mp3_bitrate": 128,
        "synth_model": "acestep-v15-xl-turbo-Q4_K_M",
        "lm_model": "acestep-5Hz-lm-1.7B-Q8_0",
        "adapter": "", "adapter_scale": 1.0,
    }
    nb = """CAPTIONS_LIST = __CAPTIONS__
REQ_BASE = __REQ_BASE__
DURATION = __DURACION__
BPM = __BPM__
KEYSCALE = __KEYSCALE__
TIMESIG = __TIMESIG__
LYRICS = __LYRICS__
VOCAL_LANG = __VOCAL_LANG__
LM_BS = __LM_BS__
SYNTH_BS = __SYNTH_BS__
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
BUILD = WORK / "build"
if not (BUILD / "libggml.so.0").exists(): sys.exit("libggml.so.0 no encontrado")
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = str(BUILD) + ":" + env.get("LD_LIBRARY_PATH", "")
print("BUILD OK", flush=True)

print("== 2. GENERAR ==", flush=True)
T0 = time.time()
for i, caption in enumerate(CAPTIONS_LIST):
    if time.time() - T0 > 55*60: break
    print("--- Cancion " + str(i+1) + "/" + str(len(CAPTIONS_LIST)) + " ---", flush=True)
    req = dict(REQ_BASE)
    req["caption"] = caption
    req["lyrics"] = LYRICS
    req["vocal_language"] = VOCAL_LANG
    req["duration"] = DURATION
    if BPM > 0: req["bpm"] = BPM
    if KEYSCALE: req["keyscale"] = KEYSCALE
    if TIMESIG: req["timesignature"] = TIMESIG
    if LM_BS > 1: req["lm_batch_size"] = LM_BS
    if SYNTH_BS > 1: req["synth_batch_size"] = SYNTH_BS
    req["seed"] = -1
    pathlib.Path("/tmp/request.json").write_text(json.dumps(req))
    print("req: " + caption[:60] + " | bpm=" + str(BPM) + " | batch=" + str(LM_BS) + "x" + str(SYNTH_BS), flush=True)
    try:
        sh(str(BUILD / "ace-lm") + " --models models --request /tmp/request.json", cwd=str(WORK), env=env)
        reqs = sorted(pathlib.Path("/tmp").glob("request[0-9]*.json"))
        for rq in reqs:
            if rq.name == "request.json": continue
            print("synth: " + rq.name, flush=True)
            sh(str(BUILD / "ace-synth") + " --models models --request " + str(rq), cwd=str(WORK), env=env)
    except SystemExit as e:
        print("ERROR: " + str(e), flush=True); continue
    cands = sorted(list(pathlib.Path("/tmp").glob("request*.mp3")) + list(WORK.glob("request*.mp3")))
    if not cands: print("Sin MP3", flush=True); continue
    for mp3 in cands:
        ts = int(time.time())
        name = "musica_" + str(ts) + "_" + str(i) + "_" + mp3.stem + ".mp3"
        dst = WORK / name
        shutil.copy2(mp3, dst)
        print("OK: " + str(dst) + " (" + str(dst.stat().st_size) + " bytes)", flush=True)
        if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("@@"):
            try:
                import base64, requests as _rq
                content = base64.b64encode(dst.read_bytes()).decode()
                url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/musica/" + name
                h = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
                r = _rq.get(url, headers=h)
                sha = r.json().get("sha") if r.status_code == 200 else None
                payload = {"message": "Add music " + name, "content": content, "branch": "main"}
                if sha: payload["sha"] = sha
                r = _rq.put(url, headers=h, json=payload)
                print("GitHub " + name + ": " + str(r.status_code), flush=True)
            except Exception as e:
                print("GitHub err: " + str(e), flush=True)
print("=== FIN OK ===", flush=True)
"""
    token = ""
    try: token = open(os.path.expanduser("~/.acestep_token")).read().strip()
    except: pass
    nb = nb.replace("@@TOKEN@@", token)
    nb = nb.replace("__CAPTIONS__", json.dumps([estilo_prompt] * cantidad))
    nb = nb.replace("__REQ_BASE__", json.dumps(req))
    nb = nb.replace("__DURACION__", str(duracion))
    nb = nb.replace("__BPM__", str(bpm))
    nb = nb.replace("__KEYSCALE__", json.dumps(keyscale))
    nb = nb.replace("__TIMESIG__", json.dumps(timesignature))
    nb = nb.replace("__LYRICS__", json.dumps(lyrics_efectiva))
    nb = nb.replace("__VOCAL_LANG__", json.dumps(vocal_language))
    nb = nb.replace("__LM_BS__", str(lm_batch_size))
    nb = nb.replace("__SYNTH_BS__", str(synth_batch_size))
    (base_tmp / "acestep_generator.ipynb").write_text(json.dumps({
        "cells": [{"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": nb.splitlines(True)}],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5
    }))
    (base_tmp / "kernel-metadata.json").write_text(json.dumps({
        "id": "lofiproducer/acestep-generator", "title": "ACEStep Generator",
        "code_file": "acestep_generator.ipynb", "language": "python", "kernel_type": "notebook",
        "is_private": "true", "enable_gpu": "true", "enable_internet": "true",
        "dataset_sources": ["lofiproducer/acestep-runtime"], "competition_sources": [], "kernel_sources": []
    }))
    print("Push a Kaggle...")
    res = subprocess.run(["kaggle", "kernels", "push", "-p", str(base_tmp)], capture_output=True, text=True)
    print(res.stdout); print(res.stderr)
    if res.returncode != 0: return "Error: " + res.stderr
    return "OK. " + str(cantidad) + " lotes, batch=" + str(lm_batch_size) + "x" + str(synth_batch_size) + "."

def generar_por_genero(nombre_genero, cantidad=1):
    p = Path(os.path.expanduser("~")) / "LofiProducer" / "data" / "agent" / "acestep_1.5_contract.json"
    c = json.load(open(p))
    if nombre_genero not in c["generos"]:
        return "Genero no existe. Disponibles: " + ", ".join(sorted(c["generos"].keys()))
    g = c["generos"][nombre_genero]
    return generar_musica_kaggle(
        estilo_prompt=g["caption"], cantidad=cantidad, duracion=g["duration"],
        vocal_language=g["vocal_language"], bpm=g["bpm"], keyscale=g["keyscale"],
        timesignature=g["timesignature"], lm_batch_size=4, synth_batch_size=2
    )
