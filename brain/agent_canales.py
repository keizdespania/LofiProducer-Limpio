"""Agente: propone canales multi-nicho por lotes de 5."""
import json
from core.config import DATA_DIR
from core.logger import get_logger
from core.llm import ask

log = get_logger("brain.canales")

PROMPT = """Propón 5 canales de YouTube para un ecosistema automatizado con IA.
RPM 2026: Finance $23, AI News $21, Tech $21, Investing $21, Politics $19, Physics $19, Economics $18, Lifestyle $17.5, History $9, Lofi $5.
Devuelve SOLO JSON válido (sin markdown):
{"canales":[{"id":"snake","nombre":"Nombre","nicho":"desc","rpm":"$X-Y","oportunidad":8.5,"duracion":"estandar","paleta":"oscuro","tags":["a"],"prompt_audio":"english prompt","justificacion":"1 linea"}]}"""


def proponer_lote(hint: str) -> list[dict]:
    prompt = PROMPT + f"\n\nEnfócate en: {hint}"
    resp = ask(prompt, temperature=0.7)
    limpio = resp.strip()
    if limpio.startswith("```"):
        limpio = limpio.split("\n", 1)[1]
    if limpio.endswith("```"):
        limpio = limpio.rsplit("```", 1)[0]
    try:
        return json.loads(limpio.strip()).get("canales", [])
    except json.JSONDecodeError as e:
        log.error("Lote invalido: %s", e)
        return []


if __name__ == "__main__":
    hints = [
        "Alto RPM (>$20): finanzas, AI news, tech, investing",
        "Educacion/ciencia: physics, economics, history",
        "Lifestyle/wellness: salud, meditacion, productividad",
        "Espanol: finanzas, tech, historia, noticias",
    ]

    todos: list[dict] = []
    for i, hint in enumerate(hints, 1):
        log.info("Lote %d/4: %s", i, hint)
        lote = proponer_lote(hint)
        log.info("  -> %d canales", len(lote))
        todos.extend(lote)

    out = DATA_DIR / "canales_propuesta.json"
    out.write_text(json.dumps({"canales": todos}, indent=2, ensure_ascii=False),
                   encoding="utf-8")

    print()
    print("=" * 60)
    print(f"TOTAL: {len(todos)} canales propuestos")
    print("=" * 60)
    for c in todos:
        print(f"  {c.get('id','?'):20} {c.get('nombre','?'):30} {c.get('rpm','?'):8}")
    print("=" * 60)
    print(f"[OK] Guardado en {out}")
