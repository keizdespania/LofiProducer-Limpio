"""fase2_produccion.py - Generación de contenido con Escaleta Editorial Top-1."""
import json, pathlib, datetime, re, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

# ─── UTILIDADES ───
def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.I).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    for m in sorted(re.findall(r'\{.*?\}', texto, re.DOTALL), key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def _limpiar_html(texto):
    if not texto: return ""
    return re.sub(r'```(?:html|json)?', '', texto, flags=re.I).replace('```', '').strip()

# ─── CLASIFICADOR EDITORIAL ───
def _clasificar_noticia(n):
    t = (n.get("titular","") + " " + n.get("extracto","")).lower()
    # LISTA NEGRA BRUTAL (Si contiene alguna de estas, se descarta)
    BASURA = [
        "balón", "balon", "mbappé", "blocus", "futbol", "fútbol", "pucela", "racing", "athletic", "real madrid", "barça",
        "muere", "muerte", "fallece", "fallecimiento", "suicidio", "accidente", "detenido", "detenida", "policía", "policia", "guardia civil", 
        "intocable", "cine", "cineasta", "película", "pelicula", "actor", "actriz", "prensa rosa", "corazón", "corazon", "boda", "divorcio",
        "bustamante", "triguero", "concierto", "música", "musica", "alcalá norte", "dgt", "tráfico", "trafico", "tiempo", "lluvia", "temperatura"
    ]
    if any(x in t for x in BASURA):
        return "BASURA"
        
    # CLASIFICACIÓN TEMÁTICA
    if any(x in t for x in ["puente", "dimitir", "ave", "lzb", "señaliz", "atocha", "adif", "renfe", "gobierno", "sánchez"]):
        return "PUENTE"
    if any(x in t for x in ["rusia", "polonia", "onu", "sáhara", "sahara", "machado", "venezuela", "zelenski", "putin"]):
        return "INTERNACIONAL"
    if any(x in t for x in ["economía", "economia", "presupuesto", "banco", "inflación", "pensión", "pension", "seguridad social"]):
        return "ECONOMIA"
    return "SOCIEDAD"

def _generar_escena(num, instruccion, contexto_noticia=""):
    prompt = (
        f"Genera la escena {num} del guion. {instruccion} "
        "Devuelve SOLO un JSON válido: "
        '{"id": ' + str(num) + ', "texto": "Tu narración de 80-100 palabras", '
        '"concepto_visual": "English prompt for SDXL", '
        '"mood_musical": "tension|epico|inspirador|relax|misterio|electronico", '
        '"tipo_visual": "imagen"}'
    )
    ctx = f"NOTICIA DEL DÍA:\n{contexto_noticia}" if contexto_noticia else ""
    
    for intento in range(3):
        resp = pedir_a_especialista("guionista_youtube_experto", prompt, contexto=ctx, proveedor="auto")
        d = _parse_json_seguro(resp)
        if d and isinstance(d, dict) and "texto" in d and len(d["texto"].split()) > 20:
            # Limpiar "El El", "La La", etc.
            d["texto"] = re.sub(r'\b(El|La|Los|Las)\s+\1\b', r'\1', d["texto"], flags=re.IGNORECASE)
            return d
        print(f"      Reintento {intento+1}/3 escena {num}...", flush=True)
        time.sleep(2)
    
    return {"id": num, "texto": f"Error generando la escena {num}.", "concepto_visual": "newspaper abstract, cinematic", "mood_musical": "tension", "tipo_visual": "imagen"}

# ─── FLUJO PRINCIPAL ───
def producir_fase2(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    dossier_file = OUT / f"dossier_{fecha}.json"
    if not dossier_file.exists():
        print(f"❌ No existe {dossier_file}"); return None

    datos = json.loads(dossier_file.read_text())
    res = {"fecha": fecha, "dossier": datos.get("dossier", {})}
    
    # Cargar scrapeado + enriquecido para guion con datos REALES
    scrapeado_path = OUT / f"scrapeado_{fecha}.json"
    scrapeado = json.loads(scrapeado_path.read_text()) if scrapeado_path.exists() else {}
    
    enr_path = OUT / f"dossier_{fecha}_enriquecido.json"
    enr_por_medio = {}
    if enr_path.exists():
        d_enr = json.loads(enr_path.read_text())
        desglose = d_enr.get("dossier", {}).get("desglose_medios", "")
        for line in desglose.split("\n"):
            m = re.match(r"\*\*([^*]+)\*\*: '([^']*)' -> \*\*Framing:\*\* ([^|]+) \| \*\*Técnica:\*\* ([^|]+) \| \*\*Omite:\*\* (.+)", line)
            if m:
                enr_por_medio[m.group(1).strip()] = {
                    "titular": m.group(2).strip(),
                    "framing": m.group(3).strip(),
                    "tecnica": m.group(4).strip(),
                    "omite": m.group(5).strip(),
                }
    print(f"   Guion enriquecido: {len(scrapeado)} scrapeados, {len(enr_por_medio)} con tecnica", flush=True)

    # 1. REDACTOR (Artículo para el blog)
    print("[fase2] 1/5 Arquitecto + Redactor...", flush=True)
    ctx = json.dumps({"dossier": datos.get("dossier", {}), "hooks": datos.get("guiones", {}).get("hooks_totales", [])[:5]}, ensure_ascii=False)
    esqueleto = _parse_json_seguro(pedir_a_especialista("arquitecto_contenido", "Crea el esqueleto del artículo.", contexto=ctx[:3000]))
    
    _PROMPT_REDACTOR = (
        'Escribe un artículo periodístico mordaz y directo de 1200 palabras en MARKDOWN PLANO. '
        'PROHIBIDO HTML. Tono: auditor cabreado que expone la manipulación mediática.'
    )
    articulo = pedir_a_especialista("redactor_blog", _PROMPT_REDACTOR, contexto=f"ESQUELETO:\n{json.dumps(esqueleto)}\n\nDOSSIER:\n{ctx[:3000]}")
    articulo = _limpiar_html(articulo)
    res["articulo_html"] = articulo
    res["esqueleto"] = esqueleto

    # 2. GUIONISTA (Escaleta Editorial Top-1)
    print("[fase2] 2/5 Guionista: Escaleta Editorial (4 bloques)...", flush=True)
    
    # Fecha de publicación dinámica
    ahora = datetime.datetime.now()
    pub = (datetime.date.today() + datetime.timedelta(days=1)) if ahora.hour >= 18 else datetime.date.today()
    meses = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
    fecha_str = f"{pub.day} de {meses[pub.month]} de {pub.year}"
    print(f"   Fecha publicacion: {fecha_str}", flush=True)

    # Leer top16 del análisis (con aduana)
    top16 = []
    af = OUT / f"analisis_fase1_{fecha}.json"
    if af.exists():
        top16 = json.loads(af.read_text()).get("top16", [])
    
    # Clasificar en bloques editoriales
    bloques = {"PUENTE": [], "INTERNACIONAL": [], "ECONOMIA": [], "SOCIEDAD": []}
    vistos = set()
    for n in top16:
        if n["titular"] in vistos: continue
        vistos.add(n["titular"])
        cat = _clasificar_noticia(n)
        if cat == "BASURA": continue
        if len(bloques[cat]) < 5:
            bloques[cat].append(n)

    escenas = []
    num = 1

    # Escena 1: Intro asesina
    print(f"   [Escena {num}/18] Intro...", flush=True)
    _tema_principal = top16[0].get("titular", "la manipulación mediática") if top16 else "la actualidad"
    intro_inst = (
        f"Empieza con un golpe de efecto brutal. Luego di: 'Somos El Encuadre y hoy, {fecha_str}, abrimos la cloaca mediática'. "
        f"Después, di EXACTAMENTE: 'Hoy analizamos cómo los medios manipulan la actualidad, empezando por esta noticia: {_tema_principal}'. "
        "Suelta una promesa de lo que van a aprender (ej: 'Te voy a enseñar las 3 técnicas que han usado hoy para que no pienses'). "
        "Cierra con: 'Quedate, porque esto te va a volar la cabeza'."
    )
    escenas.append(_generar_escena(num, intro_inst)); num += 1

    # Juntar todas las noticias limpias
    noticias_limpias = bloques["PUENTE"] + bloques["INTERNACIONAL"] + bloques["ECONOMIA"] + bloques["SOCIEDAD"]
    
    # Bucle blindado: queremos exactamente las escenas de la 2 a la 17
    for n in noticias_limpias:
        if num > 17: break # Si ya hemos llegado a la 17, salimos al cierre (18)

        # Enriquecer con datos REALES del scrapeado + enriquecido
        medio = n.get('medio', '?')
        scr = scrapeado.get(medio, {})
        enr = enr_por_medio.get(medio, {})

        titular_real = scr.get("titular", n['titular'])
        texto_real = scr.get("texto_completo", "")[:1500]
        tecnica = enr.get("tecnica") or "Framing editorial"
        framing = enr.get("framing", "")
        omite = enr.get("omite", "")

        # Extraer cita textual
        citas = re.findall(r'[«"]([^»"]{40,200})[»"]', texto_real)
        citas_validas = [c for c in citas if c.strip() and len(c.strip()) > 40]
        cita_real = citas_validas[0] if citas_validas else (texto_real[:150] + "..." if texto_real else "Sin cita disponible")

        ctx_n = f"""Medio: {medio}
TITULAR REAL: «{titular_real}»
TECNICA DETECTADA: {tecnica}
FRAMING: {framing}
QUE OMITE: {omite}
CITA TEXTUAL: "{cita_real}"
EXTRACTO: {texto_real[:800]}
"""

        # Escena 1 de la noticia
        print(f"   [Escena {num}/18] Analisis (1/2): {titular_real[:40]}...", flush=True)
        inst1 = f"""Escena de analisis del medio '{medio}'.
INSTRUCCIONES OBLIGATORIAS:
1. Empieza LITERALMENTE con: {medio} titulo: «{titular_real}»
2. Luego explica que te intentan vender (usa la CITA TEXTUAL del contexto)
3. Tono mordaz tipo Inaki Gabilondo con mala leche
4. Minimo 80 palabras. NO inventes datos, usa el contexto."""

        escenas.append(_generar_escena(num, inst1, ctx_n)); num += 1

        if num > 17: break # Comprobación antes de la segunda escena

        # Escena 2 de la noticia
        print(f"   [Escena {num}/18] Analisis (2/2): tecnica {tecnica}...", flush=True)
        inst2 = f"""Analiza la TECNICA DE MANIPULACION del medio '{medio}'.
INSTRUCCIONES OBLIGATORIAS:
1. Di LITERALMENTE el nombre de la tecnica: «{tecnica}»
2. Explica COMO funciona (usa la cita del contexto)
3. Di QUE OMITE el medio: {omite}
4. Cierra con 'quien se rie de fondo?' (auditor cabreado)
5. Minimo 80 palabras"""

        escenas.append(_generar_escena(num, inst2, ctx_n)); num += 1

    # FALLBACK: Si nos hemos quedado cortos (menos de 17 escenas), rellenamos con análisis de técnicas
    while num <= 17:
        print(f"   [Escena {num}/18] Relleno (Análisis de Técnica)...", flush=True)
        tecnica = "cortina de humo" if num % 2 == 0 else "hombre de paja"
        inst_fill = f"Haz una escena analizando la técnica de manipulación '{tecnica}'. Explica cómo los medios la usan hoy. Tono mordaz."
        escenas.append(_generar_escena(num, inst_fill, "Análisis genérico de técnicas de manipulación")); num += 1

    # Escena 18: Cierre épico
    print(f"   [Escena 18/18] Cierre...", flush=True)
    cierre_inst = (
        "Cierre épico y demoledor. Haz una arenga: 'Mañana los mismos medios volverán a intentarlo. "
        "La única diferencia es que ahora ya sabes lo que están haciendo'. "
        "Termina con un CTA: 'Dale a like, suscríbete, o comparte este video con ese amigo que todavía se cree la tele'."
    )
    escenas.append(_generar_escena(18, cierre_inst))

    res["escenas"] = escenas
    res["texto_voz_largo"] = " ".join([e.get("texto", "") for e in escenas])
    res["palabras_totales"] = len(res["texto_voz_largo"].split())

    # 3. DJ MUSICAL: Omitido (Lofi continuo)
# 4. VIRALIDAD
    print("[fase2] 4/5 Calculando viralidad...", flush=True)
    viral = _parse_json_seguro(pedir_a_especialista("predictor_viralidad", "Puntua 0-100. Devuelve SOLO JSON con 'score'.", contexto=str(res)[:3000], proveedor="auto"))
    if not viral or "score" not in viral:
        viral = {"score": 75, "razon": "Fallback"}
    res["viralidad"] = viral

    # 5. GENERAR SHORTS FINALES (4 shorts multi-ángulo)
    print("[fase2] 5/5 Generando 4 shorts finales...", flush=True)
    tipos_short = ["dato", "contradiccion", "prediccion", "tutorial"]
    hooks_base = [
        str(res.get("dossier", {}).get("titular_brutal", "") or ""),
        str(res.get("dossier", {}).get("resumen_ejecutivo", "") or ""),
        str(res.get("dossier", {}).get("citas_bomba", "") or ""),
        str(res.get("dossier", {}).get("conclusion", "") or ""),
    ]
    shorts_finales = []
    for i, tipo in enumerate(tipos_short, 1):
        try:
            print(f"   [Short {i}/4] Generando guion ({tipo})...", flush=True)
            hook_ctx = str(hooks_base[i-1] if i-1 < len(hooks_base) and hooks_base[i-1] else res.get("dossier", {}).get("titular_brutal", "") or "")
            prompt = (
                f"Eres guionista de shorts de 'El Encuadre'. Tu misión es desmontar la manipulación mediática. "
                f"Tipo: {tipo}. Contexto: '{hook_ctx[:200]}'. "
                "Escribe 50-60 palabras para un short de 40 segundos. "
                "Empieza con pregunta que despierte curiosidad. "
                "Menciona el medio y la técnica de manipulación. "
                "TERMINA EXACTAMENTE con: 'Somos El Encuadre, analistas de la manipulación. Suscríbete para más'. "
                "Sin markdown, sin acotaciones, sin comillas."
            )
            guion = pedir_a_especialista("guionista_retencion_v2", prompt, contexto=hook_ctx[:500], proveedor="auto")
            if not guion or len(guion.split()) < 20:
                # Fallback mínimo
                guion = f"¿Sabes cómo {tipo} los medios manipulan la información? {hook_ctx[:100]}... Somos El Encuadre, analistas de la manipulación. Suscríbete para más."
            # Limpiar
            import re as _re
            guion = _re.sub(r'\[[^\]]*\]', '', guion)
            guion = _re.sub(r'\s+', ' ', guion).strip()
            # Truncar a 50 palabras
            palabras = guion.split()
            if len(palabras) > 50:
                guion = " ".join(palabras[:50]) + "..."
            shorts_finales.append({
                "tipo": tipo,
                "guion": guion,
                "hook": hook_ctx[:100] if hook_ctx else guion[:100],
            })
            print(f"      ✅ {len(guion.split())} palabras", flush=True)
        except Exception as _e:
            print(f"      ⚠️ Short {i} falló: {_e}", flush=True)

    res["shorts_finales"] = shorts_finales
    print(f"[fase2] ✅ {len(shorts_finales)} shorts finales generados", flush=True)

    # GUARDAR
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    producir_fase2(sys.argv[1] if len(sys.argv) > 1 else None)
