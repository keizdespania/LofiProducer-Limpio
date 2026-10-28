"""generar_post_encuadre.py - Post largo + corto + retención."""
import sys, json, pathlib, datetime, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from post_helpers import parse_json, limpiar_md, es_valido, generar_imagen, envolver_html, publicar_en_web

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
OUT.mkdir(parents=True, exist_ok=True)

def _citas(tecnicas):
    import random
    from especialistas import pedir_a_especialista
    db_path = ROOT / "data" / "agent" / "citas_db.json"
    citas_db = json.loads(db_path.read_text()) if db_path.exists() else []
    citas = {}
    for tec in tecnicas[:3]:
        try:
            d = parse_json(pedir_a_especialista("citas_rapidas", f"Frase: {str(tec)[:100]}", contexto=""))
            if d.get("autor"): citas[tec[:60]] = d
        except: pass
    if citas_db:
        acad = [c for c in citas_db if c.get("tipo") not in ("cultura_pop", "calle")]
        juv = [c for c in citas_db if c.get("tipo") in ("cultura_pop", "calle")]
        if juv: citas["_juvenil"] = random.choice(juv)
        while len([k for k in citas if not k.startswith("_")]) < 3 and acad:
            citas["cita_" + str(len(citas))] = random.choice(acad)
    return citas

def _glosario(tecnicas):
    from especialistas import pedir_a_especialista
    try:
        return parse_json(pedir_a_especialista("glosario_medios", f"Explica: {', '.join(tecnicas)}. JSON: {{tecnica: {{definicion}}}}. Solo JSON.", contexto=""))
    except: return {}

def _retencion(medios):
    from especialistas import pedir_a_especialista
    prompt = """Genera un JSON con una lista "shorts" de 4 objetos.
Cada objeto debe tener: "id" (short_1, short_2, etc.), "tipo" (Dato, Contradiccion, Prediccion, Tutorial) y "texto" (un guion de 20-30 segundos con gancho).
Devuelve SOLO el JSON.
"""
    try:
        d = parse_json(pedir_a_especialista("retencion", prompt, contexto=json.dumps(medios)[:1500]))
        if d.get("shorts"): return d
    except: pass
    return {"shorts": [
        {"id": "short_1", "tipo": "Dato", "texto": "El 80% de la informacion desaparece. No te lo dicen."},
        {"id": "short_2", "tipo": "Contradiccion", "texto": "Dicen que es neutral, pero mira esto."},
        {"id": "short_3", "tipo": "Prediccion", "texto": "Esto va a cambiar como lees las noticias."},
        {"id": "short_4", "tipo": "Tutorial", "texto": "Hoy aprendes a detectar la manipulacion."}
    ]}


def _generar_guiones(tema, medios, comparativa):
    from especialistas import pedir_a_especialista
    prompt = """
    Genera un JSON estricto con dos claves: "video_largo" y "shorts".
    - "video_largo": Un guion de 500 palabras para narrar en voz alta. Sin HTML. Tono documental, intrigante. No uses listas ni corchetes.
    - "shorts": Una lista de 4 objetos. Cada uno con "id" (short_1, short_2, short_3, short_4) y "guion" (un texto de 60-80 palabras con gancho, desarrollo y llamada a la acción, diseñado para ser leído en 30 segundos).
    Devuelve SOLO el JSON válido.
    """
    ctx = json.dumps({"tema": tema, "medios": medios, "comparativa": comparativa}, ensure_ascii=False)
    try:
        r = pedir_a_especialista("redactor_seo", prompt, contexto=ctx[:3000])
        d = parse_json(r)
        if d.get("video_largo") and d.get("shorts"):
            return d
    except: pass
    return None

def _auditar(html, tema):
    from especialistas import pedir_a_especialista
    for intento in range(2):
        try:
            r = pedir_a_especialista("experto_blog", f"Puntúa 0-10 y reescribe si <8. Solo HTML. Tema: {tema}", contexto=html[:4000])
            d = parse_json(r)
            score = d.get("score", d.get("puntuacion", 10))
            if score >= 8 or intento == 1: return html
            nuevo = limpiar_md(r)
            if es_valido(nuevo, 1000): html = nuevo
        except: return html
    return html

