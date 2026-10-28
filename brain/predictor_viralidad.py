"""predictor_viralidad.py - Score de viralidad por tema usando 5 fuentes."""
import sys, json, pathlib, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _normalizar(s):
    if not s: return ""
    return re.sub(r'[^a-z0-9áéíóúñ ]', '', s.lower())


def _match(tema_norm, texto):
    """Devuelve True si las palabras clave del tema aparecen en el texto."""
    if not texto: return False
    texto_norm = _normalizar(texto)
    palabras_tema = [w for w in tema_norm.split() if len(w) > 3]
    if not palabras_tema: return False
    matches = sum(1 for w in palabras_tema if w in texto_norm)
    return matches >= max(1, len(palabras_tema) // 2)


def score_tema(tema, investigacion):
    """Devuelve dict con score 0-100 + desglose por fuente."""
    tema_norm = _normalizar(tema)

    # 1. YouTube demand (0-40): cuántos videos + cuántas vistas
    yt_matches = [v for v in investigacion.get("youtube", []) if _match(tema_norm, v.get("titulo", ""))]
    yt_views = sum(v.get("vistas", 0) for v in yt_matches)
    yt_score = min(40, (len(yt_matches) * 8) + (min(yt_views / 100000, 16)))

    # 2. Trends rise (0-25): keyword en trends RSS
    tr_matches = [t for t in investigacion.get("trends", []) if _match(tema_norm, t.get("keyword", ""))]
    tr_score = min(25, len(tr_matches) * 12)

    # 3. Reddit engagement (0-20)
    rd_matches = [p for p in investigacion.get("reddit", []) if _match(tema_norm, p.get("titulo", ""))]
    rd_score = min(20, len(rd_matches) * 6)

    # 4. HackerNews (0-15)
    hn_matches = [p for p in investigacion.get("hackernews", []) if _match(tema_norm, p.get("titulo", ""))]
    hn_score = min(15, len(hn_matches) * 5)

    # 5. Saturación penalty (-20 si aparece en +5 videos)
    saturacion = 0
    if len(yt_matches) >= 5:
        saturacion = -20

    total = max(0, min(100, yt_score + tr_score + rd_score + hn_score + saturacion))

    return {
        "tema": tema,
        "score": round(total, 1),
        "desglose": {
            "youtube": round(yt_score, 1),
            "trends": round(tr_score, 1),
            "reddit": round(rd_score, 1),
            "hackernews": round(hn_score, 1),
            "saturacion": saturacion,
        },
        "evidencia": {
            "youtube_matches": len(yt_matches),
            "youtube_views": yt_views,
            "trends_matches": len(tr_matches),
            "reddit_matches": len(rd_matches),
            "hn_matches": len(hn_matches),
        },
    }


def rankear_temas(investigacion, top=5):
    """Extrae temas candidatos de la investigación y los rankea."""
    # Extraer temas: usa los títulos de YouTube top + keywords de Trends
    temas_set = set()

    # Top videos YouTube (agrupa por palabra clave común)
    yts = sorted(investigacion.get("youtube", []), key=lambda x: x.get("vistas", 0), reverse=True)[:10]
    for v in yts:
        titulo = v.get("titulo", "").strip()
        if titulo and len(titulo) > 5:
            temas_set.add(titulo[:60])

    # Keywords de Trends
    for t in investigacion.get("trends", []):
        kw = t.get("keyword", "").strip()
        if kw and len(kw) > 2:
            temas_set.add(kw)

    # Reddit titles top
    for p in investigacion.get("reddit", [])[:5]:
        titulo = p.get("titulo", "").strip()
        if titulo and len(titulo) > 10:
            temas_set.add(titulo[:60])

    # Scorear todos
    resultados = [score_tema(t, investigacion) for t in temas_set]
    resultados.sort(key=lambda x: x["score"], reverse=True)

    return {
        "total_candidatos": len(resultados),
        "top": resultados[:top],
        "todos": resultados,
    }


def predecir(nicho="ia_news"):
    """Carga investigación guardada y rankea temas."""
    p = ROOT / "data" / "agent" / f"investigacion_{nicho}.json"
    if not p.exists():
        return {"error": f"Sin investigación para {nicho}. Ejecuta investigador_redes.py primero."}
    inv = json.loads(p.read_text())
    return rankear_temas(inv, top=5)


if __name__ == "__main__":
    nicho = sys.argv[1] if len(sys.argv) > 1 else "ia_news"
    print(json.dumps(predecir(nicho), indent=2, ensure_ascii=False)[:3000])
