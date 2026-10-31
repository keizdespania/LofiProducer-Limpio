"""generar_redes.py v3 - Copys SEO por red. 1 llamada por (short, red)."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WEB = "https://elencuadre.pages.dev"

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
    "youtube": 'Genera SOLO un objeto JSON con los campos SEO para YouTube de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\nCONTEXTO: {contexto}\n\nREGLAS LEGALES OBLIGATORIAS:\n- NUNCA acuses directamente a personas o medios (ej. "X es corrupto", "Y miente"). Usa: "los hechos", "el caso", "el análisis sugiere", "según el medio".\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra, genocidio, dictador, nazi, fascista.\n- Reformula con: "el suceso", "la situación", "el caso", "los hechos", "la polémica".\n- Si no puedes evitar la palabra, cambia el enfoque al MECANISMO (cómo se cuenta), no al hecho.\n\nEstructura EXACTA:\n{{\n  "titulo": "Máx 60 chars, keyword al inicio, gancho SIN palabras prohibidas",\n  "descripcion": "300-500 chars. Keyword al inicio. CTA a {web} al final. Sin acusaciones.",\n  "primer_comentario": "Comentario CTA con enlace a {web}",\n  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]\n}}\n\nREGLAS: NO markdown. NO ```json. Respeta 60 chars en titulo.',
    "tiktok": 'Genera SOLO un objeto JSON para TikTok de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente. Usa "el caso", "los hechos", "el análisis sugiere".\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra, nazi, fascista.\n- Reformula con: "el suceso", "la situación", "la polémica".\n\nEstructura EXACTA:\n{{\n  "texto": "Máx 150 chars. Gancho en primera línea. Emojis (1-2). Sin enlaces. Sin palabras prohibidas.",\n  "hashtags": "#fyp #parati #medios #psicologia #manipulacion"\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "instagram": 'Genera SOLO un objeto JSON para Instagram Reel de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente. Usa "el caso", "los hechos", "el análisis sugiere".\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra.\n- Reformula con: "el suceso", "la situación", "la polémica".\n\nEstructura EXACTA:\n{{\n  "texto": "200-400 chars. Tono emocional, emojis (2-3). Sin enlaces en caption. Sin palabras prohibidas.",\n  "hashtags": "#medios #sesgo #manipulacion #periodismo #analisis",\n  "primer_comentario": "Enlace a {web}"\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "x": 'Genera SOLO un objeto JSON para X (Twitter) de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente. Usa "el caso", "los hechos", "el análisis sugiere".\n- NUNCA uses: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, guerra.\n- Reformula con: "el suceso", "la situación", "la polémica".\n\nEstructura EXACTA:\n{{\n  "texto": "Máx 280 chars. Gancho + enlace a {web}. Tono mordaz pero SIN palabras prohibidas."\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "threads": 'Genera SOLO un objeto JSON para Threads de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente. Sin palabras prohibidas (muerte, sangre, tragedia, saqueo, víctima, crimen, corrupción, guerra).\n\nEstructura EXACTA:\n{{\n  "texto": "200-400 chars. Tono conversacional. Enlace a {web} al final. Sin palabras prohibidas."\n}}\n\nREGLAS: NO markdown. NO ```json.',
    "blogger": 'Genera SOLO un objeto JSON para Blogger de un short de análisis mediático.\n\nHOOK: "{hook}"\nÁNGULO: {tipo}\nCONTEXTO: {contexto}\n\nREGLAS LEGALES:\n- NUNCA acuses directamente. Sin palabras prohibidas (muerte, sangre, tragedia, saqueo, víctima, crimen, corrupción, guerra).\n\nEstructura EXACTA:\n{{\n  "titulo": "Título atractivo, 40-70 chars, con keyword, sin palabras prohibidas",\n  "resumen": "Resumen 2 frases con gancho, sin acusaciones"\n}}\n\nREGLAS: NO markdown. NO ```json.',
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
    "muertos": "afectados", "muerto": "fallecido", "muerta": "fallecida",
    "muerte": "suceso", "muertes": "sucesos",
    "sangre": "violencia", "sangriento": "violento", "sangrienta": "violenta",
    "tragedia": "suceso", "trágico": "grave", "trágica": "grave",
    "saqueo": "disturbio", "saqueos": "disturbios", "saquear": "alterar el orden",
    "víctima": "afectado", "víctimas": "afectados", "victima": "afectado",
    "asesinato": "caso grave", "asesino": "autor", "asesinos": "autores",
    "fallecido": "afectado", "fallecida": "afectada", "fallecidos": "afectados",
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

def _llamar_red(red, hook, tipo, contexto):
    prompt_tpl = PROMPTS.get(red)
    if not prompt_tpl: return {}
    prompt = prompt_tpl.format(hook=hook, tipo=tipo, contexto=contexto, web=WEB)
    try:
        r = pedir_a_especialista("community_manager_seo", prompt, contexto="")
    except Exception as e:
        print(f"    ⚠️ {red} exception: {e}")
        return _censurar_bloque(_fallback_red(hook, red))
    parsed = _parse_json(r) if r else None
    if parsed and isinstance(parsed, dict):
        # Censura in-place: SIEMPRE antes de devolver
        return _censurar_bloque(parsed)
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