def generar_post(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    j = OUT / f"encuadre_{fecha}.json"
    if not j.exists(): print(f"[post] No existe {j}"); return None
    d = json.loads(j.read_text())
    analisis = d.get("analisis", {})
    medios = analisis.get("medios", [])
    comparativa = analisis.get("comparativa", "")
    tema = analisis.get("tema_especifico") or d.get("tema", "medios")

    tecnicas = {tt[:80] for m in medios for tt in m.get("tecnicas", []) if tt and len(tt) > 3}
    tecnicas_lista = list(tecnicas)[:5]

    from especialistas import pedir_a_especialista

    print("[post] Retención...", flush=True); ret = _retencion(medios)
    print("[post] Citas...", flush=True); citas = _citas(tecnicas_lista)
    print("[post] Glosario...", flush=True); glosario = _glosario(tecnicas_lista)

    print("[post] Imágenes...", flush=True)
    img_url = generar_imagen(f"cinematic dark news analysis about {tema}, abstract, neon, no text", "Análisis")

    print("[post] Artículo largo...", flush=True)
    ctx = json.dumps({"medios": medios, "comparativa": comparativa}, ensure_ascii=False)
    prompt = f"Artículo HTML sobre {tema}. Estructura: intro gancho, H2 Qué ha pasado, H2 Cómo lo cuentan, H2 Técnicas, H2 Cómo detectarlo, FAQ. Tono valiente, irónico. No inventes. Devuelve solo <article>."
    hl = _auditar(limpiar_md(pedir_a_especialista("redactor_seo", prompt, contexto=ctx[:3000])), tema)
    if img_url: hl = f'<div style="text-align:center;margin:20px 0;"><img src="{img_url}" alt="Análisis" style="max-width:100%;border-radius:12px;"/></div>' + hl
    cab = '<header style="margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid #333;">'
    if ret.get("hook"): cab += f'<p style="font-size:1.3em;color:#f77f00;font-weight:600;margin:0 0 15px;">{ret["hook"]}</p>'
    cab += f'<div style="display:flex;gap:15px;font-size:0.9em;color:#888;"><span>Por <strong style="color:#e63946;">El Encuadre</strong></span><span>{fecha}</span><span>~5 min</span></div></header>'
    hl = cab + hl

    if citas:
        hl += '<h2>Fundamento académico</h2>'
        for _, info in citas.items():
            if isinstance(info, dict):
                hl += f'<blockquote><p><em>"{str(info.get("cita_breve",""))[:300]}"</em></p><cite>— {info.get("autor","")}, <strong>{info.get("libro","")}</strong> ({info.get("año","")})</cite></blockquote>'
    if glosario:
        hl += '<h2>Glosario</h2>'
        for tec, info in glosario.items():
            if isinstance(info, dict): hl += f'<h3>{tec}</h3><p>{str(info.get("definicion",""))[:300]}</p>'

    hl += '<div style="margin:40px 0;padding:20px;background:rgba(230,57,70,0.1);border-radius:12px;text-align:center;"><p style="margin:0 0 15px;font-weight:600;">Compártelo</p><a href="https://twitter.com/intent/tweet" style="display:inline-block;margin:0 5px;padding:10px 20px;background:#000;color:#fff;text-decoration:none;border-radius:8px;">X</a><a href="https://wa.me/" style="display:inline-block;margin:0 5px;padding:10px 20px;background:#25D366;color:#fff;text-decoration:none;border-radius:8px;">WhatsApp</a><a href="https://t.me/share/url" style="display:inline-block;margin:0 5px;padding:10px 20px;background:#0088cc;color:#fff;text-decoration:none;border-radius:8px;">Telegram</a></div>'
    hl += '<div style="margin:40px 0;padding:20px;background:#1a1a24;border-radius:12px;"><h2 style="font-size:1.2em;">También te puede interesar</h2><ul><li><a href="https://somoselencuadre.blogspot.com">Otros análisis</a></li><li><a href="https://elencuadre.pages.dev">Web oficial</a></li></ul></div>'

    hl = envolver_html(hl, tema, fecha, img_url)
    (OUT / f"post_largo_{fecha}.html").write_text(hl, encoding="utf-8")
    print(f"  OK largo: {len(hl)} chars")

    print("[post] Artículo corto...", flush=True)
    hc = limpiar_md(pedir_a_especialista("redactor_seo", "Resumen HTML 300-400 palabras. Termina: Lee el análisis completo en elencuadre.pages.dev.", contexto=ctx[:1500]))
    try:
        hc_h = limpiar_md(pedir_a_especialista("humanizador", "Reescribe humano:", contexto=hc[:2000]))
        if es_valido(hc_h, 1000): hc = hc_h
    except: pass
    if img_url: hc = f'<img src="{img_url}" alt="Análisis" style="max-width:100%;border-radius:12px;margin-bottom:15px;"/><br>' + hc
    (OUT / f"post_corto_{fecha}.html").write_text(hc, encoding="utf-8")
    print(f"  OK corto: {len(hc)} chars")


    print("[post] Generando guiones audiovisuales...", flush=True)
    guiones = _generar_guiones(tema, medios, comparativa)
    if guiones:
        (OUT / f"guiones_{fecha}.json").write_text(json.dumps(guiones, indent=2, ensure_ascii=False))
        print("  ✅ Guiones guardados en guiones_{fecha}.json")
    else:
        print("  ⚠️ No se pudieron generar los guiones")

    (OUT / f"retencion_{fecha}.json").write_text(json.dumps(ret, indent=2, ensure_ascii=False))
    print("[post] Publicando en web...", flush=True); publicar_en_web(fecha, tema)
    return {"fecha": fecha, "largo": str(OUT / f"post_largo_{fecha}.html"), "corto": str(OUT / f"post_corto_{fecha}.html"), "retencion": ret}

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    r = generar_post(fecha)
    if r: print(json.dumps(r, indent=2, ensure_ascii=False))
