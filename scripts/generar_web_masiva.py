"""generar_web_masiva.py - Genera los 12 posts diarios y mantiene el archivo histórico."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WEB_POSTS = ROOT / "web" / "docs" / "analisis"
WEB_POSTS.mkdir(parents=True, exist_ok=True)

def _limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'```(?:html|json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()

def _guardar_post(fecha, slug, titulo, html, resumen=""):
    # Nombre del archivo: YYYY-MM-DD-slug.md
    filename = f"{fecha}-{slug}.md"
    filepath = WEB_POSTS / filename
    
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
    print(f"  ✅ Guardado: {filename}")
    return filename

def actualizar_indice_archivo():
    """Genera el index.md de la carpeta analisis con TODOS los posts históricos."""
    posts = sorted(list(WEB_POSTS.glob("*.md")), reverse=True)
    posts = [p for p in posts if p.name != "index.md"]
    
    contenido = """# Archivo Histórico de Análisis

Todos los análisis de manipulación mediática generados por el sistema.

<div class="post-grid">
"""
    for p in posts:
        # Leer el título y la fecha del frontmatter
        texto = p.read_text()
        m_titulo = re.search(r'title:\s*(.+)', texto)
        m_fecha = re.search(r'date:\s*(.+)', texto)
        m_desc = re.search(r'description:\s*(.+)', texto)
        
        titulo = m_titulo.group(1).strip() if m_titulo else p.stem
        fecha = m_fecha.group(1).strip() if m_fecha else ""
        desc = m_desc.group(1).strip() if m_desc else ""
        
        contenido += f"""
    <div class="post-card">
        <p style="color: var(--accent); font-size: 0.8em; font-weight: bold;">{fecha}</p>
        <h3>{titulo}</h3>
        <p>{desc}</p>
        <a href="{p.stem}/">Leer análisis →</a>
    </div>
"""
    contenido += "\n</div>\n"
    
    (WEB_POSTS / "index.md").write_text(contenido, encoding="utf-8")
    print(f"✅ Índice histórico actualizado: {len(posts)} posts en total.")

def actualizar_home():
    """Actualiza la portada para mostrar solo los 5 últimos posts."""
    posts = sorted(list(WEB_POSTS.glob("*.md")), reverse=True)
    posts = [p for p in posts if p.name != "index.md"][:5]
    
    contenido = """<div class="hero-lab">
<h1>El código fuente de la realidad.</h1>
<p>No te contamos las noticias. Te enseñamos la maquinaria que hay detrás de ellas. Análisis técnico, académico e irónico sobre cómo los medios construyen tu percepción.</p>
<div style="margin-top: 30px;">
  <a href="analisis/" class="btn-lab btn-lab-primary">Ver todo el archivo →</a>
</div>
</div>

## Últimos Análisis

<div class="post-grid">
"""
    for p in posts:
        texto = p.read_text()
        m_titulo = re.search(r'title:\s*(.+)', texto)
        m_fecha = re.search(r'date:\s*(.+)', texto)
        m_desc = re.search(r'description:\s*(.+)', texto)
        
        titulo = m_titulo.group(1).strip() if m_titulo else p.stem
        fecha = m_fecha.group(1).strip() if m_fecha else ""
        desc = m_desc.group(1).strip() if m_desc else ""
        
        contenido += f"""
    <div class="post-card">
        <p style="color: var(--accent); font-size: 0.8em; font-weight: bold;">{fecha}</p>
        <h3>{titulo}</h3>
        <p>{desc}</p>
        <a href="analisis/{p.stem}/">Leer análisis →</a>
    </div>
"""
    contenido += "\n</div>\n"
    
    (ROOT / "web" / "docs" / "index.md").write_text(contenido, encoding="utf-8")
    print("✅ Portada actualizada con los últimos 5 posts.")

def generar_web_masiva(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists():
        print(f"❌ No existe {prod_file}"); return
    
    datos = json.loads(prod_file.read_text())
    dossier = datos.get("dossier", {})
    articulo = datos.get("articulo_html", "")
    seo = datos.get("seo", {}).get("youtube", {})
    
    links = """<hr><p style="font-size:0.9em;padding:10px;background:#111;border-radius:8px;"><strong>Síguenos:</strong> <a href="https://youtube.com/@SomosElEncuadre">YouTube</a> | <a href="https://tiktok.com/@somoselencuadre">TikTok</a> | <a href="https://instagram.com/somoselencuadre">Instagram</a> | <a href="https://x.com/somoselencuadre">X</a></p>"""

    # 1. POST MAESTRO
    print("  → [Web] Generando Post Maestro...")
    _guardar_post(fecha, "master", f"Resumen del Día: {dossier.get('tema_del_dia', fecha)}", articulo + links, dossier.get('el_relato_oficial', '')[:150])
    time.sleep(1)

    # 2. 3 POSTS QUIRÚRGICOS
    for i in range(1, 4):
        print(f"  → [Web] Generando Post Quirúrgico {i}...")
        ctx = f"RELATO: {dossier.get('el_relato_oficial')}\nCONTRA: {dossier.get('la_contra_narrativa')}\nPSICO: {dossier.get('analisis_psicologico')}"
        prompt = f"Escribe un post HTML de 1000 palabras analizando quirúrgicamente la noticia {i}. Usa el contexto. Tono analítico y mordaz."
        r = pedir_a_especialista("redactor_seo", prompt, contexto=ctx)
        _guardar_post(fecha, f"quirurgico-{i}", f"Análisis Forense: Noticia {i}", _limpiar_html(r) + links, f"Análisis profundo de la manipulación en la noticia {i}")
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
        _guardar_post(fecha, slug, titulo, html_base + links, f"Análisis satélite: {titulo}")

    # 4. 3 POSTS REDES
    shorts = datos.get("shorts_finales", [])
    for i, short in enumerate(shorts[:3]):
        red = short.get("id", f"red_{i}")
        print(f"  → [Web] Generando Post Red: {red}...")
        txt = f"<p>{short.get('tiktok', {}).get('texto', '')}</p>"
        _guardar_post(fecha, f"red-{red}", f"Short: {red}", txt + links, f"Contenido para redes: {red}")

    # 5. ACTUALIZAR ARCHIVOS Y PORTADA
    actualizar_indice_archivo()
    actualizar_home()
    print(f"\n[web] ✅ 12 posts generados y archivados.")

if __name__ == "__main__":
    generar_web_masiva(sys.argv[1] if len(sys.argv) > 1 else None)
