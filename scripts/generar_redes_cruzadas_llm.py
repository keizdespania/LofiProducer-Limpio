#!/usr/bin/env python3
"""Genera redes cruzadas: extractos REALES del artículo + guion + shorts."""
import json, pathlib, sys, re, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "brain"))
from redes_footer import footer as _footer
NL = chr(10)
BASE_URL = "https://elencuadre.pages.dev"

# ═══ Links cruzados a todas las redes del canal ═══
REDES_CANAL = {
    "youtube": "youtube.com/@somoselencuadre.oficial",
    "tiktok": "tiktok.com/@somoselencuadre",
    "instagram": "instagram.com/somoselencuadre",
    "x": "x.com/SomosElEncuadre",
    "threads": "threads.net/@somoselencuadre",
    "telegram": "t.me/somoselencuadre",
    "web": "elencuadre.pages.dev",
}

# Footer adaptado por red destino (para no petar límites)
FOOTER_POR_RED = {
    "x": "\n\n📺 {youtube}\n📄 {web}",
    "threads": "\n\n📺 {youtube}\n📸 {instagram}\n📩 {telegram}\n📄 {web}",
    "instagram": "\n\n📺 {youtube}\n🎵 {tiktok}\n📩 {telegram}\n🔗 Link en bio",
    "tiktok": "\n\n📩 Dossier diario: {telegram}\n📄 Análisis: {web}",
    "youtube_comunidad": "\n\n📱 {tiktok}\n📸 {instagram}\n🐦 {x}\n📩 {telegram}",
    "linkedin": "\n\n📺 {youtube}\n📄 {web}\n📩 {telegram}",
}

def _footer(red):
    """Genera footer con links cruzados a las OTRAS redes."""
    tmpl = FOOTER_POR_RED.get(red, "\n\n📄 {web}")
    return tmpl.format(**REDES_CANAL)

def _groq(prompt, max_tokens=600):
    import requests
    keys = []
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("GROQ_API_KEY"):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            if v.startswith("gsk_"): keys.append(v)
    CHROME = "Mozilla/5.0 Chrome/131.0"
    for key in keys[:2]:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": CHROME},
                json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.75, "max_tokens": max_tokens}, timeout=40)
            if r.status_code == 200:
                txt = r.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if txt: return txt
        except: continue
    return None

def _limpiar_md(path):
    if not path.exists(): return ""
    try:
        txt = path.read_text(encoding="utf-8")
        if txt.startswith("---"): txt = txt.split("---", 2)[2]
        txt = re.sub(r'<[^>]+>', '', txt)
        txt = re.sub(r'\s+', ' ', txt).strip()
        return txt
    except: return ""

def _limpiar_hook(texto):
    """Limpia basura residual del hook."""
    if not texto: return ""
    s = texto.strip()
    for b in ["Lee mas", "Leer mas", "Analisis comple", "Analisis completo"]:
        if s.endswith(b): s = s[:-len(b)].strip()
    for b in ["...", chr(8230)]:
        if s.endswith(b): s = s[:-len(b)].strip()
    if s and s[-1].isalpha() and len(s) > 100:
        up = max(s.rfind('.'), s.rfind('!'), s.rfind('?'))
        if up > 50: s = s[:up+1]
    return s.strip()


def _generar_hook_red(texto_base, tipo):
    """Hook viral 120 chars usando formulas: Rage, Curiosity, Contrarian, Data."""
    if not texto_base: return ""
    # 2026-11-09: prioridad por TIPO (garantiza hooks unicos)
    por_tipo = {
        "dato": "3 diarios, 1 noticia, 0 contexto real.",
        "contradiccion": "No es lo que te cuentan. Es lo que ocultan.",
        "prediccion": "En 6 meses esto estara en todos los medios.",
        "tutorial": "Como detectar esta manipulacion en 3 segundos.",
    }
    ejemplo = por_tipo.get(tipo, "3 diarios, 1 noticia, 0 contexto real.")
    tl = texto_base.lower()
    if False:  # (nunca, ejemplo ya definido por tipo)
        pass
    elif any(w in tl for w in ["cobra", "millones", "euros", "sueldo"]):
        ejemplo = "Cobran del Estado mientras llaman mafia a los sindicatos."
    elif any(w in tl for w in ["oculta", "omite", "silencia", "ignora"]):
        ejemplo = "7 medios ocultan esto sobre Nvidia. Solo uno lo cuenta."
    elif any(w in tl for w in ["miente", "mentira", "falso", "manipula"]):
        ejemplo = "No es un error. Es manipulacion disenada."
    else:
        pass  # ejemplo ya definido por tipo
    
    nl = chr(10)
    prompt = "Texto: " + texto_base[:350] + nl + nl + "Crea un TUIT VIRAL para X (max 120 chars). Frase completa, sin cortar. Estilo: " + ejemplo + nl + nl + "Tuit:"
    txt = _groq(prompt, 200)
    if txt and 20 < len(txt.strip()) < 200:
        clean = txt.strip().strip('"').strip("'").splitlines()[0]
        if not any(r in clean.lower() for r in ["sorry", "lo siento", "cannot", "no puedo"]):
            return clean[:280]
    return ejemplo


