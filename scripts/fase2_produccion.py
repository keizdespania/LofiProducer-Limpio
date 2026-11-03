"""fase2_produccion.py - Generación de contenido con Escaleta Editorial Top-1."""
import json, pathlib, datetime, re, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista


# ═══════════════════════════════════════════════════════════════
# LEY DE ESTILO "EL ENCUADRE" v3 (monólogo mordaz tipo Alsina)
# ═══════════════════════════════════════════════════════════════
LEY_ESTILO = """
Eres Carlos Alsina (o Iñaki Gabilondo) para 'El Encuadre'. Monólogo en primera persona, a cámara/micro.

TU VOZ:
- Amigo listo que abre los ojos, NO profesor que da lecciones
- Ironía fina, NO insulto
- Sonrisa amarga, NO risa de chiste
- "Nosotros" cómplice con el oyente
- Frases cortas y secas después de frases largas (ritmo)

LÍNEA EDITORIAL (tu tesis):
- Los medios NO informan, VENDEN una narrativa
- Cada medio vende algo: poder, miedo, urgencia, distracción
- Tu trabajo: desenmascarar QUÉ VENDE cada medio y POR QUÉ
- Cada cierre de bloque: pregunta al oyente "¿A quién beneficia esto?"

PROHIBIDO (fórmulas de IA):
- "Y a mí esto me parece..."
- "Nos hace sentir que..."
- "Así, la audiencia..."
- "Yo, como tu colega..."
- "no te pierdas la siguiente línea"
- "queda pegada al asiento"
- "Resulta que..." (repetido, máximo 1 vez por guion)
- "Mira lo que publicó..." (NUNCA)

BANCO DE FRASES MORDACES (NUNCA repetir la misma en el mismo guion):
1. "Esto no es periodismo, es marketing con teclado."
2. "Qué casualidad que todos..."
3. "Atención al detalle, porque aquí está la trampa."
4. "Y mientras ustedes leen esto, alguien está celebrando."
5. "Esto no se llama informar, se llama vender."
6. "Y ojo, que esto tiene segunda parte."
7. "Vamos a ver si me explico."
8. "No sé si lo han notado, pero..."
9. "Y aquí viene lo bueno."
10. "Permítanme una duda razonable."
11. "Y el premio a la originalidad se lo lleva..."
12. "Titular. Mentira. Otra vez. Y otra."
13. "Señores, esto es una cortina de humo."
14. "Les voy a decir una cosa: esto no se sostiene."
15. "Y ustedes me dirán: hombre, tampoco es para tanto. Pues sí lo es."
16. "Paren las rotativas. Tenemos titular."
17. "Esto es de traca."
18. "Y yo me pregunto: ¿hasta cuándo?"
19. "Lean el titular despacio, que tiene más capas que una cebolla."
20. "Alguien ha decidido que hoy toca esto. Y aquí estamos."

VARIEDAD EN "QUÉ VENDE" (NUNCA repetir el mismo en el mismo guion):
- vende miedo
- vende urgencia
- vende poder
- vende distracción
- vende salvador
- vende culpa
- vende esperanza falsa
- vende indignación
- vende normalidad
- vende caos

PUNCHLINE POR ESCENA (obligatorio, frase corta y única):
Cada escena debe tener UNA punchline corta (5-10 palabras) que se recuerde.
Ejemplos por tipo:
- "Titular. Mentira. Otra vez."
- "Esto no es noticia, es publicidad."
- "Y aquí está el truco."
- "Que se lo crean ellos."
- "Mientras, alguien celebra."
- "Puro marketing."
- "Y nadie pregunta."
- "Blanco y en botella."

RECURSOS PERMITIDOS:
- Comentarios parentéticos: "En un mes hay elecciones en Madrid (no sé si lo ha notado)"
- Pregunta retórica: "¿Tú te has dado cuenta?"
- Ironía como antífrasis: "¡Qué gran favor nos hace X contándonos esto!"
- Hipérbole burlona: "Según X, el horóscopo de Géminis es la noticia más importante del día"
- Set up + punch line: "Feijóo dice que España está en emergencia (set up). Y la emergencia es... que no sabe hacer la casa (punch line)."

EXTENSIÓN: 80-100 palabras. Sin markdown. Sin acotaciones [PAUSA] (silencio). Solo texto hablado.
"""



