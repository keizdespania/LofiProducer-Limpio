"""agente_ltx_hf.py - Genera video I2V con el Space de LTX via HTTP directo."""
import sys
import os
import json
import time
import uuid
import urllib.request
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "keizdespania/LofiProducer-Limpio"
COLA_URL = "https://raw.githubusercontent.com/" + REPO + "/main/data/agent/ltx_cola.json"
SPACE_URL = "https://lightricks-ltx-video-distilled.hf.space"

CRLF = chr(13) + chr(10)


def _post_json(url, data, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers=headers or {"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def _get_json(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def _upload_image(space_url, api_prefix, img_path, filename, headers):
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    lines = []
    lines.append("--" + boundary)
    lines.append('Content-Disposition: form-data; name="files"; filename="' + filename + '_in.png"')
    lines.append("Content-Type: image/png")
    lines.append("")
    header_part = CRLF.join(lines) + CRLF

    body = header_part.encode() + img_bytes + (CRLF + "--" + boundary + "--" + CRLF).encode()

    upload_headers = dict(headers)
    upload_headers["Content-Type"] = "multipart/form-data; boundary=" + boundary

    upload_url = space_url + api_prefix + "/upload"
    req = urllib.request.Request(upload_url, data=body, headers=upload_headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    hf_token = ""
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("HF_TOKEN="):
                hf_token = line.split("=", 1)[1].strip().strip('"').strip("'")

    headers = {"User-Agent": "LofiProducer/1.0"}
    if hf_token:
        headers["Authorization"] = "Bearer " + hf_token

    print("Leyendo /config...", flush=True)
    try:
        config = _get_json(SPACE_URL + "/config", headers=headers)
        api_prefix = config.get("api_prefix", "")
        print("  api_prefix:", repr(api_prefix), flush=True)
    except Exception as e:
        print("ERROR /config:", e, flush=True)
        return

    print("Leyendo /info...", flush=True)
    try:
        info = _get_json(SPACE_URL + api_prefix + "/info", headers=headers)
        named = info.get("named_endpoints", {})
        print("  Endpoints:", list(named.keys())[:10], flush=True)
        video_endpoint = None
        for name in named:
            if "image" in name.lower() and "video" in name.lower():
                video_endpoint = name
                break
        if not video_endpoint and named:
            video_endpoint = list(named.keys())[0]
        print("  Endpoint elegido:", video_endpoint, flush=True)
    except Exception as e:
        print("ERROR /info:", e, flush=True)
        return

    print("Descargando cola...", flush=True)
    try:
        with urllib.request.urlopen(COLA_URL, timeout=30) as r:
            cola = json.loads(r.read())
    except Exception as e:
        print("ERROR cola:", e, flush=True)
        return

    pendientes = [item for item in cola if not item.get("completado", False)]
    print("Cola:", len(pendientes), "pendientes", flush=True)
    if len(pendientes) == 0:
        print("Nada que hacer.", flush=True)
        return

    item = pendientes[0]
    filename = item["nombre"]
    prompt = item["prompt"]
    img_url = item["imagen_url"]

    print("")
    print("[1/" + str(len(pendientes)) + "] " + filename, flush=True)
    print("  Prompt:", prompt[:80] + "...", flush=True)

    img_path = str(ROOT) + "/tmp/" + filename + "_in.png"
    print("  Descargando imagen...", flush=True)
    try:
        urllib.request.urlretrieve(img_url, img_path)
        print("  Imagen:", os.path.getsize(img_path) // 1024, "KB", flush=True)
    except Exception as e:
        print("  Error descargando:", e, flush=True)
        return

    print("  Subiendo imagen al Space...", flush=True)
    try:
        upload_resp = _upload_image(SPACE_URL, api_prefix, img_path, filename, headers)
        print("  Upload resp:", str(upload_resp)[:200], flush=True)
        if isinstance(upload_resp, list) and len(upload_resp) > 0:
            uploaded_path = upload_resp[0]
        else:
            print("  ERROR upload:", upload_resp, flush=True)
            return
        print("  Ruta subida:", uploaded_path, flush=True)
    except Exception as e:
        print("  ERROR upload:", type(e).__name__, ":", e, flush=True)
        if hasattr(e, 'read'):
            print("  Body:", e.read().decode()[:500], flush=True)
        return

    print("  Llamando /call/image_to_video...", flush=True)
    call_url = SPACE_URL + api_prefix + "/call/image_to_video"
    print("  URL:", call_url, flush=True)

    # Payload con la ruta subida (sin meta, formato aceptado por Gradio)
    import uuid
    session_hash = "lofiproducer_fixed_session_001"
    print("  session_hash:", session_hash, flush=True)
    payload = {
        "data": [
            prompt,
            "worst quality, inconsistent motion, blurry, jittery, distorted",
            {"path": uploaded_path},
            "",
            480.0,
            832.0,
            "image-to-video",
            10.0,
            9.0,
            42,
            True,
            1.0,
            True
        ],
        "session_hash": session_hash
    }

    try:
        # Usar requests (maneja json= correctamente, sin serializar a string)
        import requests
        resp = requests.post(call_url, json=payload, headers=headers, timeout=600)
        print("  Status:", resp.status_code, flush=True)
        if resp.status_code != 200:
            print("  Body:", resp.text[:500], flush=True)
            return
        result = resp.json()
        print("  Respuesta inicial:", str(result)[:500], flush=True)

        event_id = result.get("event_id") if isinstance(result, dict) else None
        if event_id:
            print("  event_id:", event_id, flush=True)
            poll_url = SPACE_URL + api_prefix + "/call/image_to_video/" + str(event_id) + "?session_hash=" + session_hash
            for intento in range(90):
                time.sleep(10)
                try:
                    poll_headers = dict(headers)
                    poll_headers["Accept"] = "text/event-stream"
                    req2 = urllib.request.Request(poll_url, headers=poll_headers)
                    with urllib.request.urlopen(req2, timeout=60) as r2:
                        raw = r2.read().decode("utf-8", errors="ignore")
                    print("  Poll", intento+1, ":", raw[:200], flush=True)
                    if "process_completed" in raw:
                        print("  COMPLETADO:", raw[-800:], flush=True)
                        break
                except Exception as ep:
                    print("  Poll err:", str(ep)[:100], flush=True)
        else:
            print("  Sin event_id:", str(result)[:500], flush=True)
    except Exception as e:
        print("  Error call:", type(e).__name__, ":", e, flush=True)
        if hasattr(e, 'read'):
            print("  Body:", e.read().decode()[:500], flush=True)


if __name__ == "__main__":
    main()
