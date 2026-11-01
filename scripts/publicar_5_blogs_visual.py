"""publicar_5_blogs_visual.py - 5 posts con formato visual NYT + SEO cruzado."""
import sys, json, pathlib, urllib.request, urllib.parse, re, time, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TOKEN = ROOT / "data" / "youtube_encuadre_token.json"
BLOG_ID = "5810739452530624729"

sys.path.insert(0, str(ROOT / "scripts"))
from subir_imagenes_github import url_imagen, obtener_hero_y_secundarias

FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

REDES = {
    "YouTube": "https://youtube.com/@SomosElEncuadre",
    "TikTok": "https://tiktok.com/@somoselencuadre",
    "Instagram": "https://instagram.com/somoselencuadre",
    "X": "https://x.com/SomosElEncuadre",
    "Threads": "https://threads.net/@somoselencuadre",
    "Web": "https://elencuadre.pages.dev",
}

def _token():
    tok = json.loads(TOKEN.read_text())
    if time.time() > tok.get("expires_at", 0) - 60:
        data = urllib.parse.urlencode({
            "client_id": tok["client_id"], "client_secret": tok["client_secret"],
            "refresh_token": tok["refresh_token"], "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        tok["access_token"] = r["access_token"]
        tok["expires_at"] = time.time() + r.get("expires_in", 3600)
        TOKEN.write_text(json.dumps(tok, indent=2))
    return tok["access_token"]

def _md_a_html(md):
    import markdown
    return markdown.markdown(md, extensions=["extra", "sane_lists", "smarty"])

def _bloque_redes():
    lineas = [f'<a href="{url}" target="_blank" rel="noopener">{nombre}</a>' for nombre, url in REDES.items()]
    return f'<div class="redes-encuadre" style="margin:2em 0;padding:1.2em;background:#0a0a0f;border-left:4px solid #e63946;border-radius:6px;color:#e0e0e0;font-size:0.95em;"><strong>Síguenos en:</strong> {" · ".join(lineas)}</div>'

def _bloque_cruzado(post_actual, otros_posts):
    lineas = []
    for slug, titulo in otros_posts:
        if slug != post_actual:
            lineas.append(f'<li><a href="{{{{URL_POST_{slug}}}}}">{titulo}</a></li>')
    return f'<div class="seo-cruzado" style="margin:2em 0;padding:1.2em;background:#15151f;border-radius:6px;"><h3 style="color:#e63946;margin-top:0;">📖 Más análisis del día</h3><ul>{"".join(lineas)}</ul></div>'

def _figura(url_img, caption, es_hero=False):
    style = 'width:100%;border-radius:8px;margin:1em 0;display:block;' if es_hero else 'width:100%;border-radius:6px;margin:1em 0;display:block;'
    return f'<figure style="margin:1.5em 0;"><img src="{url_img}" alt="{caption}" style="{style}" loading="lazy"><figcaption style="font-size:0.85em;color:#888;text-align:center;margin-top:0.5em;font-style:italic;">{caption}</figcaption></figure>'

def _construir_post(titulo, md_cuerpo, meta_desc, labels, es_post_principal, otros_posts, imagenes):
    """Construye el HTML con formato NYT + SEO técnico + cruce."""
    html_md = _md_a_html(md_cuerpo)
    
    # Dividir en bloques por <h2> o <h1> para intercalar imágenes
    bloques = re.split(r'(<h[12][^>]*>.*?</h[12]>)', html_md)
    
    partes = []
    idx_img = 0
    hero_insertado = False
    
    for i, bloque in enumerate(bloques):
        partes.append(bloque)
        # Insertar hero justo después del primer header (h1 o h2)
        if not hero_insertado and re.match(r'<h[12]', bloque):
            partes.append(_figura(url_imagen(imagenes[0]), "Imagen destacada del análisis", es_hero=True))
            hero_insertado = True
        # Intercalar imágenes cada 4 bloques después del hero
        elif i > 2 and i % 4 == 0 and idx_img + 1 < len(imagenes):
            idx_img += 1
            partes.append(_figura(url_imagen(imagenes[idx_img]), f"Escena del análisis · {titulo[:50]}"))
    
    # Si no se insertó hero (no había header), meterlo al principio
    if not hero_insertado:
        partes.insert(0, _figura(url_imagen(imagenes[0]), "Imagen destacada del análisis", es_hero=True))
    
    html_cuerpo = "".join(partes)
    
    # SEO cruzado
    html_cuerpo += _bloque_cruzado("master", otros_posts)
    
    # Redes
    html_cuerpo += _bloque_redes()
    
    # JSON-LD
    ld = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": titulo,
        "description": meta_desc,
        "datePublished": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "image": url_imagen(imagenes[0]),
        "author": {"@type": "Organization", "name": "Somos El Encuadre"},
        "publisher": {"@type": "Organization", "name": "Somos El Encuadre"},
        "keywords": ", ".join(labels),
    }
    ld_script = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    meta_tag = f'<meta name="description" content="{meta_desc.replace(chr(34), "&quot;")}">'
    
    return f"{meta_tag}\n{ld_script}\n\n{html_cuerpo}"

def _limpiar_titulo(seccion_md):
    """Extrae el primer header de la sección y lo limpia."""
    if not seccion_md: return "El caso"
    primera_linea = seccion_md.split(chr(10))[0]
    # Quitar markdown headers y numeración
    limpio = re.sub(r'^#+\s*', '', primera_linea)
    limpio = re.sub(r'^\d+\.\s*', '', limpio)
    limpio = limpio.strip()
    return limpio[:50] if limpio else "El caso"

def _meta_limpia(md_texto, slug):
    """Extrae texto limpio para meta description: quita markdown, headers, líneas vacías."""
    if not md_texto: return f"Análisis {slug} del día"
    # Quitar headers, bold, italic, citas, listas
    t = re.sub(r'^#+\s*', '', md_texto, flags=re.MULTILINE)
    t = re.sub(r'^\d+\.\s*', '', t, flags=re.MULTILINE)
    t = re.sub(r'[*_`>\[\]()]', '', t)
    # Quitar saltos y espacios múltiples
    t = re.sub(r'\s+', ' ', t).strip()
    # Cortar a 160 chars sin partir palabra
    if len(t) > 160:
        t = t[:160].rsplit(' ', 1)[0] + '...'
    return t[:160] if t else f"Análisis {slug} del día"

def _generar_5_posts(fecha):
    """Genera los 5 posts: 1 principal + 4 satélites (basados en las 4 secciones del artículo)."""
    prod = json.loads((OUT / f"produccion_{fecha}.json").read_text())
    redes = json.loads((OUT / f"redes_{fecha}.json").read_text())
    md_principal = prod.get("articulo_html", "")
    dossier = prod.get("dossier", {})
    
    # Título y meta del blog principal
    blog_redes = redes["shorts"][0].get("blogger", {})
    titulo_principal = blog_redes.get("titulo") or dossier.get("titular_brutal", "Análisis del día")
    meta_principal = blog_redes.get("resumen", "")[:160]
    
    # 4 satélites: cortar el artículo en 4 partes (por <h2>)
    h2_matches = list(re.finditer(r'(?m)^## (.+)$', md_principal))
    secciones = []
    if len(h2_matches) >= 4:
        for i in range(4):
            ini = h2_matches[i].start() if i < len(h2_matches) else 0
            fin = h2_matches[i+1].start() if i+1 < len(h2_matches) else len(md_principal)
            secciones.append(md_principal[ini:fin])
    else:
        # Fallback: dividir el artículo en 4 trozos
        trozo = len(md_principal) // 4
        for i in range(4):
            secciones.append(md_principal[i*trozo:(i+1)*trozo])
    
    titulos_satelites = [
        ("controversia", "🔴 La polémica: " + _limpiar_titulo(secciones[0]) if secciones else "🔴 La polémica del día"),
        ("urgencia", "🟠 La urgencia: " + _limpiar_titulo(secciones[1]) if len(secciones) > 1 else "🟠 La urgencia del día"),
        ("justicia", "🟡 La justicia: " + _limpiar_titulo(secciones[2]) if len(secciones) > 2 else "🟡 La justicia del día"),
        ("curiosidad", "🟢 La curiosidad: " + _limpiar_titulo(secciones[3]) if len(secciones) > 3 else "🟢 La curiosidad del día"),
    ]
    
    posts = [
        {
            "slug": "master",
            "titulo": titulo_principal,
            "md": md_principal,
            "meta": meta_principal,
            "labels": ["análisis mediático", "framing", "El Encuadre", "actualidad", "periodismo"],
            "principal": True,
        }
    ]
    
    for i, (slug, titulo) in enumerate(titulos_satelites):
        posts.append({
            "slug": slug,
            "titulo": titulo,
            "md": f"# {titulo}\n\n{secciones[i]}",
            "meta": _meta_limpia(secciones[i], slug) if i < len(secciones) else f"Análisis {slug} del día",
            "labels": [slug, "análisis mediático", "framing", "El Encuadre"],
            "principal": False,
        })
    
    return posts

def _publicar_post(post, otros_posts, imagenes, dry_run=False, publish_at=None):
    html = _construir_post(post["titulo"], post["md"], post["meta"], post["labels"], post["principal"], otros_posts, imagenes)
    
    print(f"\n{'='*60}")
    print(f"[{post['slug']}] {post['titulo'][:70]}")
    print(f"  HTML: {len(html)} chars")
    print(f"  Labels: {post['labels']}")
    
    if dry_run:
        print(f"  --- PRIMEROS 300 CHARS ---")
        print(f"  {html[:300]}")
        if publish_at:
            print(f"  ⏰ Se programaría para: {publish_at}")
        return {"dry_run": True, "slug": post["slug"]}
    
    access = _token()
    
    # PASO 1: crear como BORRADOR
    endpoint_insert = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    payload = {
        "kind": "blogger#post",
        "title": post["titulo"],
        "content": html,
        "labels": post["labels"],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(endpoint_insert, data=data, method="POST",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"})
    
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        post_id = r.get("id")
        print(f"  📝 Borrador creado (ID: {post_id})")
    except urllib.error.HTTPError as e:
        print(f"  ❌ Error creando borrador: HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    
    # PASO 2: publicar (inmediato o programado)
    if publish_at:
        endpoint_pub = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/{post_id}/publish?publishDate={urllib.parse.quote(publish_at)}"
        print(f"  ⏰ Programando para: {publish_at}")
    else:
        endpoint_pub = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/{post_id}/publish"
        print(f"  🚀 Publicando ahora")
    
    req_pub = urllib.request.Request(endpoint_pub, method="POST",
        headers={"Authorization": f"Bearer {access}"})
    try:
        r_pub = json.loads(urllib.request.urlopen(req_pub, timeout=60).read())
        print(f"  ✅ {r_pub.get('url')}")
        return r_pub
    except urllib.error.HTTPError as e:
        print(f"  ❌ Error publicando: HTTP {e.code}: {e.read().decode()[:200]}")
        return None

def main(fecha, dry_run=False):
    imgs_info = obtener_hero_y_secundarias()
    if not imgs_info:
        print("❌ No hay escenas suficientes"); return False
    imagenes = imgs_info["posts"]
    
    posts = _generar_5_posts(fecha)
    otros = [(p["slug"], p["titulo"]) for p in posts]
    
    print(f"Generando {len(posts)} posts...")
    print(f"Imágenes: {imagenes}")
    print(f"Modo: {'DRY RUN' if dry_run else 'PUBLICACIÓN REAL'}")
    
    for post in posts:
        _publicar_post(post, otros, imagenes, dry_run)
        time.sleep(2)
    
    print(f"\n✅ {'Dry-run completado' if dry_run else '5 posts publicados'}")
    return True

if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    fecha = [a for a in sys.argv[1:] if not a.startswith("--")]
    fecha = fecha[0] if fecha else datetime.date.today().isoformat()
    sys.exit(0 if main(fecha, dry_run=dry) else 1)