# ═══════════════════════════════════════════════════════════════
# BANCO DE 100 FRASES MORDACES (el LLM elige NUEVAS cada vez)
# ═══════════════════════════════════════════════════════════════
BANCO_FRASES = [
    "Esto no es periodismo, es marketing con teclado.",
    "Qué casualidad que todos los medios...",
    "Atención al detalle, porque aquí está la trampa.",
    "Y mientras ustedes leen esto, alguien está celebrando.",
    "Esto no se llama informar, se llama vender.",
    "Y ojo, que esto tiene segunda parte.",
    "Vamos a ver si me explico.",
    "No sé si lo han notado, pero...",
    "Y aquí viene lo bueno.",
    "Permítanme una duda razonable.",
    "El premio a la originalidad se lo lleva...",
    "Titular. Mentira. Otra vez. Y otra.",
    "Señores, esto es una cortina de humo.",
    "Les voy a decir una cosa: esto no se sostiene.",
    "Paren las rotativas. Tenemos titular.",
    "Esto es de traca.",
    "Y yo me pregunto: ¿hasta cuándo?",
    "Lean el titular despacio, que tiene capas.",
    "Alguien ha decidido que hoy toca esto.",
    "Y aquí estamos, un día más.",
    "Esto es puro teatro.",
    "Ya estamos con el guion de siempre.",
    "El manual del buen manipulado.",
    "No me digan que no lo han visto venir.",
    "Esto es como el cuento del lobo, pero con más lobos.",
    "Y todos tan tranquilos.",
    "Pasen y vean el circo.",
    "Última hora: el mundo sigue igual, pero con más ruido.",
    "Y ahora, la noticia que no era noticia.",
    "El enésimo titular que no aguanta un análisis.",
    "Señores, tenemos nuevo campeón del titular vacío.",
    "Esto no es información, es ambientación.",
    "Y así nos va.",
    "Un titular, una mentira, y a dormir.",
    "El periodismo se ha ido de vacaciones.",
    "Y el que avisa no es traidor.",
    "Vamos con el clásico: cuanto peor, mejor titular.",
    "Si no hay noticia, se inventa.",
    "Y la verdad, para otro día.",
    "Ya está el de siempre con el mismo cuento.",
    "Esto es como el anuncio de detergente: promete, pero no limpia.",
    "Y mientras, el mundo sigue girando.",
    "Alguien ha decidido que hoy tocaba este susto.",
    "Y ustedes me dirán: hombre, no será para tanto.",
    "Pero sí lo es. Y lo saben.",
    "El titular es el anzuelo, y el lector, el pez.",
    "Esto no es la verdad, es la versión de la verdad.",
    "Y así se escribe la historia.",
    "Pasen, lean, y no pregunten.",
    "Esto es como la sopa de sobre: parece caldo, pero no alimenta.",
    "Y aquí tenemos otro titular de usar y tirar.",
    "No es periodismo, es espectáculo.",
    "Y el que se crea esto, que levante la mano.",
    "La verdad no vende. El susto, sí.",
    "Esto es una fábrica de titulares, no un medio.",
    "Y todos a coro: 'qué barbaridad'.",
    "Mientras, el que manda, tan tranquilo.",
    "Y así hasta mañana.",
    "El circo de siempre, con nuevos payasos.",
    "Esto no es noticia, es guion.",
    "Y ustedes preguntándose: ¿esto es verdad?",
    "Pues claro que no.",
    "Pero se lo han creído.",
    "Y ahí está el negocio.",
    "No me digan que no lo han pensado.",
    "Y aquí viene la parte que no les contaron.",
    "Esto es la letra pequeña del titular.",
    "Y ellos lo saben.",
    "Esto es como los anuncios de teletienda: 'llame ya'.",
    "Y así vamos, de susto en susto.",
    "La verdad, señores, es un bien escaso.",
    "Y aquí, ni se busca.",
    "Esto es más viejo que el hilo negro.",
    "Y todos a repetirlo como loros.",
    "No es periodismo, es una jaula de grillos.",
    "Y así se construye una opinión pública.",
    "Esto es como el gazpacho: todo revuelto y sin sustancia.",
    "Y ustedes, a leerlo.",
    "Esto no se sostiene por ningún lado.",
    "Y sin embargo, ahí está.",
    "Señores, el titular del día.",
    "Y el premio, para los de siempre.",
    "Esto es como la lotería: ilusiona, pero no toca.",
    "Y mientras, el que manda, sonriendo.",
    "Y así se escribe la historia, señores.",
    "No se pierdan el próximo capítulo.",
    "Esto es una tragicomedia.",
    "Y aquí, todos contentos.",
    "Y mientras, la verdad, en un cajón.",
    "Y así, un día más.",
    "Esto es el pan nuestro de cada día.",
    "Y ustedes, a tragar.",
    "Y no pregunten.",
    "Y así, señores, se hace un titular.",
    "Esto es el circo romano, pero con wifi.",
    "Y todos tan felices.",
    "Y aquí está el truco.",
    "Y aquí la verdad, en la letra pequeña.",
    "Y así, señores, hasta el próximo susto.",
    "Y colorín colorado.",
]

# 15 TIPOS DE "QUÉ VENDE"
QUE_VENDE = [
    "miedo", "urgencia", "poder", "distracción", "salvador",
    "culpa", "esperanza falsa", "indignación", "normalidad", "caos",
    "enfado", "nostalgia", "orgullo", "vergüenza", "cansancio",
]

# 50 PUNCHLINES CORTAS (5-10 palabras, para cerrar escena)
PUNCHLINES = [
    "Titular. Mentira. Otra vez.",
    "Esto no es noticia, es publicidad.",
    "Y aquí está el truco.",
    "Que se lo crean ellos.",
    "Mientras, alguien celebra.",
    "Puro marketing.",
    "Y nadie pregunta.",
    "Blanco y en botella.",
    "Y así nos va.",
    "El cuento de siempre.",
    "Y aquí paz, y después gloria.",
    "Y todos a coro.",
    "Y aquí no ha pasado nada.",
    "Esto es el circo.",
    "Y sálvese quien pueda.",
    "Y a otra cosa, mariposa.",
    "Y aquí, tan anchos.",
    "Y ustedes, a tragar.",
    "Y yo, a contarlo.",
    "Y la verdad, en el cajón.",
    "Y así hasta mañana.",
    "Y aquí, todos contentos.",
    "Y mientras, el mundo, girando.",
    "Y ustedes, a leer.",
    "Y aquí, el espectáculo.",
    "Y así se escribe la historia.",
    "Y aquí, sin preguntas.",
    "Y ustedes, a creérselo.",
    "Y así, un día más.",
    "Y el que avisa no es traidor.",
    "Y aquí, el premio.",
    "Y todos, a aplaudir.",
    "Y aquí, la trampa.",
    "Y ustedes, a votar.",
    "Y aquí, el susto.",
    "Y así, todos los días.",
    "Y aquí, el teatro.",
    "Y ustedes, a dormir.",
    "Y aquí, el cuento.",
    "Y así, señores.",
    "Y aquí, la farsa.",
    "Y ustedes, a tragar.",
    "Y aquí, el negocio.",
    "Y así, sin más.",
    "Y aquí, el anzuelo.",
    "Y ustedes, a picar.",
    "Y aquí, el guion.",
    "Y así, una vez más.",
    "Y aquí, el circo.",
    "Y colorín colorado.",
]

