"""render_short_rot.py - Genera un short con rot usando el contrato."""
import sys, pathlib, subprocess, asyncio
from rot import Project, RenderSettings, CaptionTheme, Placement
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def generar_short(img, texto, voz_path, musica_path, salida):
    theme = CaptionTheme(font="monospace", font_size=44, max_words=5, position=Placement(0.5, 0.85, anchor="center"))
    project = (
        Project(settings=RenderSettings(captions=True))
        .short_form()
        .background(str(img), fit="cover", loop=True)
        .add_speaker("narrator")
        .script(f"@narrator [audio={voz_path}]: {texto}")
        .captions(theme=theme)
    )
    if musica_path and pathlib.Path(musica_path).exists():
        project = project.soundtrack(str(musica_path), volume=0.15, ducking=True, fade_out=1.0)
    
    project.render(str(salida), overwrite=True)
    return salida

if __name__ == "__main__":
    # Ejemplo de uso rápido
    print("✅ Contrato guardado y script base creado. Listo para integrar en Fase 2.")
