"""generar_blogs_blogger.py - 5 Agentes generan 5 posts con todo el contexto."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista
from publicar_blogger import publicar

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _limpiar_html(texto):
    if not texto: return ""
    t = re.sub(r'```(?:html|json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    return t

def generar_blogs(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists():
        print(f"❌ No existe {prod_file}"); return
    
    datos = json.loads(prod_file.read_text())
    dossier = datos.get("dossier", {})
    articulo = datos.get("articulo_html", "")
    seo = datos.get("seo", {}).get("youtube", {})
    
    links = """<hr><p style="font-size:0.9em;padding:10px;background:#1a1a24;border-radius:8px;"><strong>Síguenos:</strong> <a href="https://elencuadre.pages.dev">Web</a> | <a href="https://youtube.com/@SomosElEncuadre">YouTube</a> | <a href="https://tiktok.com/@somoselencuadre">TikTok</a> | <a href="https://instagram.com/somoselencuadre">Instagram</a> | <a href="https://x.com/somoselencuadre">X</a> | <a href="https://threads.net/@somoselencuadre">Threads</a></p>"""

    posts_a_publicar = []

    # ==========================================
    # AGENTE 1: EL ARTÍCULO MAESTRO (Sin LLM, ya existe)
    # ==========================================
    print("  → Agente 1: Preparando Artículo Maestro...")
    posts_a_publicar.append({
        "titulo": f"El Encuadre — Análisis de medios {fecha}",
        "html": articulo + links
    })
    time.sleep(1)

    # ==========================================
    # AGENTE 2: EL CRÍTICO DE CINE (Hub de Vídeo)
    # ==========================================
    print("  → Agente 2: Generando Hub de Vídeo (con contexto completo)...")
    ctx_video = f"ARTÍCULO:\n{articulo}\n\nSEO YOUTUBE:\n{json.dumps(seo, ensure_ascii=False)}"
    prompt_video = "Eres un crítico de cine. Escribe un post HTML de 3 párrafos analizando por qué este vídeo es importante. Usa el artículo y el SEO como contexto. Tono: intrigante, cinéfilo."
    r_video = pedir_a_especialista("redactor_seo", prompt_video, contexto=ctx_video)
    posts_a_publicar.append({
        "titulo": f"📺 Vídeo: {seo.get('titulo', fecha)}",
        "html": _limpiar_html(r_video) + links
    })
    time.sleep(2)

    # ==========================================
    # AGENTE 3: EL FRANCOTIRADOR (Cita Bomba)
    # ==========================================
    print("  → Agente 3: Generando Cita Bomba (con dossier completo)...")
    ctx_cita = f"DOSSIER COMPLETO:\n{json.dumps(dossier, ensure_ascii=False)}"
    prompt_cita = "Eres un francotirador mediático. Escribe un post HTML corto pero letal (2 párrafos) destrozando la manipulación del día. Usa la cita bomba y el sarcasmo del dossier. Tono: mordaz, Hunter S. Thompson."
    r_cita = pedir_a_especialista("redactor_seo", prompt_cita, contexto=ctx_cita)
    posts_a_publicar.append({
        "titulo": f"💣 La Cita Bomba de hoy",
        "html": f"<blockquote><em>{dossier.get('cita_bomba')}</em></blockquote>" + _limpiar_html(r_cita) + links
    })
    time.sleep(2)

    # ==========================================
    # AGENTE 4: EL PROFESOR (Tutorial)
    # ==========================================
    print("  → Agente 4: Generando Tutorial (con análisis psicológico completo)...")
    ctx_tuto = f"ANÁLISIS PSICOLÓGICO:\n{dossier.get('analisis_psicologico')}\n\nRELATO:\n{dossier.get('el_relato_oficial')}"
    prompt_tuto = "Eres un profesor de psicología de masas. Escribe un post HTML educativo (3 párrafos) explicando cómo detectar la manipulación del día. Usa el análisis psicológico y el relato. Tono: didáctico, claro, con ejemplos."
    r_tuto = pedir_a_especialista("redactor_seo", prompt_tuto, contexto=ctx_tuto)
    posts_a_publicar.append({
        "titulo": f"🕵️ Cómo detectar la manipulación",
        "html": _limpiar_html(r_tuto) + links
    })
    time.sleep(2)

    # ==========================================
    # AGENTE 5: EL ANALISTA DE INTELIGENCIA (Radar)
    # ==========================================
    print("  → Agente 5: Generando Radar de Medios (con relato y contra-narrativa)...")
    ctx_radar = f"RELATO OFICIAL:\n{dossier.get('el_relato_oficial')}\n\nCONTRA-NARRATIVA:\n{dossier.get('la_contra_narrativa')}"
    prompt_radar = "Eres un analista de inteligencia. Escribe un post HTML (3 párrafos) comparando el relato oficial de los medios con la contra-narrativa. Tono: analítico, frío, revelador."
    r_radar = pedir_a_especialista("redactor_seo", prompt_radar, contexto=ctx_radar)
    posts_a_publicar.append({
        "titulo": f"📰 El Radar: Lo que dicen los medios",
        "html": _limpiar_html(r_radar) + links
    })

    # PUBLICACIÓN
    blog_id = None
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("EL_ENCUADRE_BLOG_ID="):
            blog_id = line.split("=",1)[1].strip()

    print(f"\n[blogger] Publicando {len(posts_a_publicar)} posts en Blogger...", flush=True)
    for i, post in enumerate(posts_a_publicar):
        print(f"  → Publicando {i+1}/5: {post.get('titulo')[:40]}...")
        try:
            res = publicar(post.get("titulo"), post.get("html"), blog_id=blog_id)
            print(f"     {res[:100]}...")
        except Exception as e:
            print(f"     ❌ Error: {e}")

if __name__ == "__main__":
    generar_blogs(sys.argv[1] if len(sys.argv) > 1 else None)
