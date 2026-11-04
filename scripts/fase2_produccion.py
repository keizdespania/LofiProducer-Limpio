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

REGLAS GRAMATICALES Y DE DATOS (OBLIGATORIO, si fallas aquí se nota):
- CONCORDANCIA: "Todas las cabeceras" (femenino), "Los titulares" (masculino). NUNCA "Todos los cabeceras".
- NOMBRES PROPIOS: "Europa Press" (dos palabras, no EuropaPress), "El País", "El Mundo", "The Guardian", "20 Minutos", "Efe" o "EFE".
- NÚMEROS: usar punto de miles SIEMPRE. "4.000 millones", NUNCA "4. 000 millones" ni "4,000". "1.500", no "1. 500".
- FECHAS: la primera vez que menciones el día di la fecha real (ej. "3 de noviembre de 2026"), NO dos veces "hoy" seguidas.
- ARTÍCULOS: revisa género antes de escribir. "el agua" (femenino pero con "el"), "la aula", "el área", "las cabeceras".
- "LEE ENTRE LÍNEAS" → PROHIBIDO. Infantiliza. Usa "ya me entiendes", "fíjate", "atiende" o simplemente el ejemplo.
- "CAPRICHOSAMENTE" → PROHIBIDO. Si algo es deliberado, di "deliberadamente", "calculadamente" o "a propósito".
- "UN MISMO HECHO" → solo si REALMENTE es el mismo hecho.
- FUENTES OFICIALES: el BOE es SOLO para noticias españolas. Para noticias internacionales (Trump, Israel, Ucrania, Rusia, China, Irán, EEUU, OTAN, ONU, Gaza, cualquier país extranjero), PROHIBIDO mencionar el BOE. Usa EFE/Reuters/AP/Wikipedia. NUNCA digas "el BOE no recoge" una noticia internacional: es de cajón y queda ridículo. Si son 3 noticias distintas (tragedias ferroviarias + Trump + Urda), di "un mismo día, tres distracciones".

PALABRAS PROHIBIDAS (evitar por gastadas):
- "caprichosamente", "pegada al asiento", "no te pierdas", "resulta que" (más de 1 vez)
- "en la era de la atención fragmentada" (cliché)
- "la maquinaria del ruido" (cliché)

CTA FINAL:
- PROHIBIDO "dale a like", "suscríbete", "dale a la campanita". Es de youtuber, no de Alsina.
- Si hay CTA, que sea de complicidad: "compártelo con quien lo necesite", "nos vemos mañana", "ya sabes dónde encontrarme".
- Si cierras prometiendo "tres preguntas", HAZLAS explícitas justo después. No dejes la promesa colgando.

ACTO 3 — TÉCNICAS:
- Usa SOLO las técnicas que te doy en el contexto "TECNICAS REALES DEL DÍA" (del dossier de hoy). NO inventes ejemplos genéricos (ni azúcar/depresión, ni tablet/madre, ni IVA/sanidad).
- Cada técnica del dossier debe aplicarse a UNA noticia REAL del top16.
- PROHIBIDO "Primero... Segundo... Tercero..." → entrelaza con narrativa ("Y luego está lo de...", "Y lo peor viene cuando...").

ESTRUCTURA POR MEDIO (ACTO 2):
- Por CADA medio del top16, responde explícitamente a las 3 preguntas:
  1. ¿Qué dice el titular? (resumen en 1 frase)
  2. ¿Por qué lo cuenta HOY? (interés editorial del medio, explícito)
  3. ¿A quién beneficia? (explícito)
- NO dejes medios sin las 3 respuestas. Si no las sabes, dilo ("no lo sabemos, pero...").

ANÉCDOTA (ACTO 1):
- La anécdota debe ser DIFERENTE cada día. NO uses siempre "el abuelo/el portero/la salsa". Si te doy una anécdota en el contexto, úsala LITERAL. Si no, invéntala pero cambia el escenario: puede ser una película, un partido de fútbol, un libro, una anécdota histórica, una escena cotidiana (supermercado, metro, peluquería). Varía.

═══════════════════════════════════════════════════════════════════
CONEXIONES PROHIBIDAS (si fallas aquí, el guion parece de IA tonta):
- Si las noticias son de temas distintos (nacional vs internacional, tren vs Trump, BOE vs Israel), NO inventes conexiones.
- PROHIBIDO: "este medio omite la conexión entre X e Y" si X e Y no tienen relación real.
- PROHIBIDO: "sugiere un trasfondo de...", "mezcla la crisis interna con...", "omite la conexión con...".
- Si no sabes por qué el medio publica algo, di: "no lo sabemos, pero está ahí" o "simplemente es la noticia del día" o "es la noticia internacional de hoy".
- NUNCA atribuyas intención editorial a la mera coexistencia de noticias en portada.

CITAS — REGLA DE ORO:
- Si pones comillas («...» o "..." o '...'), el texto DEBE estar LITERAL en el extracto real del artículo.
- Si no estás 100% seguro de que está literal, PARAFRASEA sin comillas.
- PROHIBIDO inventar citas. "Trump dijo 'ellos ya no lo necesitan'" solo si esa frase EXACTA aparece en el extracto.
- Si dudas: "Trump anunció que ya no les hacía falta" (sin comillas).

GRAMÁTICA — REVISIÓN OBLIGATORIA:
- Revisa cada verbo. "dicte" NO existe como 3ª persona. Usa "dice" o "dijo".
- "él dice", "él dijo", "según X, Y afirma" — concordancias correctas.
- Repasa artículos: "el acta" (femenino con "el"), "las cabeceras", "los titulares".
- Si dudas entre dos formas, usa la más simple.

═══════════════════════════════════════════════════════════════════
HACKS ANTIALUCINACIÓN (lee esto, es importante para no quedar como un becario):

HACK 1 — ANCLAJE AL EXTRACTO:
Si en el contexto hay "EXTRACTO REAL DEL ARTICULO", empieza cada párrafo sobre ese medio con un dato LITERAL del extracto. Luego desarrolla. Pero el dato de apertura es del extracto, no inventado.

HACK 2 — CHECKLIST INTERNA antes de cada párrafo:
Antes de escribir una frase con "no se menciona X" o "se omite X":
  a) ¿X está en el extracto? SÍ → adelante. NO → cambia a "no se menciona el detalle" o salta el punto.
  b) ¿La cita con comillas está literal en el extracto? SÍ → adelante. NO → parafrasea.
  c) ¿La conexión que voy a hacer tiene base real? SÍ → adelante. NO → "no lo sabemos".

