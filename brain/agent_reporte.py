"""Agente 3: genera reporte diario en Markdown."""
from datetime import datetime, timezone
from pathlib import Path
from core.config import DATA_DIR
from core.logger import get_logger

log = get_logger("brain.reporte")

def generar_reporte(secciones: dict) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = DATA_DIR / f"reporte_{ts}.md"
    lineas = [f"# 📊 Reporte KeiZ — {ts}", ""]
    for titulo, contenido in secciones.items():
        lineas.append(f"## {titulo}")
        if isinstance(contenido, dict):
            lineas.append("```json")
            import json
            lineas.append(json.dumps(contenido, indent=2, ensure_ascii=False))
            lineas.append("```")
        else:
            lineas.append(str(contenido))
        lineas.append("")
    out.write_text("\n".join(lineas), encoding='utf-8')
    log.info("Reporte: %s", out)
    return out

if __name__ == "__main__":
    r = generar_reporte({"Demo": {"status": "OK"}})
    print(f"✅ {r}")
