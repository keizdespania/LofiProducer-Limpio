"""generar_web_v3.py - Anti-medio: 1 post largo + 1 mediano/día con técnicas reales."""
import sys, json, pathlib, datetime, re, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_web"
COLA.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))
from especialistas import pedir_a_especialista
from auto_corregir_post import corregir

FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
WEB = "https://elencuadre.pages.dev"
IMG_MAP = ROOT / "output" / "cola_blogger" / "imagenes_urls.json"

ROTACION = {
    0: "quirurgico",
    1: "tutorial",
    2: "radar",
    3: "cita",
    4: "medio_analizado",
    5: "dossier",
    6: "medio_crudo",
}

def _imagen():
    if IMG_MAP.exists():
        try:
            m = json.loads(IMG_MAP.read_text())
            return next(iter(m.values()), "")
        except: pass
    return ""

def _bloque_redes():
    return """<hr>
<div style="background:#0a0a0f;border-left:4px solid #e63946;padding:1em;border-radius:6px;margin:2em 0;">
<strong>Síguenos:</strong> <a href="https://youtube.com/@somoselencuadre.oficial">YouTube</a> · <a href="https://tiktok.com/@somoselencuadre">TikTok</a> · <a href="https://instagram.com/somoselencuadre">Instagram</a> · <a href="https://x.com/SomosElEncuadre">X</a> · <a href="https://threads.net/@somoselencuadre">Threads</a>
</div>"""

def _validar(html, min_chars=800, min_h2=2):
    if not html or len(html) < min_chars: return False
    if html.count("<h2") < min_h2: return False
    prohibido = ["None", "no puedo", "necesito que me", "dame el texto", "sin el texto", "N/A"]
    if any(p in html[:500] for p in prohibido): return False
    return True

def _md_a_html(md):
    import markdown
    return markdown.markdown(md, extensions=["extra", "sane_lists", "smarty"])

def _ctx(fecha):
    prod = json.loads((OUT / f"produccion_{fecha}.json").read_text())
    # Usar enriquecido si existe (fallback al original)
    enr = OUT / f"dossier_{fecha}_enriquecido.json"
    dossier_path = enr if enr.exists() else (OUT / f"dossier_{fecha}.json")
    dossier = json.loads(dossier_path.read_text())
    analisis_path = OUT / f"analisis_fase1_{fecha}.json"
    analisis = json.loads(analisis_path.read_text()) if analisis_path.exists() else {}
    scrapeado_path = OUT / f"scrapeado_{fecha}.json"
    scrapeado = json.loads(scrapeado_path.read_text()) if scrapeado_path.exists() else {}
    return {
        "articulo": prod.get("articulo_html", ""),
        "texto_voz": prod.get("texto_voz_largo", ""),
        "dossier": dossier.get("dossier", {}),
        "top3": dossier.get("top3", {}),
        "hooks": dossier.get("guiones", {}).get("hooks_totales", []),
        "citas": dossier.get("citas", []),
        "enriquecido": enr.exists(),
        "scrapeado": scrapeado,
    }

def _tecnicas_del_dia(ctx):
    """Lista única de técnicas del desglose enriquecido."""
    desglose = ctx["dossier"].get("desglose_medios", "")
    tecnicas = []
    for line in desglose.split("\n"):
        if "Técnica:" in line:
            t = line.split("Técnica:")[1].split("|")[0].strip().strip("*").strip()
            if t and t not in tecnicas:
                tecnicas.append(t)
    return tecnicas

def _medios_con_tecnica(ctx):
    """Lista de {medio, titular, framing, tecnica, omite, url, texto}."""
    desglose = ctx["dossier"].get("desglose_medios", "")
    scrapeado = ctx.get("scrapeado", {})
    medios = []
    for line in desglose.split("\n"):
        m = re.match(r"\*\*([^*]+)\*\*: '([^']*)' -> \*\*Framing:\*\* ([^|]+) \| \*\*Técnica:\*\* ([^|]+) \| \*\*Omite:\*\* (.+)", line)
        if m:
            nombre = m.group(1).strip()
            datos_scr = scrapeado.get(nombre, {})
            medios.append({
                "medio": nombre,
                "titular": m.group(2).strip(),
                "framing": m.group(3).strip(),
                "tecnica": m.group(4).strip(),
                "omite": m.group(5).strip(),
                "url": datos_scr.get("url", ""),
                "texto": datos_scr.get("texto_completo", ""),
                "chars": datos_scr.get("chars", 0),
            })
    return medios

