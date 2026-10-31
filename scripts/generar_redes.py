"""generar_redes.py v3 - Copys SEO por red. 1 llamada por (short, red)."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WEB = "https://elencuadre.pages.dev"

# URLs de las redes (rellenar con las reales cuando estén creadas)
REDES_URLS = {
    "youtube": "https://youtube.com/@SomosElEncuadre",
    "tiktok": "https://tiktok.com/@somoselencuadre",
    "instagram": "https://instagram.com/somoselencuadre",
    "x": "https://x.com/SomosElEncuadre",
    "threads": "https://threads.net/@somoselencuadre",
    "blogger": "https://iaglobalnews.blogspot.com",
    "web": "https://elencuadre.pages.dev",
}

def _otros_enlaces(red_actual):
    """Devuelve string con enlaces a las OTRAS redes (excluye la actual)."""
    lineas = []
    for red, url in REDES_URLS.items():
        if red != red_actual and red != "web":
            lineas.append(f"{red.capitalize()}: {url}")
    return " | ".join(lineas)


def _parse_json(texto):
    if not texto: return None
    t = re.sub(r"```(?:json)?", "", texto, flags=re.IGNORECASE).replace("```", "").strip()
    try: return json.loads(t)
    except: pass
    depth = 0; start = -1
    for i, c in enumerate(t):
        if c == "{":
            if depth == 0: start = i
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try: return json.loads(t[start:i+1])
                except: pass
    return None

PROMPTS = {
    "youtube": 'Genera SOLO un objeto JSON con los campos SEO para YouTube de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\nCONTEXTO: {contexto}\n\nREGLAS LEGALES OBLIGATORIAS:\n- NUNCA acuses directamente a personas o medios. Usa: "los hechos", "el caso", "el análisis sugiere".\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra, nazi, fascista.\n- Reformula con: "el suceso", "la situación", "el caso", "los hechos", "la polémica".\n\nSEO CRUZADO (obligatorio al final de la descripción):\nIncluye esta línea al final:\n"Síguenos en: TikTok https://tiktok.com/@somoselencuadre | IG https://instagram.com/somoselencuadre | X https://x.com/SomosElEncuadre | Threads https://threads.net/@somoselencuadre"\n\nEstructura EXACTA:\n{{\n  "titulo": "Máx 60 chars, keyword al inicio, gancho SIN palabras prohibidas",\n  "descripcion": "300-500 chars. Keyword al inicio + CTA + al final la línea SEO CRUZADO con enlaces a OTRAS redes",\n  "primer_comentario": "Comentario CTA con enlace a {web} + 2 enlaces cruzados",\n  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n}}\n\nREGLAS: NO markdown. NO ```json. Respeta 60 chars en titulo.',
    "tiktok": 'Genera SOLO un objeto JSON para TikTok de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente.\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra, nazi, fascista.\n\nSEO CRUZADO: Menciona brevemente OTRAS plataformas al final del texto (NO TikTok, obviamente):\n"Análisis completo en YouTube @SomosElEncuadre y web elencuadre.pages.dev"\n\nEstructura EXACTA:\n{{\n  "texto": "Máx 150 chars. Gancho en primera línea + mención a YouTube o web al final. Sin enlaces directos (TikTok penaliza links externos en texto).",\n  "hashtags": "#fyp #parati #medios #psicologia #manipulacion"\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "instagram": 'Genera SOLO un objeto JSON para Instagram Reel de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente.\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra.\n\nSEO CRUZADO:\n- En el texto: "Análisis completo en YouTube @SomosElEncuadre"\n- En primer_comentario: enlaces a TODAS las otras redes:\n"YouTube: https://youtube.com/@SomosElEncuadre | TikTok: https://tiktok.com/@somoselencuadre | X: https://x.com/SomosElEncuadre | Threads: https://threads.net/@somoselencuadre | Web: https://elencuadre.pages.dev"\n\nEstructura EXACTA:\n{{\n  "texto": "200-400 chars. Tono emocional, emojis (2-3). Mención a YouTube al final. Sin enlaces en caption.",\n  "hashtags": "#medios #sesgo #manipulacion #periodismo #analisis",\n  "primer_comentario": "Enlaces cruzados a TODAS las otras redes + web"\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "x": 'Genera SOLO un objeto JSON para X (Twitter) de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente.\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, guerra.\n\nSEO CRUZADO (obligatorio):\n- Incluye enlaces a web + 2 otras redes al final:\n"Análisis completo: https://elencuadre.pages.dev | YouTube: https://youtube.com/@SomosElEncuadre | TikTok: https://tiktok.com/@somoselencuadre"\n\nEstructura EXACTA:\n{{\n  "texto": "Máx 280 chars. Gancho + enlace web + 2 enlaces cruzados. Los enlaces cuentan ~23 chars cada uno."\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "threads": 'Genera SOLO un objeto JSON para Threads de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente.\n- Sin palabras prohibidas (muerte, sangre, tragedia, saqueo, víctima, crimen, corrupción, guerra).\n\nSEO CRUZADO:\n- En el texto: mención a YouTube\n- Al final del texto: "Análisis completo: https://elencuadre.pages.dev | YouTube: https://youtube.com/@SomosElEncuadre"\n\nEstructura EXACTA:\n{{\n  "texto": "200-400 chars. Tono conversacional. Mención a YouTube + web al final."\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "blogger": 'Genera SOLO un objeto JSON para Blogger de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\nCONTEXTO: {contexto}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente.\n- Sin palabras prohibidas (muerte, sangre, tragedia, saqueo, víctima, crimen, corrupción, guerra).\n\nSEO CRUZADO (obligatorio): el resumen debe terminar con mención a TODAS las redes:\n"También puedes seguirnos en YouTube, TikTok, Instagram, X y Threads como @SomosElEncuadre"\n\nEstructura EXACTA:\n{{\n  "titulo": "Título atractivo, 40-70 chars, con keyword",\n  "resumen": "Resumen 2-3 frases con gancho + mención a redes al final"\n}}\n\nREGLAS: NO markdown. NO ```json.',
}

def _fallback_red(hook, red):
    if red == "youtube":
        return {"titulo": hook[:60], "descripcion": f"{hook}\n\nAnálisis completo: {WEB}", "primer_comentario": f"Lee el análisis: {WEB}", "tags": ["análisis mediático", "framing", "El Encuadre"]}
    if red == "tiktok":
        return {"texto": hook[:150], "hashtags": "#fyp #parati #medios #sesgo"}
    if red == "instagram":
        return {"texto": hook[:300], "hashtags": "#medios #sesgo #manipulación", "primer_comentario": f"Análisis: {WEB}"}
    if red == "x":
        return {"texto": f"{hook[:200]}... {WEB}"}
    if red == "threads":
        return {"texto": f"{hook[:300]}... {WEB}"}
    if red == "blogger":
        return {"titulo": hook[:60], "resumen": hook[:200]}
    return {}

# --- Censura in-place (última red de seguridad) ---
import re as _re_cens

SUSTITUCIONES = {
    "muertos": "afectados", "muerto": "afectado", "muerta": "afectada", "muertas": "afectadas",
    "muerte": "suceso", "muertes": "sucesos",
    "sangre": "violencia", "sangriento": "violento", "sangrienta": "violenta",
    "tragedia": "suceso", "trágico": "grave", "trágica": "grave",
    "saqueo": "disturbio", "saqueos": "disturbios", "saquear": "alterar el orden",
    "víctima": "afectado", "víctimas": "afectados", "victima": "afectado",
    "asesinato": "caso grave", "asesino": "autor", "asesinos": "autores",
    "fallecido": "afectado", "fallecida": "afectada", "fallecidos": "afectados", "fallecidas": "afectadas",
    "crimen": "caso", "criminal": "presunto", "criminales": "presuntos",
    "corrupción": "irregularidad", "corrupto": "cuestionado", "corruptos": "cuestionados",
    "fraude": "irregularidad", "estafa": "irregularidad", "estafador": "presunto",
    "guerra": "conflicto", "guerras": "conflictos", "guerrilla": "grupo armado",
    "nazi": "extremista", "nazis": "extremistas", "fascista": "extremista", "fascistas": "extremistas",
    "golpe": "cambio", "dictador": "líder autoritario", "dictadura": "régimen",
    "genocidio": "crimen contra la humanidad", "masacre": "suceso violento",
    "matar": "acabar con", "matanza": "suceso violento",
    "terrorista": "extremista", "terroristas": "extremistas",
    "violación": "agresión", "violador": "presunto agresor",
}

def _censurar_texto(texto):
    if not texto or not isinstance(texto, str): return texto
    t = texto
    for prohibida, neutra in SUSTITUCIONES.items():
        t = _re_cens.sub(r'\b' + _re_cens.escape(prohibida) + r'\b', neutra, t, flags=_re_cens.IGNORECASE)
    return t

def _censurar_bloque(bloque):
    if isinstance(bloque, str): return _censurar_texto(bloque)
    if isinstance(bloque, dict): return {k: _censurar_bloque(v) for k, v in bloque.items()}
    if isinstance(bloque, list): return [_censurar_bloque(x) for x in bloque]
    return bloque

# --- Fin censura ---

# Campos esperados por red (para validar que el LLM no devuelve vacíos)
CAMPOS_ESPERADOS = {
    "youtube": ["titulo", "descripcion", "primer_comentario", "tags"],
    "tiktok": ["texto", "hashtags"],
    "instagram": ["texto", "hashtags", "primer_comentario"],
    "x": ["texto"],
    "threads": ["texto"],
    "blogger": ["titulo", "resumen"],
}

def _validar_bloque(bloque, red):
    """Devuelve True si el bloque tiene todos los campos esperados y no están vacíos."""
    if not isinstance(bloque, dict): return False
    esperados = CAMPOS_ESPERADOS.get(red, [])
    for campo in esperados:
        if campo not in bloque: return False
        v = bloque[campo]
        if isinstance(v, str) and not v.strip(): return False
        if isinstance(v, list) and not v: return False
    return True

def _llamar_red(red, hook, tipo, contexto):
    prompt_tpl = PROMPTS.get(red)
    if not prompt_tpl: return _censurar_bloque(_fallback_red(hook, red))
    prompt = prompt_tpl.format(hook=hook, tipo=tipo, contexto=contexto, web=WEB)
    try:
        r = pedir_a_especialista("community_manager_seo", prompt, contexto="")
    except Exception as e:
        print(f"    ⚠️ {red} exception: {e}")
        return _censurar_bloque(_fallback_red(hook, red))
    parsed = _parse_json(r) if r else None
    if parsed and _validar_bloque(parsed, red):
        return _censurar_bloque(parsed)
    if parsed and isinstance(parsed, dict):
        print(f"    ⚠️ {red} bloque incompleto (faltan campos), usando fallback")
    else:
        print(f"    ⚠️ {red} parse falló")
    return _censurar_bloque(_fallback_red(hook, red))

def generar_redes(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    dossier_file = OUT / f"dossier_{fecha}.json"
    if not prod_file.exists():
        print("❌ No hay producción"); return False
    if not dossier_file.exists():
        print("❌ No hay dossier"); return False

    datos = json.loads(prod_file.read_text())
    dossier_completo = json.loads(dossier_file.read_text())

    # El dossier resumido dentro de produccion (para contexto de noticias)
    dossier = datos.get("dossier", {})

    # Los hooks viven en dossier_{fecha}.json, no en produccion
    hooks_list = dossier_completo.get("guiones", {}).get("hooks_totales", [])
    if not hooks_list:
        print("❌ No hay hooks en dossier"); return False

    top3 = dossier.get("top3", {})
    noticias = " | ".join([str(v)[:80] for v in list(top3.values())[:3]]) if isinstance(top3, dict) else str(top3)[:250]
    contexto = f"Noticias del día: {noticias}"

    REDES_LIST = ["youtube", "tiktok", "instagram", "x", "threads", "blogger"]
    shorts_finales = []
    ok_count = 0
    total_calls = 4 * len(REDES_LIST)

    print(f"[redes] Generando {total_calls} bloques SEO ({len(REDES_LIST)} redes × 4 shorts)...")
    print(f"        Web: {WEB}")
    print()

    for i, hook_obj in enumerate(hooks_list[:4]):
        num = i + 1
        hook = hook_obj.get("hook", "Análisis del día")
        tipo = hook_obj.get("tipo", "dato")
        print(f"[SHORT {num}/4] {tipo}: {hook[:60]}")

        short_obj = {"id": f"short_{num}"}
        for red in REDES_LIST:
            print(f"  → {red}...", end=" ", flush=True)
            bloque = _llamar_red(red, hook, tipo, contexto)
            short_obj[red] = bloque
            fallback = _fallback_red(hook, red)
            if bloque and bloque != fallback:
                ok_count += 1
                print("✅")
            else:
                print("⚠️ fallback")
            time.sleep(0.3)

        shorts_finales.append(short_obj)
        print()

    data = {"fecha": fecha, "shorts": shorts_finales}
    out = OUT / f"redes_{fecha}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"✅ Guardado: {out}")
    print(f"   {ok_count}/{total_calls} bloques con LLM, {total_calls-ok_count} con fallback")
    return True

if __name__ == "__main__":
    sys.exit(0 if generar_redes(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