class GuionEstado:
    """Memoria del guion en construcción. Anti-repetición + coherencia."""
    def __init__(self):
        self.frases_usadas = set()
        self.que_vende_usado = set()
        self.punchlines_usadas = set()
        self.medios_usados = set()
        self.estructuras_usadas = set()
        self.tecnicas_usadas = set()

    def add_frase(self, frase):
        self.frases_usadas.add(frase)

    def add_que_vende(self, tipo):
        self.que_vende_usado.add(tipo)

    def add_medio(self, medio):
        self.medios_usados.add(medio)

    def frases_disponibles(self):
        """Frases del banco de 100 que aún no se han usado."""
        return [f for f in BANCO_FRASES if f not in self.frases_usadas]

    def punchlines_disponibles(self):
        """Punchlines del banco de 50 que aún no se han usado."""
        return [p for p in PUNCHLINES if p not in self.punchlines_usadas]

    def registrar_usos(self, texto):
        """Escanea el texto generado y registra frases/punchlines/qué vende usados."""
        for frase in BANCO_FRASES:
            if frase in texto:
                self.frases_usadas.add(frase)
        for punch in PUNCHLINES:
            if punch in texto:
                self.punchlines_usadas.add(punch)
        for tipo in QUE_VENDE:
            if f"vende {tipo}" in texto.lower():
                self.que_vende_usado.add(tipo)

    def que_vende_disponibles(self):
        """Tipos de 'qué vende' no usados aún (15 opciones)."""
        return [t for t in QUE_VENDE if t not in self.que_vende_usado]

    def resumen_para_prompt(self):
        """Resumen del estado para pasar al LLM (con 100 frases y 50 punchlines)."""
        frases_disp = self.frases_disponibles()
        punch_disp = self.punchlines_disponibles()
        qv_disp = self.que_vende_disponibles()
        return f"""
ESTADO ACTUAL DEL GUION (NO REPETIR):
- Frases ya usadas: {len(self.frases_usadas)} de 100
- "Qué vende" ya usado: {list(self.que_vende_usado) or "ninguno"}
- Punchlines ya usadas: {len(self.punchlines_usadas)} de 50

FRASES DISPONIBLES (elige 1 NUEVA de estas 10): {frases_disp[:10]}

PUNCHLINES DISPONIBLES (elige 1 NUEVA de estas 10): {punch_disp[:10]}

"QUÉ VENDE" DISPONIBLE (elige 1 NUEVO): {qv_disp[:8]}

REGLA CRÍTICA: USA 1 FRASE + 1 PUNCHLINE + 1 QUÉ VENDE que NO estén ya usados.
"""



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


def _parsear_desglose(desglose_str):
    """Parsea el string de desglose_medios a lista de dicts.
    Formato: **Medio**: 'titular' -> **Framing:** X | **Técnica:** Y | **Omite:** Z
    """
    if not desglose_str:
        return []
    medios = []
    # Buscar bloques **Medio**: ...
    patron = r'\*\*([^*]+)\*\*:\s*[\'"«]([^\'"»]+)[\'"»]\s*->\s*\*\*Framing:\*\*\s*([^|]+)\|\s*\*\*Técnica:\*\*\s*([^|]+)\|\s*\*\*Omite:\*\*\s*(.+?)(?=\n\*\*|$)'
    for m in re.finditer(patron, desglose_str, re.DOTALL):
        medios.append({
            "medio": m.group(1).strip(),
            "titular": m.group(2).strip(),
            "framing": m.group(3).strip(),
            "tecnica": m.group(4).strip(),
            "omite": m.group(5).strip()[:200],
        })
    return medios

def _extraer_medios_unicos(top16, desglose_medios):
    """Combina top16 (titulares reales) + desglose (técnicas) → lista única por medio."""
    medios_dict = {}
    # Primero del desglose (tiene técnica + omite)
    for m in _parsear_desglose(desglose_medios):
        medios_dict[m["medio"]] = {
            "medio": m["medio"],
            "titular": m["titular"],
            "tecnica": m["tecnica"],
            "framing": m["framing"],
            "omite": m["omite"],
            "extracto": "",
        }
    # Luego de top16 (si no está, añadir)
    for t in top16:
        medio = t.get("medio", "")
        if not medio or medio in medios_dict:
            continue
        medios_dict[medio] = {
            "medio": medio,
            "titular": t.get("titular", ""),
            "tecnica": "Framing editorial",
            "framing": "",
            "omite": "",
            "extracto": t.get("extracto", ""),
        }
    # Añadir extractos a los que ya estaban
    for t in top16:
        medio = t.get("medio", "")
        if medio in medios_dict and not medios_dict[medio]["extracto"]:
            medios_dict[medio]["extracto"] = t.get("extracto", "")
    return list(medios_dict.values())