HACK 3 — CIERRE POR MEDIO (evita invenciones):
Cada medio termina con UNA de estas 3 fórmulas (elige la que encaje):
  - "[Medio] lo cuenta porque [razón clara del extracto o del medio]."
  - "[Medio] lo cuenta simplemente porque es la noticia del día. No hay más."
  - "No sabemos por qué [medio] lo cuenta hoy. Y eso, a veces, es la noticia."

HACK 4 — PROHIBIDO EL "SUGIERE":
La palabra "sugiere" (y "sugeriría") está PROHIBIDA cuando hablas de intenciones de medios. Di "el medio dice" o "el medio omite". No "sugiere que...". Si algo "sugiere", es porque el lector lo infiere; tú no sugieres nada.

HACK 5 — SI NO HAY CONEXIÓN, DILO:
Si las 3 noticias no tienen relación temática, ABRE el ACTO 2 así: "Hoy los medios hablan de tres cosas distintas. Tres. Y las tres importan. Pero solo una te la van a contar entera." Eso convierte la falta de conexión en el gancho.

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
        import random as _rnd
        frases_disp = self.frases_disponibles()
        punch_disp = self.punchlines_disponibles()
        qv_disp = self.que_vende_disponibles()
        # Muestreo aleatorio para forzar variedad real (fix 2026-11-03)
        _fr = _rnd.sample(frases_disp, min(10, len(frases_disp))) if frases_disp else []
        _pu = _rnd.sample(punch_disp, min(10, len(punch_disp))) if punch_disp else []
        _qv = _rnd.sample(qv_disp, min(8, len(qv_disp))) if qv_disp else []
        return f"""
ESTADO ACTUAL DEL GUION (NO REPETIR):
- Frases ya usadas: {len(self.frases_usadas)} de 100
- "Qué vende" ya usado: {list(self.que_vende_usado) or "ninguno"}
- Punchlines ya usadas: {len(self.punchlines_usadas)} de 50

FRASES DISPONIBLES (OBLIGATORIO usar 1 EXACTA de estas 10): {_fr}

PUNCHLINES DISPONIBLES (OBLIGATORIO usar 1 EXACTA de estas 10): {_pu}

"QUÉ VENDE" DISPONIBLE (OBLIGATORIO usar 1 EXACTO de estos 8): {_qv}

REGLA CRÍTICA: USA 1 FRASE + 1 PUNCHLINE + 1 QUÉ VENDE LITERALES de las listas de arriba.
Cópialas TAL CUAL, sin parafrasear. Si no las usas, la escena se rechaza.
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

def _sanear_huerfanos(texto):
    """Limpia patrones rotos típicos del LLM: 'pero. .', 'porque .', ', sin mencionar que. .'"""
    if not texto:
        return texto
    t = texto
    # 1) "pero. ." / "pero ." / "pero,"  -> quitar conector huérfano
    t = re.sub(r'\(?\bpero\b\)?\s*[\.\,\;]\s*[\.\s]*', ' ', t, flags=re.IGNORECASE)
    # 2) "porque ." / "porque y " / "porque,"  -> quitar
    t = re.sub(r'\bporque\b\s+(y\s+)?[\.\,\;]?\s*', ' ', t, flags=re.IGNORECASE)
    # 3) ", sin mencionar que. ." / ", pero ." -> quitar
    t = re.sub(r'\,\s*sin mencionar que[^.]{0,4}\.\s*\.?', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\,\s*pero\s*\.[^.]{0,4}\.?', '', t, flags=re.IGNORECASE)
    # 4) ", pero ." / ", pero . ,"  -> quitar
    t = re.sub(r'\,\s*pero\s*[\.,]\s*', ' ', t, flags=re.IGNORECASE)
    # 5) Restos: " .", " ,", ". .", ", ,"  -> normalizar (reforzado 2026-11-03)
    t = re.sub(r'\s+\.\s*', '. ', t)
    t = re.sub(r'\s+\,\s*', ', ', t)
    t = re.sub(r'\.\s+\.', '.', t)
    # comas dobles / triples -> una sola
    t = re.sub(r'\,{2,}', ',', t)
    # coma antes de signo de apertura -> quitar
    t = re.sub(r'\,\s*([\¿\¡\?\.])', r' \1', t)
    # coma huérfana al final de frase -> punto
    t = re.sub(r'\,\s*$', '.', t)
    # 6) Espacios múltiples
    t = re.sub(r'[ \t]{2,}', ' ', t)
    # 7) Espacio antes de puntuación
    t = re.sub(r'\s+([\.\,\;\:\!\?])', r'\1', t)
    # 8) Garantizar espacio antes de ¿ ¡ si vienen tras palabra
    t = re.sub(r'([^\s\¿\¡\n])([\¿\¡])', r'\1 \2', t)
    # 9) Coma al final antes de mayúscula con ¿ ¡ -> limpiar
    t = re.sub(r'\,\s+\¿', ' ¿', t)
    t = re.sub(r'\,\s+\¡', ' ¡', t)
    return t.strip()


def _tiene_huerfano(texto):
    """True si el texto tiene patrones rotos ('pero. .', 'porque .', '. .', ' , .')."""
    if not texto:
        return False
    patrones = [
        r'\.\s*\.',       # ". ."
        r'\bpero\s*[\.\,]',  # "pero." o "pero,"
        r'\bporque\s*[\.\,]', # "porque."
        r'\,\s*\.',      # ", ."
        r'\s\.\s',       # " . "
    ]
    return any(re.search(p, texto) for p in patrones)


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
            # Sanear huérfanos tipo "pero. .", "porque ." (2026-11-03)
            _antes = d["texto"]
            d["texto"] = _sanear_huerfanos(d["texto"])
            if d["texto"] != _antes:
                print(f"      🧹 Huérfanos saneados en escena {num}", flush=True)
            if _tiene_huerfano(d["texto"]):
                print(f"      ⚠️ Escena {num} sigue con huérfanos tras sanear, reintento", flush=True)
                continue
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

    # Escena 1: INTRO DINÁMICA (LLM decide la apertura cada día)
    print(f"   [Escena {num}/18] Intro dinámica...", flush=True)
    
    # Rotar estilo de apertura cada día
    import hashlib
    estilos_intro = [
        "Pregunta incómoda al oyente",
        "Dato bomba de 5 palabras",
        "Escena absurda cotidiana",
        "Confesión personal del presentador",
        "Paradoja periodística",
        "Anécdota breve + giro",
    ]
    dia_hash = int(hashlib.md5(fecha_str.encode()).hexdigest(), 16)
    estilo_hoy = estilos_intro[dia_hash % len(estilos_intro)]
    
    intro_inst = f"""{LEY_ESTILO}

