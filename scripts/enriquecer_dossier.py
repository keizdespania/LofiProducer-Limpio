"""enriquecer_dossier.py - Enriquece desglose_medios sin tocar el pipeline.
NO modifica el dossier original. Genera dossier_{fecha}_enriquecido.json.
"""
import sys, json, pathlib, datetime, re, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))
from especialistas import pedir_a_especialista

FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Lista cerrada de técnicas del glosario de El Encuadre (51)
# Cada entrada: nombre normalizado + keywords para fallback heurístico
TECNICAS_GLOSARIO = {
    "Framing": ["encuadre", "selección", "prominente", "marco"],
    "Anchoring": ["dato inicial", "cifra", "ancla", "primer dato", "millones"],
    "Omisión": ["no menciona", "no dice", "silencia", "omite", "sin mencionar"],
    "Agenda-setting": ["agenda", "de qué hablar", "prioriza", "destaca"],
    "Priming": ["estímulo previo", "prepara", "predispone"],
    "Bandwagon": ["todos", "mayoría", "todo el mundo", "efecto arrastre"],
    "Testimonial": ["famoso", "celebridad", "conocido", "estrella"],
    "Transfer": ["asocia", "vincula", "respeto", "prestigio ajeno"],
    "Card Stacking": ["solo datos", "solo cifras", "baraja", "selección de datos"],
    "Glittering Generalities": ["palabras bonitas", "libertad", "progreso", "esperanza"],
    "Name Calling": ["etiqueta", "descalifica", "insulta", "califica"],
    "Plain Folks": ["pueblo", "gente", "como tú", "cercano", "sencillo"],
    "Fear Appeal": ["miedo", "alerta", "peligro", "amenaza", "catástrofe"],
    "Scarcity": ["escaso", "última oportunidad", "solo quedan", "urgente"],
    "Confirmation Bias": ["confirma", "creencias", "ya lo sabía"],
    "Halo Effect": ["brilla", "bueno en todo", "ejemplar", "referente"],
    "Availability Heuristic": ["recuerdas", "vivido", "impactante", "memorable"],
    "Dunning-Kruger": ["no sabe", "ignorante", "experto improvisado"],
    "Sunk Cost": ["ya invertido", "no abandonar", "seguir"],
    "Gambler's Fallacy": ["ya toca", "por probabilidad", "racha"],
    "Authority Bias": ["autoridad", "experto", "según", "fuentes", "informe", "estudio"],
    "In-group Bias": ["los nuestros", "nosotros", "afines", "grupo"],
    "Negativity Bias": ["negativo", "trágico", "dramático", "catastrofista"],
    "Recency Bias": ["último", "reciente", "ayer", "hoy"],
    "Illusory Truth Effect": ["repite", "insiste", "vuelve a decir", "otra vez"],
    "Bait-and-Switch": ["promete", "luego da", "cambia", "desvía"],
    "False Dilemma": ["o esto o", "solo dos", "either", "uno u otro"],
    "Slippery Slope": ["llevará a", "desastre", "pendiente", "consecuencia"],
    "Straw Man": ["caricatura", "exagera", "títere", "versión ridícula"],
    "Appeal to Emotion": ["emoción", "corazón", "sentimiento", "indignación"],
    "Ad Hominem": ["ataque personal", "descalifica a la persona", "insulto"],
    "Cherry Picking": ["cerezas", "solo lo que conviene", "selecciona datos"],
    "Tu Quoque": ["tú también", "y tú más", "lo mismo"],
    "Load Ad": ["pregunta cargada", "asume", "ya implica"],
    "Questioning": ["pregunta repetida", "insiste", "cuestiona"],
    "Overton Window": ["ventana", "aceptable", "lo que se puede decir"],
    "Manufacturing Consent": ["fabricar", "consentimiento", "propaganda"],
    "Diversion": ["desvía", "distrae", "cambia de tema", "cortina de humo"],
    "Gradual Change": ["poco a poco", "gradual", "sin que se note"],
    "Dehumanization": ["menos humano", "animaliza", "cosifica", "horda"],
    "Polarization": ["divide", "dos bandos", "extremos", "polariza"],
    "Emotional Contagion": ["contagia", "emoción colectiva", "multitud"],
    "Crowd Psychology": ["masa", "multitud", "turba"],
    "Suggestion": ["sugiere", "insinúa", "sin decir"],
    "Prestige Effect": ["prestigio", "prestigioso", "renombre"],
    "Repetition": ["repite", "insiste", "machaca"],
    "Assertion": ["afirma sin pruebas", "asegura", "sin evidencia"],
    "Contagion": ["se contagia", "se propaga", "viraliza"],
    "Illusion of Control": ["control", "cree controlar", "ilusión"],
    "Planning Fallacy": ["planifica", "todo saldrá", "optimismo"],
    "Reactance": ["haz lo contrario", "rebeldía", "por llevar la contraria"],
}

