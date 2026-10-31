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
    intro_inst = (
        f"Empieza con un golpe de efecto brutal. Luego di: 'Somos El Encuadre y hoy, {fecha_str}, abrimos la cloaca mediática'. "
        "Suelta una promesa de lo que van a aprender. "
        "Cierra con: 'Quedate, porque esto te va a volar la cabeza'."
    )
    escenas.append(_generar_escena(num, intro_inst)); num += 1

    # Juntar todas las noticias limpias en una sola lista
    noticias_limpias = bloques["PUENTE"] + bloques["INTERNACIONAL"] + bloques["ECONOMIA"] + bloques["SOCIEDAD"]
    
    # Si tenemos menos de 16 noticias, duplicamos el análisis (2 escenas por noticia)
    # Ejemplo: Escena A -> El titular y la máscara. Escena B -> La técnica y el beneficiario.
    if len(noticias_limpias) < 16:
        print(f"   ⚠️ Solo {len(noticias_limpias)} noticias limpias. Haciendo 2 escenas por noticia para llegar a 18.", flush=True)
        for n in list(noticias_limpias):
            if num >= 17: break
            print(f"   [Escena {num}/18] Análisis Profundo (1/2): {n['titular'][:30]}...", flush=True)
            ctx_n = f"Medio: {n.get('medio', '?')}\nTitular: {n['titular']}\nExtracto: {n.get('extracto', '')[:200]}"
            inst1 = f"Analiza el titular y la máscara del medio '{n.get('medio','?')}': '{n['titular']}'. ¿Qué te intentan vender? Tono mordaz."
            escenas.append(_generar_escena(num, inst1, ctx_n)); num += 1
            
            if num >= 17: break
            print(f"   [Escena {num}/18] Análisis Profundo (2/2): {n['titular'][:30]}...", flush=True)
            inst2 = f"Analiza la técnica de manipulación y el beneficiario de '{n['titular']}'. ¿Quién se ríe de fondo? Tono de auditor cabreado."
            escenas.append(_generar_escena(num, inst2, ctx_n)); num += 1
    else:
        # Si tenemos 16 o más, hacemos 1 escena por noticia
        for n in noticias_limpias:
            if num >= 18: break
            print(f"   [Escena {num}/18] Noticia: {n['titular'][:30]}...", flush=True)
            ctx_n = f"Medio: {n.get('medio', '?')}\nTitular: {n['titular']}\nExtracto: {n.get('extracto', '')[:200]}"
            inst = f"Analiza la manipulación del medio '{n.get('medio','?')}' en el titular '{n['titular']}'. Tono de auditor cabreado."
            escenas.append(_generar_escena(num, inst, ctx_n)); num += 1

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

    # GUARDAR
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase2] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    producir_fase2(sys.argv[1] if len(sys.argv) > 1 else None)
