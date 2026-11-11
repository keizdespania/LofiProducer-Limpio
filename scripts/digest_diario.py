#!/usr/bin/env python3
"""digest_diario.py — Digest operativo diario al chat privado."""
import sys, json, pathlib, datetime, urllib.request, urllib.parse, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))

TOKEN_FILE = ROOT / "data" / "youtube_encuadre_token.json"
AGENT = ROOT / "data" / "agent"
OUT = ROOT / "output" / "encuadre"
WEB = "https://elencuadre.pages.dev"


def _access():
    try:
        from subir_youtube import token
        return token("data/youtube_encuadre_token.json")
    except Exception:
        return None


def _api_get(url, access):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {access}"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:200]
        return {"_err": f"HTTP {e.code}: {body}"}
    except Exception as e:
        return {"_err": str(e)}


def _yt_basico(access, dias=7):
    ahora = datetime.datetime.utcnow()
    desde = (ahora - datetime.timedelta(days=dias)).strftime("%Y-%m-%dT00:00:00Z")
    r = _api_get("https://www.googleapis.com/youtube/v3/channels?part=statistics&mine=true", access)
    if "_err" in r: return {"_err": r["_err"]}
    st = (r.get("items") or [{}])[0].get("statistics") or {}
    canal = {
        "subs": int(st.get("subscriberCount", 0)),
        "views": int(st.get("viewCount", 0)),
        "videos": int(st.get("videoCount", 0)),
    }
    r2 = _api_get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails&mine=true", access)
    if "_err" in r2: return {"canal": canal}
    uploads = (r2.get("items") or [{}])[0].get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not uploads: return {"canal": canal}

    vids = []
    page = None
    while True:
        q = {"part": "contentDetails", "playlistId": uploads, "maxResults": "50"}
        if page: q["pageToken"] = page
        rr = _api_get(f"https://www.googleapis.com/youtube/v3/playlistItems?{urllib.parse.urlencode(q)}", access)
        if "_err" in rr: break
        for it in rr.get("items", []):
            vid = it.get("contentDetails", {}).get("videoId")
            pub = it.get("contentDetails", {}).get("videoPublishedAt", "")
            if vid and pub >= desde: vids.append({"id": vid, "pub": pub})
        page = rr.get("nextPageToken")
        if not page: break
    if not vids: return {"canal": canal, "videos": []}

    stats_map = {}
    for i in range(0, len(vids), 50):
        chunk = vids[i:i+50]
        ids = ",".join(v["id"] for v in chunk)
        rr = _api_get(f"https://www.googleapis.com/youtube/v3/videos?part=statistics,snippet,contentDetails&id={ids}", access)
        if "_err" in rr: continue
        for v in rr.get("items", []):
            dur = v["contentDetails"].get("duration", "PT0S")
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", dur)
            secs = int(m.group(1) or 0)*3600 + int(m.group(2) or 0)*60 + int(m.group(3) or 0) if m else 0
            stats_map[v["id"]] = {
                "titulo": v["snippet"]["title"],
                "views": int(v["statistics"].get("viewCount", 0)),
                "likes": int(v["statistics"].get("likeCount", 0)),
                "dur": secs,
                "tipo": "short" if secs <= 61 else "largo",
            }
    videos = []
    for v in vids:
        if v["id"] in stats_map:
            videos.append({**stats_map[v["id"]], "id": v["id"], "pub": v["pub"]})
    videos.sort(key=lambda x: x["views"], reverse=True)
    return {"canal": canal, "videos": videos}


def _yt_analytics(access, dias=7):
    hoy = datetime.date.today()
    desde = (hoy - datetime.timedelta(days=dias)).isoformat()
    hasta = hoy.isoformat()
    q = {
        "ids": "channel==MINE",
        "startDate": desde,
        "endDate": hasta,
        "metrics": "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage",
        "dimensions": "video",
        "sort": "-views",
        "maxResults": "10",
    }
    r = _api_get(f"https://youtubeanalytics.googleapis.com/v2/reports?{urllib.parse.urlencode(q)}", access)
    if "_err" in r:
        return None
    filas = r.get("rows") or []
    if not filas: return None
    cols = [h["name"] for h in r.get("columnHeaders", [])]
    idx = {c: i for i, c in enumerate(cols)}
    out = []
    for f in filas:
        out.append({
            "id": f[idx["video"]],
            "views": int(f[idx["views"]]),
            "watch_min": int(f[idx["estimatedMinutesWatched"]]),
            "avg_ret": round(float(f[idx["averageViewPercentage"]]), 1),
        })
    return out


