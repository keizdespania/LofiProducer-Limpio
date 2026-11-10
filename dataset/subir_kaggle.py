import os
from kaggle.api.kaggle_api_extended import KaggleApi

# 1. Autenticar
api = KaggleApi()
api.authenticate()

# 2. Ruta a la carpeta
ruta = os.path.expanduser("~/LofiProducer/dataset/kaggle_upload")
print(f"→ Subiendo dataset desde: {ruta}")

try:
    print("→ Intentando crear dataset nuevo...")
    api.dataset_create_new(folder=ruta, dir_mode='zip', public=False)
    print("✅ Dataset creado correctamente.")
except Exception as e:
    print(f"⚠️ Aviso: {e}")
    print("→ Intentando crear nueva versión (por si ya existía)...")
    try:
        api.dataset_create_version(folder=ruta, version_notes="v1", dir_mode='zip')
        print("✅ Nueva versión creada correctamente.")
    except Exception as e2:
        print(f"❌ Error definitivo: {e2}")
