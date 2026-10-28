"""generar_redes.py - Genera textos SEO específicos para cada red social."""
import sys, json, pathlib, datetime, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    matches = re.findall(r'\{.*?\}', texto, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def generar_redes(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists():
        print("❌ No hay producción"); return
    
    datos = json.loads(prod_file.read_text())
    dossier = datos.get("dossier", {})
    guiones = datos.get("guiones", {})
    hooks = guiones.get("hooks_totales", [])
    shorts = datos.get("shorts_finales", [])[:4]
    web_url = "https://elencuadre.pages.dev"
    
    ctx = json.dumps({"dossier": dossier, "hooks": hooks[:5], "shorts": shorts}, ensure_ascii=False)
    
    prompt = f"""
    Genera un JSON estricto con una lista llamada "shorts" con 4 objetos (uno por cada short).
    Para cada short, genera el SEO y los copys para TODAS las plataformas. 
    REGLA DE ORO: No pongas enlaces de una red social dentro de su propia red. AÑADE SIEMPRE un CTA a la newsletter: 'Suscribete al boletin en elencuadre.pages.dev/newsletter' (ej. no pongas link de TikTok en el texto de TikTok).
    Usa esta estructura exacta:
    {{
      "shorts": [
        {{
          "id": "short_1",
          "newsletter": {{ "asunto": "Asunto del email", "hook": "Hook breve", "cta": "Lee el analisis completo en elencuadre.pages.dev" }}, "youtube": {{ "titulo": "Título SEO (max 60 chars)", "descripcion": "Descripción con enlaces a {web_url} y redes", "primer_comentario": "Llamada a la acción con enlace a {web_url}", "tags": ["tag1", "tag2"] }},
          "tiktok": {{ "texto": "Texto persuasivo con gancho", "hashtags": "#fyp #parati #medios #psicologia" }},
          "instagram": {{ "texto": "Texto emocional", "hashtags": "#medios #sesgo #manipulacion", "primer_comentario": "Enlace a {web_url}" }},
          "x": {{ "texto": "Tuit de 280 chars con gancho y enlace a {web_url}" }},
          "threads": {{ "texto": "Texto para Threads con enlace a {web_url}" }},
          "blogger": {{ "titulo": "Título atractivo para Blogger", "resumen": "Resumen de 2 frases" }}
        }}
      ]
    }}
    Devuelve SOLO el JSON.
    """
    
    print("[redes] Generando copys definitivos con el LLM...", flush=True)
    r = pedir_a_especialista("redactor_seo", prompt, contexto=ctx[:3000])
    data = _parse_json_seguro(r)
    
    if data.get("shorts"):
        (OUT / f"redes_{fecha}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"✅ Copys generados en redes_{fecha}.json")
    else:
        print("⚠️ Fallback: usando hooks del dossier...")
        fallback = {"shorts": []}
        for i, s in enumerate(shorts):
            hook = hooks[i].get("hook", "Análisis del día") if i < len(hooks) else "Análisis del día"
            fallback["shorts"].append({
                "id": f"short_{i+1}",
                "youtube": {"titulo": hook[:60], "descripcion": f"Análisis: {hook[:100]}. Más en {web_url}", "primer_comentario": f"Lee el análisis completo: {web_url}", "tags": ["medios", "sesgo"]},
                "tiktok": {"texto": hook[:150], "hashtags": "#fyp #parati #medios"},
                "instagram": {"texto": hook[:150], "hashtags": "#medios #psicologia", "primer_comentario": f"Link en bio: {web_url}"},
                "x": {"texto": f"{hook[:200]}... Lee más: {web_url}"},
                "threads": {"texto": f"{hook[:200]}... Hilo completo: {web_url}"},
                "blogger": {"titulo": hook[:50], "resumen": hook[:150]}
            })
        (OUT / f"redes_{fecha}.json").write_text(json.dumps(fallback, indent=2, ensure_ascii=False))
        print("✅ Fallback guardado.")

if __name__ == "__main__":
    generar_redes(sys.argv[1] if len(sys.argv) > 1 else None)
