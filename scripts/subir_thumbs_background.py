#!/usr/bin/env python3
"""Sube miniaturas en background con retry hasta acabar (o 24h máx)."""
import pathlib, json, sys, requests, time, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from subir_youtube import token

ROOT = pathlib.Path(__file__).resolve().parent.parent
ESTADO = ROOT / "data/agent" / "thumbs_subidas.json"
LOG = ROOT / "data/logs" / "subir_thumbs.log"
LOG.parent.mkdir(exist_ok=True)

def log(m):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    with open(LOG, "a") as f: f.write(f"[{ts}] {m}\n")
    print(f"[{ts}] {m}", flush=True)

def cargar_estado():
    if not ESTADO.exists(): return {}
    try: return json.loads(ESTADO.read_text())
    except: return {}

def guardar_estado(e):
    ESTADO.write_text(json.dumps(e, indent=2))

def _key(thumb):
    parts = thumb.stem.split("_")
    if len(parts) < 4: return None
    return f"{parts[1]}_{parts[2]}_{parts[3]}"

def subir_una(thumb, access):
    name = thumb.stem
    parts = name.split("_")
    if len(parts) < 4: return None, "mal nombre"
    fecha, tipo, vid8 = parts[1], parts[2], parts[3]
    yt_path = ROOT / f"data/agent/youtube_urls_{fecha}.json"
    if not yt_path.exists(): return None, "sin yt json"
    try: yt = json.loads(yt_path.read_text())
    except: return None, "json roto"
    full_vid = None
    if tipo == "largo" and isinstance(yt.get("largo"), dict):
        full_vid = yt["largo"].get("video_id")
    elif tipo == "short":
        for s in (yt.get("shorts") or []):
            if isinstance(s, dict) and str(s.get("video_id", "")).startswith(vid8):
                full_vid = s["video_id"]; break
    if not full_vid: return None, "sin video_id"
    try:
        with open(thumb, "rb") as f:
            r = requests.post(
                f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={full_vid}",
                headers={"Authorization": f"Bearer {access}", "Content-Type": "image/png"},
                data=f.read(), timeout=60)
        if r.status_code in (200, 204): return f"{fecha}_{tipo}_{vid8}", None
        if r.status_code == 429: return None, "429"
        return None, f"HTTP {r.status_code}: {r.text[:100]}"
    except Exception as e:
        return None, str(e)[:60]

def main():
    inicio = time.time()
    limite = 24 * 3600
    intento = 0
    while time.time() - inicio < limite:
        intento += 1
        try:
            access = token("data/youtube_encuadre_token.json")
        except Exception as e:
            log(f"❌ token: {e}. Reintento en 60s")
            time.sleep(60); continue
        estado = cargar_estado()
        thumbs = sorted((ROOT / "output/encuadre").glob("thumb_*.png"))
        if len(estado) >= len(thumbs):
            log(f"✅ TODAS SUBIDAS ({len(estado)}/{len(thumbs)})")
            return
        pendientes = [t for t in thumbs if _key(t) not in estado]
        log(f"Intento {intento}: {len(pendientes)} pendientes / {len(thumbs)} total")
        for thumb in pendientes:
            k = _key(thumb)
            if not k: continue
            key, err = subir_una(thumb, access)
            if key:
                estado[key] = True
                guardar_estado(estado)
                log(f"  ✅ {key} ({len(estado)}/{len(thumbs)})")
                time.sleep(45)
            elif err == "429":
                log(f"  ⏳ 429 → esperando 30min")
                time.sleep(1800)
                break
            elif err:
                log(f"  ⚠️ {thumb.stem}: {err}")
                time.sleep(5)
        time.sleep(60)

if __name__ == "__main__":
    main()
