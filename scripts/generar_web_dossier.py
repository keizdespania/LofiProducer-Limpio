"""generar_web_dossier.py - Post mediano tipo DOSSIER con texto real (sin tocar el pipeline)."""
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
IMG_MAP = ROOT / "output" / "cola_blogger" / "imagenes_urls.json"

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

def _validar(html, min_chars=1000, min_h2=3):
    if not html or len(html) < min_chars: return False
    if html.count("<h2") < min_h2: return False
    prohibido = ["None", "no puedo", "necesito que me", "dame el texto"]
    if any(p in html[:500] for p in prohibido): return False
    return True

def _md_a_html(md):
    import markdown
    return markdown.markdown(md, extensions=["extra", "sane_lists", "smarty"])

def _ctx(fecha):
    prod = json.loads((OUT / f"produccion_{fecha}.json").read_text())
    enr = OUT / f"dossier_{fecha}_enriquecido.json"
    d_path = enr if enr.exists() else (OUT / f"dossier_{fecha}.json")
    dossier = json.loads(d_path.read_text())
    scrapeado_path = OUT / f"scrapeado_{fecha}.json"
    scrapeado = json.loads(scrapeado_path.read_text()) if scrapeado_path.exists() else {}
    return {
        "articulo": prod.get("articulo_html", ""),
        "dossier": dossier.get("dossier", {}),
        "top3": dossier.get("top3", {}),
        "scrapeado": scrapeado,
    }

def _medios_con_datos(ctx):
    """Lista de medios con {medio, titular, tecnica, omite, url, texto}."""
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
    for _ in range(max_retries):
        try:
            r = pedir_a_especialista("redactor_blog", prompt, contexto="")
            html = re.sub(r'```(?:html|markdown)?', '', r or '', flags=re.IGNORECASE).replace('```', '').strip()
            if html: return html
        except Exception as e:
            print(f"  LLM error: {e}", flush=True)
        time.sleep(1)
    return ""

