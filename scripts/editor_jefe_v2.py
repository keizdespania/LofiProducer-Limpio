import re
# ═══════════════════════════════════════════════════════════════════
# EDITOR JEFE V2 — Top 1 mundial (2026-11-03)
# 4 capas: pre-filtro + scoring + LLM rúbrica + validación/fallback
# ═══════════════════════════════════════════════════════════════════

BASURA_V2 = [
    # Gastronomía / virales / publirreportajes
    "jamón", "jamon", "taco", "ensalada", "restaurante", "gastronomía", "chef",
    "cerámica", "cacharro", "tupper", "barista", "cafetera",
    "publirreportaje", "socio operativo", "revoluciona el mercado",
    "presenta su nueva", "anuncia el lanzamiento", "acerca la experiencia",
    "líder en su sector", "nodus", "incapto", "kmzeroia",
    # Deportes
    "alcaraz", "nadal", "motogp", "laliga", "la liga", "champions",
    "copa del rey", "europa league", "fichaje", "delantero", "portero",
    "atleti", "betis", "real madrid", "barça", "mbappé", "athletic",
    "partido de fútbol", "balón",
    # Farándula / corazón
    "ana obregón", "obregón", "dell'atte", "sálvame", "supervivientes",
    "gran hermano", "operación triunfo", "masterchef", "influencer",
    "prensa rosa", "corazón", "corazon", "famoso", "celebridad",
    "boda", "divorcio", "embarazo", "reconciliación", "ruptura",
    # Sucesos sin gestión pública
    "apuñal", "atraco", "robo", "asalto", "agredido",
    "vidas truncadas", "tragedia ferroviaria",
    # Deportes (ampliado 2026-11-03)
    "striker", "on-field", "on field", "delantero", "defensa central",
    "deportivo", "deportes", "gol ", "goles", "penalti", "árbitro", "arbitro",
    "entrenamiento", "lesión", "lesion", "temporada", "liga ", "copa ",
    # Curiosidades internacionales (no framing político)
    "nike clothes", "religious authority rules", "wear nike",
    # Audiencias / local sin impacto global (2026-11-03)
    "en direct", "audition de", "audition au", "audition à",
    "commission d'enquête", "assemblée nationale",
    # Misc
    "intocable", "blocus", "apagón", "apagon", "sin luz",
]

# Keywords que SUBEN el score (impacto público)
KEYWORDS_IMPACTO = {
    "gobierno": 8, "congreso": 8, "senado": 7, "fiscalía": 8, "fiscalia": 8,
    "tribunal supremo": 8, "constitucional": 8, "boe": 7, "moncloa": 7,
    "presupuesto": 7, "inflación": 7, "inflacion": 7, "pensiones": 7,
    "vivienda": 7, "empleo": 7, "paro": 6, "energía": 6, "energia": 6,
    "puente": 6, "sánchez": 6, "sanchez": 6, "feijóo": 6, "feijoo": 6,
    "trump": 7, "israel": 7, "gaza": 7, "ucrania": 7, "rusia": 7,
    "china": 6, "eeuu": 6, "onu": 6, "ue": 6, "europa": 5,
    "elecciones": 7, "referéndum": 7, "referendum": 7,
    "reforma": 6, "ley": 5, "decreto": 5, "sentencia": 6,
    "banco central": 6, "bce": 6, "fed": 6, "tipos de interés": 6,
    "pib": 6, "deuda": 6, "déficit": 6, "deficit": 6,
    "inmigración": 6, "inmigracion": 6, "frontera": 6,
    "sanidad": 5, "educación": 5, "educacion": 5, "justicia": 5,
    "guerra": 8, "conflicto": 6, "sanciones": 6, "tratado": 6,
    "ataque": 6, "crisis": 6, "rescate": 6,
}

# Keywords que BAJAN el score
KEYWORDS_RUIDO = {
    "curiosidad": -15, "virales": -15, "viral": -15,
    "tiktok": -20, "instagram": -20,
    "receta": -15, "plato": -15,
    "famoso": -20, "famosa": -20, "celebridad": -20,
    "concierto": -10, "película": -10, "pelicula": -10,
    "actor": -15, "actriz": -15,
}