def _tecnicas_unicas(medios):
    """Saca las técnicas únicas (no repetir)."""
    tecnicas = []
    for m in medios:
        t = m.get("tecnica", "").strip()
        if t and t not in tecnicas:
            tecnicas.append(t)
    return tecnicas

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
            # FORZAR id, concepto_visual, mood_musical, tipo_visual (2026-11-03)
            d["id"] = num
            d.setdefault("concepto_visual", "newspaper abstract, cinematic")
            d.setdefault("mood_musical", "tension")
            d.setdefault("tipo_visual", "imagen")
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

    # ═══════════════════════════════════════════════════════════════
    # GUION MONÓLOGO PROFESIONAL (estructura Alsina/Gabilondo)
    # 4 actos: HOOK → PATRÓN → TÉCNICA → CIERRE
    # ═══════════════════════════════════════════════════════════════
    escenas = []
    num = 1
    estado = GuionEstado()  # Anti-repetición

    # Extraer medios únicos con datos reales (top16 + desglose)
    medios_unicos = _extraer_medios_unicos(top16, datos.get("dossier", {}).get("desglose_medios", ""))
    tecnicas_unicas = _tecnicas_unicas(medios_unicos)
    print(f"   Medios únicos: {len(medios_unicos)} | Técnicas: {len(tecnicas_unicas)}", flush=True)

    # Filtrar medios con titular válido (no vacío, >20 chars)
    # Filtrar basura (horóscopo, sucesos, deportes, farándula)
    BASURA_KEYWORDS = ['horóscopo', 'horoscopo', 'géminis', 'géminis', 'signo zodiacal',
                       'fallecid', 'muert', 'sangre', 'tragedia', 'crimen', 'suceso',
                       'fútbol', 'futbol', 'baloncesto', 'tenis', 'deportes',
                       'famosos', 'farándula', 'farandula', 'celebridad']
    medios_validos = []
    for m in medios_unicos:
        titular = m.get("titular", "")
        if not titular or len(titular) < 20:
            continue
        if any(k in titular.lower() for k in BASURA_KEYWORDS):
            continue
        medios_validos.append(m)
    medios_validos = medios_validos[:6]
    print(f"   Medios filtrados (sin basura): {len(medios_validos)}", flush=True)
    print(f"   Medios con titular válido: {len(medios_validos)}", flush=True)

    # ═══ ACTO 1: HOOK (escenas 1-2) ═══
    print(f"   [ACTO 1] HOOK (escenas 1-2)", flush=True)
    _tema_principal = medios_validos[0]["titular"][:80] if medios_validos else "la manipulación mediática"

    # Escena 1: Gancho + presentación
    print(f"   [Escena {num}/18] Hook inicial...", flush=True)
    hook_inst = f"""{LEY_ESTILO}

ACTO 1 — HOOK INICIAL (escena 1 de 18):

INSTRUCCIONES:
1. Abre con una FRASE BOMBA de 5-7 palabras. Contraintuitiva, incómoda, o absurda.
   Ejemplos:
   - "Hoy los medios han amanecido con una misión."
   - "España está en emergencia. O eso dicen."
   - "Atención al titular del día, porque tiene miga."
2. Di LITERALMENTE: 'Somos El Encuadre, y hoy, {fecha_str}, vamos a abrir la cloaca mediática.'
3. Di EXACTAMENTE: 'Hoy vamos a analizar cómo los medios manipulan la actualidad, empezando por: {_tema_principal}'
4. Añade promesa + pregunta: 'Te voy a enseñar las {len(tecnicas_unicas)} técnicas que han usado hoy. ¿Preparado?'
5. Cliffhanger mordaz: 'Quédate, porque lo que viene te va a explicar por qué todos los medios repiten lo mismo.'

Mínimo 80 palabras. Máximo 110."""
    escenas.append(_generar_escena(num, hook_inst)); num += 1

    # Escena 2: El "pero antes"
    print(f"   [Escena {num}/18] Hook transición...", flush=True)
    # Usar titulares reales del día para el patrón
    titulares_dia = [m["titular"][:60] for m in medios_validos[:3]]

    trans_inst = f"""{LEY_ESTILO}

ACTO 1b — TRANSICIÓN (escena 2 de 18):

Usa estos TITULARES REALES del día (NO inventes):
{chr(10).join('  - ' + t for t in titulares_dia)}

INSTRUCCIONES:
1. Empieza con: 'Pero antes de entrar en materia, quiero que veas algo.'
2. Conecta los 3 titulares de arriba: 'Tres medios distintos. Tres titulares distintos. Y los tres con el mismo truco escondido.'
3. Lanza la tesis editorial: 'Los medios no improvisan. Siguen un guion. Y hoy vamos a verlo.'
4. Cierra con pregunta cómplice: '¿Preparado para ver lo que hay debajo del titular?'

Prohibido: inventar ejemplos, "resulta que..." (repetido), fórmulas de IA.

Mínimo 70 palabras. Máximo 90."""
    escenas.append(_generar_escena(num, trans_inst)); num += 1

    # ═══ ACTO 2: PATRÓN (escenas 3-8, 6 medios) ═══
    print(f"   [ACTO 2] PATRÓN (escenas 3-8, {len(medios_validos)} medios)", flush=True)
    for medio_data in medios_validos:
        if num > 8: break
        medio = medio_data["medio"]
        titular = medio_data["titular"]
        tecnica = medio_data.get("tecnica", "Framing editorial")
        omite = medio_data.get("omite", "")
        extracto = medio_data.get("extracto", "")

        # Cita textual: si hay extracto, extraer cita; si no, usar el titular como "cita"
        citas = re.findall(r'[«"]([^»"]{40,200})[»"]', extracto) if extracto else []
        cita = citas[0] if citas else titular[:150]

        ctx = f"""Medio: {medio}
TITULAR: «{titular}»
QUÉ OMITE: {omite}
CITA: "{cita}"
EXTRACTO: {extracto[:500]}"""

        # 9 estructuras distintas (rotan por escena, NO se repiten)
        ESTRUCTURAS = [
            "Atención al titular de {medio}, que tiene miga:",
            "Y ahora la pieza clave del día. {medio}:",
            "El remate se lo lleva {medio}. Atención:",
            "Para terminar, fíjate en {medio}. Titular:",
            "Y el premio a la originalidad es para {medio}:",
            "Vamos con {medio}. Permítanme una duda razonable:",
            "Y aquí viene lo bueno. {medio} nos regala esto:",
            "No sé si lo han notado, pero {medio} titula:",
            "Señores, {medio} ha decidido que hoy toca:",
        ]
        # Elegir UNA estructura según el índice
        estructura = ESTRUCTURAS[(num - 3) % len(ESTRUCTURAS)]

        print(f"   [Escena {num}/18] Patrón: {medio}...", flush=True)
        patron_inst = f"""{LEY_ESTILO}
{estado.resumen_para_prompt()}

ACTO 2 — PATRÓN (escena {num} de 18, medio {medio}):

DATOS REALES:
- Medio: {medio}
- Titular: «{titular}»
- Cita textual: "{cita}"
- Qué omite: {omite}
- Técnica (NO nombrar): {tecnica}

INSTRUCCIONES (sigue el monólogo, eres el presentador):

1. Empieza EXACTAMENTE con esta estructura (cambia solo el titular/cita):
   "{estructura.format(medio=medio)} «{titular[:80]}»"

2. Comenta el titular con IRONÍA FINA (no insulto, no descripción):
   - "¿Clave para quién?" / "¿Y esto es noticia?" / "Permítanme dudarlo"
   - "Qué casualidad que..." / "Atención al detalle, porque aquí está la trampa"

3. Di QUÉ VENDE este medio (obligatorio, 1 frase):
   - Vende miedo / vende urgencia / vende poder / vende distracción / vende salvador

4. Usa la CITA TEXTUAL entre comillas (si la hay).

5. Conecta con el medio anterior (si no es el primero):
   - "Como hacía {medio_anterior} ayer, hoy {medio} repite la jugada"
   - "Y {medio} no se queda atrás"

6. Cierra con pregunta al oyente: "¿A quién beneficia esto?" / "¿Tú te habías dado cuenta?"

PROHIBIDO:
- "Mira lo que publicó"
- "Resulta que..." (máx 1 vez en TODO el guion)
- "Y a mí esto me parece..."
- "Nos hace sentir que..."
- Describir la técnica con su nombre (Card Stacking, Framing, etc.)

Mínimo 80 palabras. Máximo 100. Sin markdown."""
        _esc = _generar_escena(num, patron_inst, ctx)
        estado.registrar_usos(_esc.get("texto", ""))
        estado.add_medio(medio)
        escenas.append(_esc); num += 1

    # ═══ ACTO 3: TÉCNICA (escenas 9-14, 3 técnicas × 2 escenas) ═══
    print(f"   [ACTO 3] TÉCNICA (escenas 9-14)", flush=True)
    # Elegir 3 técnicas con más medios
    tecnicas_con_medios = {}
    for m in medios_validos:
        t = m.get("tecnica", "")
        if t:
            tecnicas_con_medios.setdefault(t, []).append(m["medio"])

    tecnicas_top = sorted(tecnicas_con_medios.items(), key=lambda x: len(x[1]), reverse=True)[:3]

    # Generar hasta 3 pares (6 escenas) para llenar ACTO 3
    for idx, (tecnica, medios_ejemplo) in enumerate(tecnicas_top):
        if num > 14: break

        # Escena A: ¿Qué consigue? (sin nombrarla)
        print(f"   [Escena {num}/18] Técnica A: {tecnica}...", flush=True)
        tecnica_inst_a = f"""{LEY_ESTILO}

ACTO 3 — TÉCNICA (escena {num} de 18, técnica: {tecnica} — NO nombrar):

INSTRUCCIONES:
1. Abre con: "¿Y por qué funciona todo esto?" o "Ahora la pregunta del millón: ¿por qué nos lo creemos?"

2. NO nombres la técnica. Describe el EFECTO en el oyente con una metáfora:
   - Card Stacking → "Apilan citas, expertos, datos. Y cuando has visto 10, tu cerebro dice: hay consenso. Aunque los 10 sean del mismo grupo."
   - Fear Appeal → "Te meten el miedo en vena. Y con miedo, votas, compras, callas."
   - Name Calling → "Le ponen la etiqueta. Y la etiqueta se queda pegada. Como el precio en una camiseta."
   - Authority Bias → "Ponen la bata. Y con bata, todo suena a verdad."
   - False Dilemma → "Te dan dos puertas. Y tú eliges una. Pero hay 10 más."
   - Negativity Bias → "Lo negativo pega 10 veces más. Y lo saben."

3. Usa UNA frase mordaz del banco: "Esto no es periodismo, es marketing con teclado." / "Y ojo, que esto tiene segunda parte." / "Qué casualidad que todos..."

4. Cierra con: "¿Lo pillas? Yo tampoco lo pillé la primera vez. Pero ahora lo veo."

Mínimo 80 palabras. Máximo 100. Sin markdown."""
        escenas.append(_generar_escena(num, tecnica_inst_a)); num += 1

        if num > 14: break

        # Escena B: Ejemplo concreto con medio
        medio_ej = medios_ejemplo[0] if medios_ejemplo else "un medio"
        print(f"   [Escena {num}/18] Técnica B: ejemplo {medio_ej}...", flush=True)
        tecnica_inst_b = f"""{LEY_ESTILO}

ACTO 3b — EJEMPLO CONCRETO (escena {num} de 18, medio: {medio_ej}, técnica: {tecnica} — NO nombrar):

INSTRUCCIONES:
1. Abre con: "Y esto lo vimos ayer en {medio_ej}. Fíjate cómo lo hicieron:"
2. Cuenta el ejemplo concreto (usa titular + cita si están en el contexto).
3. Aplica la ironía mordaz:
   - "¡Qué gran favor nos hace {medio_ej} contándonos esto!"
   - "Y mientras ustedes leen, alguien está celebrando."
4. Cierra con: "¿Ves la trampa? El truco es que no hay truco: es marketing con teclado."

Mínimo 70 palabras. Máximo 90. Sin markdown."""
        escenas.append(_generar_escena(num, tecnica_inst_b)); num += 1

    # ═══ ACTO 4: CIERRE (escenas 15-18) ═══
    print(f"   [ACTO 4] CIERRE (escenas 15-18)", flush=True)

    # Relleno si faltan escenas
    while num <= 17:
        print(f"   [Escena {num}/18] Relleno técnico...", flush=True)
        relleno_inst = "Sigue el monólogo. Añade una reflexión breve sobre cómo detectar la manipulación en el día a día. 80-90 palabras."
        escenas.append(_generar_escena(num, relleno_inst)); num += 1

    # Escena 17: Reflexión final
    if num <= 17:
        print(f"   [Escena {num}/18] Reflexión final...", flush=True)
        reflexion_inst = """Estás cerrando el monólogo. El presentador reflexiona:

'Mañana los mismos medios volverán a intentarlo. La única diferencia es que ahora ya sabes lo que están haciendo.'

Añade una nota de esperanza: 'No se trata de no creer nada. Se trata de saber cuándo te están vendiendo algo'.

Mínimo 80 palabras. Máximo 100. Tono: cercano, casi íntimo."""
        escenas.append(_generar_escena(num, reflexion_inst)); num += 1

    # Escena 18: Cierre + CTA
    print(f"   [Escena 18/18] Cierre épico + CTA...", flush=True)
    cierre_inst = f"""{LEY_ESTILO}

ACTO 4 — CIERRE ÉPICO (escena 18 de 18, ÚLTIMA):

INSTRUCCIONES:
1. Vuelve al gancho inicial (cierra el círculo): "Hoy los medios han amanecido con una misión. Y mañana volverán a intentarlo."
2. Da la tesis final mordaz: "La diferencia es que ahora ya sabes el truco. Y el truco es que no hay truco: es marketing con teclado."
3. CTA sin genérico de IA: "Dale a like si te ha servido. Suscríbete si quieres más. Y comparte esto con ese amigo que todavía se cree la tele."
4. Cierre con "punch" filosófico: "Mañana volverán a intentarlo. La única diferencia es que ahora ya lo ves."

PROHIBIDO: "Dale a like, suscríbete, o comparte" (genérico). Usa el mío de arriba.

Mínimo 80 palabras. Máximo 100. Tono: épico, cercano, con ganas."""
    escenas.append(_generar_escena(18, cierre_inst)); num += 1

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