ACTO 1 — INTRO (escena 1 de 18, ~100 palabras):

ESTILO DE APERTURA PARA HOY: {estilo_hoy}

INSTRUCCIONES CRÍTICAS:
1. NO empieces siempre igual. NO uses "Buenas noches, Arquitecto" ni "Hoy vamos a hablar de..."
2. Aplica el estilo "{estilo_hoy}" como gancho de apertura.
3. Di LITERALMENTE: "Somos El Encuadre, hoy {fecha_str}."
4. Menciona el tema: "Hoy analizamos cómo los medios manipulan la actualidad."
5. Promesa concreta: "Te voy a enseñar 3 técnicas que han usado hoy."
6. Cliffhanger: "Si te quedas, no volverás a leer un titular igual."
7. PROHIBIDO mencionar URLs, webs o links en la intro.

Tono: Alsina (amigo listo, ironía fina, frases cortas).
Mínimo 90 palabras. Máximo 120."""
    
    escenas.append(_generar_escena(num, intro_inst)); num += 1

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
        # Generar con validación de alucinaciones
        for _intento in range(3):
            _esc = _generar_escena(num, patron_inst, ctx)
            _aluc = _validar_alucinaciones(_esc.get("texto", ""), top16)
            if len(_aluc) <= 5:
                break
            print(f"      ⚠️ {len(_aluc)} alucinaciones ({_aluc[:3]}), regenerando {_intento+1}/3", flush=True)
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

    # Escena 18: OUTRO DINÁMICO (LLM decide el cierre cada día)
    print(f"   [Escena 18/18] Outro dinámico...", flush=True)
    
    estilos_outro = [
        "Reflexión filosófica corta",
        "Pregunta abierta al oyente",
        "Vuelta a la anécdota del principio",
        "Dato que resume el día",
        "Frase seca de las que se recuerdan",
        "Llamada a la acción directa",
    ]
    estilo_outro = estilos_outro[dia_hash % len(estilos_outro)]
    
    outro_inst = f"""{LEY_ESTILO}

ACTO 4 — OUTRO (escena 18 de 18, ~90 palabras):

ESTILO DE CIERRE PARA HOY: {estilo_outro}

INSTRUCCIONES CRÍTICAS:
1. NO uses siempre el mismo cierre. NO repitas "dale a like, suscríbete".
2. Aplica el estilo "{estilo_outro}" para cerrar el monólogo.
3. CTA natural y breve (1-2 frases máximo). Ejemplos:
   - "Si te ha servido, comparte. Si no, no."
   - "Nos vemos mañana. O no. Tú decides."
   - "Suscríbete si quieres saber lo que viene. O no. Da igual. Yo lo cuento igual."
4. PROHIBIDO mencionar URLs, webs, links, "elencuadre.pages.dev" o cualquier dominio.
5. PROHIBIDO "dale a like, suscríbete y comparte" (el genérico de IA).

Tono: Alsina íntimo (baja la voz, confía en el oyente).
Mínimo 70 palabras. Máximo 100."""
    
    escenas.append(_generar_escena(18, outro_inst)); num += 1

    # Validar que se usan frases del banco (BANCO_FRASES + PUNCHLINES)
    texto_total = " ".join([e.get("texto","") for e in escenas])
    frases_usadas = [f for f in BANCO_FRASES if f in texto_total]
    punches_usadas = [p for p in PUNCHLINES if p in texto_total]
    total_marcadores = len(frases_usadas) + len(punches_usadas)
    print(f"   ✅ Banco: {len(frases_usadas)}/{len(BANCO_FRASES)} frases + {len(punches_usadas)}/{len(PUNCHLINES)} punchlines = {total_marcadores} totales", flush=True)
    if total_marcadores == 0:
        print(f"   ⚠️ 0 marcadores del banco. NO se martillea (regla 2026-11-03). Log para revisar prompt.", flush=True)

    res["escenas"] = escenas
    res["texto_voz_largo"] = _sanitizar_monologo(" ".join([e.get("texto", "") for e in escenas]), fecha)
    # Reaplicar a cada escena para que voz_edge lea limpio
    for _e in escenas:
        _e["texto"] = _sanitizar_monologo(_e.get("texto", ""), fecha)
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
        # Primer intento: tema completo
        resultado = buscar_contexto(titular, medio, tema)
        if resultado and len(resultado) > 100:
            return resultado
        
        # Segundo intento: tema simplificado (2 palabras clave)
        import re as _re_ctx
        palabras = [w for w in tema.split() if len(w) > 4][:2]
        if palabras:
            tema_simple = " ".join(palabras)
            print(f"      🔄 Reintento DDG con tema simplificado: '{tema_simple}'", flush=True)
            resultado = buscar_contexto(titular, medio, tema_simple)
            if resultado and len(resultado) > 100:
                return resultado
        
        return ""
    except Exception as e:
        print(f"   ⚠️ Contexto fallback: {e}", flush=True)
        return ""

def _pasar_abogado_del_diablo(texto_capa, medios_validos):
    """Valida que la capa no invente datos que no estén en los medios.
    Si detecta alucinaciones, reintenta o elimina la frase problemática."""
    from especialistas import pedir_a_especialista
    import re as _re
    
    # Extraer datos verificables del contexto (medios + titulares)
    datos_reales = ""
    for m in medios_validos:
        datos_reales += f"MEDIO: {m['medio']}\n"
        datos_reales += f"TITULAR: {m['titular']}\n"
        if m.get('cita'): datos_reales += f"CITA: {m['cita'][:300]}\n"
        if m.get('extracto'): datos_reales += f"EXTRACTO: {m['extracto'][:300]}\n"
        if m.get('omite'): datos_reales += f"OMITE: {m['omite']}\n"
        datos_reales += "\n"
    
    # Pedir al abogado que detecte alucinaciones
    prompt_abogado = f"""Eres un ABOGADO DEL DIABLO + VERIFICADOR DE HECHOS.

TAREA: Analiza este texto de monólogo periodístico y detecta ALUCINACIONES.

TEXTO A VERIFICAR:
{texto_capa}

DATOS REALES (lo único que puede aparecer):
{datos_reales[:2000]}

INSTRUCCIONES:
1. Lee el texto a verificar
2. Detecta CUALQUIER dato, cifra, nombre o afirmación que NO esté en los datos reales
3. Devuelve SOLO un JSON con este formato:
   {{"alucinaciones": ["frase 1", "frase 2"], "ok": true|false}}