def _detectar_tecnica_heuristica(titular, omite):
    """Fallback determinista: detecta técnica del glosario por keywords."""
    texto = f"{titular} {omite}".lower()
    for tecnica, keywords in TECNICAS_GLOSARIO.items():
        if any(k in texto for k in keywords):
            return tecnica
    return "Framing"  # default del glosario

def _extraer_framing_heuristico(titular):
    """Extrae el framing implícito del titular."""
    t = titular.lower()
    if "?" in t or "¿" in t: return "pregunta retórica"
    if any(w in t for w in ["caos", "alerta", "crisis"]): return "alarma"
    if any(w in t for w in ["escudo", "protección", "blindaje"]): return "defensa/justificación"
    if any(w in t for w in ["polemica", "polémica", "escándalo"]): return "confrontación"
    if any(w in t for w in ["según", "fuentes"]): return "atribución"
    return "editorial neutro"

def _titulares_reales(fecha):
    """Extrae {medio: titular} de recoleccion, ignorando None."""
    rec_path = OUT / f"recoleccion_{fecha}.json"
    if not rec_path.exists():
        return {}
    rec = json.loads(rec_path.read_text())
    titulares = {}
    for cat, medios in rec.items():
        if cat == "audios": continue
        if isinstance(medios, dict):
            for medio, noticias in medios.items():
                if isinstance(noticias, list):
                    for n in noticias:
                        if isinstance(n, dict):
                            t = n.get("titular")
                            if t and t not in ("None", "none", "N/A", ""):
                                titulares[medio] = t
                                break
    return titulares