def _cloudflare_web(dias=7):
    try:
        from cloudflare_stats import resumen
        r = resumen(dias)
        return {
            "page_views": r.get("page_views", 0),
            "visitas": r.get("visitas", 0),
            "top_paginas": r.get("top_paginas", [])[:3],
            "top_paises": r.get("top_paises", [])[:3],
        }
    except Exception:
        return None


def _contenido_completo(fecha):
    if not (OUT / f"video_largo_{fecha}.mp4").exists(): return False
    n_shorts = len(list(OUT.glob(f"short_*_{fecha}.mp4")))
    if n_shorts < 4: return False
    yt = AGENT / f"youtube_urls_{fecha}.json"
    if not yt.exists(): return False
    try:
        d = json.loads(yt.read_text())
        if not (d.get("largo") or {}).get("video_id"): return False
        if len(d.get("shorts") or []) < 4: return False
    except: return False
    n_posts = len(list((ROOT / "web" / "docs" / "analisis").glob(f"{fecha}-*.md")))
    if n_posts < 2: return False
    return True


def contenido_completo_hoy(fecha=None):
    """API pública: True si el pipeline ya subió todo el contenido del día."""
    if fecha is None:
        fecha = datetime.date.today().isoformat()
    return _contenido_completo(fecha)


def _fmt_num(n):
    if n >= 1000: return f"{n/1000:.1f}K"
    return str(n)


def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()

    access = _access()
    if not access:
        print("ERROR: sin token YouTube")
        return False

    NL = chr(10)
    lineas = [f"📊 <b>SOMOS EL ENCUADRE · {fecha}</b>", ""]

    yt = _yt_basico(access, dias=7)
    if "_err" in yt:
        lineas.append(f"⚠️ YouTube: {yt['_err'][:100]}")
    else:
        c = yt["canal"]
        lineas.append("📈 <b>CANAL (7d)</b>")
        lineas.append(f"· {_fmt_num(c['subs'])} subs · {_fmt_num(c['views'])} vistas · {c['videos']} vídeos")
        vids = yt.get("videos") or []
        if vids:
            lineas.append("")
            lineas.append("🔥 <b>TOP 3</b>")
            for i, v in enumerate(vids[:3], 1):
                emoji = "📱" if v["tipo"] == "short" else "🎬"
                lineas.append(f"{i}. {emoji} {v['titulo'][:50]}")
                lineas.append(f"   · {v['views']} vistas · {v['likes']} likes")

    an = _yt_analytics(access, dias=7)
    if an and yt.get("videos"):
        lookup = {v["id"]: v for v in yt["videos"]}
        mejoras = []
        for a in an[:3]:
            if a["id"] in lookup:
                v = lookup[a["id"]]
                mejoras.append(f"· {v['titulo'][:40]}… · {a['avg_ret']}% ret · {a['watch_min']}min")
        if mejoras:
            lineas.append("")
            lineas.append("📊 <b>RETENCIÓN (Analytics)</b>")
            lineas.extend(mejoras)

    cf = _cloudflare_web(7)
    if cf:
        lineas.append("")
        lineas.append("🌐 <b>WEB (7d)</b>")
        lineas.append(f"· {_fmt_num(cf['page_views'])} visitas · {_fmt_num(cf['visitas'])} sesiones")
        if cf["top_paginas"]:
            top = cf["top_paginas"][0]
            lineas.append(f"· Top: {top[0][:50]} ({top[1]})")

    lineas.append("")
    lineas.append("⏰ <b>HOY</b>")
    if _contenido_completo(fecha):
        lineas.append("· ✅ Pipeline completo")
    else:
        lineas.append("· ⚠️ Pipeline INCOMPLETO → revisa log")

    if datetime.date.today().weekday() == 6:
        lineas.append("")
        lineas.append("📅 <b>RESUMEN SEMANAL</b>")
        lineas.append("· Revisar calendario editorial")

    texto = NL.join(lineas)

    try:
        from notificador_top1 import _post, CHAT_PRIVADO
        ok = _post(CHAT_PRIVADO, texto)
        print(f"{'OK' if ok else 'FAIL'} Digest enviado ({len(texto)} chars)")
        print(texto)
        return ok
    except Exception as e:
        print(f"ERROR enviar: {e}")
        return False


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