Si no hay alucinaciones → {{"alucinaciones": [], "ok": true}}
Si hay alucinaciones → lista las frases inventadas

PROHIBIDO: explicar, markdown, texto fuera del JSON."""
    
    try:
        resultado = pedir_a_especialista("abogado_del_diablo", prompt_abogado, contexto="", proveedor="auto")
        # Limpiar markdown
        resultado = _re.sub(r'^```json\s*', '', resultado.strip())
        resultado = _re.sub(r'```\s*$', '', resultado)
        data = json.loads(resultado)
        
        if data.get("ok"):
            return texto_capa, []
        
        # Hay alucinaciones → devolver lista para que el caller decida
        return texto_capa, data.get("alucinaciones", [])
    except Exception as e:
        print(f"      ⚠️ Abogado falló: {e}, pasando texto sin verificar", flush=True)
        return texto_capa, []

def _limpiar_alucinaciones(texto_capa, alucinaciones):
    """Elimina frases alucinadas del texto."""
    import re as _re
    texto_limpio = texto_capa
    for frase in alucinaciones:
        if len(frase) > 10:
            # Reemplazar la frase por "[dato verificado]"
            texto_limpio = texto_limpio.replace(frase, "")
    # Limpiar dobles espacios
    texto_limpio = _re.sub(r'\s+', ' ', texto_limpio)
    texto_limpio = _re.sub(r'\s*\.\s*\.', '.', texto_limpio)
    return texto_limpio.strip()


def _generar_monologo_llm(anecdota, medios_validos, contexto_global, fecha_str, tecnicas_unicas, extractos_map=None):
    """Genera el monólogo en 4 llamadas separadas (1 por capa) para asegurar longitud."""
    from especialistas import pedir_a_especialista
    import re as _re
    
    def _limpiar(t):
        t = _re.sub(r'\[.*?\]', '', t)
        t = _re.sub(r'\(.*?\)', '', t)
        t = _re.sub(r'[*_#`>]', '', t)
        t = _re.sub(r'\n{3,}', '\n\n', t)
        return t.strip()
    
    def _llm(prompt, min_palabras=200):
        for intento in range(2):
            try:
                txt = pedir_a_especialista("guionista_retencion_v2", prompt, contexto="", proveedor="auto")
                txt = _limpiar(txt) if txt else ""
                if len(txt.split()) >= min_palabras:
                    return txt
                print(f"      ⚠️ Intento {intento+1}: {len(txt.split())} palabras < {min_palabras}, reintentando...", flush=True)
            except Exception as e:
                print(f"      ⚠️ LLM intento {intento+1}: {e}", flush=True)
        return txt if 'txt' in locals() else ""
    
    # ─── CAPA 1: ANÉCDOTA (300-400 palabras) ───
    print(f"   [1/4] Anécdota ({anecdota['categoria']})...", flush=True)
    # Pasar las 3 noticias reales para que NO invente noticias del día (fix A 2026-11-04)
    _noticias_para_anecdota = ""
    for _m in medios_validos[:3]:
        _noticias_para_anecdota += "  - " + _m['medio'] + ": " + _m['titular'][:120] + chr(10)
    
    capa1_prompt = f"""Eres Carlos Alsina + Buenafuente + Wyoming juntos. Escribe la CAPA 1 de un monólogo (300-400 palabras).

NOTICIAS REALES DEL DÍA (las que se analizarán después):
{_noticias_para_anecdota}

TAREA: Empieza contando esta anécdota LITERAL:
"{anecdota['texto']}"

Después:
1. Explica qué te sugiere la anécdota (2-3 frases)
2. Conecta con el TEMA GENERAL (manipulación, apariencias, medios que venden). PROHIBIDO inventar noticias: NO menciones "reforma fiscal", "reality de presupuestos", "austeridad es una ganga" ni similares. La anécdota conecta con el TEMA, NO con noticias concretas del día.
3. Cierra con puente: "Y te voy a enseñar por qué esto importa. Quédate."

TONO: frases cortas (máx 15 palabras), conectores ("Mira", "Oye", "Fíjate"), pausas naturales (\n\n), ironía fina.

PROHIBIDO: "Mira lo que publicó", "Resultado que...", fórmulas de IA, markdown, acotaciones.

Devuelve SOLO el texto de la capa 1, sin preámbulo."""
    capa1 = _llm(capa1_prompt, min_palabras=250)
    print(f"      ✅ {len(capa1.split())} palabras", flush=True)
    
    # ─── CAPA 2: INFORMAR (500-600 palabras) ───
    print(f"   [2/4] Informar (3 medios)...", flush=True)
    medios_txt = ""
    for i, m in enumerate(medios_validos[:3], 1):
        medios_txt += f"\n--- MEDIO {i}: {m['medio']} ---\n"
        medios_txt += f"Titular: «{m['titular']}»\n"
        if m.get('cita'): medios_txt += f"Cita: {m['cita'][:300]}\n"
        if m.get('tecnica'): medios_txt += f"Técnica: {m['tecnica']}\n"
        if m.get('omite'): medios_txt += f"Qué omite: {m['omite'][:200]}\n"
        # EXTRACTO REAL del articulo (fix 2026-11-04)
        _extracto = (extractos_map or {}).get(m.get('titular', ''), '')
        if _extracto:
            medios_txt += f"EXTRACTO REAL DEL ARTICULO (usa DATOS de aqui, no inventes):\n{_extracto[:800]}\n"
    
    capa2_prompt = f"""Eres Carlos Alsina. Escribe la CAPA 2 del monólogo (500-600 palabras): INFORMAR.

Analiza estas 3 noticias REALES de hoy:
{medios_txt}

Contexto verificado por noticia (usa SOLO el contexto de cada noticia, NO mezcles):
{contexto_global[:2500] if contexto_global else "(sin contexto, usa solo los medios)"}

