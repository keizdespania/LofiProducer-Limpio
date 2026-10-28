import json, pathlib, urllib.request, urllib.parse, sys, time, os, mimetypes

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN = ROOT / "data/youtube_token.json"

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
    tok = json.loads(token_path.read_text())
    if time.time() > tok.get("expires_at", 0) - 60:
        return _refresh(tok, token_path)
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
