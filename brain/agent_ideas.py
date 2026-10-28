"""Agente 2: brainstorming de nichos e ideas."""
import json
from core.logger import get_logger
from core.llm import ask

log = get_logger("brain.ideas")

def brainstorming(nicho: str, n: int = 5) -> dict:
    prompt = f"""Genera {n} ideas de contenido para el nicho "{nicho}" en YouTube.
Analiza RPM, competencia y formato.

Devuelve JSON:
{{"ideas": [{{"titulo": "...", "formato": "...", "rpm_estimado": "$X-Y", "competencia": "baja|media|alta", "monetizacion": "..."}}]}}"""
    resp = ask(prompt, temperature=0.9)
    try:
        inicio = resp.find("{"); fin = resp.rfind("}")
        return json.loads(resp[inicio:fin+1])
    except Exception as e:
        return {"error": str(e), "raw": resp[:300]}

if __name__ == "__main__":
    import sys
    nicho = sys.argv[1] if len(sys.argv) > 1 else "productividad con IA"
    print(json.dumps(brainstorming(nicho), indent=2, ensure_ascii=False))