# ═══════════════════════════════════════════════════════════════
# MODO MONÓLOGO (2026-11-03): 1 texto concatenado → 18 escenas
# El esquema de produccion_FECHA.json es IDÉNTICO al de producir_fase2().
# ───────────────────────────────────────────────────────────────

def _cargar_anecdota_dia():
    """Lee la anécdota del día del rotador."""
    try:
        from anecdotas_rotador import coger_anecdota
        return coger_anecdota()
    except Exception as e:
        print(f"   ⚠️ Anécdota fallback: {e}", flush=True)
        return {
            "id": 0,
            "categoria": "fallback",
            "texto": "El otro día, en el bar de Paco, alguien me dijo: 'Lo he leído en el periódico, así que es verdad'. Y yo le dije: 'Como el anuncio de la crema que quita arrugas'. Y el hombre se quedó pensando.",
        }

def _cargar_contexto_verificado(titular, medio, tema):
    """Busca contexto en fuentes oficiales (EFE/Reuters/BOE/Wikipedia)."""
    try:
        from contexto_verificado import buscar_contexto
        return buscar_contexto(titular, medio, tema)
    except Exception as e:
        print(f"   ⚠️ Contexto fallback: {e}", flush=True)
        return ""

def _generar_monologo_llm(anecdota, medios_validos, contexto_global, fecha_str, tecnicas_unicas):
    """Genera el monólogo completo (~1700 palabras) con LLM."""
    # Preparar contexto de los 3 medios principales
    medios_txt = ""
    for i, m in enumerate(medios_validos[:3], 1):
        medios_txt += f"\n--- MEDIO {i}: {m['medio']} ---\n"
        medios_txt += f"Titular: «{m['titular']}»\n"
        if m.get('cita'): medios_txt += f"Cita: {m['cita'][:300]}\n"
        if m.get('tecnica'): medios_txt += f"Técnica (NO nombrar): {m['tecnica']}\n"
        if m.get('omite'): medios_txt += f"Qué omite: {m['omite'][:200]}\n"
    
    tecnicas_txt = ", ".join(tecnicas_unicas[:4]) if tecnicas_unicas else "manipulación"
    
    prompt = f"""Eres Carlos Alsina + Buenafuente + Wyoming juntos. Monólogo de 11 min para 'El Encuadre'.
Fecha: {fecha_str}

TAREA: Escribe un monólogo CONCATENADO de ~1700 palabras. 4 capas en este orden exacto:

═══ CAPA 1: ANÉCDOTA (300-400 palabras) ═══
Empieza contando esta anécdota REAL del día:
"{anecdota['texto']}"

Después, conecta la anécdota con lo que publicaron hoy los medios:
"Y esto me recuerda a lo que publicaron hoy..."

═══ CAPA 2: INFORMAR (500-600 palabras) ═══
Analiza las 3 noticias de hoy (usa datos reales):
{medios_txt}

Contexto verificado de fuentes oficiales (EFE/BOE/Wikipedia):
{contexto_global[:1500] if contexto_global else "(sin contexto)"}

Di: qué dice cada medio, qué dicen las fuentes oficiales, dónde está el gap. 
NO inventes. Usa SOLO los datos reales.

═══ CAPA 3: ENTRENAR (500 palabras) ═══
Enseña 3 TÉCNICAS de manipulación de estas noticias ({tecnicas_txt}).
NO nombres las técnicas con su nombre técnico. Describe su EFECTO:
- "Apilan expertos para que parezca consenso"
- "Repiten el miedo hasta que te lo creas"
- "Le ponen la etiqueta y se queda pegada"

═══ CAPA 4: CONCIENCIAR (300-400 palabras) ═══
Cierra con:
1. Reflexión empática: "No es tu culpa. El sistema está diseñado así."
2. 3 preguntas para detectar manipulación mañana
3. Vuelve a la anécdota inicial (cierra el círculo)
4. CTA natural: "Si te ha servido, comparte. Si no, no."

TONO:
- Frases CORTAS (máx 15 palabras por frase)
- Conectores coloquiales: "Mira", "Oye", "Fíjate", "Vamos a ver"
- Ironía fina, NO insulto
- Pausas naturales (párrafos separados por \n\n)
- Punchlines cortas: "Titular. Mentira. Otra vez." / "Puro marketing."

PROHIBIDO:
- "Mira lo que publicó"
- "Y a mí esto me parece"
- "Nos hace sentir que"
- "Resulta que..." (máx 1 vez)
- "¿A quién beneficia esto?" (repetido)
- Nombres técnicos de técnicas (Card Stacking, Fear Appeal...)
- Markdown, HTML, acotaciones [PAUSA]

Devuelve SOLO el texto del monólogo. Sin introducción, sin preámbulo, sin marcar las capas."""
    
    from especialistas import pedir_a_especialista
    texto = pedir_a_especialista("guionista_retencion_v2", prompt, contexto="", proveedor="auto")
    if not texto or len(texto.split()) < 800:
        raise RuntimeError(f"Monólogo muy corto: {len(texto.split() if texto else 0)} palabras")
    # Limpiar
    import re as _re
    texto = _re.sub(r'\[.*?\]', '', texto)
    texto = _re.sub(r'\(.*?\)', '', texto)
    texto = _re.sub(r'[*_#`>]', '', texto)
    texto = _re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