TEMAS = {
    "politica": ["gobierno", "congreso", "senado", "moncloa", "sánchez", "sanchez",
                 "feijóo", "feijoo", "puente", "psoe", "pp", "vox", "sumar",
                 "elecciones", "reforma", "ley", "decreto"],
    "economia": ["inflación", "inflacion", "pib", "deuda", "déficit", "deficit",
                 "presupuesto", "pensiones", "empleo", "paro", "bce", "fed",
                 "tipos de interés", "vivienda", "energía", "energia"],
    "geopolitica": ["trump", "israel", "gaza", "ucrania", "rusia", "china",
                    "eeuu", "onu", "ue", "europa", "guerra", "conflicto",
                    "sanciones", "tratado", "ataque"],
    "justicia": ["fiscalía", "fiscalia", "tribunal supremo", "constitucional",
                 "sentencia", "juez", "jueza", "fiscal"],
    "sociedad": ["inmigración", "inmigracion", "frontera", "sanidad",
                 "educación", "educacion", "vivienda", "pensiones"],
    "tecnologia": ["ia", "inteligencia artificial", "google", "apple", "microsoft",
                   "openai", "chip", "semiconductor", "ciberseguridad"],
}


def _inferir_tema(titular, extracto=""):
    """Infiere tema con prioridad + límites de palabra. Prioridad: politica > geopolitica > economia > justicia > sociedad > tecnologia."""
    texto = (" " + titular + " " + extracto + " ").lower()
    prioridad = ["politica", "geopolitica", "economia", "justicia", "sociedad", "tecnologia"]
    for tema in prioridad:
        kws = TEMAS.get(tema, [])
        for k in kws:
            # límites de palabra para evitar falsos positivos ("era" en "Puerta del Sol")
            if re.search(r'\b' + re.escape(k) + r'\b', texto):
                return tema
    return "otros"


def _score_noticia(n):
    """Score 0-100: impacto público - ruido + bonus por extracto."""
    t = n.get("titular", "").lower()
    e = (n.get("extracto", "") or "").lower()
    score = 0
    for kw, w in KEYWORDS_IMPACTO.items():
        if kw in t:
            score += w * 2  # más peso en titular
        elif kw in e:
            score += w
    for kw, w in KEYWORDS_RUIDO.items():
        if kw in t:
            score += w * 2
        elif kw in e:
            score += w
    # Bonus por extracto largo (noticia real, no publirreportaje de 100 chars)
    if len(e) > 800:
        score += 10
    elif len(e) > 400:
        score += 5
    # Bonus medio de referencia
    medio = n.get("medio", "").lower()
    if any(m in medio for m in ["el país", "el pais", "el mundo", "abc", "reuters",
                                 "bloomberg", "efe", "europa press", "guardian",
                                 "financial times", "nyt", "le monde", "bbc"]):
        score += 5
    return max(0, min(100, 50 + score))


def _es_basura(n):
    texto = (n.get("titular", "") + " " + (n.get("extracto", "") or "")).lower()
    return any(b in texto for b in BASURA_V2)


_PALABRAS_VACIAS = {"el", "la", "los", "las", "un", "una", "unos", "unas",
                    "de", "del", "al", "a", "en", "con", "por", "para",
                    "y", "o", "que", "se", "su", "sus", "es", "son", "ha",
                    "han", "tras", "sobre", "entre", "sin", "más", "mas"}


def _palabras_significativas(titular):
    """Devuelve set de palabras >3 chars del titular (sin stopwords)."""
    palabras = re.findall(r'\b[a-záéíóúñü]{4,}\b', titular.lower())
    return set(p for p in palabras if p not in _PALABRAS_VACIAS)


ENTIDADES_AGENDA = {
    # Entidades que agrupan noticias del mismo evento/caso
    "puente", "urda", "atocha", "iryo", "adif", "renfe",
    "trump", "israel", "gaza", "ucrania", "rusia", "iran", "irán",
    "sánchez", "sanchez", "feijóo", "feijoo", "abascal", "iglesias",
    "biedma", "leire", "díez", "diez",
    "lula", "sheinbaum", "milei", "bukele",
    "ave", "madrid-sevilla",
    "bce", "fed", "letras", "ibex",
}


