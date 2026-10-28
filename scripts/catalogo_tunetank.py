"""catalogo_tunetank.py - Catálogo completo de Tunetank (incluye playlists y guía)."""
import json, urllib.request, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "agent" / "tunetank_catalogo.json"
MCP_URL = "https://mcp.tunetank.com"

def _mcp(tool, args=None):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": args or {}}}
    data = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0"}
    req = urllib.request.Request(MCP_URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        for l in resp.splitlines():
            if l.startswith("data: "): return json.loads(l[6:])
        return json.loads(resp)
    except Exception as e:
        print(f"❌ {tool}: {e}")
        return None

def _extraer(res):
    if not res: return []
    try:
        for b in res.get("result", {}).get("content", []):
            if b.get("type") == "text":
                d = json.loads(b.get("text", "{}"))
                if isinstance(d, list): return d
                for v in d.values():
                    if isinstance(v, list): return v
    except: pass
    return []

def generar():
    print("[catalogo] Consultando API oficial de Tunetank MCP...", flush=True)
    cat = {}
    
    # 1. Listas básicas
    for tool, clave in [("list_moods", "moods"), ("list_genres", "generos"), ("list_themes", "temas")]:
        print(f"  🔍 {clave}...", flush=True)
        cat[clave] = _extraer(_mcp(tool))
        print(f"     ✅ {len(cat[clave])}", flush=True)
    
    # 2. Playlists (nuevo)
    print("  🔍 playlists...", flush=True)
    cat["playlists"] = _extraer(_mcp("list_playlists", {"limit": 20}))
    print(f"     ✅ {len(cat['playlists'])}", flush=True)
    
    # 3. Guía de parámetros (según doc oficial)
    cat["_guia_dj"] = {
        "buscar_musica": {
            "herramienta": "search_music",
            "parametros": {
                "query": "Texto libre (nombre de canción o artista)",
                "name": "Nombre exacto de la canción",
                "artist": "Nombre del artista",
                "genre": "Nombre o ID numérico del género",
                "mood": "Nombre o ID numérico del mood",
                "theme": "Nombre o ID numérico del tema",
                "duration": "Duración objetivo en segundos (ej. 30)",
                "tolerance": "Margen ± en segundos (por defecto 5)",
                "limit": "Máximo de resultados (por defecto 20, máx 50)"
            }
        },
        "buscar_efectos": {
            "herramienta": "search_sfx",
            "parametros": {
                "query": "Texto libre (ej. 'whoosh')",
                "category": "Categoría del SFX",
                "duration": "Duración objetivo en segundos",
                "tolerance": "Margen ± en segundos",
                "limit": "Máximo de resultados"
            }
        },
        "licencia": "Gratis para YouTube, Shorts, TikTok, Reels, podcasts. Se puede monetizar. Atribución no obligatoria pero agradecida. Claims se resuelven en tunetank.com/copyright-claims [citation:2][citation:5]"
    }
    
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cat, indent=2, ensure_ascii=False))
    print(f"\n✅ Catálogo completo guardado en {OUT}", flush=True)

if __name__ == "__main__": generar()
