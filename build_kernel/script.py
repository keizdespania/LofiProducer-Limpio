import os, subprocess, json, sys, zipfile, urllib.request

print("=== 1. COMPILANDO ACESTEP (30 MIN) ===", flush=True)
subprocess.run(["git", "clone", "--depth", "1", "--recurse-submodules", "https://github.com/ServeurpersoCom/acestep.cpp.git", "/kaggle/working/acestep.cpp"], check=True)

os.chdir("/kaggle/working/acestep.cpp")
subprocess.run(["ln", "-sf", "/usr/local/nvidia/lib64/libcuda.so", "/usr/local/cuda/lib64/libcuda.so"], check=False)
subprocess.run(["ln", "-sf", "/usr/local/nvidia/lib64/libcuda.so.1", "/usr/local/cuda/lib64/libcuda.so.1"], check=False)
subprocess.run(["sed", "-i", "s|CUDA::cuda_driver|/usr/local/nvidia/lib64/libcuda.so|g", "CMakeLists.txt"], check=False)
subprocess.run(["sed", "-i", "s|CUDA::cuda_driver|/usr/local/nvidia/lib64/libcuda.so|g", "ggml/src/ggml-cuda/CMakeLists.txt"], check=False)

os.makedirs("build", exist_ok=True)
os.chdir("build")
subprocess.run(["cmake", "..", "-DGGML_CUDA=ON", "-DGGML_NCCL=OFF", "-DGGML_CUDA_NO_VMM=ON", "-DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc", "-DCMAKE_CUDA_ARCHITECTURES=75", "-DCUDA_cuda_driver_LIBRARY=/usr/local/nvidia/lib64/libcuda.so", "-DCMAKE_PREFIX_PATH=/usr/local/nvidia"], check=True)
subprocess.run(["cmake", "--build", ".", "--config", "Release", "-j", "2"], check=True)

print("=== 2. DESCARGANDO MODELOS GGUF ===", flush=True)
os.chdir("/kaggle/working/acestep.cpp")
os.makedirs("models", exist_ok=True)
ggufs = ["acestep-v15-xl-turbo-Q4_K_M.gguf", "acestep-5Hz-lm-1.7B-Q8_0.gguf", "Qwen3-Embedding-0.6B-Q8_0.gguf", "vae-BF16.gguf"]
for g in ggufs:
    subprocess.run(["wget", "-q", "--content-disposition", f"https://huggingface.co/Serveurperso/ACE-Step-1.5-GGUF/resolve/main/{g}?download=true"], cwd="models", check=True)

print("=== 3. EMPAQUETANDO Y SUBIENDO A KAGGLE ===", flush=True)
rt = "/kaggle/working/dataset_upload"
os.makedirs(rt, exist_ok=True)
subprocess.run(["tar", "-czf", f"{rt}/acestep-runtime.tgz", "build", "models"], check=True)

meta = {"title": "ACESTEP Runtime", "id": "lofiproducer/acestep-runtime", "licenses": [{"name": "CC0-1.0"}]}
with open(f"{rt}/dataset-metadata.json", "w") as f:
    json.dump(meta, f)

# --- SUBIDA ---
os.environ["KAGGLE_USERNAME"] = "lofiproducer"
os.environ["KAGGLE_KEY"] = "KGAT_bd6e00f266d2200b0e679cafb26d18f4"

print("Intentando CLI...", flush=True)
r = subprocess.run(["kaggle", "datasets", "create", "-p", rt, "--dir-mode", "zip"], capture_output=True, text=True)
out = (r.stdout or "") + (r.stderr or "")
cli_ok = r.returncode == 0 and "error" not in out.lower() and "failed" not in out.lower()

if not cli_ok:
    print("CLI falló, usando REST multipart (estilo LTX)...", flush=True)
    zip_path = "/kaggle/working/upload_temp.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for root, dirs, files in os.walk(rt):
            for f in files:
                if f == "dataset-metadata.json" or f == "upload_temp.zip": continue
                fp = os.path.join(root, f)
                z.write(fp, os.path.relpath(fp, rt))
    
    boundary = "----kaggleBoundary"
    body = b""
    for name, fname, content, ctype in [
        ("metadata", "dataset-metadata.json", json.dumps(meta).encode(), "application/json"),
        ("file", "upload_temp.zip", open(zip_path, "rb").read(), "application/zip"),
    ]:
        body += b"--" + boundary.encode() + b"\r\n"
        body += b'Content-Disposition: form-data; name="' + name.encode() + b'"; filename="' + fname.encode() + b'"\r\n'
        body += b"Content-Type: " + ctype.encode() + b"\r\n\r\n"
        body += content + b"\r\n"
    body += b"--" + boundary.encode() + b"--\r\n"

    req = urllib.request.Request(
        "https://www.kaggle.com/api/v1/datasets/create/new",
        data=body, method="POST",
        headers={"Authorization": "Bearer " + os.environ["KAGGLE_KEY"],
                 "Content-Type": "multipart/form-data; boundary=" + boundary},
    )
    try:
        with urllib.request.urlopen(req, timeout=900) as resp:
            print("✅ REST OK:", resp.read().decode()[:500], flush=True)
    except Exception as e:
        body_err = e.read()[:500].decode(errors="replace") if hasattr(e, "read") else str(e)[:500]
        print("❌ REST fallo:", type(e).__name__, body_err, flush=True)
    if os.path.exists(zip_path): os.remove(zip_path)
else:
    print("✅ CLI creó el dataset OK", flush=True)

print("=== FIN ===", flush=True)