def _entidades_dominantes(n):
    """Entidades de agenda presentes en el titular."""
    palabras = set(re.findall(r'\b[a-záéíóúñü]{4,}\b', n.get("titular", "").lower()))
    return palabras & ENTIDADES_AGENDA


def _es_mismo_evento(n1, n2, umbral_jaccard=0.30, min_comunes=2):
    """True si dos noticias son del mismo evento. 3 reglas:
       1) Jaccard >= umbral
       2) >=2 palabras fuertes comunes (no genéricas)
       3) comparten >=1 entidad dominante Y su Jaccard >= 0.15
    """
    p1 = _palabras_significativas(n1.get("titular", ""))
    p2 = _palabras_significativas(n2.get("titular", ""))
    if not p1 or not p2:
        return False
    comunes = p1 & p2
    jaccard = len(comunes) / len(p1 | p2)
    # Regla 1: Jaccard alto
    if jaccard >= umbral_jaccard:
        return True
    # Regla 2: >=2 palabras fuertes
    genericos = {"tras", "sobre", "entre", "desde", "hasta", "puede", "puedo",
                 "asegura", "dice", "afirma", "segun", "según", "todo", "toda",
                 "reconoce", "reconeix", "gravetat", "situacio", "situació"}
    fuertes = comunes - genericos
    if len(fuertes) >= min_comunes:
        return True
    # Regla 3: comparten entidad de agenda
    e1 = _entidades_dominantes(n1)
    e2 = _entidades_dominantes(n2)
    if (e1 & e2) and jaccard >= 0.15:
        return True
    return False


def _limpiar_titular(t):
    """Limpia CDATA, HTML entities y espacios extra."""
    import re as _r, html as _h
    if not t:
        return ""
    t = _r.sub(r'<!\[CDATA\[', '', t)
    t = _r.sub(r'\]\]>', '', t)
    t = _h.unescape(t)
    t = _r.sub(r'\s+', ' ', t).strip()
    return t


