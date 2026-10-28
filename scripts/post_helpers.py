"""post_helpers.py - Helpers para generar_post_encuadre.py"""
import json, pathlib, re, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def parse_json(texto):
    if not texto: return {}
    try: return json.loads(texto.strip())
    except: pass
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return {}

def limpiar_md(s):
    if not s: return ""
    s = re.sub(r"^\s*```(?:html)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```\s*$", "", s)
    return s.strip()

def es_valido(texto, min_chars=500):
    if not texto or len(texto) < min_chars: return False
    for e in ["ERROR 502", "ERROR 500", "ERROR 400", "Bad Gateway", "Connection refused"]:
        if e in texto[:300]: return False
    return True

def generar_imagen(prompt, alt=""):
    try:
        from generar_imagen import generar
        r = generar(prompt, preset="cinematic", aspect="16:9", canal="encuadre")
        m = re.search(r"(/media/[^\s\"']+)", str(r))
        if m: return m.group(1)
    except Exception as e:
        print(f"[post] imagen fallo: {e}", flush=True)
    return None

def envolver_html(fragmento, tema, fecha, img_url):
    if "<html" in fragmento.lower(): return fragmento
    meta = f'<meta property="og:title" content="{tema}"><meta property="og:image" content="{img_url or ""}"><meta name="description" content="Análisis: {tema}">'
    schema = f'<script type="application/ld+json">{{"@context":"https://schema.org","@type":"NewsArticle","headline":"{tema}","datePublished":"{fecha}","image":"{img_url or ""}"}}</script>'
    return f'<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{tema} - Somos El Encuadre</title>\n{meta}\n{schema}\n</head>\n<body style="max-width:800px;margin:0 auto;padding:20px;font-family:system-ui,sans-serif;background:#0a0a12;color:#e0e0e0;line-height:1.7;">\n{fragmento}\n</body>\n</html>'

def publicar_en_web(fecha, tema):
    import shutil
    try:
        src = OUT / f"post_largo_{fecha}.html"
        if not src.exists(): return
        web_analisis = ROOT / "web" / "docs" / "analisis"
        web_analisis.mkdir(parents=True, exist_ok=True)
        slug = f"post-{fecha}.html"
        shutil.copy2(src, web_analisis / slug)
        index = web_analisis / "index.md"
        if index.exists():
            txt = index.read_text()
            if slug not in txt:
                index.write_text(txt + f"\n## {fecha}\n- [{tema}]({slug})\n")
        r = subprocess.run(["mkdocs", "build", "-f", str(ROOT / "web" / "mkdocs.yml"), "-d", str(ROOT / "web" / "site")], check=False, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[web] ❌ Build falló: {r.stderr[-200:]}")
            return
        print("[web] ✅ Build OK")
        subprocess.run(["git", "add", "web/docs/analisis/", "web/site/"], cwd=str(ROOT), check=False)
        subprocess.run(["git", "commit", "-m", f"auto: post {fecha}"], cwd=str(ROOT), check=False)
        subprocess.run(["git", "push", "origin", "main"], cwd=str(ROOT), check=False)
        print("[web] ✅ Push OK")
    except Exception as e:
        print(f"[web] fallo: {e}")
