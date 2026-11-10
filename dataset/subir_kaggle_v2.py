import os, json, zipfile, urllib.request, sys

DATASET_ID = "lofiproducer/acestep-lofi-dataset"
KAGGLE_TOKEN = "KGAT_bd6e00f266d2200b0e679cafb26d18f4"
rt = os.path.expanduser("~/LofiProducer/dataset/kaggle_upload")

# 1. Verificar que la carpeta no esté vacía
if not os.listdir(rt):
    print("❌ ERROR: La carpeta kaggle_upload está vacía. No hay archivos para subir.")
    sys.exit(1)

# 2. Comprimir
zip_path = os.path.expanduser("~/LofiProducer/dataset/upload_temp.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
    for root, dirs, files in os.walk(rt):
        for f in files:
            if f == "dataset-metadata.json": continue
            fp = os.path.join(root, f)
            z.write(fp, os.path.relpath(fp, rt))

print(f"ZIP creado: {os.path.getsize(zip_path) // 1024 // 1024} MB")

# 3. PASO 1: Subir archivo para obtener token
boundary = "----kaggleBoundary"
body = b"--" + boundary.encode() + b"\r\n"
body += b'Content-Disposition: form-data; name="file"; filename="upload_temp.zip"\r\n'
body += b"Content-Type: application/zip\r\n\r\n"
body += open(zip_path, "rb").read() + b"\r\n"
body += b"--" + boundary.encode() + b"--\r\n"

req_upload = urllib.request.Request(
    "https://www.kaggle.com/api/v1/datasets/upload",
    data=body, method="POST",
    headers={
        "Authorization": "Bearer " + KAGGLE_TOKEN,
        "Content-Type": "multipart/form-data; boundary=" + boundary
    },
)

try:
    with urllib.request.urlopen(req_upload, timeout=900) as resp:
        upload_resp = json.loads(resp.read().decode())
        file_token = upload_resp.get("token")
        print(f"✅ Token obtenido: {file_token}")
except Exception as e:
    body_err = e.read()[:500].decode(errors="replace") if hasattr(e, "read") else str(e)[:500]
    print(f"❌ Error en subida: {body_err}")
    sys.exit(1)

# 4. PASO 2: Crear dataset con el token
create_payload = {
    "title": "ACEStep Lofi Dataset",
    "slug": "acestep-lofi-dataset",
    "ownerSlug": "lofiproducer",
    "licenseName": "CC0-1.0",
    "isPrivate": False,
    "files": [{"token": file_token}]
}

req_create = urllib.request.Request(
    "https://www.kaggle.com/api/v1/datasets/create/new",
    data=json.dumps(create_payload).encode(),
    method="POST",
    headers={
        "Authorization": "Bearer " + KAGGLE_TOKEN,
        "Content-Type": "application/json"
    },
)

try:
    with urllib.request.urlopen(req_create, timeout=900) as resp:
        print("✅ Dataset creado:", resp.read().decode()[:500])
except Exception as e:
    body_err = e.read()[:500].decode(errors="replace") if hasattr(e, "read") else str(e)[:500]
    print(f"❌ Error al crear: {body_err}")

# Limpieza
if os.path.exists(zip_path): os.remove(zip_path)
