"""Agente 1: detecta tendencias de YouTube en el nicho."""
import json
from datetime import datetime, timezone
from pathlib import Path
from core.logger import get_logger
from core.llm import ask

log = get_logger("brain.tendencias")

def analizar(tendencias_json: Path) -> dict:
    data = json.loads(tendencias_json.read_text(encoding='utf-8'))
    top10 = data.get("videos", [])[:10]
    lista = "\n".join(f"- {v['titulo']} ({v['vistas']:,} vistas)" for v in top10)
    prompt = f"""Analiza estas tendencias Lofi virales:
{lista}

Devuelve JSON con:
{{"patrones": ["..."], "keywords_alta_demanda": ["..."], "saturacion": "baja|media|alta", "recomendacion": "..."}}"""
    resp = ask(prompt, temperature=0.5)
    try:
        inicio = resp.find("{"); fin = resp.rfind("}")
        return json.loads(resp[inicio:fin+1])
    except Exception as e:
        log.warning("Error parseando: %s", e)
        return {"error": str(e), "raw": resp[:300]}

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python -m brain.agent_tendencias <tendencias.json>")
        sys.exit(1)
    print(json.dumps(analizar(Path(sys.argv[1])), indent=2, ensure_ascii=False))
