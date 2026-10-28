"""generar_blogs_blogger.py - Genera los 5 posts y los encola para publicación paulatina."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_blogger"
COLA.mkdir(parents=True, exist_ok=True)
COLA_FILE = ROOT / "output" / "cola_publicacion.json"

def _limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'```(?:html|json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()

def _guardar_post_en_cola(fecha, slug, titulo, html):
    filename = f"{fecha}-{slug}.json"
    filepath = COLA / filename
    filepath.write_text(json.dumps({"titulo": titulo, "html": html}, ensure_ascii=False, indent=2))
    print(f"  ✅ En cola: {filename}")
    return filename

def generar_blogs(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists(): return

    datos = json.loads(prod_file.read_text())
    dossier = datos.get("dossier", {})
    articulo = datos.get("articulo_html", "")
    seo = datos.get("seo", {}).get("youtube", {})
    links = """<hr><p style="font-size:0.9em;padding:10px;background:#1a1a24;border-radius:8px;"><strong>Síguenos:</strong> <a href="https://elencuadre.pages.dev">Web</a> | <a href="https://youtube.com/@SomosElEncuadre">YouTube</a> | <a href="https://tiktok.com/@somoselencuadre">TikTok</a></p>"""

    posts_en_cola = []

    # AGENTE 1: ARTÍCULO
    print("  → Agente 1: Preparando Artículo Maestro...")
    posts_en_cola.append({"slug": "master", "titulo": f"El Encuadre — Análisis de medios {fecha}", "html": articulo + links})

    # AGENTE 2: HUB VÍDEO
    print("  → Agente 2: Generando Hub de Vídeo...")
    ctx_video = f"ARTÍCULO:\n{articulo}\n\nSEO YOUTUBE:\n{json.dumps(seo, ensure_ascii=False)}"
    prompt_video = "Eres un crítico de cine. Escribe un post HTML de 3 párrafos analizando por qué este vídeo es importante. Tono: intrigante, cinéfilo."
    r_video = pedir_a_especialista("redactor_seo", prompt_video, contexto=ctx_video)
    posts_en_cola.append({"slug": "video", "titulo": f"📺 Vídeo: {seo.get('titulo', fecha)}", "html": _limpiar_html(r_video) + links})
    time.sleep(2)

    # AGENTE 3: CITA BOMBA
    print("  → Agente 3: Generando Cita Bomba...")
    ctx_cita = f"DOSSIER COMPLETO:\n{json.dumps(dossier, ensure_ascii=False)}"
    prompt_cita = "Eres un francotirador mediático. Escribe un post HTML corto (2 párrafos) destrozando la manipulación del día. Tono: mordaz."
    r_cita = pedir_a_especialista("redactor_seo", prompt_cita, contexto=ctx_cita)
    posts_en_cola.append({"slug": "cita", "titulo": f"💣 La Cita Bomba de hoy", "html": f"<blockquote><em>{dossier.get('cita_bomba')}</em></blockquote>" + _limpiar_html(r_cita) + links})
    time.sleep(2)

    # AGENTE 4: TUTORIAL
    print("  → Agente 4: Generando Tutorial...")
    ctx_tuto = f"ANÁLISIS PSICOLÓGICO:\n{dossier.get('analisis_psicologico')}\n\nRELATO:\n{dossier.get('el_relato_oficial')}"
    prompt_tuto = "Eres un profesor de psicología de masas. Escribe un post HTML educativo (3 párrafos) explicando cómo detectar la manipulación del día. Tono: didáctico."
    r_tuto = pedir_a_especialista("redactor_seo", prompt_tuto, contexto=ctx_tuto)
    posts_en_cola.append({"slug": "tutorial", "titulo": f"🕵️ Cómo detectar la manipulación", "html": _limpiar_html(r_tuto) + links})
    time.sleep(2)

    # AGENTE 5: RADAR
    print("  → Agente 5: Generando Radar de Medios...")
    ctx_radar = f"RELATO OFICIAL:\n{dossier.get('el_relato_oficial')}\n\nCONTRA-NARRATIVA:\n{dossier.get('la_contra_narrativa')}"
    prompt_radar = "Eres un analista de inteligencia. Escribe un post HTML (3 párrafos) comparando el relato oficial con la contra-narrativa. Tono: analítico, frío."
    r_radar = pedir_a_especialista("redactor_seo", prompt_radar, contexto=ctx_radar)
    posts_en_cola.append({"slug": "radar", "titulo": f"📰 El Radar: Lo que dicen los medios", "html": _limpiar_html(r_radar) + links})

    # GUARDAR EN COLA
    ahora = datetime.datetime.now()
    cola_actual = []
    if COLA_FILE.exists():
        try: cola_actual = json.loads(COLA_FILE.read_text())
        except: cola_actual = []

    for i, post in enumerate(posts_en_cola):
        # Publicar cada 3 horas (empezando 1 hora después del maestro)
        hora_pub = (ahora + datetime.timedelta(hours=1 + i*3)).isoformat()
        filename = _guardar_post_en_cola(fecha, post["slug"], post["titulo"], post["html"])
        cola_actual.append({
            "tipo": "blogger",
            "fecha": fecha,
            "filename": filename,
            "hora_publicacion": hora_pub,
            "publicado": False
        })
    
    COLA_FILE.write_text(json.dumps(cola_actual, indent=2))
    print(f"\n[blogger] ✅ {len(posts_en_cola)} posts en cola (se publicarán cada 3h).")

if __name__ == "__main__":
    generar_blogs(sys.argv[1] if len(sys.argv) > 1 else None)