def _llamar(prompt, max_retries=2):
    for i in range(max_retries):
        try:
            r = pedir_a_especialista("redactor_blog", prompt, contexto="")
            html = re.sub(r'```(?:html|markdown)?', '', r or '', flags=re.IGNORECASE).replace('```', '').strip()
            if html: return html
        except Exception as e:
            print(f"  LLM error: {e}", flush=True)
        time.sleep(1)
    return ""

def _post_largo(ctx, tema):
    """Post largo anti-medio: 8 analisis LLM + ensamblaje determinista."""
    medios = _medios_con_tecnica(ctx)
    scrapeado = ctx.get("scrapeado", {})

    # FASE 1: 8 analisis cortos (uno por medio)
    analisis = []
    for m in medios:
        nombre = m["medio"]
        tecnica = m["tecnica"]
        titular = m["titular"]
        url = m.get("url", "")
        if nombre not in scrapeado or scrapeado[nombre].get("chars", 0) < 200:
            continue
        texto = scrapeado[nombre]["texto_completo"][:1500]
        print(f"     -> Analizando {nombre} ({tecnica})...", end=" ", flush=True)

        prompt_f1 = "Analiza como el medio " + nombre + " construyo su relato usando la tecnica " + tecnica + "."
        prompt_f1 += "\n\nTITULAR REAL: «" + titular + "»"
        prompt_f1 += "\n\nTEXTO REAL DEL MEDIO:\n" + texto
        prompt_f1 += "\n\nTAREA: Escribe un analisis de 150-180 palabras en HTML (SOLO <p> parrafos, sin H2, sin H1) sobre:"
        prompt_f1 += "\n1. Que palabra o frase del texto delata la tecnica (cita TEXTUAL entre comillas)"
        prompt_f1 += "\n2. Que te hace sentir esa eleccion"
        prompt_f1 += "\n3. Como detectarlo tu la proxima vez"
        prompt_f1 += "\n\nREGLAS: SOLO parrafos <p>. Tono mordaz. Cita TEXTUAL. NO inventes. Sin palabras: muerte, muerto, sangre, tragedia, saqueo, victima, asesinato, crimen, corrupcion, fraude, guerra."

        try:
            r = _llamar(prompt_f1, max_retries=2)
            if r and len(r) > 200:
                # Limpiar posibles H2/H1 que el LLM meta
                r = re.sub(r'<h[12][^>]*>.*?</h[12]>', '', r, flags=re.DOTALL | re.IGNORECASE)
                analisis.append({
                    "medio": nombre,
                    "tecnica": tecnica,
                    "titular": titular,
                    "url": url,
                    "html": r.strip(),
                })
                print(f"OK ({len(r)} chars)", flush=True)
            else:
                print("vacio", flush=True)
        except Exception as e:
            print(f"ERROR: {e}", flush=True)
        time.sleep(1.5)

    if not analisis:
        print("  ! Sin analisis, fallback articulo", flush=True)
        return _md_a_html(ctx["articulo"])

    # FASE 2: H1 + entradilla + cierre (1 llamada corta)
    print(f"     -> Generando H1 y entradilla...", end=" ", flush=True)
    medios_nombres = ", ".join([a["medio"] for a in analisis])
    tecnicas_lista = ", ".join([a["tecnica"] for a in analisis])
    prompt_f2 = "Eres el editor jefe de SOMOS EL ENCUADRE, un ANTI-MEDIO mordaz tipo Gabilondo."
    prompt_f2 += "\n\nTEMA DEL DIA: " + tema
    prompt_f2 += "\n\nMEDIOS ANALIZADOS: " + medios_nombres
    prompt_f2 += "\nTECNICAS DETECTADAS: " + tecnicas_lista
    prompt_f2 += "\n\nTAREA: Genera SOLO esto (en HTML, sin <html>, sin <body>):"
    prompt_f2 += "\n1. Un <h1> con titular fuerte que prometa revelacion (max 80 chars)"
    prompt_f2 += "\n2. Un parrafo de entradilla de 2 frases que enganche"
    prompt_f2 += "\n3. Un parrafo de intro de 3-4 lineas con contexto y promesa"
    prompt_f2 += "\n4. Un <h2>El mecanismo, expuesto</h2> seguido de un cierre potente (2-3 frases)"
    prompt_f2 += "\n\nREGLAS: SOLO esos 4 bloques. Sin markdown. Sin palabras: muerte, muerto, sangre, tragedia, saqueo, victima, asesinato, crimen, corrupcion, fraude, guerra."

    try:
        r2 = _llamar(prompt_f2, max_retries=2)
    except:
        r2 = ""

    # Extraer H1, entradilla, intro, cierre
    h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', r2 or '', re.DOTALL | re.IGNORECASE)
    h1 = h1_match.group(1).strip() if h1_match else tema

    # Quitar el H1 del r2 para quedarnos con el resto
    resto = re.sub(r'<h1[^>]*>.*?</h1>', '', r2 or '', flags=re.DOTALL | re.IGNORECASE)
    # Quitar el H2 del cierre (lo ponemos nosotros)
    resto = re.sub(r'<h2[^>]*>.*?</h2>', '', resto, flags=re.DOTALL | re.IGNORECASE)
    resto = resto.strip()

    # ENSAMBLAJE DETERMINISTA
    piezas = []
    piezas.append("<h1>" + h1 + "</h1>")
    if resto:
        piezas.append(resto)

    for a in analisis:
        h2 = "<h2>" + a["medio"] + ": " + a["tecnica"] + "</h2>"
        piezas.append(h2)
        piezas.append("<p><strong>Titular real:</strong> «" + a["titular"] + "»</p>")
        if a["url"]:
            piezas.append("<p><strong>Fuente:</strong> <a href=\"" + a["url"] + "\" target=\"_blank\" rel=\"noopener\">Leer en " + a["medio"] + "</a></p>")
        piezas.append(a["html"])

    # Cierre
    piezas.append("<h2>El mecanismo, expuesto</h2>")
    piezas.append("<p>Mañana volverán a hacerlo. Y tú ya sabrás dónde mirar. Eso es El Encuadre.</p>")

    # Descargo legal determinista
    descargo = '<div style="background:#1a1a24;padding:1em;border-radius:8px;margin:2em 0;font-size:0.9em;"><strong>Aviso legal:</strong> Esto no es una acusación. Es una autopsia. Los medios están citados y enlazados. El derecho de cita (art. 32 LPI) nos ampara. Si te duele, es que te has visto reflejado.</div>'
    piezas.append(descargo)

    html_final = "\n\n".join(piezas)

    # Limpieza final
    html_final = re.sub(r'<!DOCTYPE[^>]*>', '', html_final, flags=re.IGNORECASE)
    html_final = re.sub(r'<html[^>]*>', '', html_final, flags=re.IGNORECASE)
    html_final = re.sub(r'</html>', '', html_final, flags=re.IGNORECASE)
    html_final = re.sub(r'<head[^>]*>.*?</head>', '', html_final, flags=re.DOTALL | re.IGNORECASE)
    html_final = re.sub(r'<body[^>]*>', '', html_final, flags=re.IGNORECASE)
    html_final = re.sub(r'</body>', '', html_final, flags=re.IGNORECASE)
    html_final = re.sub(r'<style[^>]*>.*?</style>', '', html_final, flags=re.DOTALL | re.IGNORECASE)

    print(f"OK ({len(html_final)} chars, {len(analisis)} medios)", flush=True)
    return html_final

