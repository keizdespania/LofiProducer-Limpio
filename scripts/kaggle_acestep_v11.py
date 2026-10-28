# ACE-Step v11 - Kaggle Kernel (acestep.cpp + GGUF) - auto-upload a GitHub
CAPTIONS_LIST = __CAPTIONS_LIST__
DURATION = __DURATION__
GITHUB_TOKEN = "__GITHUB_TOKEN__"
GITHUB_REPO = "keizdespania/LofiProducer-backup"

import subprocess, pathlib, json, shutil, sys, time

def sh(cmd, cwd=None):
    print("$ " + cmd, flush=True)
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if r.stdout: print(r.stdout[-2000:], flush=True)
    if r.returncode != 0:
        print(r.stderr[-2000:], flush=True)
        sys.exit("FAIL: " + cmd)

WORK = pathlib.Path("/kaggle/working")
REPO = WORK / "acestep.cpp"
MODELS = REPO / "models"

print("== 1. clonar acestep.cpp ==", flush=True)
sh("git clone --depth 1 --recurse-submodules https://github.com/ServeurpersoCom/acestep.cpp.git " + str(REPO))

print("== 2. compilar CUDA (arch=75 T4 + driver real Kaggle) ==", flush=True)
sh("ls -la /usr/local/nvidia/lib64/libcuda.so* || true")
sh("ln -sf /usr/local/nvidia/lib64/libcuda.so /usr/local/cuda/lib64/libcuda.so || true")
sh("ln -sf /usr/local/nvidia/lib64/libcuda.so.1 /usr/local/cuda/lib64/libcuda.so.1 || true")
sh("sed -i 's|CUDA::cuda_driver|/usr/local/nvidia/lib64/libcuda.so|g' CMakeLists.txt || true")
sh("sed -i 's|CUDA::cuda_driver|/usr/local/nvidia/lib64/libcuda.so|g' ggml/src/ggml-cuda/CMakeLists.txt || true")
sh("rm -rf build && mkdir build && cd build && cmake .. -DGGML_CUDA=ON -DGGML_NCCL=OFF -DGGML_CUDA_NO_VMM=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc -DCMAKE_CUDA_ARCHITECTURES=75 -DCUDA_cuda_driver_LIBRARY=/usr/local/nvidia/lib64/libcuda.so -DCMAKE_PREFIX_PATH=/usr/local/nvidia && cmake --build . --config Release -j 2", cwd=str(REPO))

print("== 3. GGUF (~3.5GB) ==", flush=True)
MODELS.mkdir(exist_ok=True)
for f in [
    "acestep-v15-turbo-Q4_K_M.gguf",
    "acestep-5Hz-lm-0.6B-Q8_0.gguf",
    "Qwen3-Embedding-0.6B-Q8_0.gguf",
    "vae-BF16.gguf",
]:
    url = "https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/" + f + "?download=true"
    sh('wget -q --content-disposition --tries=3 --timeout=60 "' + url + '"', cwd=str(MODELS))

print("== 4. request.json ==", flush=True)
request = {
    "lm_model": "acestep-5Hz-lm-0.6B-Q8_0.gguf",
    "synth_model": "acestep-v15-turbo-Q4_K_M.gguf",
    "caption": "",  # se rellena dentro del bucle for
    "task_type": __TASK_TYPE__,
    "lyrics": __LYRICS__,
    "instrumental": __INSTRUMENTAL__,
    "vocal_language": __VOCAL_LANGUAGE__,
    "duration": DURATION,
    "bpm": __BPM__,
    "keyscale": __KEYSCALE__,
    "timesignature": __TIMESIG__,
    "inference_steps": __STEPS__,
    "guidance_scale": __GUIDANCE__,
    "shift": __SHIFT__,
    "lm_temperature": __LM_TEMP__,
    "lm_cfg_scale": __LM_CFG__,
    "lm_top_p": __LM_TOP_P__,
    "seed": __SEED__,
    "output_format": __OUTPUT_FORMAT__,
    "mp3_bitrate": 128,
}
print("== 5-8. Generando " + str(len(CAPTIONS_LIST)) + " canciones (max 55 min) ==", flush=True)
T_START = time.time()
T_MAX = 55 * 60  # 55 minutos maximo

for i, caption in enumerate(CAPTIONS_LIST):
    if time.time() - T_START > T_MAX:
        print(f"TIMEOUT interno a los 55 min. Generadas {i}/{len(CAPTIONS_LIST)}. Abortando.", flush=True)
        break
    
    print(f"\n─── Cancion {i+1}/{len(CAPTIONS_LIST)} ───", flush=True)
    request["caption"] = caption
    request["seed"] = request.get("seed", -1) + i if request.get("seed", -1) != -1 else -1
    pathlib.Path("/tmp/request.json").write_text(json.dumps(request))
    print(json.dumps(request, indent=2)[:300], flush=True)
    
    try:
        sh("./build/ace-lm --models models --request /tmp/request.json", cwd=str(REPO))
        sh("./build/ace-synth --models models --request /tmp/request0.json", cwd=str(REPO))
    except SystemExit as e:
        print(f"ERROR en cancion {i+1}: {e}", flush=True)
        continue
    
    # Buscar el MP3
    candidates = list(pathlib.Path("/tmp").glob("request00*.mp3")) + list(REPO.glob("request00*.mp3"))
    if not candidates:
        print(f"Sin MP3 para cancion {i+1}, saltando", flush=True)
        continue
    mp3 = candidates[0]
    ts = int(time.time())
    dest_name = f"musica_{ts}_{i}.mp3"
    dst = WORK / dest_name
    shutil.copy2(mp3, dst)
    print(f"OK local: {dst} ({dst.stat().st_size} bytes)", flush=True)
    
    # Subir a GitHub
    if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("__"):
        try:
            import base64, requests as _rq
            dest_path = f"output/musica/{dest_name}"
            with open(str(dst), "rb") as f:
                content = base64.b64encode(f.read()).decode()
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{dest_path}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
            r = _rq.get(url, headers=headers)
            sha = r.json().get("sha") if r.status_code == 200 else None
            payload = {"message": f"Add music {dest_name}", "content": content, "branch": "main"}
            if sha: payload["sha"] = sha
            r = _rq.put(url, headers=headers, json=payload)
            print(f"GitHub {dest_name}: {r.status_code}", flush=True)
        except Exception as e:
            print(f"Error GitHub {dest_name}: {e}", flush=True)

print(f"\n=== FIN: {len(CAPTIONS_LIST)} intentos en {int(time.time()-T_START)}s ===", flush=True)