def _analizar_medio_con_llm(medio, noticia, contexto_extra=""):
    """Llama a forense_medios con contexto completo. Devuelve dict o None."""
    # Cruzar con titular real de recoleccion
    titulares = _titulares_reales(FECHA)
    titular_real = titulares.get(medio, "")
    
    if titular_real:
        contexto_titular = f"TITULAR REAL DE {medio} (su noticia específica): «{titular_real}»"
    else:
        contexto_titular = f"(No se capturó el titular de {medio}. Analiza por su línea editorial conocida.)"
    
    prompt = f"""Analiza UN SOLO medio: {medio}
{contexto_titular}
Noticia principal del día (contexto general): {noticia}
{contexto_extra}

Devuelve SOLO un objeto JSON con esta estructura exacta:
{{
  "titular": "el titular del medio (o el que se te da)",
  "palabra_cuchillo": "la palabra que más carga emocional tiene",
  "framing": "el encuadre: defensa, ataque, alarma, confrontación, justificación...",
  "tecnica": "UNA SOLA de estas 50 técnicas específicas (copia el nombre EXACTO, NO uses 'Framing' porque es demasiado genérico): Anchoring, Omisión, Agenda-setting, Priming, Bandwagon, Testimonial, Transfer, Card Stacking, Glittering Generalities, Name Calling, Plain Folks, Fear Appeal, Scarcity, Confirmation Bias, Halo Effect, Availability Heuristic, Dunning-Kruger, Sunk Cost, Gambler's Fallacy, Authority Bias, In-group Bias, Negativity Bias, Recency Bias, Illusory Truth Effect, Bait-and-Switch, False Dilemma, Slippery Slope, Straw Man, Appeal to Emotion, Ad Hominem, Cherry Picking, Tu Quoque, Load Ad, Questioning, Overton Window, Manufacturing Consent, Diversion, Gradual Change, Dehumanization, Polarization, Emotional Contagion, Crowd Psychology, Suggestion, Prestige Effect, Repetition, Assertion, Contagion, Illusion of Control, Planning Fallacy, Reactance",
  "mensaje_real": "qué te quiere hacer sentir el medio (1 frase, con sarcasmo)",
  "omite": "qué información importante omite (1 frase)"
}}

REGLAS: SOLO JSON. Sin markdown. Sin explicaciones antes ni después. Sin "N/A" en los campos."""
    
    try:
        r = pedir_a_especialista("forense_medios", prompt, contexto=noticia[:2000])
        # Parser robusto
        t = re.sub(r'```(?:json)?', '', r or '', flags=re.IGNORECASE).replace('```', '').strip()
        try:
            d = json.loads(t)
        except:
            m = re.search(r'\{.*\}', t, re.DOTALL)
            if m:
                try: d = json.loads(m.group(0))
                except: d = None
            else:
                d = None
        
        if d and isinstance(d, dict):
            # Limpiar markdown residual
            d["tecnica"] = d.get("tecnica", "").strip().strip("*").strip()
            d["framing"] = d.get("framing", "").strip().strip("*").strip()
            # Validar que la técnica está en el glosario
            if d["tecnica"] not in TECNICAS_GLOSARIO:
                # Buscar coincidencia laxa (case-insensitive)
                for t in TECNICAS_GLOSARIO:
                    if t.lower() == d["tecnica"].lower():
                        d["tecnica"] = t
                        break
                else:
                    return None  # técnica inventada
            if not d.get("framing") or d["framing"] == "N/A":
                return None
            # Si el LLM insiste en "Framing" genérico, intentar heurístico específico
            if d["tecnica"] == "Framing":
                # Forzar técnicas más específicas basadas en keywords
                alt_tecnicas = {
                    "Omisión": ["no menciona", "omite", "silencio", "no dice"],
                    "Diversion": ["distrae", "desvía", "cortina"],
                    "Agenda-setting": ["agenda", "prioriza", "destaca"],
                    "Priming": ["prepara", "predispone", "estímulo"],
                    "Authority Bias": ["experto", "fuente", "informe"],
                    "Fear Appeal": ["alerta", "peligro", "miedo", "crisis"],
                    "Name Calling": ["etiqueta", "califica", "insulta"],
                    "Transfer": ["asocia", "vincula", "prestigio"],
                    "Testimonial": ["testigo", "superviviente", "víctima", "protagonista"],
                    "Card Stacking": ["solo datos", "solo cifras", "baraja"],
                }
                titular_lower = (d.get("titular", "") + " " + noticia).lower()
                for alt, kws in alt_tecnicas.items():
                    if any(k in titular_lower for k in kws):
                        d["tecnica"] = alt
                        break
                else:
                    # Si no hay match, dejar Framing pero marcarlo
                    d["tecnica"] = "Framing"
                    d["_framing_generico"] = True
            return d
    except Exception as e:
        print(f"  LLM error {medio}: {e}", flush=True)
    return None

