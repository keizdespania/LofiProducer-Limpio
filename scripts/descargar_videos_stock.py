"""descargar_videos_stock.py - Coverr (sintaxis oficial) + Wikimedia fallback."""
import sys, json, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre" / "videos"
OUT.mkdir(parents=True, exist_ok=True)

def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def _descargar(url, destino):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as r, open(destino, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"    ❌ Error descargando: {e}")
        return False

def buscar_coverr(query, cantidad=1):
    key = _leer_env("COVERR_API_KEY")
    if not key:
        return []
    # Sintaxis oficial: header Authorization + parámetro urls=true
    params = urllib.parse.urlencode({"query": query, "page_size": cantidad, "urls": "true"})
    url = f"https://api.coverr.co/videos?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": "Mozilla/5.0"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=20).read())
        hits = data.get("hits", [])
        descargas = []
        for h in hits[:cantidad]:
            urls = h.get("urls", {})
            mp4 = urls.get("mp4") or urls.get("mp4_download")
            if not mp4: continue
            nombre = f"coverr_{h.get('id', 'x')}.mp4"
            destino = OUT / nombre
            if not destino.exists() and _descargar(mp4, destino):
                descargas.append({"archivo": nombre, "query": query, "url": mp4, "fuente": "Coverr", "titulo": h.get("title")})
                print(f"    ✅ Coverr: {nombre} ({h.get('title', '')})")
        return descargas
    except Exception as e:
        print(f"    ⚠️ Coverr falló: {e}")
        return []

if __name__ == "__main__":
    queries = ["politics", "news", "chess", "manipulation"]
    todos = []
    for q in queries:
        print(f"🔍 Buscando: {q}")
        res = buscar_coverr(q, 1)
        todos.extend(res)
    
    (OUT / "index.json").write_text(json.dumps(todos, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(todos)} clips descargados")
