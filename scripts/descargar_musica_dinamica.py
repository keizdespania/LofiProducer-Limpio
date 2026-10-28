"""descargar_musica_dinamica.py - Descarga música de Tunetank (Bypass Cloudflare 1010)."""
import sys, json, urllib.request, pathlib
from analista_audio import analizar_pista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)

MCP_URL = "https://mcp.tunetank.com"

MOODS_TUNETANK = {
    "tension": "dark",
    "epico": "epic",
    "relax": "calm",
    "misterio": "mysterious",
    "inspirador": "inspiring",
    "electronico": "electronic"
}

def _llamar_mcp(tool, argumentos):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": argumentos}
    }
    data = json.dumps(payload).encode()
    
    # LA CLAVE: User-Agent de Chrome para saltar el bloqueo 1010
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    
    req = urllib.request.Request(MCP_URL, data=data, headers=headers, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", errors="replace")
        for linea in resp.splitlines():
            if linea.startswith("data: "):
                return json.loads(linea[6:])
        return json.loads(resp)
    except Exception as e:
        print(f"[tunetank] Error: {e}")
        return None

def descargar_por_mood(mood, cantidad=1):
    mood_tunetank = MOODS_TUNETANK.get(mood.lower(), "calm")
    print(f"   🔍 Buscando en Tunetank: mood='{mood_tunetank}'...", flush=True)
    res = _llamar_mcp("search_music", {"mood": mood_tunetank, "limit": 5})
    if not res:
        return []
    
    tracks = []
    try:
        content = res.get("result", {}).get("content", [])
        for bloque in content:
            if bloque.get("type") == "text":
                datos = json.loads(bloque.get("text", "{}"))
                if isinstance(datos, dict):
                    tracks = datos.get("tracks", datos.get("results", []))
                elif isinstance(datos, list):
                    tracks = datos
                break
    except Exception:
        return []
    
    if not tracks:
        print(f"⚠️ Sin resultados para mood: {mood_tunetank}")
        return []
    
    descargados = []
    for track in tracks[:cantidad]:
        preview_url = track.get("preview") or track.get("preview_url")
        if not preview_url: continue
        nombre = f"{mood}_{track.get('id', 'x')}.mp3"
        destino = OUT / nombre
        if not destino.exists():
            req_audio = urllib.request.Request(preview_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_audio, timeout=60) as r, open(destino, 'wb') as f:
                f.write(r.read())
        # Analizar el audio para encontrar el pico de energía
        print(f"   🔍 Analizando energía de {nombre}...", flush=True)
        analisis = analizar_pista(destino)
        

        descargados.append({
            "archivo": nombre,
            "url": preview_url,
            "analisis_audio": analisis,
            "atribucion": f"Tunetank - {track.get('name', '')} by {track.get('artist', '')}"
        })
        print(f"   ✅ Descargado: {nombre}", flush=True)
    return descargados


def pedir_efecto(categoria, duracion_seg=2):
    """Busca un efecto de sonido (whoosh, impact, etc.) en Tunetank."""
    args = {"category": categoria, "duration": duracion_seg, "tolerance": 1, "limit": 3}
    print(f"   🔊 Buscando SFX: '{categoria}'...", flush=True)
    res = _llamar_mcp("search_sfx", args)
    if not res: return []
    
    # Extraer resultados (misma estructura que search_music)
    tracks = []
    try:
        content = res.get("result", {}).get("content", [])
        for bloque in content:
            if bloque.get("type") == "text":
                datos = json.loads(bloque.get("text", "{}"))
                if isinstance(datos, dict):
                    tracks = datos.get("sfx", datos.get("results", []))
                elif isinstance(datos, list):
                    tracks = datos
                break
    except: pass
    
    if not tracks: return []
    
    for s in tracks[:1]:
        url = s.get("preview")
        if not url: continue
        nombre = f"sfx_{categoria}_{s.get('id','x')}.mp3"
        destino = OUT / nombre
        if not destino.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r, open(destino, "wb") as f:
                f.write(r.read())
        print(f"   ✅ {nombre}", flush=True)
        return [{"archivo": nombre, "categoria": categoria, "atribucion": f"Tunetank SFX - {categoria}"}]
    return []

if __name__ == "__main__":
    mood = sys.argv[1] if len(sys.argv) > 1 else "relax"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    res = descargar_por_mood(mood, n)
    print(json.dumps(res, indent=2, ensure_ascii=False))