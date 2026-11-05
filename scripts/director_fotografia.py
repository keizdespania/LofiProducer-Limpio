"""director_fotografia.py - Traduce cualquier texto a un prompt visual de cine (Top 1 SDXL).
Usa Groq 4 directo (qwen3.8-27b) saltándose el firewall de especialistas.
"""
import urllib.request, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROMPT_MAESTRO = """Eres el mejor director de fotografía de cine. Traduce el texto a una descripción visual en INGLÉS.
REGLAS: Describe solo lo que se ve (sujetos, objetos, acciones). Sin conceptos abstractos. Sin listas de etiquetas. Máximo 25 palabras.
Devuelve EXCLUSIVAMENTE el prompt visual en inglés, sin explicaciones.

EJEMPLO:
Texto: "Los medios no informan, venden."
Prompt: A man in a dark room watching a wall of glowing television screens that are displaying red price tags instead of news, cinematic, 16:9, no text.

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

def generar_prompt_visual(texto, vertical=False):
    """Convierte un texto en un prompt en inglés usando la cascada de Groq."""
    if not texto or len(texto.strip()) < 10:
        return "cinematic abstract scene, 16:9, no text"
        
    if "[PATTERN INTERRUPT]" in texto:
        return "abstract glowing question mark in a dark room, red lighting, cinematic, 16:9, no text"

    prompt_final = PROMPT_MAESTRO.replace("{TEXTO}", texto[:300])
    keys = _leer_groq_keys()

    # Cascada por si alguna key está agotada
    for key in keys:
        try:
            r = _llamar_groq(prompt_final, key)
            r = r.strip().strip('"').strip("'").split('\n')[-1]
            # Verificar que es inglés (sin tildes ni ñ)
            if len(r) > 15 and not re.search(r'[ñáéíóú]', r.lower()):
                # Si es vertical, lo adaptamos para el short
                if vertical:
                    return f"{r.replace('16:9', '9:16 vertical')}, cinematic, no text"
                return r
        except Exception:
            continue # Si falla esta key, pasamos a la siguiente de la cascada

    # Fallback (si todas las IAs han fallado)
    texto_lower = texto.lower()
    for kw, prompt in DICCIONARIO_FALLBACK.items():
        if kw in texto_lower:
            if vertical:
                return prompt.replace("16:9", "9:16 vertical")
            return prompt

    # Fallback final
    if vertical:
        return "cinematic abstract scene about media analysis, 9:16 vertical, no text"
    return "cinematic abstract scene about media analysis, 16:9, no text"

if __name__ == "__main__":
    # Test rápido si se ejecuta directo
    print(generar_prompt_visual("El tren descarriló y dejó 115 muertos."))
