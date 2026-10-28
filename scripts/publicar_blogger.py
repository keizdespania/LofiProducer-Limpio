"""Publica un post en Blogger vía API de Google (mismo OAuth que YouTube)."""
import sys, json, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent

def _token():
    import time, urllib.parse
    tok_path = ROOT / "data" / "youtube_token.json"
    tok = json.loads(tok_path.read_text())
    # Refrescar si expiro (o expira en <60s)
    if time.time() > tok.get("expires_at", 0) - 60:
        print("  [token] refrescando...")
        try:
            data = urllib.parse.urlencode({
                "client_id": tok["client_id"],
                "client_secret": tok["client_secret"],
                "refresh_token": tok["refresh_token"],
                "grant_type": "refresh_token"
            }).encode()
            req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
            r = json.loads(urllib.request.urlopen(req).read())
            tok["access_token"] = r["access_token"]
            tok["expires_at"] = time.time() + r.get("expires_in", 3600)
            tok_path.write_text(json.dumps(tok, indent=2))
            print("  [token] OK")
        except Exception as e:
            print(f"  [token] fallo: {e}")
    return tok["access_token"]

def publicar(titulo, contenido_html, blog_id=None):
    """Publica un post en Blogger con retry automático."""
    for intento in range(3):
        try:
            return _publicar_una_vez(titulo, contenido_html, blog_id)
        except urllib.error.HTTPError as e:
            if e.code == 401 and intento < 2:
                print(f"  [retry] Token expirado, refrescando (intento {intento+1}/3)...")
                # Forzar refresh del token
                tok_path = ROOT / "data" / "youtube_token.json"
                tok = json.loads(tok_path.read_text())
                tok["expires_at"] = 0  # forzar refresh
                tok_path.write_text(json.dumps(tok, indent=2))
                continue
            raise
    return "ERROR: 3 reintentos fallidos"

def _publicar_una_vez(titulo, contenido_html, blog_id=None):
    """Intento único de publicación."""
    if not blog_id:
        # Obtener el primer blog del usuario
        req = urllib.request.Request(
            "https://www.googleapis.com/blogger/v3/users/self/blogs",
            headers={"Authorization": f"Bearer {_token()}"})
        r = json.loads(urllib.request.urlopen(req).read())
        if not r.get("items"):
            return "ERROR: No hay blogs en esta cuenta. Crea uno en blogger.com"
        blog_id = r["items"][0]["id"]
        print(f"  Blog: {r['items'][0]['name']} ({blog_id})")

    endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts/"
    payload = {"kind": "blogger#post", "title": titulo, "content": contenido_html}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(endpoint, data=data, method="POST",
        headers={"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    return f"OK: Post publicado en Blogger (ID {r.get('id')}). URL: {r.get('url')}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python scripts/publicar_blogger.py 'Título' 'Contenido HTML' [blog_id]")
        sys.exit(1)
    print(publicar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None))
