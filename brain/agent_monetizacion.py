"""Agente 4: analiza opciones de monetización para un nicho."""
import json
from core.logger import get_logger
from core.llm import ask

log = get_logger("brain.monetizacion")

def analizar(nicho: str) -> dict:
    prompt = f"""Analiza TODAS las fuentes de monetización posibles
para un canal de YouTube del nicho "{nicho}" en 2027.

Devuelve JSON con:
{{
  "fuentes": [
    {{
      "tipo": "AdSense|afiliados|patrocinios|productos|servicios|B2B",
      "descripcion": "...",
      "rpm_estimado": "$X-Y",
      "tiempo_activar": "X meses",
      "dificultad": "baja|media|alta",
      "requisitos": "..."
    }}
  ],
  "prioridad_recomendada": ["..."],
  "ingresos_estimados_mes_6": "$X-Y",
  "ingresos_estimados_mes_12": "$X-Y"
}}"""
    resp = ask(prompt, temperature=0.7)
    try:
        i, f = resp.find("{"), resp.rfind("}")
        return json.loads(resp[i:f+1])
    except Exception as e:
        return {"error": str(e), "raw": resp[:400]}

if __name__ == "__main__":
    import sys
    nicho = sys.argv[1] if len(sys.argv) > 1 else "lofi music"
    print(json.dumps(analizar(nicho), indent=2, ensure_ascii=False))
