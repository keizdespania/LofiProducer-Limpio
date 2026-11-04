import json, pathlib, urllib.request, urllib.parse, sys, time, os, mimetypes

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN = ROOT / "data/youtube_token.json"


def _atribuciones_para(fecha):
    """Lee atribuciones del día y devuelve bloque de texto para la descripción."""
    import json as _j, pathlib as _p
    f = _p.Path(__file__).resolve().parent.parent / "output" / "encuadre" / ("atribuciones_" + fecha + ".json")
    if not f.exists(): return ""
    try:
        atrs = _j.loads(f.read_text())
        if not atrs: return ""
        return "\n\n--- Música ---\n" + "\n".join(atrs)
    except: return ""

def _refresh(tok, token_path):
    data = urllib.parse.urlencode({
        "client_id": tok["client_id"], "client_secret": tok["client_secret"],
        "refresh_token": tok["refresh_token"], "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    r = json.loads(urllib.request.urlopen(req).read())
    tok["access_token"] = r["access_token"]
    tok["expires_at"] = time.time() + r.get("expires_in", 3600)
    token_path.write_text(json.dumps(tok, indent=2))
    return tok["access_token"]

def token(token_path=None):
    if token_path is None:
        token_path = TOKEN
    else:
        token_path = pathlib.Path(token_path)  # FIX: str → Path
    tok = json.loads(token_path.read_text())
    # REFRESH SIEMPRE antes de subir (petición 2026-11-03)
    try:
        return _refresh(tok, token_path)
    except Exception as e:
        print(f"   ⚠️ Refresh falló ({e}), usando token actual")
        if time.time() > tok.get("expires_at", 0) - 60:
            raise RuntimeError("Token expirado y refresh falló. Ejecuta scripts/reautorizar_youtube.py")
        return tok["access_token"]

def subir(video, titulo, descripcion="", tags=None, privacidad=None, publish_at=None, token_file=None):
    """Sube vídeo a YouTube vía API v3 (resumable upload)."""
    if privacidad is None:
        privacidad = os.environ.get("YOUTUBE_PRIVACY", "private")
    print(f"  Privacidad: {privacidad}")
    access = token(token_file) if token_file else token()
    size = os.path.getsize(video)
    mime = mimetypes.guess_type(video)[0] or "video/mp4"

    # 1. Iniciar sesión de subida
    metadata = {"snippet": {"title": titulo, "description": descripcion, "tags": tags or [], "categoryId": "22"},
                "status": {"privacyStatus": "private" if publish_at else privacidad}}
    if publish_at:
        metadata["status"]["publishAt"] = publish_at
    req = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(metadata).encode(),
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json; charset=UTF-8",
                 "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": mime},
        method="POST")
    session = urllib.request.urlopen(req).headers.get("Location")

    # 2. Subir el fichero entero
    with open(video, "rb") as f:
        cuerpo = f.read()
    req2 = urllib.request.Request(session, data=cuerpo, method="PUT",
        headers={"Content-Type": mime, "Content-Length": str(size)})
    r = json.loads(urllib.request.urlopen(req2, timeout=600).read())
    return r

def actualizar_video(video_id, publish_at=None, titulo=None, descripcion=None, tags=None, token_file=None):
    """Actualiza publishAt / metadata de un vídeo existente (debe estar en privado)."""
    access = token(token_file) if token_file else token()
    # Construir body solo con los campos a actualizar
    body = {"id": video_id}
    part = []
    if publish_at:
        body["status"] = {"privacyStatus": "private", "publishAt": publish_at}
        part.append("status")
    if titulo or descripcion or tags:
        body["snippet"] = {"categoryId": "25"}  # 25 = News & Politics (ideal para El Encuadre)
        if titulo: body["snippet"]["title"] = titulo
        if descripcion: body["snippet"]["description"] = descripcion
        if tags: body["snippet"]["tags"] = tags
        part.append("snippet")
    if not part:
        print(f"   ⚠️ Nada que actualizar en {video_id}")
        return None
    part_str = ",".join(part)
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/videos?part={part_str}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json; charset=UTF-8"},
        method="PUT")
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return r
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP {e.code}: {e.read()[:200]}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/subir_youtube.py VIDEO.mp4 'Título' ['desc'] [privacidad: public|unlisted|private]")
        sys.exit(1)
    video, titulo = sys.argv[1], sys.argv[2]
    desc = sys.argv[3] if len(sys.argv) > 3 else ""
    priv = sys.argv[4] if len(sys.argv) > 4 else None
    r = subir(video, titulo, desc, privacidad=priv)
    print(f"✅ Subido: https://youtu.be/{r['id']}")
    print(f"   Estado: {r['status']['privacyStatus']}")
