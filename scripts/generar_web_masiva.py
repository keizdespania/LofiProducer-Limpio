"""generar_web_masiva.py - Genera los 12 posts y los encola para publicación paulatina."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_web"
COLA.mkdir(parents=True, exist_ok=True)
COLA_FILE = ROOT / "output" / "cola_publicacion.json"

def _limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'```(?:html|json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()

def _guardar_post_en_cola(fecha, slug, titulo, html, resumen=""):
    filename = f"{fecha}-{slug}.md"
    filepath = COLA / filename
    frontmatter = f"""---
title: {titulo}
date: {fecha}
description: {resumen}
tags:
  - analisis
  - medios
  - manipulacion
---

# {titulo}

{html}
"""
    filepath.write_text(frontmatter, encoding="utf-8")
    print(f"  ✅ En cola: {filename}")
    return filename

def generar_web_masiva(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists(): return

    datos = json.loads(prod_file.read_text())
    dossier = datos.get("dossier", {})
    articulo = datos.get("articulo_html", "")
    seo = datos.get("seo", {}).get("youtube", {})
    links = """<hr><p style="font-size:0.9em;padding:10px;background:#111;border-radius:8px;"><strong>Síguenos:</strong> <a href="https://youtube.com/@SomosElEncuadre">YouTube</a> | <a href="https://tiktok.com/@somoselencuadre">TikTok</a> | <a href="https://instagram.com/somoselencuadre">Instagram</a> | <a href="https://x.com/somoselencuadre">X</a></p>"""

    posts_en_cola = []
    
    # 1. POST MAESTRO
    print("  → [Web] Generando Post Maestro...")
    posts_en_cola.append({"slug": "master", "titulo": f"Resumen del Día: {dossier.get('tema_del_dia', fecha)}", "html": articulo + links, "resumen": dossier.get('el_relato_oficial', '')[:150]})

    # 2. 3 POSTS QUIRÚRGICOS
    for i in range(1, 4):
        print(f"  → [Web] Generando Post Quirúrgico {i}...")
        ctx = f"RELATO: {dossier.get('el_relato_oficial')}\nCONTRA: {dossier.get('la_contra_narrativa')}\nPSICO: {dossier.get('analisis_psicologico')}"
        prompt = f"Escribe un post HTML de 1000 palabras analizando quirúrgicamente la noticia {i}. Usa el contexto. Tono analítico y mordaz."
        r = pedir_a_especialista("redactor_seo", prompt, contexto=ctx)
        posts_en_cola.append({"slug": f"quirurgico-{i}", "titulo": f"Análisis Forense: Noticia {i}", "html": _limpiar_html(r) + links, "resumen": f"Análisis profundo de la manipulación en la noticia {i}"})
        time.sleep(1)

    # 3. 5 POSTS SATÉLITE
    satelites = [
        ("cita", "La Cita Bomba", f"<blockquote>{dossier.get('cita_bomba')}</blockquote><p>{dossier.get('sarcasmo_del_dia')}</p>"),
        ("tutorial", "Cómo Detectarlo", f"<p>{dossier.get('analisis_psicologico')}</p>"),
        ("radar", "El Radar de Medios", f"<p>{dossier.get('el_relato_oficial')}</p>"),
        ("pueblo", "La Voz del Pueblo", f"<p>Transcripciones de TV/Radio del día.</p>"),
        ("dossier", "Dossier Completo", f"<pre>{json.dumps(dossier, indent=2, ensure_ascii=False)}</pre>")
    ]
    for slug, titulo, html_base in satelites:
        print(f"  → [Web] Generando Post Satélite: {titulo}...")
        posts_en_cola.append({"slug": slug, "titulo": titulo, "html": html_base + links, "resumen": f"Análisis satélite: {titulo}"})

    # 4. 3 POSTS REDES
    shorts = datos.get("shorts_finales", [])
    for i, short in enumerate(shorts[:3]):
        red = short.get("id", f"red_{i}")
        print(f"  → [Web] Generando Post Red: {red}...")
        txt = f"<p>{short.get('tiktok', {}).get('texto', '')}</p>"
        posts_en_cola.append({"slug": f"red-{red}", "titulo": f"Short: {red}", "html": txt + links, "resumen": f"Contenido para redes: {red}"})

    # 5. GUARDAR EN COLA Y CREAR TIMELINE DE PUBLICACIÓN
    ahora = datetime.datetime.now()
    cola_actual = []
    if COLA_FILE.exists():
        try: cola_actual = json.loads(COLA_FILE.read_text())
        except: cola_actual = []

    for i, post in enumerate(posts_en_cola):
        # Publicar cada 2 horas empezando por el maestro
        hora_pub = (ahora + datetime.timedelta(hours=i*2)).isoformat()
        filename = _guardar_post_en_cola(fecha, post["slug"], post["titulo"], post["html"], post["resumen"])
        cola_actual.append({
            "tipo": "web",
            "fecha": fecha,
            "filename": filename,
            "hora_publicacion": hora_pub,
            "publicado": False
        })
    
    COLA_FILE.write_text(json.dumps(cola_actual, indent=2))
    print(f"\n[web] ✅ {len(posts_en_cola)} posts en cola (se publicarán cada 2h).")

if __name__ == "__main__":
    generar_web_masiva(sys.argv[1] if len(sys.argv) > 1 else None)
