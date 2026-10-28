"""optimizador_adsense.py - A/B testing de anuncios."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
CONF = ROOT / "output" / "adsense_config.json"
CONF.write_text(json.dumps({"posicion": "top", "test": "A"}, indent=2))
print("✅ Configuración de AdSense actualizada.")
