"""Agente 5: genera PDF con ideas y notifica al móvil."""
from datetime import datetime, timezone
from pathlib import Path
from core.config import DATA_DIR
from core.logger import get_logger

log = get_logger("brain.pdf")

def generar_pdf_md(contenido: str, titulo: str) -> Path:
    """Genera un .md y lo convierte a PDF si hay pandoc."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    md = DATA_DIR / f"reporte_{ts}.md"
    md.write_text(f"# {titulo}\n\n{contenido}", encoding="utf-8")

    pdf = DATA_DIR / f"reporte_{ts}.pdf"
    import shutil
    if shutil.which("pandoc"):
        import subprocess
        subprocess.run(
            ["pandoc", str(md), "-o", str(pdf)],
            capture_output=True, text=True
        )
        if pdf.exists():
            return pdf
    return md

def notificar(ruta: Path, mensaje: str = "Reporte listo"):
    import shutil, subprocess
    if not shutil.which("termux-notification"):
        log.warning("termux-notification no disponible")
        return
    subprocess.run([
        "termux-notification",
        "--title", "📊 KeiZ Productions",
        "--content", mensaje,
        "--priority", "high",
        "--action", f"termux-open {ruta}",
    ], capture_output=True)

if __name__ == "__main__":
    r = generar_pdf_md("## Demo\nContenido de prueba", "Reporte Demo")
    print(f"✅ {r}")
    notificar(r, "PDF demo listo")