def _post_mediano(ctx, tipo):
    """Post mediano top-1: 7 tipos + contexto real + anti-alucinacion + descargo."""
    tema = ctx["dossier"].get("titular_brutal", "Análisis del día")[:80]
    tecnicas = _tecnicas_del_dia(ctx)
    medios_data = _medios_con_tecnica(ctx)
    scrapeado = ctx.get("scrapeado", {})
    hooks = ctx["hooks"]
    citas = ctx["citas"]

    # Seleccion segun tipo
    fuente_medio = None
    fuente_titular = ""
    fuente_url = ""
    fuente_texto = ""
    tecnica_foco = tecnicas[0] if tecnicas else "Framing"

    if tipo in ("medio_analizado", "medio_crudo") and medios_data:
        offset = 0 if tipo == "medio_analizado" else 5
        idx = (hash(FECHA) + offset) % len(medios_data)
        m = medios_data[idx]
        fuente_medio = m["medio"]
        fuente_titular = m["titular"]
        fuente_url = m.get("url", "")
        tecnica_foco = m["tecnica"]
        if fuente_medio in scrapeado:
            fuente_texto = scrapeado[fuente_medio].get("texto_completo", "")[:1500]

    # Prompts por tipo
    comun = """
REGLAS CRITICAS ANTI-ALUCINACION:
1. Usa SOLO los datos del contexto.
2. NUNCA inventes que dijo un medio.
3. Nombres propios EXACTOS (Oscar Puente, Pedro Sanchez).
4. NUNCA inventes frases entre comillas.
REGLAS: SOLO HTML (sin markdown, sin <html>, sin <body>). Tono mordaz tipo Gabilondo. Sin palabras: muerte, muerto, sangre, tragedia, saqueo, victima, asesinato, crimen, corrupcion, fraude, guerra.
"""

    if tipo == "quirurgico":
        hook = hooks[0].get("hook", "El caso del día") if hooks else tema
        foco = hook
        titulo = "El ángulo que nadie cuenta: " + hook[:50]
        prompt = "Analiza el angulo: " + foco + "\n\n" + comun
        prompt += "\n\nEstructura: H1 con el angulo. Entradilla 2 frases. 3-4 H2: contexto del hook, tecnica usada, por que funciona, como detectarla. Cierre potente."
        prompt += "\nLongitud: 1000-1300 palabras."
    elif tipo == "tutorial":
        foco = tecnica_foco
        titulo = "Cómo detectar la técnica: " + foco
        prompt = "Escribe un tutorial sobre la tecnica " + foco + "\n\n" + comun
        prompt += "\n\nEstructura: H1. Entradilla. 5 H2: que es, como se usa, ejemplo real, como detectarlo, como combatirlo. Cita ejemplos del contexto. Cierre."
        prompt += "\nLongitud: 1000-1500 palabras."
    elif tipo == "radar":
        medios_3 = medios_data[:3]
        if medios_3:
            foco = "comparativa de " + str(len(medios_3)) + " medios"
            titulo = "Radar de medios: " + tema[:50]
            prompt = "Compara como 3 medios cubrieron el tema: " + tema + "\n\n" + comun
            for mm in medios_3:
                prompt += "\nMEDIO: " + mm["medio"] + " | Titular: «" + mm["titular"] + "» | Tecnica: " + mm["tecnica"]
            prompt += "\n\nEstructura: H1. Entradilla. 3 H2 (uno por medio con titular, tecnica, que omite). H2 sintesis: lo que comparten. Cierre."
            prompt += "\nLongitud: 1000-1400 palabras."
        else:
            prompt = "Compara medios sobre: " + tema + "\n\n" + comun
            titulo = "Radar de medios: " + tema[:50]
    elif tipo == "cita":
        cita = citas[0] if citas else tema
        foco = str(cita)[:100]
        titulo = "La cita que lo cambia todo"
        prompt = "Analiza esta cita: «" + foco + "»\n\n" + comun
        prompt += "\n\nEstructura: H1. Entradilla. Blockquote con la cita. 4 H2: quien lo dijo, contexto, que queria decir, que oculta. Cierre."
        prompt += "\nLongitud: 1000-1200 palabras."
    elif tipo in ("medio_analizado", "medio_crudo"):
        if fuente_medio:
            titulo = fuente_medio + ": la tecnica del " + tecnica_foco.lower()
            prompt = "Analiza el medio " + fuente_medio + " (tecnica: " + tecnica_foco + ")"
            prompt += "\n\nTITULAR REAL: «" + fuente_titular + "»"
            prompt += "\n\nTEXTO REAL:\n" + fuente_texto
            prompt += "\n\n" + comun
            prompt += "\n\nEstructura: H1 con el medio y la tecnica. Entradilla. 3-4 H2: que dijo, como lo dijo (cita textual), que omitio, como detectarlo. Cierre."
            prompt += "\nLongitud: 900-1200 palabras."
        else:
            titulo = "El medio del dia"
            prompt = "Analiza como los medios cubrieron: " + tema + "\n\n" + comun
    elif tipo == "dossier":
        foco = "resumen ejecutivo"
        titulo = "Dossier completo del dia"
        prompt = "Escribe un dossier ejecutivo del dia. Tema: " + tema
        prompt += "\n\nMedios y tecnicas detectadas: " + ", ".join([m["medio"] + " (" + m["tecnica"] + ")" for m in medios_data[:8]])
        prompt += "\n\n" + comun
        prompt += "\n\nEstructura: H1. Entradilla. 5 H2: noticias, medios, tecnicas, sesgos, conclusion. Tabla HTML con medios. Cierre."
        prompt += "\nLongitud: 1000-1500 palabras."
    else:
        titulo = "El mecanismo del dia"
        prompt = "Analiza el mecanismo mediatico de hoy: " + tema + "\n\n" + comun

    # Llamar al LLM
    html = _llamar(prompt, max_retries=2)
    if not _validar(html, 800, 2):
        print(f"  ⚠️ LLM falló {tipo}, fallback articulo", flush=True)
        html = _md_a_html(ctx["articulo"][:3000])

    # Limpieza
    html = re.sub(r'<!DOCTYPE[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<html[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</html>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<body[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</body>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Fuente + tecnica deterministas
    piezas = []
    piezas.append(html.strip())

    if fuente_medio and fuente_titular:
        piezas.append("<p><strong>Titular real de " + fuente_medio + ":</strong> «" + fuente_titular + "»</p>")
        if fuente_url:
            piezas.append("<p><strong>Fuente:</strong> <a href=\"" + fuente_url + "\" target=\"_blank\" rel=\"noopener\">Leer en " + fuente_medio + "</a></p>")
        piezas.append("<p><strong>Tecnica detectada:</strong> " + tecnica_foco + "</p>")

    # Descargo legal
    piezas.append('<div style="background:#1a1a24;padding:1em;border-radius:8px;margin:2em 0;font-size:0.9em;"><strong>Aviso legal:</strong> Esto no es una acusacion. Es una autopsia. Los medios estan citados y enlazados. El derecho de cita (art. 32 LPI) nos ampara.</div>')

    html_final = "\n\n".join(piezas)
    print(f"  OK {tipo} ({len(html_final)} chars)", flush=True)
    return html_final, titulo, tipo

def _guardar(slug, titulo, html, fecha, tipo):
    from _figuras_helper import cargar_imgs, construir_hero_e_inline
    _tipo_img = "largo" if tipo == "largo" else "mediano"
    _imgs = cargar_imgs(fecha, _tipo_img)
    hero, html = construir_hero_e_inline(html, _imgs, titulo)
    contenido = f"""---
title: "{titulo}"
date: {fecha}
description: "Analisis {tipo}: {titulo[:100]}"
tags:
  - analisis
  - medios
  - framing
  - {tipo}
  - {fecha}
---

{hero}
{html}
{_bloque_redes()}
"""
    p = COLA / f"{fecha}-{slug}.md"
    p.write_text(contenido, encoding="utf-8")
    # Autocorrección determinista
    try:
        corregir(p, verbose=False)
        print(f"     💾 {p.name} ({p.stat().st_size} bytes, autocorregido)")
    except Exception as e:
        print(f"     💾 {p.name} ({p.stat().st_size} bytes, auto-error: {e})")
    return p

def main(fecha=None):
    fecha = fecha or FECHA
    print(f"Generando 2 posts anti-medio para {fecha}...")
    print("=" * 60)
    
    ctx = _ctx(fecha)
    if not ctx["articulo"]:
        print("❌ No hay articulo"); return False
    
    print(f"Dossier: {'ENRIQUECIDO' if ctx['enriquecido'] else 'original'}")
    tecnicas = _tecnicas_del_dia(ctx)
    print(f"Tecnicas detectadas: {len(tecnicas)}")
    print(f"   {', '.join(tecnicas[:8])}")
    print()
    
    dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
    tipo_mediano = ROTACION.get(dt.weekday(), "quirurgico")
    tema = ctx["dossier"].get("titular_brutal", "Análisis del día")[:60]
    
    # POST LARGO
    print(f"1. POST LARGO (2.000-2.500 palabras):")
    html_largo = _post_largo(ctx, tema)
    _guardar("largo", tema, html_largo, fecha, "largo")
    
    # POST MEDIANO
    print(f"\n2. POST MEDIANO ({tipo_mediano}):")
    html_med, titulo_med, tipo = _post_mediano(ctx, tipo_mediano)
    _guardar(f"mediano-{tipo}", titulo_med, html_med, fecha, tipo)
    
    print("=" * 60)
    print(f"✅ 2 posts generados en {COLA}")
    return True

if __name__ == "__main__":
    ok = main(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)