def _load(fecha):
    d = {"prod": {}, "seo": {}, "yt": {},
         "md_largo": "", "md_dossier": "", "md_mediano": "", "guion_largo": ""}
    for k, f in [("prod", f"produccion_{fecha}.json"), ("seo", f"seo_{fecha}.json")]:
        p = OUT / f
        if p.exists():
            try: d[k] = json.loads(p.read_text())
            except: pass
    p_yt = ROOT / "data" / "agent" / f"youtube_urls_{fecha}.json"
    if p_yt.exists():
        try: d["yt"] = json.loads(p_yt.read_text())
        except: pass
    # Artículos .md
    for key, fname in [
        ("md_largo", f"{fecha}-largo.md"),
        ("md_dossier", f"{fecha}-dossier-v2.md"),
        ("md_mediano", f"{fecha}-mediano-quirurgico.md"),
    ]:
        d[key] = _limpiar_md(ROOT / "web" / "docs" / "analisis" / fname)
    # Guion del vídeo largo (texto_voz_largo de produccion)
    d["guion_largo"] = d["prod"].get("texto_voz_largo", "")[:5000]
    return d

def _frases_candidatas(md, min_len=80, max_len=280):
    """Extrae frases candidatas del CUERPO del artículo (excluye lead)."""
    import re as _re
    cuerpo = md[500:-500] if len(md) > 1500 else md[200:]
    frases = _re.split(r'(?<=[.!?])\s+', cuerpo)
    buenas = []
    palabras = ["manipulación", "técnica", "medios", "prensa", "sesgo", "narrativa",
                "mentira", "temor", "miedo", "control", "poder", "oculta", "silencia",
                "manipula", "vende", "engaña", "distorsiona", "deshumaniza", "encuadre",
                "estrategia", "editorial", "miente", "convierte", "transforma", "circo", "carnicería"]
    for f in frases:
        f = f.strip()
        if len(f) < min_len or len(f) > max_len: continue
        if "Leer completo" in f or "http" in f.lower(): continue
        score = sum(1 for p in palabras if p in f.lower())
        if score >= 2:
            buenas.append((score, f))
    buenas.sort(reverse=True)
    return [f for _, f in buenas[:10]]

def _extraer_frase(md, instruccion, max_tokens=300):
    """Extrae 1 frase con pre-filtro local + LLM sobre candidatas."""
    candidatas = _frases_candidatas(md)
    if not candidatas:
        return md[500:750].strip() if len(md) > 750 else md[:250]
    contexto = "\n".join(candidatas[:5])[:900]
    prompt = f"""Frases candidatas del artículo:
{contexto}

{instruccion}

Devuelve SOLO el texto de la frase elegida (sin comillas, sin introducción):"""
    txt = _groq(prompt, max_tokens)
    if txt and len(txt.strip()) > 30 and not any(r in txt.lower() for r in ["sorry", "lo siento", "cannot", "no puedo", "no dispongo"]):
        low = txt.lower().strip()
        # Detectar rechazos del LLM
        rechazos = ["i'm sorry", "i am sorry", "no puedo ayudar", "cannot help",
                    "no dispongo", "lo siento", "i can't help", "unable to"]
        if not any(r in low for r in rechazos):
            return txt.strip()
    return candidatas[0]

