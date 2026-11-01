"""publicar_blogger_encuadre.py - Publica el artículo del día en Blogger con SEO."""
import sys, json, pathlib, urllib.request, urllib.parse, re, time, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TOKEN = ROOT / "data" / "youtube_encuadre_token.json"
BLOG_ID = "5810739452530624729"  # iaglobalnews.blogspot.com

FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def _token():
    tok = json.loads(TOKEN.read_text())
    if time.time() > tok.get("expires_at", 0) - 60:
        print("  [token] refrescando...")
        data = urllib.parse.urlencode({
            "client_id": tok["client_id"],
            "client_secret": tok["client_secret"],
            "refresh_token": tok["refresh_token"],
            "grant_type": "refresh_token",
        }).encode()
        req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
        r = json.loads(urllib.request.urlopen(req, timeout=20).read())
        tok["access_token"] = r["access_token"]
        tok["expires_at"] = time.time() + r.get("expires_in", 3600)
        TOKEN.write_text(json.dumps(tok, indent=2))
        print("  [token] OK")
    return tok["access_token"]

def _md_a_html(md_texto):
    """Convierte markdown a HTML con extensiones."""
    import markdown
    return markdown.markdown(
        md_texto,
        extensions=["extra", "sane_lists", "smarty", "toc"],
        output_format="html5",
    )

def _construir_html(md_texto, titulo, meta_desc, keywords):
    """Convierte markdown + inyecta SEO técnico."""
    html_cuerpo = _md_a_html(md_texto)
    
    # JSON-LD para SEO técnico
    ld_json = {
        "@context": "https://schema.org",
        "@type": "NewsArticle",
        "headline": titulo,
        "description": meta_desc,
        "datePublished": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "author": {"@type": "Organization", "name": "Somos El Encuadre"},
        "publisher": {"@type": "Organization", "name": "Somos El Encuadre"},
        "keywords": ", ".join(keywords),
    }
    ld_script = f'<script type="application/ld+json">{json.dumps(ld_json, ensure_ascii=False)}</script>'
    
    # Meta description inyectado (workaround: Blogger no lo setea por API)
    meta_tag = f'<meta name="description" content="{meta_desc.replace(chr(34), "&quot;")}">'
    
    return f"{meta_tag}\n{ld_script}\n\n{html_cuerpo}"

def _extraer_keywords(dossier, titulo, max_kw=8):
    """Extrae keywords del dossier y del título."""
    kws = set()
    # Del título
    palabras_titulo = re.findall(r'\b[A-Za-zÁÉÍÓÚÑáéíóúñ]{5,}\b', titulo)
    for p in palabras_titulo[:3]:
        kws.add(p.lower())
    # Del dossier
    top3 = dossier.get("top3", {})
    if isinstance(top3, dict):
        for noticia in top3.values():
            palabras = re.findall(r'\b[A-Za-zÁÉÍÓÚÑáéíóúñ]{6,}\b', str(noticia))
            for p in palabras[:2]:
                kws.add(p.lower())
    # Fijos
    kws.update(["análisis mediático", "framing", "El Encuadre", "sesgo informativo"])
    return sorted(kws)[:max_kw]

def publicar(fecha=None):
    fecha = fecha or FECHA
    prod_path = OUT / f"produccion_{fecha}.json"
    redes_path = OUT / f"redes_{fecha}.json"
    
    if not prod_path.exists():
        print(f"❌ No existe {prod_path}"); return False
    if not redes_path.exists():
        print(f"❌ No existe {redes_path}"); return False
    
    prod = json.loads(prod_path.read_text())
    redes = json.loads(redes_path.read_text())
    
    md_texto = prod.get("articulo_html", "")
    dossier = prod.get("dossier", {})
    
    if not md_texto or len(md_texto) < 500:
        print(f"❌ articulo_html muy corto ({len(md_texto)} chars)"); return False
    
    # Título y meta del bloque blogger de redes (short 1)
    bloque_blogger = redes.get("shorts", [{}])[0].get("blogger", {})
    titulo = bloque_blogger.get("titulo") or dossier.get("titular_brutal", "Análisis del día")
    meta_desc = bloque_blogger.get("resumen", "")[:160]
    
    # Keywords
    keywords = _extraer_keywords(dossier, titulo)
    
    # HTML final
    html_final = _construir_html(md_texto, titulo, meta_desc, keywords)
    
    print(f"📝 Publicando en Blogger")
    print(f"   Título: {titulo}")
    print(f"   Meta desc: {meta_desc[:100]}...")
    print(f"   HTML: {len(html_final)} chars")
    print(f"   Labels: {keywords}")
    print(f"   Blog ID: {BLOG_ID}")
    
    # Llamar a la API
    access = _token()
    endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts/"
    payload = {
        "kind": "blogger#post",
        "title": titulo,
        "content": html_final,
        "labels": keywords,
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint, data=data, method="POST",
        headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
    )
    
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        print()
        print(f"✅ PUBLICADO")
        print(f"   URL: {r.get('url')}")
        print(f"   ID:  {r.get('id')}")
        print()
        print("📋 SEARCH DESCRIPTION (pegar manualmente en Blogger → Editar → Descripción de búsqueda):")
        print(f"   {meta_desc}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        print(f"❌ HTTP {e.code}: {e.reason}")
        print(f"   Body: {body}")
        return False
    except Exception as e:
        print(f"❌ {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    ok = publicar(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)