INSTRUCCIONES:
1. Empieza con: "Vamos a ver qué dicen los medios hoy."
2. Analiza cada medio (NO digas "el medio titula X", INTEGRA: "Fíjate en [medio], que publicó..."): titular, cita, qué omite
3. Compara: "Tres medios, tres versiones, un mismo hecho. ¿Cuál es la verdad?"
4. Usa el contexto oficial disponible (Wikipedia, EFE, agencias). Si la noticia es INTERNACIONAL (Trump, Israel, Ucrania, Rusia, China, Irán, EEUU, ONU, OTAN, Gaza), PROHIBIDO mencionar el BOE: el BOE es solo para noticias ESPAÑOLAS. Para internacional, usa EFE/Reuters/AP/Wikipedia.
5. OBLIGATORIO: cuando digas "no se menciona que X" o "se omite X", X debe ser un DATO REAL del EXTRACTO REAL del articulo. NUNCA dejes "no se menciona que," a medias. Si no tienes el dato, di "no se menciona el detalle" o salta al siguiente punto.
6. PROHIBIDO: escribir "No se menciona que,.", "Tampoco se explica que.", "ni que." o similares. Si no tienes el dato, no prometas explicarlo.
7. GEOGRAFÍA: Urda es Toledo, Atocha es Madrid. NO los mezcles.
8. CONTEXTO INVENTADO PROHIBIDO: si es Puente/Atocha, NO menciones Gaza ni reformas fiscales.
9. TRUMP ES PRESIDENTE (2026), no exmandatario.
5. Pregunta al oyente: "¿Por qué este medio cuenta esto HOY?"

TONO: frases cortas, pausas naturales, ironía fina.
PROHIBIDO: nombar técnicas, "Mira lo que publicó", "Resulta que...", fórmulas IA.

Devuelve SOLO el texto de la capa 2."""
    capa2 = _llm(capa2_prompt, min_palabras=400)
    print(f"      ✅ {len(capa2.split())} palabras, pasando abogado del diablo...", flush=True)
    capa2, alucinaciones2 = _pasar_abogado_del_diablo(capa2, medios_validos)
    if alucinaciones2:
        print(f"      🚨 {len(alucinaciones2)} alucinaciones detectadas, limpiando...", flush=True)
        for a in alucinaciones2[:3]:
            print(f"         - {a[:80]}", flush=True)
        capa2 = _limpiar_alucinaciones(capa2, alucinaciones2)
    print(f"      ✅ Capa 2 limpia: {len(capa2.split())} palabras", flush=True)
    
    # ─── CAPA 3: ENTRENAR (500 palabras) ───
    print(f"   [3/4] Entrenar (técnicas)...", flush=True)
    tecnicas_txt = ", ".join(tecnicas_unicas[:4]) if tecnicas_unicas else "manipulación"
    # Inyectar extractos reales para ejemplos de técnicas (fix 2026-11-04)
    _extractos_txt = ""
    for _m in medios_validos[:3]:
        _ex = (extractos_map or {}).get(_m.get('titular',''), '')
        if _ex:
            _extractos_txt += f"\n--- {_m['medio']} ---\n{_ex[:600]}\n"
    if _extractos_txt:
        _extractos_txt = "EXTRACTOS REALES DE LOS ARTICULOS (usa estos DATOS en tus ejemplos, NO inventes):" + _extractos_txt
    
    capa3_prompt = f"""Eres Carlos Alsina + Wyoming. Escribe la CAPA 3 del monólogo (400-500 palabras): ENTRENAR.

{_extractos_txt}

TAREA: Enseña 3 TÉCNICAS de manipulación que has detectado en las noticias anteriores.
Técnicas detectadas (NO las nombres con nombre técnico, describe su EFECTO): {tecnicas_txt}

EJEMPLOS de cómo describirlas:
- Card Stacking → "Apilan expertos, citas, datos. Y cuando has visto 10, tu cerebro dice: 'hay consenso'. Aunque los 10 sean del mismo grupo. Eso no es consenso, es eco."
- Fear Appeal → "Te meten el miedo en vena. Y con miedo, votas, compras, callas. El miedo vende."
- Name Calling → "Le ponen la etiqueta. Y la etiqueta se queda pegada. Como el precio en una camiseta."

INSTRUCCIONES:
1. Empieza con: "Ahora la pregunta del millón: ¿por qué nos lo creemos?"
2. Explica 3 técnicas (una por párrafo), cada una con un ejemplo cotidiano
3. Cierra con: 3 preguntas que el oyente debe hacerse mañana
   - ¿Dice la palabra clave o la esconde?
   - ¿Dice el dato o solo la emoción?
   - ¿Dice la fuente o solo la versión?

TONO: didáctico pero mordaz, frases cortas, pausas naturales.
PROHIBIDO: nombres técnicos (Card Stacking, Fear Appeal...), markdown, acotaciones.

Devuelve SOLO el texto de la capa 3."""
    capa3 = _llm(capa3_prompt, min_palabras=300)
    print(f"      ✅ {len(capa3.split())} palabras", flush=True)
    
    # ─── CAPA 4: CONCIENCIAR (300-400 palabras) ───
    print(f"   [4/4] Concienciar (cierre)...", flush=True)
    capa4_prompt = f"""Eres Carlos Alsina + Buenafuente. Escribe la CAPA 4 del monólogo (300-400 palabras): CIERRE.

INSTRUCCIONES:
1. Vuelve a la anécdota inicial: "Como [personaje de la anécdota], que no lee el BOE..." (recuerda la anécdota: {anecdota['texto'][:100]}...)
2. Reflexión empática: "No es tu culpa. El sistema está diseñado así. Pero tú puedes cambiarlo."
3. Repite las 3 preguntas: "Mañana, cuando veas un titular, pregúntate: ¿dice la palabra clave o la esconde? ¿Dice el dato o solo la emoción? ¿Dice la fuente o solo la versión?"
4. CTA natural: "Si te ha servido, comparte. Si no, no. Pero no te lo creas todo."
5. Cierre punch: "Mañana volverán a intentarlo. La diferencia es que ahora ya lo ves."

TONO: épico, cercano, con ganas. Frases cortas, pausas naturales.
PROHIBIDO: "Dale a like, suscríbete o comparte" (genérico), fórmulas IA.