def _extraer_todos(d, titular):
    """Extrae fragmentos: LLM con pre-filtro para X/Threads/IG/LinkedIn + hook directo para shorts."""
    md_largo = d["md_largo"]
    out = {}

    # ═══ Artículo (largo) ═══
    print("     → fragmento para X...")
    out["HOOK_X"] = _extraer_frase(md_largo,
        "Elige 1 frase del artículo que sea un TUIT PERIODÍSTICO con tono CRÍTICO e IRÓNICO (OBLIGATORIO 150-280 caracteres). Nombra el medio o político (El Español, Ayuso, Sánchez). Usa ironía fina, no insultos. Sin 'me deja', 'siento', 'creo'. Ej: 'El Español llama mafia a los sindicatos mientras su CEO cobra del Estado. Circo periodístico.'",
        max_tokens=400)

    print("     → fragmento para Threads...")
    out["ANALISIS_THREADS"] = _extraer_frase(md_largo,
        "Elige 1 párrafo que ANALICE CRÍTICAMENTE al medio con DATOS. Expón qué ocultó, cuánto cobra, qué ignoró. Tono de auditor. Empieza fuerte: 'OkDiario omite:', 'La Vanguardia no cuenta:'. Termina con reflexión: 'Eso no es periodismo, es publicidad.'",
        max_tokens=500)

    print("     → fragmento para Instagram...")
    out["CIERRE_IG"] = _extraer_frase(md_largo,
        "Elige 1 frase como CIERRE para Instagram: pregunta reflexiva al lector O afirmación que genere debate. Ej: 'Si criticas la manipulación pero sigues consumiendo ese medio, eres parte del problema.' Tono honesto, sin complacencia.",
        max_tokens=300)

    print("     → fragmento para LinkedIn...")
    out["LINKEDIN_LARGO"] = _extraer_frase(md_largo,
        "Elige 1 párrafo para LinkedIn (profesional pero CRÍTICO). Habla de la técnica con nombre técnico + análisis. Tono auditor objetivo, no académico. Ej: 'El framing de agenda que El País aplicó hoy no es sesgo: es publicidad pagada.'",
        max_tokens=500)

    # ═══ Shorts: hook directo del JSON (ya escrito por guionista mordaz) ═══
    shorts_data = d["prod"].get("shorts_finales", [])
    for i, s in enumerate(shorts_data[:4]):
        tipo = s.get("tipo", "")
        hook = (s.get("hook") or "").strip()
        guion = (s.get("guion") or "").strip()

        # Prioridad: hook > primera frase guion > artículo filtrado
        # 2026-11-09: forzar regeneracion con formulas virales
        base = guion or hook or titular
        # 2026-11-09: si el LLM devuelve hook repetido, forzar fallback unico por tipo
        _generado = _generar_hook_red(base, tipo)
        _usados = [out.get(f"SHORT{j}_TIKTOK", "") for j in range(1, i+1)]
        if _generado in _usados:
            _generado = {"dato": "3 diarios, 1 noticia, 0 contexto real.", "contradiccion": "No es lo que te cuentan. Es lo que ocultan.", "prediccion": "En 6 meses esto estara en todos los medios.", "tutorial": "Como detectar esta manipulacion en 3 segundos."}.get(tipo, _generado)
        out[f"SHORT{i+1}_TIKTOK"] = _generado

    return out
def _post_hook(md_texto, slug):
    if not md_texto: return ""
    texto = md_texto
    prefixes = ["El Encuadre:", "Dossier del dia:", "Dossier del d", "El angulo que nadie cuenta:", "El ángulo que nadie cuenta:"]
    for p in prefixes:
        if texto.startswith(p):
            idx = texto.find(".", 30)
            if 0 < idx < 400: texto = texto[idx+1:].strip()
            break
    if len(texto) > 400 and texto.startswith(md_texto[:20]):
        texto = texto[350:]
    texto = texto.replace("!", ".").replace("?", ".")
    sents = texto.split(". ")
    body = []
    for s in sents:
        s = s.strip()
        if len(s) > 60 and not s.startswith("Fuentes") and not s.startswith("Leer"):
            body.append(s + ".")
            if len(" ".join(body)) > 200: break
    if not body: return texto[:250]
    hook = " ".join(body)[:280]
    cliffs = {"largo": "Pero lo que ocultan es peor. 👇", "dossier": "Y lo que los medios no te cuentan es esto. 👇", "mediano": "Y esto es lo que nadie conecta. 👇"}
    return hook + chr(10) + chr(10) + cliffs.get(slug, "👇")

