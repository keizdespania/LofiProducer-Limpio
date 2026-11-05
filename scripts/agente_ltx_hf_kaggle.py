"""agente_ltx_hf_kaggle.py - Lanza un kernel de Kaggle que usa gradio_client
para llamar al Space de LTX (que sí funciona en Python 3.10).
"""
import sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from kaggle_bearer import push_kernel, estado_kernel

KAGGLE_USER = "keizproductions"
KERNEL_SLUG = "ltx-hf-client"
REPO = "keizdespania/LofiProducer-Limpio"
COLA_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola.json"


def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _construir_kernel():
    github_token = _leer_env("GITHUB_TOKEN")
    hf_token = _leer_env("HF_TOKEN")

    codigo = '''"""LTX I2V via gradio_client en Kaggle (Python 3.10)."""
import sys, subprocess, os, json, time, pathlib, urllib.request, base64

COLA_URL = "''' + COLA_URL + '''"
GITHUB_TOKEN = "''' + github_token + '''"
HF_TOKEN = "''' + hf_token + '''"
GITHUB_REPO = "''' + REPO + '''"

print("=== LTX I2V via gradio_client (Kaggle) ===", flush=True)

# 1. Instalar gradio_client
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "gradio_client", "requests"], check=True)
from gradio_client import Client, handle_file

# 2. Descargar cola
print("Descargando cola...", flush=True)
with urllib.request.urlopen(COLA_URL) as r:
    cola = json.loads(r.read())
pendientes = [item for item in cola if not item.get("completado", False)]
print("Cola:", len(pendientes), "pendientes", flush=True)
if not pendientes:
    print("Nada que hacer.", flush=True)
    sys.exit(0)

# 3. Conectar al Space
print("Conectando al Space...", flush=True)
client = Client("Lightricks/ltx-video-distilled", token=HF_TOKEN or None)
print("Conectado", flush=True)

# 4. Procesar cada item
for i, item in enumerate(pendientes):
    filename = item["nombre"]
    prompt = item["prompt"]
    img_url = item["imagen_url"]

    print("", flush=True)
    print("[" + str(i+1) + "/" + str(len(pendientes)) + "] " + filename, flush=True)

    img_path = "/kaggle/working/" + filename + "_in.png"
    urllib.request.urlretrieve(img_url, img_path)
    print("Imagen:", os.path.getsize(img_path) // 1024, "KB", flush=True)

    print("Llamando a client.predict...", flush=True)
    try:
        result = client.predict(
            prompt=prompt,
            negative_prompt="worst quality, inconsistent motion, blurry, jittery, distorted",
            input_image_filepath=handle_file(img_path),
            input_video_filepath=None,
            height_ui=480,
            width_ui=832,
            mode="image-to-video",
            duration_ui=8,
            ui_frames_to_use=9,
            seed_ui=42,
            randomize_seed=True,
            ui_guidance_scale=1,
            improve_texture_flag=True,
            api_name="/image_to_video"
        )
        print("Resultado:", str(result)[:300], flush=True)

        # Extraer el video (el Space devuelve una tupla anidada)
        video_path = None
        if isinstance(result, tuple) and len(result) > 0:
            # Primer elemento de la tupla suele ser un dict con 'video'
            primero = result[0]
            if isinstance(primero, dict):
                video_path = primero.get("video") or primero.get("path")
            elif isinstance(primero, str):
                video_path = primero
        elif isinstance(result, dict):
            video_path = result.get("video") or result.get("path")
        elif isinstance(result, (list, str)):
            video_path = result[0] if isinstance(result, list) and result else result

        print("video_path extraido:", video_path, flush=True)

        if video_path and os.path.exists(str(video_path)):
            print("Video generado:", video_path, flush=True)
            # Copiar a una ruta con nombre
            import shutil
            out_path = "/kaggle/working/" + filename + ".mp4"
            shutil.copy(str(video_path), out_path)
            size_kb = os.path.getsize(out_path) // 1024
            print("Copiado a:", out_path, "(", size_kb, "KB)", flush=True)

            # Subir a GitHub
            if GITHUB_TOKEN:
                import requests
                url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/output/videos/" + filename + ".mp4"
                headers = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
                r = requests.get(url, headers=headers)
                sha = r.json().get("sha") if r.status_code == 200 else None
                data = {
                    "message": "Add " + filename + ".mp4",
                    "content": base64.b64encode(pathlib.Path(out_path).read_bytes()).decode(),
                    "branch": "main"
                }
                if sha: data["sha"] = sha
                r = requests.put(url, headers=headers, json=data)
                print("GitHub:", "OK" if r.status_code in (200, 201) else r.text[:100], flush=True)
                if r.status_code in (200, 201):
                    item["completado"] = True
        else:
            print("Sin video:", result, flush=True)
    except Exception as e:
        print("ERROR predict:", type(e).__name__, ":", e, flush=True)

# 5. Actualizar cola
if GITHUB_TOKEN:
    import requests
    url = "https://api.github.com/repos/" + GITHUB_REPO + "/contents/data/agent/ltx_cola.json"
    headers = {"Authorization": "token " + GITHUB_TOKEN, "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        sha = r.json().get("sha")
        data = {
            "message": "Update ltx_cola",
            "content": base64.b64encode(json.dumps(cola, indent=2).encode()).decode(),
            "branch": "main",
            "sha": sha
        }
        requests.put(url, headers=headers, json=data)

print("=== FIN ===", flush=True)
'''
    return codigo


def lanzar():
    print("Lanzando LTX HF client a Kaggle (Python 3.10)...")
    codigo = _construir_kernel()
    print("   Código:", len(codigo), "chars")
    res = push_kernel(KAGGLE_USER + "/" + KERNEL_SLUG, codigo, enable_gpu=False, enable_internet=True)
    print("   Push:", res)
    return not (isinstance(res, dict) and res.get("hasError"))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "lanzar"
    if cmd == "lanzar":
        sys.exit(0 if lanzar() else 1)
    elif cmd == "estado":
        print(json.dumps(estado_kernel(KAGGLE_USER + "/" + KERNEL_SLUG), indent=2))
