"""pixabay_descarga.py — Descarga clips de Pixabay según preset del contrato.
Soporta vertical (Shorts) y horizontal (vídeo largo).
"""
import os, sys, json, pathlib, urllib.parse, time
try:
    from curl_cffi import requests as _req
except ImportError:
    import urllib.request as _req

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRATO = ROOT / "data" / "agent" / "pixabay_contract.json"
CACHE = ROOT / "output" / "pixabay"
CACHE.mkdir(parents=True, exist_ok=True)


def _leer_env(k):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _preset(nombre):
    if not CONTRATO.exists():
        return None
    d = json.loads(CONTRATO.read_text())
    return d.get("presets", {}).get(nombre)


def _buscar(params, key):
    qs = urllib.parse.urlencode({**params, "key": key})
    url = f"https://pixabay.com/api/videos/?{qs}"
    try:
        r = _req.get(url, impersonate="chrome", timeout=20)
        return r.json().get("hits", [])
    except Exception as e:
        print(f"[pixabay] busqueda fallo: {e}", flush=True)
        return []


def _descargar(url, dest):
    try:
        r = _req.get(url, impersonate="chrome", timeout=60)
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"[pixabay] descarga fallo: {e}", flush=True)
        return False


def descargar(preset_nombre, max_clips=3, tag="clip"):
    """Descarga N clips del preset. Devuelve lista de rutas locales."""
    key = _leer_env("PIXABAY_KEY") or _leer_env("PIXABAY_API_KEY")
    if not key:
        return {"error": "sin PIXABAY_KEY en .env"}

    p = _preset(preset_nombre)
    if not p:
        return {"error": f"preset '{preset_nombre}' no existe"}

    params = dict(p.get("params", {}))
    per_page = params.pop("per_page", 5)
    params["per_page"] = min(per_page, 20)

    print(f"[pixabay] preset={preset_nombre} q='{params.get('q')}' ori={params.get('orientation','all')}", flush=True)
    hits = _buscar(params, key)
    if not hits:
        print(f"[pixabay] 0 resultados", flush=True)
        return {"clips": [], "preset": preset_nombre, "vacio": True}

    # Pixabay devuelve videos en varias calidades: large, medium, small, tiny
    queremos = "large" if params.get("orientation") == "horizontal" else "medium"
    clips = []
    for h in hits:
        if len(clips) >= max_clips:
            break
        vid = h.get("videos", {})
        url = (vid.get(queremos) or vid.get("medium") or vid.get("small") or {}).get("url")
        if not url:
            continue
        fname = f"{tag}_{h.get('id','x')}_{queremos}.mp4"
        dest = CACHE / fname
        if dest.exists() and dest.stat().st_size > 10_000:
            clips.append(str(dest))
            print(f"[pixabay] cache {fname}", flush=True)
            continue
        if _descargar(url, dest):
            clips.append(str(dest))
            print(f"[pixabay] OK {fname} ({dest.stat().st_size//1024} KB)", flush=True)
        time.sleep(0.5)

    return {"clips": clips, "preset": preset_nombre, "total": len(clips)}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: pixabay_descarga.py <preset> [max_clips] [tag]")
        sys.exit(1)
    preset = sys.argv[1]
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    tag = sys.argv[3] if len(sys.argv) > 3 else preset
    print(json.dumps(descargar(preset, maxn, tag), indent=2, ensure_ascii=False))