def _build(fecha):
    d = _load(fecha)
    prod, seo, yt = d["prod"], d["seo"], d["yt"]
    dossier = prod.get("dossier", {})
    titular = dossier.get("titular_brutal", "Analisis del dia")[:150]

    yt_largo = "https://youtu.be/" + yt['largo']['video_id'] if (yt.get("largo") or {}).get("video_id") else ""
    yt_shorts = ["https://youtu.be/" + s['video_id'] for s in (yt.get("shorts") or []) if s.get("video_id")]
    post_largo = BASE_URL + "/analisis/" + fecha + "-largo/"
    post_dossier = BASE_URL + "/analisis/" + fecha + "-dossier-v2/"
    post_mediano = BASE_URL + "/analisis/" + fecha + "-mediano-quirurgico/"

    print("  -> LLM extrayendo fragmentos...")
    frags = _extraer_todos(d, titular)

    # ═══ LARGO ═══
    titulo_largo = seo.get("largo", {}).get("titulo", titular)
    header = "VIDEO: " + titulo_largo[:100] + NL + NL
    link_yt = (NL + NL + "Miralo: " + yt_largo) if yt_largo else ""
    link_web = NL + "Web: " + post_largo

    largo = {
        "num": 0, "tipo": "largo", "titulo": titulo_largo,
        "video_id": (yt.get("largo") or {}).get("video_id"),
        "link_yt": yt_largo, "link_post": post_largo, "link_dossier": post_dossier,
        "redes": {
            "x": {"texto": header + frags["HOOK_X"] + link_yt + link_web + _footer("x")},
            "threads": {"texto": header + frags["ANALISIS_THREADS"] + link_yt + link_web + _footer("threads")},
            "instagram": {"texto": header + frags["CIERRE_IG"] + link_web + _footer("instagram")},
            "youtube_comunidad": {"texto": frags["HOOK_X"]},
        }
    }

    # ═══ SHORTS ═══
    prod_shorts = prod.get("shorts_finales", [])
    seo_shorts = seo.get("shorts", [])
    shorts = []
    for i, s in enumerate(prod_shorts[:4]):
        tipo = s.get("tipo", "")
        seo_s = seo_shorts[i] if i < len(seo_shorts) else {}
        yt_s = yt_shorts[i] if i < len(yt_shorts) else ""
        frag = frags.get("SHORT" + str(i+1) + "_TIKTOK", "") or s.get("hook", "")[:150]
        titulo_s = seo_s.get("titulo", "Short " + str(i+1))[:100]
        link_s = (NL + NL + "Miralo: " + yt_s) if yt_s else ""

        shorts.append({
            "num": i+1, "tipo": tipo, "hook": frag,
            "link_yt": yt_s, "link_largo": yt_largo, "link_post": post_largo,
            "redes": {
                "tiktok": {"texto": frag + _footer("tiktok"), "hashtags": "#ElEncuadre #" + tipo},
                "youtube": {"titulo": titulo_s, "descripcion": seo_s.get("descripcion", "")[:400] + _footer("youtube_comunidad"), "tags": seo_s.get("tags", [])[:10]},
                "x": {"texto": frag + link_s + _footer("x")},
                "threads": {"texto": frag + link_s + _footer("threads")},
                "instagram": {"texto": frag + _footer("instagram")},
            }
        })

    # === POSTS ===
    linkedin_shared = frags.get("LINKEDIN_LARGO", "") or titular
    posts = []
    for slug, tipo_post, url, md_texto in [
        ("largo", "Analisis Largo", post_largo, d["md_largo"]),
        ("dossier", "Dossier Ejecutivo", post_dossier, d["md_dossier"] or d["md_largo"]),
        ("mediano", "Analisis Mediano", post_mediano, d["md_mediano"] or d["md_largo"]),
    ]:
        post_body = _post_hook(md_texto, slug)
        yt_post = (NL + NL + "Video: " + yt_largo) if yt_largo else ""
        url_line = NL + NL + "Lee: " + url
        titulo_post = (seo.get("largo", {}).get("titulo") if slug == "largo" else md_texto[:80]) or titular
        if slug == "largo":
            li_text = linkedin_shared
        else:
            li_text = post_body[:400]
        posts.append({
            "slug": slug, "tipo": tipo_post, "titulo": titulo_post,
            "url": url, "link_short": yt_shorts[0] if yt_shorts else "", "link_yt_largo": yt_largo,
            "redes": {
                "x": {"texto": post_body + url_line + yt_post},
                "threads": {"texto": post_body + url_line + yt_post},
                "linkedin": {"texto": li_text + url_line + yt_post},
                "instagram": {"texto": post_body[:200] + NL + NL + "Link en bio"},
            }
        })
    
    return {"fecha": fecha, "largo": largo, "shorts": shorts, "posts": posts, "links_globales": {"yt_largo": yt_largo, "yt_shorts": yt_shorts, "web": BASE_URL}}

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    print(f"Redes cruzadas v3 (artículo+guion) {fecha}...")
    r = _build(fecha)
    out = OUT / f"redes_{fecha}_cruzadas.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=2))
    print(f"OK {out.name}")
    print("\n=== largo X ==="); print(r["largo"]["redes"]["x"]["texto"][:300])
    print("\n=== short1 TikTok ==="); print(r["shorts"][0]["redes"]["tiktok"]["texto"][:300])
    print("\n=== post LinkedIn ==="); print(r["posts"][0]["redes"]["linkedin"]["texto"][:300])
