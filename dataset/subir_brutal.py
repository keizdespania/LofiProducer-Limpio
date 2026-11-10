import os, json, zipfile, urllib.request, sys

# Configuración de la cuenta 2 (lofiproducer)
DATASET_ID = "lofiproducer/acestep-lofi-dataset"
KAGGLE_TOKEN = "KGAT_bd6e00f266d2200b0e679cafb26d18f4"
KAGGLE_USER = "lofiproducer"
rt = os.path.expanduser("~/LofiProducer/dataset/kaggle_upload")

print("=== [1/3] Preparando Metadata ===", flush=True)
meta = {"title": "ACEStep Lofi Dataset", "id": DATASET_ID, "licenses": [{"name": "CC0-1.0"}]}
with open(os.path.join(rt, "dataset-metadata.json"), "w") as f:
    json.dump(meta, f, indent=2)

print("=== [2/3] Comprimiendo archivos (ignorando metadata) ===", flush=True)
zip_path = os.path.expanduser("~/LofiProducer/dataset/upload_temp.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
    for root, dirs, files in os.walk(rt):
        for f in files:
            if f == "dataset-metadata.json" or f == "upload_temp.zip": continue
            fp = os.path.join(root, f)
            z.write(fp, os.path.relpath(fp, rt))
            
print("ZIP creado:", os.path.getsize(zip_path) // 1024 // 1024, "MB", flush=True)

print("=== [3/3] Subiendo vía REST (Bearer) ===", flush=True)
boundary = "----kaggleBoundary"
body = b""

# Multipart manual
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
    headers={
        "Authorization": "Bearer " + KAGGLE_TOKEN,
        "Content-Type": "multipart/form-data; boundary=" + boundary
    },
)

try:
    with urllib.request.urlopen(req, timeout=900) as resp:
        print("✅ RESPUESTA DE KAGGLE:", resp.read().decode()[:500], flush=True)
except Exception as e:
    body_err = e.read()[:500].decode(errors="replace") if hasattr(e, "read") else str(e)[:500]
    print("❌ ERROR REAL:", type(e).__name__, body_err, flush=True)

# Limpieza
if os.path.exists(zip_path): os.remove(zip_path)
print("=== FIN ===", flush=True)