def producir_monologo(fecha=None):
    """Genera produccion_FECHA.json en MODO MONÓLOGO.
    Esquema IDÉNTICO a producir_fase2() pero las 18 escenas vienen de 1 texto."""
    import datetime, json as _json
    fecha = fecha or datetime.date.today().isoformat()
    dossier_file = OUT / f"dossier_{fecha}.json"
    if not dossier_file.exists():
        print(f"❌ No existe {dossier_file}")
        return None
    
    datos = _json.loads(dossier_file.read_text())
    res = {"fecha": fecha, "dossier": datos.get("dossier", {})}
    
    # Redactor (artículo blog) — igual que en producir_fase2
    print("[monologo] 1/5 Redactor (artículo blog)...", flush=True)
    ctx = _json.dumps({"dossier": datos.get("dossier", {})}, ensure_ascii=False)
    esqueleto = _parse_json_seguro(pedir_a_especialista("arquitecto_contenido", "Crea el esqueleto del artículo.", contexto=ctx[:3000]))
    _PROMPT_REDACTOR = (
        'Escribe un artículo periodístico mordaz y directo de 1200 palabras en MARKDOWN PLANO. '
        'PROHIBIDO HTML. Tono: auditor cabreado que expone la manipulación mediática.'
    )
    articulo = pedir_a_especialista("redactor_blog", _PROMPT_REDACTOR, contexto=f"ESQUELETO:\n{_json.dumps(esqueleto)}\n\nDOSSIER:\n{ctx[:3000]}")
    articulo = _limpiar_html(articulo)
    res["articulo_html"] = articulo
    res["esqueleto"] = esqueleto
    
    # Datos del día
    print("[monologo] 2/5 Cargando datos del día...", flush=True)
    ahora = datetime.datetime.now()
    meses = {1:"enero",2:"febrero",3:"marzo",4:"abril",5:"mayo",6:"junio",7:"julio",8:"agosto",9:"septiembre",10:"octubre",11:"noviembre",12:"diciembre"}
    fecha_str = f"{ahora.day} de {meses[ahora.month]} de {ahora.year}"
    
    # Top16
    top16 = []
    af = OUT / f"analisis_fase1_{fecha}.json"
    if af.exists():
        top16 = _json.loads(af.read_text()).get("top16", [])
    
    # Medios únicos con contexto
    desglose = datos.get("dossier", {}).get("desglose_medios", "")
    medios = _extraer_medios_unicos(top16, desglose)
    tecnicas = _tecnicas_unicas(medios)
    BASURA = ['horóscopo', 'horoscop', 'géminis', 'fallecid', 'muert', 'sangre', 'tragedia', 'crimen', 'suceso', 'fútbol', 'futbol', 'baloncesto', 'tenis', 'deportes', 'famosos']
    medios_validos = [m for m in medios if m.get("titular") and len(m["titular"]) > 20 and not any(k in m["titular"].lower() for k in BASURA)][:3]
    print(f"   Medios válidos: {len(medios_validos)} | Técnicas: {len(tecnicas)}", flush=True)
    
    if not medios_validos:
        print("❌ Sin medios válidos para el monólogo")
        return None
    
    # Anécdota + contexto
    print("[monologo] 3/5 Anécdota + contexto verificado...", flush=True)
    anecdota = _cargar_anecdota_dia()
    print(f"   Anécdota categoría: {anecdota['categoria']}", flush=True)
    
    contexto_global = ""
    for m in medios_validos[:3]:
        tema = m["titular"][:80]
        ctx_m = _cargar_contexto_verificado(m["titular"], m["medio"], tema)
        if ctx_m:
            contexto_global += f"\n=== {m['medio']} ===\n{ctx_m}\n"
    
    # Generar monólogo
    print("[monologo] 4/5 Generando monólogo LLM...", flush=True)
    texto_monologo = _generar_monologo_llm(anecdota, medios_validos, contexto_global, fecha_str, tecnicas)
    print(f"   Monólogo: {len(texto_monologo.split())} palabras", flush=True)
    
    # Splitter 1 → 18
    print("[monologo] 5/5 Dividiendo en 18 escenas...", flush=True)
    from splitter_monologo import splitter
    escenas = splitter(texto_monologo, num_escenas=18)
    print(f"   Escenas generadas: {len(escenas)}", flush=True)
    
    res["escenas"] = escenas
    res["texto_voz_largo"] = " ".join([e.get("texto", "") for e in escenas])
    res["palabras_totales"] = len(res["texto_voz_largo"].split())
    
    # Viralidad
    print("[monologo] Calculando viralidad...", flush=True)
    viral = _parse_json_seguro(pedir_a_especialista("predictor_viralidad", "Puntua 0-100. Devuelve SOLO JSON con 'score'.", contexto=texto_monologo[:3000], proveedor="auto"))
    if not viral or "score" not in viral:
        viral = {"score": 75, "razon": "Fallback"}
    res["viralidad"] = viral
    
    # Shorts finales (igual que producir_fase2)
    print("[monologo] Generando shorts finales...", flush=True)
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
            hook_ctx = str(hooks_base[i-1] if i-1 < len(hooks_base) and hooks_base[i-1] else "")
            prompt_s = (
                f"Eres guionista de shorts de 'El Encuadre'. Desmonta manipulación mediática. "
                f"Tipo: {tipo}. Contexto: '{hook_ctx[:200]}'. "
                "50-60 palabras para short de 40s. Empieza con pregunta. "
                "Menciona medio y técnica. TERMINA con 'Somos El Encuadre, analistas de la manipulación. Suscríbete para más'. "
                "Sin markdown."
            )
            guion = pedir_a_especialista("guionista_retencion_v2", prompt_s, contexto=hook_ctx[:500], proveedor="auto")
            if not guion or len(guion.split()) < 20:
                guion = f"¿Sabías cómo {tipo} los medios manipulan? {hook_ctx[:100]}... Somos El Encuadre, suscríbete."
            import re as _re2
            guion = _re2.sub(r'\[[^\]]*\]', '', guion)
            guion = _re2.sub(r'\s+', ' ', guion).strip()
            palabras_g = guion.split()
            if len(palabras_g) > 50:
                guion = " ".join(palabras_g[:50]) + "..."
            shorts_finales.append({"tipo": tipo, "guion": guion, "hook": hook_ctx[:100] if hook_ctx else guion[:100]})
        except Exception as _e:
            print(f"   ⚠️ Short {i}: {_e}", flush=True)
    
    res["shorts_finales"] = shorts_finales
    print(f"   Shorts: {len(shorts_finales)}/4", flush=True)
    
    # Guardar
    out_json = OUT / f"produccion_{fecha}.json"
    out_json.write_text(_json.dumps(res, indent=2, ensure_ascii=False))
    print(f"\n[monologo] ✅ Guardado en {out_json}", flush=True)
    print(f"   Escenas: {len(escenas)} | Palabras: {res['palabras_totales']} | Shorts: {len(shorts_finales)}", flush=True)
    return res



if __name__ == "__main__":
    import sys as _sys
    modo = "fase2"
    fecha_arg = None
    for i, arg in enumerate(_sys.argv[1:], 1):
        if arg == "--modo" and i < len(_sys.argv) - 1:
            modo = _sys.argv[i+1]
        elif not arg.startswith("--") and not (i > 1 and _sys.argv[i-1] == "--modo"):
            fecha_arg = arg
    
    if modo == "monologo":
        print("[fase2] MODO MONÓLOGO activado", flush=True)
        producir_monologo(fecha_arg)
    else:
        print("[fase2] MODO FASE2 clásico", flush=True)
        producir_fase2(fecha_arg)
