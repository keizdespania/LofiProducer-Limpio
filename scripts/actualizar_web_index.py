"""actualizar_web_index.py - Regenera home + analisis/index.md desde los .md existentes."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "web" / "docs"
ANALISIS = DOCS / "analisis"

def _parsear_fm(md_path):
    txt = md_path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.DOTALL)
    if not m: return None
    datos = {}
    for line in m.group(1).split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            datos[k.strip()] = v.strip().strip(chr(34)).strip(chr(39))
    return datos

def _categoria(nombre):
    if "-largo" in nombre: return ("🔥 Análisis Diario", "badge-new", "diario")
    if "-dossier" in nombre: return ("📁 Dossier Ejecutivo", "badge-dossier", "dossier")
    if "-mediano" in nombre: return ("📄 Análisis Mediano", "badge-guide", "mediano")
    return ("📄 Artículo", "badge-guide", "otros")

def _extraer_url_fuente(md_path):
    """Extrae la primera URL externa del cuerpo (la noticia original analizada)."""
    try:
        txt = md_path.read_text(encoding="utf-8")
        # Buscar primer href a dominio externo
        matches = re.findall(r'href="(https?://[^"]+)"', txt)
        excluir = ['youtube.com/@somoselencuadre.oficial', 'tiktok.com/@somoselencuadre',
                   'instagram.com/somoselencuadre', 'x.com/somoselencuadre',
                   'files.catbox.moe', 'youtube.com/', 'twitter.com/',
                   'facebook.com/', 'linkedin.com/']
        for url in matches:
            if not any(x in url for x in excluir):
                return url
    except Exception:
        pass
    return ""


def _dominio(url):
    """Devuelve el dominio limpio de una URL (sin www, sin protocolo)."""
    try:
        from urllib.parse import urlparse
        dom = urlparse(url).netloc
        return dom.replace("www.", "").replace("m.", "")
    except Exception:
        return ""


def _todos_los_posts():
    posts = []
    if not ANALISIS.exists(): return posts
    for f in ANALISIS.glob("*.md"):
        if f.name == "index.md": continue
        fm = _parsear_fm(f)
        if not fm: continue
        fecha = fm.get("date", "2026-01-01")
        titulo = fm.get("title", f.stem)
        desc = fm.get("description", "")[:150]
        badge, badge_class, cat = _categoria(f.stem)
        fuente = _extraer_url_fuente(f)
        posts.append({"fecha": fecha, "titulo": titulo, "desc": desc,
                      "slug": f.stem, "badge": badge, "badge_class": badge_class, "cat": cat,
                      "fuente_url": fuente, "fuente_dom": _dominio(fuente) if fuente else ""})
    posts.sort(key=lambda p: (p["fecha"], p["slug"]), reverse=True)
    return posts

def _card(post, con_data_cat=False, con_imagen=False, prefijo=""):
    import pathlib as _pl
    _root = _pl.Path(__file__).resolve().parent.parent
    img = ""
    if con_imagen:
        _fecha = post.get("fecha", "")
        _cand = None
        for _cat in (post.get("cat", ""), "largo", "dossier", "mediano"):
            if not _cat:
                continue
            _p = _root / "web" / "media" / "imagenes" / f"post_{_fecha}_{_cat}_1.png"
            if _p.exists():
                _cand = _p
                break
        if _cand:
            img = (f'<img src="/media/imagenes/{_cand.name}" alt="Hero" loading="lazy" '
                   f'style="width:100%;border-radius:6px;margin-bottom:0.5em;">')
    dc = f" data-category=\"{post['cat']}\"" if con_data_cat else ""
    fuente = post.get("fuente_url", "")
    fuente_html = ""
    if fuente:
        dom = post.get("fuente_dom", "fuente")
        fuente_html = (f'\n    <a href="{fuente}" target="_blank" rel="noopener" '
                       f'onclick="event.stopPropagation()" class="holo-fuente">'
                       f'🔗 Ver fuente · {dom}</a>')
    return (f"  <div class=\"holo-card\" style=\"cursor:pointer\" "
            f"onclick=\"window.location.href='{prefijo}{post['slug']}/'\"{dc}>\n"
            f"    <div class=\"holo-badge {post['badge_class']}\">{post['badge']}</div>\n"
            f"    {img}\n"
            f"    <h3>{post['titulo']}</h3>\n"
            f"    <p>{post['desc']}</p>\n"
            f"    <div class=\"holo-meta\"><span>📅 {post['fecha']}</span></div>\n"
            f"    {fuente_html}\n"
            f"  </div>")

GLOSARIO_CARD = """  <a href="glosario/" class="holo-card">
    <div class="holo-badge badge-guide">📚 Guía Definitiva</div>
    <h3>Las 51 técnicas de manipulación y sesgos cognitivos</h3>
    <p>El arsenal completo. Desde el anclaje de Kahneman hasta la fabricación de consentimiento de Chomsky.</p>
    <div class="holo-meta"><span>📅 Evergreen</span><span>⏱️ 20 min</span></div>
  </a>"""

def _generar_home(posts):
    recientes = posts[:5]
    cards = [_card(p, con_imagen=True, prefijo="analisis/") for p in recientes]
    cards.append(GLOSARIO_CARD)
    contenido = "---\nhide:\n  - navigation\n  - toc\n---\n\n"
    contenido += "<div class=\"holo-hero\">\n"
    contenido += "  <h1>Desmontamos la manipulación mediática</h1>\n"
    contenido += "  <p>No te contamos las noticias. Te enseñamos la maquinaria que hay detrás. Análisis técnico, académico e irónico.</p>\n"
    contenido += "  <a href=\"analisis/\" class=\"md-button md-button--primary\">Ver todos los análisis →</a>\n"
    contenido += "</div>\n\n"
    contenido += "<h2 class=\"holo-section-title\">Últimos Análisis</h2>\n\n"
    contenido += "<div class=\"holo-grid\">\n"
    contenido += "\n".join(cards)
    contenido += "\n</div>\n\n"
    contenido += "<h2 class=\"holo-section-title\">Arsenal del Anti-Medio</h2>\n\n"
    contenido += "<div class=\"holo-grid\">\n"
    contenido += "  <div class=\"holo-card\" style=\"cursor: default;\"><h3>🗞️ El Fin del Periodismo Pasivo</h3><p>No te decimos qué pensar. Te damos las herramientas para que veas el truco.</p></div>\n"
    contenido += "  <div class=\"holo-card\" style=\"cursor: default;\"><h3>🔍 Verificable y Transparente</h3><p>Cada afirmación está enlazada a la fuente original. Citamos titulares y exponemos datos ocultos.</p></div>\n"
    contenido += "  <div class=\"holo-card\" style=\"cursor: default;\"><h3>⚖️ Rigor Legal (Art. 32 LPI)</h3><p>Analizamos bajo el derecho de cita. No acusamos de delitos, describimos técnicas.</p></div>\n"
    contenido += "</div>\n"
    (DOCS / "index.md").write_text(contenido, encoding="utf-8")
    print(f"✅ index.md: {len(recientes)} ultimos + glosario")

def _generar_analisis(posts):
    cards = [_card(p, con_data_cat=True, con_imagen=True) for p in posts]
    contenido = "---\nhide:\n  - navigation\n---\n\n"
    contenido += "<div class=\"holo-hero\">\n"
    contenido += "  <h1>El Archivo del Anti-Medio</h1>\n"
    contenido += f"  <p>Todo nuestro arsenal. {len(posts)} análisis publicados. Sin filtros, con enlaces verificables.</p>\n"
    contenido += "</div>\n\n"
    contenido += "<div class=\"holo-filters\">\n"
    contenido += f"  <button class=\"holo-filter-btn active\" data-filter=\"all\">Todos ({len(posts)})</button>\n"
    n_diario = sum(1 for p in posts if p["cat"] == "diario")
    n_dossier = sum(1 for p in posts if p["cat"] == "dossier")
    n_mediano = sum(1 for p in posts if p["cat"] == "mediano")
    if n_diario: contenido += f"  <button class=\"holo-filter-btn\" data-filter=\"diario\">Diarios ({n_diario})</button>\n"
    if n_dossier: contenido += f"  <button class=\"holo-filter-btn\" data-filter=\"dossier\">Dossiers ({n_dossier})</button>\n"
    if n_mediano: contenido += f"  <button class=\"holo-filter-btn\" data-filter=\"mediano\">Medianos ({n_mediano})</button>\n"
    contenido += "</div>\n\n"
    contenido += "<div class=\"holo-grid\" id=\"archivo-grid\">\n"
    contenido += "\n".join(cards)
    contenido += "\n</div>\n\n"
    contenido += "<div style=\"text-align:center;margin:4rem 0 2rem 0;\"><p style=\"color:var(--holo-muted);font-size:0.9rem;\"><strong>El pipeline genera 2 posts nuevos al día.</strong><br>Vuelve mañana.</p></div>\n"
    (ANALISIS / "index.md").write_text(contenido, encoding="utf-8")
    print(f"✅ analisis/index.md: {len(posts)} posts ({n_diario} diarios, {n_dossier} dossiers, {n_mediano} medianos)")

def main():
    posts = _todos_los_posts()
    if not posts:
        print("❌ No hay posts para regenerar")
        return False
    _generar_home(posts)
    _generar_analisis(posts)
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)