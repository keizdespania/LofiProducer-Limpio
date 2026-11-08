"""director_fotografia.py - Traduce cualquier texto a un prompt visual de cine (Top 1 SDXL).
Usa Groq 4 directo (qwen3.8-27b) saltándose el firewall de especialistas.
"""
import urllib.request, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROMPT_MAESTRO = """Eres un director de fotografía. Traduce el texto a una descripción visual directa y literal en INGLÉS.
REGLAS:
1. Describe la ropa, los muebles, las caras y las acciones de forma sencilla.
2. PROHIBIDO pedir texto legible. Si el texto habla de noticias o fechas, di "newspaper with red marker" o "papers on a desk".
3. Usa máximo 25 palabras. No uses etiquetas de marketing ("8k, masterpiece").
4. Devuelve EXCLUSIVAMENTE el prompt visual en inglés, sin explicaciones.

EJEMPLO 1:
Texto: "Los medios no informan, venden."
Prompt: A man watching a wall of glowing television screens, red price tags on the screens, 16:9, no text.

EJEMPLO 2:
Texto: "El político dimite por el accidente de tren."
Prompt: Two politicians in suits sitting on red leather sofas, tense angry faces, a Spanish flag in the background, 16:9, no text.

Texto: "{TEXTO}"
Prompt:"""

# Fallback desesperado (si Groq explota)
DICCIONARIO_FALLBACK = {
    "tren": "A crashed train on fire, cinematic, 16:9, no text",
    "muerto": "A silent memorial with white candles, cinematic, 16:9, no text",
    "medios": "A wall of glowing television screens, cinematic, 16:9, no text",
    "prensa": "A stack of old newspapers, cinematic, 16:9, no text",
    "dinero": "Falling stock market charts in red, cinematic, 16:9, no text",
    "gobierno": "A politician standing alone in a dark hall, cinematic, 16:9, no text",
    "súper": "A supermarket aisle with fluorescent lights, cinematic, 16:9, no text",
    "oferta": "A glowing red price tag on a supermarket shelf, cinematic, 16:9, no text",
    "calle": "An empty street at night with neon lights, cinematic, 16:9, no text",
    "guerra": "A dark military map with red pins, cinematic, 16:9, no text",
    "fake": "A cracked television screen, cinematic, 16:9, no text",
    "mentira": "A cracked mirror in a dark room, cinematic, 16:9, no text",
}

# 2026-11-08: 8 estilos visuales rotativos (anti-monotonía)
ESTILOS_VISUALES = [
    "cinematic noir, high contrast, wet streets at night, 16:9, no text",
    "documentary photojournalism, natural light, subtle grain, 16:9, no text",
    "editorial illustration, muted palette, cross-hatching, 16:9, no text",
    "70s film archive, faded warm colors, dust specks, 16:9, no text",
    "neon cyberpunk, magenta and cyan, shallow depth, 16:9, no text",
    "minimalist product shot, dramatic single shadow, 16:9, no text",
    "macro detail close-up, extreme shallow depth of field, 16:9, no text",
    "wide landscape golden hour, backlit silhouette, 16:9, no text",
]

PATTERN_INTERRUPTS = [
    "broken mirror reflecting distorted faces, dark room, red light, 16:9, no text",
    "hourglass draining sand, dramatic single beam, 16:9, no text",
    "red thread connecting pins on a world map, 16:9, no text",
    "single match igniting in darkness, macro, 16:9, no text",
    "ripple expanding in black water, top-down, 16:9, no text",
    "static TV noise with faint silhouette, 16:9, no text",
    "macro human eye reflecting chaos, 16:9, no text",
    "shattered glass spiral frozen mid-air, 16:9, no text",
    "clock with no hands, empty room, 16:9, no text",
    "chalk outline on dark floor, single spotlight, 16:9, no text",
]

def _elegir_estilo(fecha, idx):
    import random as _r
    seed = (hash(str(fecha)) ^ (int(idx) * 2654435761)) & 0xFFFFFFFF
    return ESTILOS_VISUALES[_r.Random(seed).randint(0, len(ESTILOS_VISUALES)-1)]

def _elegir_pattern(fecha, idx):
    import random as _r
    seed = (hash(str(fecha)) ^ (int(idx) * 7919)) & 0xFFFFFFFF
    return PATTERN_INTERRUPTS[_r.Random(seed).randint(0, len(PATTERN_INTERRUPTS)-1)]


def _leer_groq_keys():
    keys = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY"):
                keys.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    return keys

def _llamar_groq(prompt, key):
    payload = {
        "model": "qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 500
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        out = json.loads(r.read())
        return out["choices"][0]["message"]["content"].strip()

def generar_prompt_visual(texto, vertical=False, idx=0, fecha=""):
    """Convierte texto en prompt en inglés. Rota 8 estilos visuales por (fecha, idx)."""
    _f = str(fecha) or "hoy"
    if not texto or len(texto.strip()) < 10:
        p = _elegir_estilo(_f, idx)
        return p.replace("16:9", "9:16 vertical") if vertical else p

    if "[PATTERN INTERRUPT]" in texto:
        p = _elegir_pattern(_f, idx)
        return p.replace("16:9", "9:16 vertical") if vertical else p

    prompt_final = PROMPT_MAESTRO.replace("{TEXTO}", texto[:300])
    keys = _leer_groq_keys()
    estilo = _elegir_estilo(_f, idx)

    for key in keys:
        try:
            r = _llamar_groq(prompt_final, key)
            r = r.strip().strip('"').strip("'").split("\n")[-1]
            if len(r) > 15 and not re.search(r'[ñáéíóú]', r.lower()):
                r_clean = re.sub(r',\s*16:9[^,]*$', '', r).strip().rstrip(',').strip()
                if vertical:
                    return f"{r_clean}, 9:16 vertical, no text"
                sufijo = estilo.split(', ', 1)[1] if ', ' in estilo else 'cinematic, 16:9, no text'
                return f"{r_clean}, {sufijo}"
        except Exception:
            continue

    texto_lower = texto.lower()
    for kw, prompt in DICCIONARIO_FALLBACK.items():
        if kw in texto_lower:
            return prompt.replace("16:9", "9:16 vertical") if vertical else prompt

    p = _elegir_estilo(_f, idx)
    return p.replace("16:9", "9:16 vertical") if vertical else p


if __name__ == "__main__":
    # Test rápido si se ejecuta directo
    print(generar_prompt_visual("El tren descarriló y dejó 115 muertos."))
