"""investigador_redes.py - Detective multi-fuente de tendencias."""
import json, sys, pathlib, datetime, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def _leer_env(k):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39))
    return None

def _youtube_buscar(query, dias=30, max_results=10, region="ES"):
    try:
        from fases.tendencias import buscar_videos, detalle_videos, normalizar
        ids = buscar_videos(query, dias=dias, max_results=max_results)
        if not ids: return []
        items = detalle_videos(ids)
        return [normalizar(it) for it in items]
    except Exception as e:
        print(f"[investigador] YouTube fallo: {e}", flush=True)
        return []

def _youtube_trending_region(region="ES", max_results=10):
    key = _leer_env("YOUTUBE_API_KEY")
    if not key: return []
    params = {"key": key, "part": "snippet,statistics", "chart": "mostPopular", "regionCode": region, "maxResults": max_results}
    url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(params)
    try:
        r = json.loads(urllib.request.urlopen(url, timeout=15).read())
        out = []
        for it in r.get("items", []):
            s = it.get("snippet", {}); st = it.get("statistics", {})
            out.append({"id": it.get("id"), "titulo": s.get("title", ""), "canal": s.get("channelTitle", ""), "vistas": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)), "fuente": "youtube_trending"})
        return out
    except Exception as e:
        print(f"[investigador] YT trending fallo: {e}", flush=True)
        return []

def _google_trends(keywords=None, geo="ES"):
    """Google Trends via RSS público (sin pandas, sin trendspyg)."""
    import urllib.request, re
    out = []
    try:
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
        titulos = re.findall(r"<title>(.*?)</title>", r)
        for titulo in titulos[1:]:  # el primero es el titulo del feed
            out.append({"keyword": titulo, "fuente": "google_trends_rss"})
    except Exception as e:
        print(f"[investigador] Trends RSS fallo: {e}", flush=True)
    return out


def _reddit(subreddits):
    """Reddit via RSS publico (sin libreria redd, sin bloqueo 403)."""
    import urllib.request, re
    out = []
    for sub in subreddits[:3]:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.rss"
            req = urllib.request.Request(url, headers={"User-Agent": "LofiProducer/1.0"})
            r = urllib.request.urlopen(req, timeout=15).read().decode("utf-8")
            import time as _t; _t.sleep(1)
            titulos = re.findall(r"<title>(.*?)</title>", r)
            for titulo in titulos[1:6]:
                out.append({"titulo": titulo, "subreddit": sub, "score": 0, "fuente": "reddit_rss"})
        except Exception as e:
            print(f"[investigador] Reddit r/{sub} fallo: {e}", flush=True)
    return out


def _hackernews():
    try:
        url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        ids = json.loads(urllib.request.urlopen(url, timeout=10).read())[:10]
        out = []
        for i in ids:
            try:
                it = json.loads(urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{i}.json", timeout=5).read())
                out.append({"titulo": it.get("title", ""), "score": it.get("score", 0), "fuente": "hackernews"})
            except Exception:
                continue
        return out
    except Exception as e:
        print(f"[investigador] HN fallo: {e}", flush=True)
        return []

def _cargar_cfg_nicho(nicho):
    cfg = json.loads((ROOT / "config" / "nichos.json").read_text())
    return cfg.get(nicho, {})

def investigar(nicho, region="ES"):
    cfg = _cargar_cfg_nicho(nicho)
    queries = cfg.get("queries_youtube", []); subs = cfg.get("subreddits", []); kws = cfg.get("keywords_trends", [])
    print(f"[investigador] {nicho}: {len(queries)} q, {len(subs)} subs, {len(kws)} kw", flush=True)
    resultados = {"youtube": [], "trending": [], "trends": [], "reddit": [], "hackernews": [], "nichos": nicho}
    def _tarea_yt(q): return (q, _youtube_buscar(q, region=region))
    with ThreadPoolExecutor(max_workers=4) as ex:
        futuros = [ex.submit(_tarea_yt, q) for q in queries[:3]]
        for fut in as_completed(futuros):
            try:
                q, res = fut.result(timeout=30)
                resultados["youtube"].extend(res)
            except Exception as e:
                print(f"[investigador] tarea yt fallo: {e}", flush=True)
    resultados["trending"] = _youtube_trending_region(region, 10)
    resultados["trends"] = _google_trends(kws)
    resultados["reddit"] = _reddit(subs)
    resultados["hackernews"] = _hackernews()
    out_path = ROOT / "data" / "agent" / f"investigacion_{nicho}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({**resultados, "ts": datetime.datetime.now().isoformat()}, indent=2, ensure_ascii=False))
    print(f"[investigador] Guardado: {out_path}", flush=True)
    return resultados

def resumen_texto(nicho="ia_news", top=10):
    try:
        r = investigar(nicho)
        lineas = [f"=== TENDENCIAS {nicho} ==="]
        for v in r["youtube"][:top]:
            lineas.append(f"YT: {v.get(chr(116)+chr(105)+chr(116)+chr(117)+chr(108)+chr(111), chr(63))} ({v.get(chr(118)+chr(105)+chr(115)+chr(116)+chr(97)+chr(115), 0)} vistas)")
        for t in r["trends"]:
            lineas.append(f"Trends: {t[chr(107)+chr(101)+chr(121)+chr(119)+chr(111)+chr(114)+chr(100)]} ({chr(83)+chr(85)+chr(66)+chr(69) if t[chr(115)+chr(117)+chr(98)+chr(101)] else chr(66)+chr(65)+chr(74)+chr(65)})")
        for p in r["reddit"][:5]:
            lineas.append(f"Reddit/{p[chr(115)+chr(117)+chr(98)+chr(114)+chr(101)+chr(100)+chr(100)+chr(105)+chr(116)]}: {p[chr(116)+chr(105)+chr(116)+chr(117)+chr(108)+chr(111)]}")
        return chr(10).join(lineas)
    except Exception as e:
        return f"ERROR investigador: {e}"

if __name__ == "__main__":
    nicho = sys.argv[1] if len(sys.argv) > 1 else "ia_news"
    print(json.dumps(investigar(nicho), indent=2, ensure_ascii=False)[:2000])