def generar_dossier(fecha=None):
    fecha = fecha or FECHA
    print(f"Generando post DOSSIER con texto real para {fecha}...")
    print("=" * 60)
    
    ctx = _ctx(fecha)
    tema = ctx["dossier"].get("titular_brutal", "Análisis del día")[:80]
    medios = _medios_con_datos(ctx)
    scrapeado = ctx.get("scrapeado", {})
    
    print(f"Medios en desglose: {len(medios)}")
    print(f"Con texto real: {sum(1 for m in medios if m['chars'] > 200)}")
    print()
    
    # Construir contexto con TEXTO REAL
    contexto = []
    medios_usados = []
    for m in medios:
        if m["chars"] < 200:
            continue
        medios_usados.append(m)
        texto = m["texto"][:1800]
        contexto.append(f"""=== {m['medio']} ===
TITULAR: «{m['titular']}»
TECNICA: {m['tecnica']}
URL: {m['url']}
TEXTO REAL:
{texto}
""")
    
    if len(medios_usados) < 3:
        print("❌ Menos de 3 medios con texto real, abortando")
        return False
    
    contexto_str = "\n---\n".join(contexto)
    
    prompt = f"""Eres el editor jefe de SOMOS EL ENCUADRE. Eres un ANTI-MEDIO: no informas, destapas el mecanismo.

Vas a escribir un DOSSIER EJECUTIVO del día.

TEMA DEL DÍA: {tema}

MEDIOS CON TEXTO REAL (USA SOLO ESTO, NUNCA INVENTES):

{contexto_str[:14000]}

REGLAS CRÍTICAS ANTI-ALUCINACIÓN:
1. Usa SOLO los datos que aparecen en el TEXTO REAL de cada medio arriba.
2. NUNCA inventes declaraciones, hechos, ruedas de prensa, oposiciones, funcionarios.
3. NUNCA inventes qué dijo un medio. Si no está en su TEXTO REAL, NO LO MENCIONES.
4. Nombres propios EXACTOS del contexto (Óscar Puente, Pedro Sánchez).
5. Cita TEXTUALMENTE frases del TEXTO REAL entre comillas. NUNCA inventes citas.
6. Si un medio no tiene texto real, NO LO MENCIONES.

TAREA: Escribe un dossier ejecutivo de 1.000-1.500 palabras en HTML con esta estructura EXACTA:

H1: Título completo (NO lo cortes, escribe el tema entero). Ej: "Dossier del día: la 'doctrina Marlaska' y las 8 técnicas de los medios"

Entradilla (3-4 líneas): contexto del día + promesa.

H2: Noticias del día
  - Resumen de las 2-3 noticias principales (SOLO datos del texto real)
  - Cita textual de 2 medios diferentes

H2: Los medios y sus técnicas
  - Tabla HTML con: Medio | Técnica | Omite
  - Un párrafo introductorio

H2: Las técnicas al detalle
  - Por cada técnica detectada (mínimo 4):
    * Nombre de la técnica
    * Qué medio la usó
    * CITA TEXTUAL del texto real entre comillas
    * Cómo detectarla

H2: Los sesgos compartidos
  - Qué patrones se repiten entre medios
  - Por qué funcionan

H2: Conclusión
  - Cierre potente: "El mecanismo, expuesto. Mañana volverán a hacerlo."

REGLAS DE FORMATO:
- SOLO HTML (sin markdown, sin <html>, sin <body>, sin <style>)
- Tono mordaz tipo Gabilondo
- Sin palabras: muerte, muerto, sangre, tragedia, saqueo, víctima, asesinato, crimen, corrupción, fraude, guerra
- Cada cita textual DEBE estar en el contexto

Devuelve SOLO el HTML."""
    
    print(f"Llamando al LLM con {len(contexto_str)} chars de contexto real...")
    html = _llamar(prompt, max_retries=2)
    
    if not _validar(html, 1000, 3):
        print("⚠️ LLM falló, fallback al artículo")
        html = _md_a_html(ctx["articulo"][:3000])
    
    # Limpieza
    html = re.sub(r'<!DOCTYPE[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<html[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</html>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<head[^>]*>.*?</head>', '', html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r'<body[^>]*>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</body>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
    
    # Fuentes deterministas al final
    fuentes = ["<hr>", "<h3>Fuentes consultadas:</h3>", "<ul>"]
    for m in medios_usados:
        fuentes.append(f'<li><strong>{m["medio"]}:</strong> «{m["titular"]}» — <a href="{m["url"]}" target="_blank" rel="noopener">Leer completo</a></li>')
    fuentes.append("</ul>")
    fuentes_html = "\n".join(fuentes)
    
    # Descargo legal
    descargo = '<div style="background:#1a1a24;padding:1em;border-radius:8px;margin:2em 0;font-size:0.9em;"><strong>Aviso legal:</strong> Esto no es una acusación. Es una autopsia. Los medios están citados y enlazados. El derecho de cita (art. 32 LPI) nos ampara.</div>'
    
    html_final = html + "\n\n" + fuentes_html + "\n\n" + descargo
    
    # Guardar (3 imágenes dinámicas)
    hero_blocks = []
    img_map_path = ROOT / "web" / "media" / "imagenes" / f"web_urls_{fecha}.json"
    if img_map_path.exists():
        try:
            img_map = json.loads(img_map_path.read_text())
            # Usamos las del dossier si existen, o las del largo/mediano
            imgs = img_map.get("dossier", img_map.get("largo", []))
            for i, img_name in enumerate(imgs[:3]):
                if i == 0:
                    # La primera imagen como portada
                    hero_blocks.append(f'<figure><img src="../../media/imagenes/{img_name}" alt="Dossier del día" style="width:100%;border-radius:8px;" loading="lazy"></figure>')
                else:
                    # Las demás repartidas, o al final del post. Aquí las ponemos en el encabezado
                    hero_blocks.append(f'<figure><img src="../../media/imagenes/{img_name}" alt="Análisis" style="width:100%;border-radius:8px;margin-top:1em;" loading="lazy"></figure>')
        except Exception as e:
            print(f'   Error leyendo imágenes: {e}')
    hero = "\n".join(hero_blocks)
    
    contenido = f"""---
title: "Dossier del día: {tema[:60]}"
date: {fecha}
description: "Dossier ejecutivo: {tema[:100]}"
tags:
  - analisis
  - medios
  - dossier
  - {fecha}
---

{hero}
{html_final}
{_bloque_redes()}
"""
    
    p = COLA / f"{fecha}-dossier-v2.md"
    p.write_text(contenido, encoding="utf-8")
    # Autocorrección determinista
    try:
        corregir(p, verbose=False)
        print(f"   Autocorregido: {p.name}")
    except Exception as e:
        print(f"   Auto-error: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ Guardado: {p}")
    print(f"   {p.stat().st_size} bytes, {len(html_final)} chars")
    print(f"   {len(medios_usados)} medios con texto real")
    return True

if __name__ == "__main__":
    ok = generar_dossier(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)