def _editor_jefe_v2(pool_noticias, pedir_llm, verbose=True):
    """Selecciona top16 con 4 capas. pedir_llm: función pedir_a_especialista(rol, prompt, contexto=..., proveedor=...)."""
    import json as _json

    # Limpiar titulares al entrar (fix CDATA / HTML entities 2026-11-03)
    for n in pool_noticias:
        if "titular" in n:
            n["titular"] = _limpiar_titular(n["titular"])

    # ─── CAPA 1: pre-filtro ───
    limpio = [n for n in pool_noticias if not _es_basura(n)]
    if verbose:
        print(f"[editor_v2] Pre-filtro: {len(pool_noticias)} -> {len(limpio)} (descartadas {len(pool_noticias)-len(limpio)})", flush=True)

    # ─── CAPA 2: scoring ───
    for n in limpio:
        n["_score"] = _score_noticia(n)
        n["_tema"] = _inferir_tema(n.get("titular",""), n.get("extracto",""))
    limpio.sort(key=lambda x: x["_score"], reverse=True)

    # Top 30 para el LLM (no 52)
    top_pool = limpio[:30]

    # ─── CAPA 3: LLM con rúbrica ───
    ctx_lines = []
    for i, n in enumerate(top_pool, 1):
        exc = (n.get("extracto", "") or "")[:150].replace("\n", " ")
        ctx_lines.append(f"{i}. [{n['medio']}] {n['titular']} | {n['_tema']} | score {n['_score']} | {exc}")
    ctx = "\n".join(ctx_lines)

    prompt = """Eres el EDITOR JEFE de 'El Encuadre', medio de análisis de framing periodístico.
Tu misión: seleccionar las 16 noticias que mejor permitan analizar cómo los medios
construyen la realidad HOY.

CRITERIOS (en orden de peso):
1. IMPACTO PÚBLICO (40%): afecta a >1M personas o instituciones clave
2. DIVERSIDAD DE MEDIO (30%): MÁXIMO 2 noticias por medio
3. DIVERSIDAD TEMÁTICA (20%): al menos 4 temas distintos
4. POTENCIAL DE FRAMING (10%): el titular ya revela sesgo, omisión o carga emocional

DESCARTAR SIEMPRE:
- Publirreportajes, marcas, "presenta", "revoluciona", "líder en"
- Corazón, famosos, bodas, "Ana Obregón"
- Deportes, fichajes, partidos
- Sucesos sin gestión pública
- Gastronomía, virales, curiosidades
- Duplicados del mismo hecho (elige el medio más relevante)

FORMATO JSON ESTRICTO:
{"aprobadas": [{"titular": "...", "medio": "...", "url": "...", "razon": "una frase"}]}"""

    top16 = []
    try:
        resp = pedir_llm("editor_jefe", prompt, contexto=ctx, proveedor="auto")
        # Parsear (reusar _parse_json del módulo si está disponible)
        try:
            d = _parse_json(resp)
        except NameError:
            d = _json.loads(resp) if isinstance(resp, str) else resp
        aprobadas = d.get("aprobadas", []) if isinstance(d, dict) else []
    except Exception as e:
        print(f"[editor_v2] LLM falló: {e}", flush=True)
        aprobadas = []

    # ─── CAPA 4: validación del LLM ───
    por_medio = {}
    por_tema = {}
    titulos_vistos = set()
    for a in aprobadas:
        if len(top16) >= 16:
            break
        tit = a.get("titular", "").strip()
        if not tit or tit in titulos_vistos:
            continue
        # Buscar la noticia original para recuperar _tema y _score
        orig = next((n for n in top_pool if n["titular"] == tit), None)
        if not orig:
            continue
        medio = orig["medio"]
        tema = orig["_tema"]
        if por_medio.get(medio, 0) >= 2:
            continue
        if por_tema.get(tema, 0) >= 4:
            continue
        # Fix A2: descartar duplicados de evento (mismo hecho, distinto medio)
        if any(_es_mismo_evento(orig, prev) for prev in top16):
            continue
        top16.append(orig)
        titulos_vistos.add(tit)
        por_medio[medio] = por_medio.get(medio, 0) + 1
        por_tema[tema] = por_tema.get(tema, 0) + 1

    if verbose:
        print(f"[editor_v2] LLM aprobó {len(top16)}/16 tras validación", flush=True)

    # ─── CAP POR ENTIDAD: máx 2 por entidad dominante fuerte ───
    ENTIDADES_FUERTES = {"puente", "urda", "trump", "israel", "gaza", "sánchez", "sanchez",
                          "feijóo", "feijoo", "abascal", "biedma", "leire", "lula",
                          "sheinbaum", "milei", "bukele", "ucrania", "rusia", "iran", "irán"}

    def _entidades_fuertes(n):
        palabras = set(re.findall(r'\b[a-záéíóúñü]{4,}\b', n.get("titular", "").lower()))
        return palabras & ENTIDADES_FUERTES

    # Contar por entidad en top16
    cont_entidad = {}
    for n in top16:
        for e in _entidades_fuertes(n):
            cont_entidad[e] = cont_entidad.get(e, 0) + 1

    # Filtrar top16 si alguna entidad supera 2
    top16_filtrado = []
    for n in top16:
        ents = _entidades_fuertes(n)
        if any(cont_entidad.get(e, 0) > 2 for e in ents):
            # Este elemento rompe el cap; solo lo quitamos si no somos el primero con esa entidad
            # Mantener máximo 2: dejar pasar solo si ya hay <2 con esa entidad
            if any(sum(1 for x in top16_filtrado if e in _entidades_fuertes(x)) >= 2 for e in ents):
                if verbose:
                    print(f"[editor_v2] Cap entidad: descartada {n['titular'][:60]}", flush=True)
                continue
        top16_filtrado.append(n)

    if len(top16_filtrado) != len(top16):
        if verbose:
            print(f"[editor_v2] Cap entidad: {len(top16)} -> {len(top16_filtrado)}", flush=True)
        top16 = top16_filtrado

    # ─── FALLBACK: rellenar hasta 16 con variedad por scoring ───
    if len(top16) < 16:
        if verbose:
            print(f"[editor_v2] Fallback Python: rellenando {16-len(top16)} por score", flush=True)
        # Pasada 1: estricta (máx 2 medio, máx 4 tema, dedup)
        for n in top_pool:
            if len(top16) >= 16:
                break
            if n["titular"] in titulos_vistos:
                continue
            if por_medio.get(n["medio"], 0) >= 2:
                continue
            if por_tema.get(n["_tema"], 0) >= 4:
                continue
            if any(_es_mismo_evento(n, prev) for prev in top16):
                continue
            top16.append(n)
            titulos_vistos.add(n["titular"])
            por_medio[n["medio"]] = por_medio.get(n["medio"], 0) + 1
            por_tema[n["_tema"]] = por_tema.get(n["_tema"], 0) + 1

        # Pasada 2: relajar si aún faltan (medio hasta 3, tema hasta 6, dedup sí)
        if len(top16) < 16 and verbose:
            print(f"[editor_v2] Fallback pasada 2 (relajada): faltan {16-len(top16)}", flush=True)
        for n in top_pool:
            if len(top16) >= 16:
                break
            if n["titular"] in titulos_vistos:
                continue
            if por_medio.get(n["medio"], 0) >= 3:
                continue
            if por_tema.get(n["_tema"], 0) >= 6:
                continue
            if any(_es_mismo_evento(n, prev) for prev in top16):
                continue
            top16.append(n)
            titulos_vistos.add(n["titular"])
            por_medio[n["medio"]] = por_medio.get(n["medio"], 0) + 1
            por_tema[n["_tema"]] = por_tema.get(n["_tema"], 0) + 1

        # Pasada 3: última red (solo dedup, sin restricciones medio/tema)
        if len(top16) < 16 and verbose:
            print(f"[editor_v2] Fallback pasada 3 (mínima): faltan {16-len(top16)}", flush=True)
        for n in top_pool:
            if len(top16) >= 16:
                break
            if n["titular"] in titulos_vistos:
                continue
            if any(_es_mismo_evento(n, prev) for prev in top16):
                continue
            top16.append(n)
            titulos_vistos.add(n["titular"])
            titulos_vistos.add(n["titular"])
            por_medio[n["medio"]] = por_medio.get(n["medio"], 0) + 1
            por_tema[n["_tema"]] = por_tema.get(n["_tema"], 0) + 1

    # ─── RE-APLICAR CAP ENTIDAD tras fallback (por si rellenó con más de la cuenta) ───
    cont_entidad = {}
    for n in top16:
        for e in _entidades_fuertes(n):
            cont_entidad[e] = cont_entidad.get(e, 0) + 1
    top16_final = []
    for n in top16:
        ents = _entidades_fuertes(n)
        # Si ya hay 2 con esta entidad en top16_final, saltar
        if any(sum(1 for x in top16_final if e in _entidades_fuertes(x)) >= 2 for e in ents):
            continue
        top16_final.append(n)
    if len(top16_final) < len(top16):
        if verbose:
            print(f"[editor_v2] Cap final: {len(top16)} -> {len(top16_final)}", flush=True)
    top16 = top16_final

    # ─── FIX 12: re-rellenar hasta 16 respetando cap (2026-11-03) ───
    if len(top16) < 16:
        if verbose:
            print(f"[editor_v2] Re-relleno post-cap: faltan {16-len(top16)}", flush=True)
        titulos_actuales = {n["titular"] for n in top16}
        for n in top_pool:
            if len(top16) >= 16:
                break
            if n["titular"] in titulos_actuales:
                continue
            ents = _entidades_fuertes(n)
            # Respetar cap de 2 por entidad
            if any(sum(1 for x in top16 if e in _entidades_fuertes(x)) >= 2 for e in ents):
                continue
            # Respetar dedup de evento
            if any(_es_mismo_evento(n, prev) for prev in top16):
                continue
            top16.append(n)
            titulos_actuales.add(n["titular"])

    if verbose:
        print(f"[editor_v2] TOP16 final:", flush=True)
        for i, n in enumerate(top16, 1):
            print(f"  {i:2d}. [{n['_tema']:12s}] [{n['medio'][:18]:18s}] {n['titular'][:70]}", flush=True)

    # Limpiar campos internos
    for n in top16:
        n.pop("_score", None)
        n.pop("_tema", None)
    return top16