def enriquecer(fecha=None):
    fecha = fecha or FECHA
    dossier_path = OUT / f"dossier_{fecha}.json"
    analisis_path = OUT / f"analisis_fase1_{fecha}.json"
    
    if not dossier_path.exists():
        print(f"❌ No existe {dossier_path}"); return False
    
    dossier = json.loads(dossier_path.read_text())
    analisis = json.loads(analisis_path.read_text()) if analisis_path.exists() else {}
    
    desglose_actual = dossier.get("dossier", {}).get("desglose_medios", "")
    analisis_medios = analisis.get("analisis", {})
    
    print(f"Medios en analisis_fase1: {len(analisis_medios)}")
    print(f"Desglose actual: {len(desglose_actual)} chars")
    
    # Parsear desglose actual (formato "**Medio**: 'titular' -> **Framing:** X | **Técnica:** Y | **Omite:** Z")
    medios_desglose = {}
    for linea in desglose_actual.split("\n"):
        m = re.match(r"\*\*([^*]+)\*\*: '([^']*)' -> (?:\*\*Framing:\*\* [^|]+ \| )?\*\*Técnica:\*\* ([^|]+) \| (?:\*\*Palabra:\*\* ([^|]*) \| )?\*\*Omite:\*\* (.+)", linea)
        if m:
            medio, titular, tecnica, palabra, omite = m.groups()
            # Framing no existe en formato nuevo; derivarlo de la tecnica
            framing = (tecnica or "N/A").strip()
            medios_desglose[medio] = {
                "titular": titular,
                "framing": framing,
                "tecnica": tecnica.strip(),
                "palabra": (palabra or "").strip(),
                "omite": omite.strip(),
            }
    
    print(f"Medios parseados del desglose: {len(medios_desglose)}")
    
    # Detectar los que tienen N/A
    medios_a_enriquecer = []
    for medio, datos in medios_desglose.items():
        if datos["framing"] == "N/A" or datos["tecnica"] == "N/A":
            medios_a_enriquecer.append(medio)
    
    print(f"Medios a enriquecer: {len(medios_a_enriquecer)}")
    print()
    
    # Contexto del top3
    top3 = dossier.get("top3", {})
    noticia_principal = list(top3.values())[0] if isinstance(top3, dict) and top3 else ""
    
    enriquecidos = 0
    for i, medio in enumerate(medios_a_enriquecer, 1):
        print(f"[{i}/{len(medios_a_enriquecer)}] {medio}...", end=" ", flush=True)
        
        datos_actuales = medios_desglose[medio]
        resultado = _analizar_medio_con_llm(medio, noticia_principal)
        
        if resultado:
            medios_desglose[medio] = {
                "titular": resultado.get("titular") or datos_actuales["titular"],
                "framing": resultado.get("framing", "editorial neutro"),
                "tecnica": resultado.get("tecnica", "framing editorial"),
                "omite": resultado.get("omite") or datos_actuales["omite"],
                "mensaje_real": resultado.get("mensaje_real", ""),
                "palabra_cuchillo": resultado.get("palabra_cuchillo", ""),
            }
            enriquecidos += 1
            print("✅ LLM", flush=True)
        else:
            # Fallback heurístico
            framing_h = _extraer_framing_heuristico(datos_actuales["titular"])
            tecnica_h = _detectar_tecnica_heuristica(datos_actuales["titular"], datos_actuales["omite"])
            medios_desglose[medio]["framing"] = framing_h
            medios_desglose[medio]["tecnica"] = tecnica_h
            print(f"⚠️ heurístico ({tecnica_h})", flush=True)
        
        time.sleep(0.5)
    
    # Reconstruir desglose_medios como string
    nuevas_lineas = []
    for medio, datos in medios_desglose.items():
        linea = f"**{medio}**: '{datos['titular']}' -> **Framing:** {datos['framing']} | **Técnica:** {datos['tecnica']} | **Omite:** {datos['omite']}"
        nuevas_lineas.append(linea)
    
    dossier["dossier"]["desglose_medios"] = "\n".join(nuevas_lineas)
    dossier["dossier"]["_enriquecido"] = {
        "fecha": datetime.datetime.now().isoformat(),
        "medios_enriquecidos": enriquecidos,
        "medios_heuristicos": len(medios_a_enriquecer) - enriquecidos,
    }
    
    # Guardar como _enriquecido (NO sobrescribe el original)
    out_path = OUT / f"dossier_{fecha}_enriquecido.json"
    out_path.write_text(json.dumps(dossier, indent=2, ensure_ascii=False))
    
    print()
    print(f"✅ Guardado: {out_path}")
    print(f"   {enriquecidos} con LLM, {len(medios_a_enriquecer) - enriquecidos} heurísticos")
    print(f"   Original intacto: {dossier_path}")
    return True

if __name__ == "__main__":
    sys.exit(0 if enriquecer(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