Devuelve SOLO el texto de la capa 4."""
    capa4 = _llm(capa4_prompt, min_palabras=200)
    print(f"      ✅ {len(capa4.split())} palabras", flush=True)
    
    # Combinar
    texto_final = f"{capa1}\n\n{capa2}\n\n{capa3}\n\n{capa4}"
    print(f"\n   📝 Monólogo total: {len(texto_final.split())} palabras", flush=True)
    
    if len(texto_final.split()) < 1200:
        raise RuntimeError(f"Monólogo muy corto: {len(texto_final.split())} palabras")
    
    return texto_final

def _sanitizar_monologo(texto, fecha_iso=None):
    """Sanitiza patrones prohibidos que el LLM se salta. Determinista, no depende del LLM."""
    import re as _r, datetime as _dt
    if not texto:
        return texto
    t = texto

    # FECHA REAL: si hay doble "hoy", cambiar el segundo por fecha real
    try:
        d = _dt.date.fromisoformat(fecha_iso) if fecha_iso else _dt.date.today()
        MESES = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
        fecha_larga = f"{d.day} de {MESES[d.month-1]} de {d.year}"
    except Exception:
        fecha_larga = "hoy"
    t = t.replace("Somos El Encuadre, hoy.", f"Somos El Encuadre, este {fecha_larga}.")

    # NÚMEROS con espacio: "4. 000" -> "4.000" (miles) y "1. 500" -> "1.500"
    t = _r.sub(r'(\d)\. (\d{3})\b', r'\1.\2', t)

    # CABECERAS femenino
    t = _r.sub(r'\bTodos los cabeceras\b', 'Todas las cabeceras', t)
    t = _r.sub(r'\b[tT]odos los cabecera\b', 'Todas las cabeceras', t)

    # CTA: quitar "dale a like" y "suscríbete"
    t = _r.sub(r'[Dd]ale a like\.?\s*', '', t)
    t = _r.sub(r'Suscríbete si quieres más\.?\s*', '', t)
    t = _r.sub(r'Suscríbete\.?\s*', '', t)
    t = _r.sub(r'\bdale a la campanita\b\.?', '', t, flags=_r.I)

    # "caprichosamente" -> "deliberadamente"
    t = _r.sub(r'\bcaprichosamente\b', 'deliberadamente', t, flags=_r.I)

    # "Lee entre líneas" -> "Ya me entiendes"
    t = _r.sub(r'\b[Ll]ee entre líneas\b\.?', 'Ya me entiendes.', t)

    # "un mismo hecho" -> "un mismo día"
    t = _r.sub(r'\bun mismo hecho\b', 'un mismo día', t)

    # "hilo de sangre" -> "hilo de intereses"
    t = _r.sub(r'\bhilo de sangre\b', 'hilo de intereses', t)

    # "EuropaPress" -> "Europa Press"
    t = _r.sub(r'\bEuropaPress\b', 'Europa Press', t)

    # "Hablando de nuevas reformas" -> "Hablando de nueva gestión"
    t = _r.sub(r'\bnuevas reformas\b', 'nueva gestión', t)

    # FORZAR fecha en la intro: si aparece "Hasta este hoy" o variantes, sustituir por fecha real
    # Fecha: sustituir "hoy" tras "Hasta" por fecha real, y quitar duplicado de "Somos El Encuadre, fecha"
    t = _r.sub(r'Hasta\s+(este\s+)?(hoy|día de hoy|este día)', f'Hasta este {fecha_larga}', t, flags=_r.I)
    # Quitar duplicado "Somos El Encuadre, (este) fecha_larga" si ya hay fecha antes
    t = _r.sub(r'Somos El Encuadre,?\s*(este\s+)?' + _r.escape(fecha_larga) + r'\.', 'Somos El Encuadre.', t)
    meses = ["enero","febrero","marzo","abril","mayo","junio","julio","agosto","septiembre","octubre","noviembre","diciembre"]
    tiene_fecha = any(m in t.lower() for m in meses)
    if not tiene_fecha and "Somos El Encuadre." in t:
        t = t.replace("Somos El Encuadre.", f"Somos El Encuadre, {fecha_larga}.", 1)

    # FORZAR 3 preguntas antes del CTA si no aparecen
    preguntas_ok = ("palabra clave" in t.lower() and "emoción" in t.lower() and "versión" in t.lower())
    if not preguntas_ok:
        # Insertar bloque antes de "Nos vemos" o "comparte" o "Si esto"
        bloque_3p = "Y recuerda las tres preguntas de siempre: ¿dice la palabra clave o la esconde? ¿dice el dato o solo la emoción? ¿dice la fuente o solo la versión? "
        for marca in ["Nos vemos", "Si esto", "Comparte esto", "Comparte"]:
            if marca in t:
                t = t.replace(marca, bloque_3p + marca, 1)
                break

    # Limpieza CTA: "Si te ha servido, Y comparte" -> "Si te ha servido, comparte"
    t = _r.sub(r'Si te ha servido,\s*Y\s+', 'Si te ha servido, ', t, flags=_r.I)
    t = _r.sub(r',\s*Y\s+comparte', ', comparte', t, flags=_r.I)
    t = _r.sub(r',\s*,\s*', ', ', t)
    # HUÉRFANOS DE CONTENIDO (fix 2026-11-04): el LLM promete "no se menciona que X" y no rellena X
    # Caso 1: "No se menciona que,." / "No se menciona que." / "No se menciona que, ni que."
    t = _r.sub(r'[Nn]o se menciona que\s*[,.]', 'No se menciona el detalle.', t)
    t = _r.sub(r'[Nn]o se menciona que[^.]*?ni que\s*[,.]', 'No se mencionan los detalles.', t)
    # Caso 2: "Tampoco se explica que." / "Tampoco se explica que,"
    t = _r.sub(r'[Tt]ampoco se explica que\s*[,.]', 'Tampoco se explica el detalle.', t)
    # Caso 3: "... ni que." (huérfano al final)
    t = _r.sub(r',?\s*ni que\s*[,.]', '.', t)
    # Caso 4: "Además, no menciona que X ni que." -> "Además, no menciona el detalle."
    t = _r.sub(r'[Aa]demás, no menciona que[^.]*?(ni que\s*[,.]|\.)', 'Además, no menciona el detalle.', t)
    # Caso 5: "la verdad es que, pero..." / "la verdad es que, ni que..."
    t = _r.sub(r'la verdad es que\s*,\s*(pero|ni que|y que)', 'la verdad es que el detalle se omite, y', t, flags=_r.I)
    # Caso 6: cualquier "que," o "que." huérfano precedido de "no se menciona/tampoco/omite"
    t = _r.sub(r'\bque\s*,\s*\.', '.', t)
    t = _r.sub(r'\bque\s*\.\s*\.', '.', t)

    # LIMPIEZA AGRESIVA POST-LLM (fix 2026-11-04): el LLM no obedece todo
    # 1. "sugiere" / "sugieren" -> "indica" / "indican"
    t = _r.sub(r'\bsugiere\b', 'indica', t, flags=_r.I)
    t = _r.sub(r'\bsugieren\b', 'indican', t, flags=_r.I)
    t = _r.sub(r'\bsugeriría\b', 'indicaría', t, flags=_r.I)
    t = _r.sub(r'\bsugerirían\b', 'indicarían', t, flags=_r.I)

    # 2. "Además,." / "Además, ," -> "Además." / eliminar
    t = _r.sub(r'\bAdemás\s*[,.]\s*[,.]', 'Además.', t, flags=_r.I)
    t = _r.sub(r'\bAdemás\s*[,.]\s*\.', 'Además.', t, flags=_r.I)
    t = _r.sub(r'\bAdemás,\s*\.', 'Además.', t, flags=_r.I)

    # 3. Números con espacio: "4 000" -> "4.000"
    t = _r.sub(r'\b(\d{1,3}) (\d{3})\b', r'\1.\2', t)

    # 4. Huérfanos "que,." / "que ." / "ni que."
    t = _r.sub(r'\bque\s*[,.]\s*[,.]', 'el detalle.', t, flags=_r.I)
    t = _r.sub(r'\bque\s*[,.]\s*\.', 'el detalle.', t, flags=_r.I)
    t = _r.sub(r',?\s*ni que\s*[,.]', '.', t)

    # HUÉRFANOS CON VERBO + QUE (fix 2026-11-04): "asegura que." / "dice que." / "sino que."
    # Verbos que suelen quedar colgados con "que,." o "que ."
    VERBOS_QUE = r"(dice|dijo|asegura|aseguró|afirma|afirmó|sostiene|sostuvo|explica|explicó|reconoce|reconoció|admite|admitió|niega|negó|señala|señaló|indica|indicó|mantiene|mantuvo|defiende|defendió|insiste|insistió)"
    # "asegura que." o "asegura que,." -> "asegura el dato." (o eliminar el "que")
    t = _r.sub(VERBOS_QUE + r'\s+que\s*[,.]\s*[,.]?', r'\1 algo. ', t, flags=_r.I)
    t = _r.sub(VERBOS_QUE + r'\s+que\s*\.', r'\1 algo. ', t, flags=_r.I)
    # "sino que." -> "sino que el detalle." (o eliminar)
    t = _r.sub(r'\bsino que\s*[,.]\s*[,.]?', 'sino que el detalle. ', t, flags=_r.I)
    # "pero que." -> "pero el detalle."
    t = _r.sub(r'\bpero que\s*[,.]\s*[,.]?', 'pero el detalle.', t, flags=_r.I)
    # "y que." aislado -> "y el detalle."
    t = _r.sub(r'\by que\s*[,.]\s*[,.]?', 'y el detalle.', t, flags=_r.I)

    # 5. Doble punto o doble coma
    t = _r.sub(r'\.\s*\.(?!\.)', '.', t)
    t = _r.sub(r',\s*,', ',', t)

    # 6. Espacio antes de punto/coma
    t = _r.sub(r'\s+([.,;:!?])', r'\1', t)

    # C: doble cierre
    _m='Esto es El Encuadre.'
    if t.count(_m)>1: t=t[:t.find(_m)+len(_m)].strip()
    _m2='Mañana volverán a intentarlo'
    if t.count(_m2)>1:
        _p=t.find(_m2); _s=t.find(_m2,_p+1); t=t[:_s].rstrip()+' Esto es El Encuadre.'
    # D
    t=_r.sub(r'exmandatario','Trump',t,flags=_r.I)
    t=_r.sub(r'ex presidente','Trump',t,flags=_r.I)
    # E
    t=_r.sub(r'\.\s*Si no, no\.\s*','. ',t)
    t=_r.sub(r'Si no, no\.?\s*','',t)
    # Limpieza
    t = _r.sub(r'\s+', ' ', t)
    t = _r.sub(r'\s+\.', '.', t)
    t = _r.sub(r'\s+,', ',', t)
    # Comas dobles que hayan podido quedar
    t = _r.sub(r',\s*,', ',', t)
    return t.strip()


def _cargar_extractos(fecha):
    """Carga extractos de articulos del scrapeada.json para inyectar en el ACTO 2."""
    try:
        scr = OUT / f"recoleccion_{fecha}_scrapeada.json"
        if not scr.exists():
            scr = OUT / f"scrapeado_{fecha}.json"
        if not scr.exists():
            return {}
        d = json.loads(scr.read_text())
        # Formato 1: {"pool": [{titular, extracto}, ...]}
        pool = d.get("pool", [])
        if pool:
            return {n.get("titular",""): n.get("extracto","") or n.get("texto","") for n in pool if n.get("titular")}
        # Formato 2: {medio: [{titular, extracto}, ...]}
        out = {}
        for medio, lst in d.items():
            if isinstance(lst, list):
                for n in lst:
                    if isinstance(n, dict) and n.get("titular"):
                        out[n["titular"]] = n.get("extracto","") or n.get("texto","")
        return out
    except Exception as _e:
        print(f"   [extractos] Fallo carga: {_e}", flush=True)
        return {}


def producir_monologo(fecha=None):
    """Genera produccion_FECHA.json en MODO MONÓLOGO.
    Esquema IDÉNTICO a producir_fase2() pero las 18 escenas vienen de 1 texto."""
    import datetime, json as _json
    fecha = fecha or datetime.date.today().isoformat()
    # Cargar extractos reales de articulos (fix 2026-11-04: LLM decia "no se menciona que X" sin X)
    _extractos_map = _cargar_extractos(fecha)
    print(f"   [extractos] {len(_extractos_map)} articulos con extracto para inyectar", flush=True)
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
        # Extraer tema SIMPLIFICADO (2-3 palabras clave)
        titular = m["titular"]
        # Quitar comillas, CDATA, HTML
        import re as _re_ctx
        titular_limpio = _re_ctx.sub(r'<[^>]+>|CDATA\[|\]\]', '', titular).strip()
        titular_limpio = _re_ctx.sub(r'[«»""]', '', titular_limpio)
        # Coger primeras 4-5 palabras significativas
        palabras = [w for w in titular_limpio.split()[:8] if len(w) > 3]
        tema = " ".join(palabras[:4]) or titular_limpio[:60]
        print(f"   🔍 Tema: '{tema}'", flush=True)
        ctx_m = _cargar_contexto_verificado(titular_limpio[:100], m["medio"], tema)
        if ctx_m:
            contexto_global += f"\n=== {m['medio']} ===\n{ctx_m}\n"
        else:
            print(f"      ⚠️ Sin contexto para {m['medio']}", flush=True)
    
    # Generar monólogo
    print("[monologo] 4/5 Generando monólogo LLM...", flush=True)
    texto_monologo = _generar_monologo_llm(anecdota, medios_validos, contexto_global, fecha_str, tecnicas, extractos_map=_extractos_map)
    print(f"   Monólogo: {len(texto_monologo.split())} palabras", flush=True)
    
    # Splitter 1 → 18
    print("[monologo] 5/5 Dividiendo en 18 escenas...", flush=True)
    from splitter_monologo import splitter
    escenas = splitter(texto_monologo, num_escenas=18)
    print(f"   Escenas generadas: {len(escenas)}", flush=True)
    
    res["escenas"] = escenas
    res["texto_voz_largo"] = _sanitizar_monologo(" ".join([e.get("texto", "") for e in escenas]), fecha)
    for _e in escenas:
        _e["texto"] = _sanitizar_monologo(_e.get("texto", ""), fecha)
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




# ═══════════════════════════════════════════════════════════════
# FIXES 2026-11-03: tema + alucinaciones
# ═══════════════════════════════════════════════════════════════
def _extraer_tema(titular):
    """Extrae el tema/entidad clave de un titular. Robusto."""
    if not titular: return ""
    m = re.search(r'[«"]([^»"]{15,80})[»"]', titular)
    if m: return m.group(1).strip()[:60]
    ARTICULOS = {'El','La','Los','Las','Un','Una','Y','O','En','De','Del','Al','Por','Para','Con','Sin','Que'}
    for w in titular.split():
        w_clean = re.sub(r'[^A-Za-zÁÉÍÓÚÑáéíóúñ]', '', w)
        if len(w_clean) > 3 and w_clean[0].isupper() and w_clean not in ARTICULOS:
            return w_clean
    palabras = [w for w in titular.split() if len(w) > 3][:5]
    return " ".join(palabras)


def _validar_alucinaciones(texto, top16):
    """Devuelve lista de nombres propios que NO están en el top16."""
    nombres = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b', texto)
    texto_top = ' '.join([t.get('titular','') + ' ' + t.get('extracto','') for t in top16])
    WHITELIST = {'España','Madrid','Barcelona','Gobierno','Congreso','Senado','BOE',
                 'Europa','Español','Española','Nacional','General','Real','Policía',
                 'Agencia','EFE','Reuters','AP','Wikipedia','Teléfono','WhatsApp',
                 'Telegram','Twitter','Facebook','Instagram','TikTok','YouTube',
                 'Somos','Encuadre','Club','Lunes','Martes','Miércoles','Jueves',
                 'Viernes','Sábado','Domingo','Enero','Febrero','Marzo','Abril',
                 'Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre',
                 'Diciembre','Señor','Señora','Don','Doña'}
    alucinaciones = []
    for n in set(nombres):
        if n not in texto_top and n not in WHITELIST:
            alucinaciones.append(n)
    return alucinaciones


def _buscar_contexto_ddg(titular, medio, entidad_clave=""):
    """Contexto real: DDG (UA honesto) -> fallback Google News RSS. Sin API key."""
    import urllib.request, urllib.parse, re as _re, html as _html
    NL = chr(10)

    UA = "LofiProducer/1.0 (Termux; +https://github.com/keizdespania/LofiProducer)"
    HEADERS = {
        "User-Agent": UA,
        "Accept-Language": "es-ES,es;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def _ddg(q, max_r=3):
        try:
            url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote_plus(q)
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=6) as r:
                if r.status != 200:
                    print("[ddg] HTTP " + str(r.status) + " -> fallback", flush=True)
                    return ""
                txt = r.read().decode("utf-8", errors="ignore")
            if "result__a" not in txt:
                print("[ddg] sin result__a -> fallback", flush=True)
                return ""
            bloques = _re.findall(
                r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                txt, _re.DOTALL
            )
            out = []
            for url_res, tit, snip in bloques[:max_r]:
                tit = _re.sub(r"<[^>]+>", "", _html.unescape(tit)).strip()[:120]
                snip = _re.sub(r"<[^>]+>", "", _html.unescape(snip)).strip()[:250]
                out.append("  - " + tit + NL + "    " + snip)
            return NL.join(out)
        except Exception as e:
            print("[ddg] " + type(e).__name__ + ": " + str(e) + " -> fallback", flush=True)
            return ""

    def _gnews(q, max_r=3):
        try:
            url = "https://news.google.com/rss/search?q=" + urllib.parse.quote_plus(q) + "&hl=es&gl=ES&ceid=ES:es"
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as r:
                txt = r.read().decode("utf-8", errors="ignore")
            items = _re.findall(r"<item>(.*?)</item>", txt, _re.DOTALL)
            out = []
            for it in items[:max_r]:
                t = _re.search(r"<title>(.*?)</title>", it, _re.DOTALL)
                d = _re.search(r"<pubDate>(.*?)</pubDate>", it, _re.DOTALL)
                if not t:
                    continue
                tit = _html.unescape(_re.sub(r"<[^>]+>", "", t.group(1))).strip()[:140]
                fecha = ""
                if d:
                    fecha = _re.sub(r"<[^>]+>", "", d.group(1)).strip()[:30]
                linea = "  - " + tit
                if fecha:
                    linea += "  [" + fecha + "]"
                out.append(linea)
            return NL.join(out)
        except Exception as e:
            print("[gnews] " + type(e).__name__ + ": " + str(e), flush=True)
            return ""

    tema = entidad_clave or _extraer_tema(titular) or " ".join(titular.split()[:5])
    medio_limpio = medio.strip()

    q1 = chr(34) + titular[:80] + chr(34)
    r1 = _ddg(q1, max_r=3)
    if not r1:
        r1 = _gnews(tema + " " + medio_limpio, max_r=3)
        if r1:
            r1 = "[GNEWS]" + NL + r1

    q2 = chr(34) + tema + chr(34) + " agencia EFE Reuters Europa Press"
    r2 = _ddg(q2, max_r=3)
    if not r2:
        r2 = _gnews(tema + " EFE OR Reuters OR Europa Press", max_r=3)
        if r2:
            r2 = "[GNEWS]" + NL + r2

    partes = []
    if r1:
        partes.append("COBERTURA EN OTROS MEDIOS:" + NL + r1)
    if r2:
        partes.append("FUENTES OFICIALES / AGENCIAS:" + NL + r2)
    return (NL + NL).join(partes)



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

def _a_especialista(rol, tarea, contexto=""):
    """Alias de pedir_a_especialista."""
    from especialistas import pedir_a_especialista
    return pedir_a_especialista(rol, tarea, contexto=contexto)

def _monologo(*args, **kwargs):
    """Alias placeholder (no debería usarse)."""
    return ""

def _text(*args, **kwargs):
    """Alias placeholder (no debería usarse)."""
    return ""
