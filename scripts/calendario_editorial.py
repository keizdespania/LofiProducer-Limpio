"""calendario_editorial.py - Planifica 7 días de contenido."""
import json, pathlib, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "calendario_editorial.json"

def planificar():
    dias = [(datetime.date.today() + datetime.timedelta(days=i)).isoformat() for i in range(7)]
    plan = {d: "Noticias de actualidad" for d in dias}
    OUT.write_text(json.dumps(plan, indent=2))
    print("✅ Calendario de 7 días generado.")

if __name__ == "__main__": planificar()
