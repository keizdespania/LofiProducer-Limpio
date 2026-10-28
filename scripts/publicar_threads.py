"""Publica un post en Threads vía API oficial de Meta."""
import sys, json, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def publicar(texto, imagen_url=None):
    """Publica texto (y opcionalmente imagen) en Threads."""
    app_id = _env("THREADS_APP_ID")
    app_secret = _env("THREADS_APP_SECRET")
    token = _env("THREADS_ACCESS_TOKEN")
    user_id = _env("THREADS_USER_ID")

    if not all([app_id, app_secret, token, user_id]):
        return "ERROR: faltan THREADS_APP_ID, THREADS_APP_SECRET, THREADS_ACCESS_TOKEN o THREADS_USER_ID en .env"

    # Paso 1: crear contenedor
    params = {"media_type": "TEXT", "text": texto, "access_token": token}
    if imagen_url:
        params["media_type"] = "IMAGE"
        params["image_url"] = imagen_url
    url = f"https://graph.threads.net/v1.0/{user_id}/threads"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    r = json.loads(urllib.request.urlopen(req, timeout=30).read())
    container_id = r.get("id")
    if not container_id:
        return f"ERROR: no se creó contenedor: {r}"

    # Paso 2: publicar
    pub_url = f"https://graph.threads.net/v1.0/{user_id}/threads_publish"
    pub_data = urllib.parse.urlencode({"creation_id": container_id, "access_token": token}).encode()
    req2 = urllib.request.Request(pub_url, data=pub_data, method="POST")
    r2 = json.loads(urllib.request.urlopen(req2, timeout=30).read())
    if r2.get("id"):
        return f"OK: Hilo publicado (ID {r2['id']})"
    return f"ERROR: {r2}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/publicar_threads.py 'texto' [imagen_url]")
        sys.exit(1)
    print(publicar(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
