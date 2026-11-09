"""prompt_thumbnail.py - Prompt SDXL top-1 para miniaturas El Encuadre.
3 capas: concepto del titular + estilo El Encuadre + composición thumbnail."""
import re

# ═══════════════════════════════════════════════════════════
# CAPA 1: Concepto del titular → objeto visual dominante
# ═══════════════════════════════════════════════════════════
CONCEPTOS = {
    # Política / Gobierno
    "ayuso": "shadowy puppet strings attached to a red high heel",
    "sánchez": "a hand pulling strings of a marionette wearing a suit",
    "sanchez": "a hand pulling strings of a marionette wearing a suit",
    "feijóo": "a giant chess piece casting a long shadow",
    "feijoo": "a giant chess piece casting a long shadow",
    "psoe": "a red rose wilting on a marble floor",
    "pp": "a blue suit jacket on a wooden hanger in a dark room",
    "vox": "a torn green flag flapping in the wind",
    "gobierno": "empty parliamentary seats with microphones glowing red",
    "congreso": "a giant gavel suspended over a cracked floor",
    "elecciones": "a ballot box with a shadowy hand reaching out",
    
    # Economía / Dinero
    "inflación": "shopping cart with prices rising like flames",
    "inflacion": "shopping cart with prices rising like flames",
    "nvidia": "a glowing microchip casting red reflections on dark glass",
    "bitcoin": "a golden coin falling into a dark chasm",
    "vivienda": "a small house crushed by falling coins",
    "alquiler": "keys hanging on a rusty hook, dark corridor",
    "desahucio": "a cracked door with faded shadows on the floor",
    "hipoteca": "a house sinking into dark water",
    
    # Sucesos / Tragedias
    "tren": "a derailed train car in darkness, emergency lights",
    "accidente": "shattered glass reflecting red emergency lights",
    "urda": "a train track ending abruptly in fog",
    "paracuellos": "old faded photographs scattered on a dark table",
    "guerra": "a child's toy soldier lying on burnt ground",
    "muerte": "a single white flower on a cracked surface",
    
    # Medios / Información
    "medios": "a wall of glowing TV screens showing blurred faces",
    "manipulación": "a hand inside a puppet theater cast in red light",
    "manipulacion": "a hand inside a puppet theater cast in red light",
    "prensa": "a stack of newspapers burning slowly at the edges",
    "noticias": "a broken television screen with static",
    "desinformación": "a cracked mirror reflecting a distorted face",
    "desinformacion": "a cracked mirror reflecting a distorted face",
    "sesgo": "a distorted prism casting two different shadows",
    "framing": "a photo frame crooked on a dark wall",
    
    # Geopolítica
    "israel": "a bullet casing on a map of the Middle East",
    "gaza": "smoke rising over silhouettes of buildings at dusk",
    "ucrania": "a shattered sunflower on cracked earth",
    "china": "a dragon statue with glowing red eyes in smoke",
    "rusia": "a single red star glowing in dark fog",
    "eeuu": "a tarnished eagle statue in a dark room",
    "trump": "a golden podium with a shadow of a hand on it",
    
    # Tecnología
    "ia": "a glowing humanoid eye made of circuits in darkness",
    "inteligencia artificial": "a human brain made of glowing wires",
    "chatgpt": "a floating keyboard with fingers dissolving into pixels",
    "openai": "a paperclip bending shadows on a dark desk",
    "google": "a magnifying glass on a cracked screen",
    "musk": "a rocket silhouette against a blood-red sky",
    
    # Deporte
    "fútbol": "a football frozen mid-air in the rain",
    "futbol": "a football frozen mid-air in the rain",
    "mbappé": "a lone football boot on an empty stadium floor",
    "mbappe": "a lone football boot on an empty stadium floor",
}

# ═══════════════════════════════════════════════════════════
# CAPA 2: Estilo visual El Encuadre (fijo)
# ═══════════════════════════════════════════════════════════
ESTILO = "dramatic cinematic lighting, red and cold blue split lighting, deep shadows, dark moody thriller atmosphere, high contrast, professional editorial photography, shallow depth of field"

# ═══════════════════════════════════════════════════════════
# CAPA 3: Composición thumbnail (fijo)
# ═══════════════════════════════════════════════════════════
COMPOSICION = "16:9 aspect, single dominant subject centered with negative space on one side for text, no text no letters no words no watermark, minimalist, sharp focus, thumbnail-friendly"

def generar_prompt(titular, tipo="largo"):
    """Genera prompt completo: concepto + estilo + composición."""
    if not titular: return f"Newspaper on dark table with red lighting, {ESTILO}, {COMPOSICION}"
    
    # Buscar concepto (primera coincidencia de mayor longitud)
    low = titular.lower()
    mejor_match = ""
    mejor_score = 0
    for kw, visual in CONCEPTOS.items():
        if kw in low:
            score = len(kw)  # keyword más específica gana
            if score > mejor_score:
                mejor_score = score
                mejor_match = visual
    
    if not mejor_match:
        # Fallback: extraer entidad principal del titular
        # Buscar nombres propios (mayúscula seguida de minúsculas)
        nombres = re.findall(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,}\b', titular)
        stop = {"El", "La", "Los", "Las", "Un", "Una", "Del", "De", "En", "Por", "Para", "Con", "Sin", "Y", "O", "Pero"}
        nombres = [n for n in nombres if n not in stop][:2]
        if nombres:
            mejor_match = f"symbolic object representing {', '.join(nombres)}, abstract editorial still life"
        else:
            mejor_match = "newspaper burning slowly, dramatic red lighting"
    
    return f"{mejor_match}, {ESTILO}, {COMPOSICION}"


if __name__ == "__main__":
    # Test con 5 titulares reales
    tests = [
        "ABC: La vivienda, mayor problema nacional entre los votantes",
        "Ayuso: la mafia sindical contra Sánchez",
        "Nvidia: investigación sobre el consejero delegado",
        "Tren descarrilado en Urda: sin víctimas",
        "Manipulación mediática en la campaña electoral",
    ]
    for t in tests:
        print(f"\n📰 {t[:60]}")
        print(f"   → {generar_prompt(t)[:200]}")
