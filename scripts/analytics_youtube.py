"""analytics_youtube.py - Extrae métricas para el feedback loop."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "agent" / "analytics_aprendizaje.json"
OUT.parent.mkdir(parents=True, exist_ok=True)

def extraer():
    # Placeholder para YouTube Analytics API
    datos = {"mejor_ctr": 8.5, "mejor_retencion": 45.0, "palabras_clave": ["manipulacion", "medios"]}
    OUT.write_text(json.dumps(datos, indent=2))
    print(f"✅ Analytics guardados en {OUT}")

if __name__ == "__main__": extraer()
