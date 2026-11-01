"""render_short_rot.py - Genera un short con rot usando el contrato."""
import sys, pathlib, subprocess, asyncio
from rot import Project, RenderSettings, CaptionTheme, Placement
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def generar_short(img, texto, voz_path, musica_path, salida):
    import re
    texto = re.sub(r"[\r\n]+", " ", texto).replace('"', "").strip()
    theme = CaptionTheme(font="monospace", font_size=44, position=Placement(0.5, 0.85, anchor="center"))
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



def _dur_audio(audio_path):
    """Duración real del audio (voz). Fallback: 30s."""
    try:
        import subprocess
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=10
        )
        return float(r.stdout.strip()) if r.stdout.strip() else 30.0
    except:
        return 30.0


def generar_short_multi(imagenes, texto, voz_path, musica_path, salida, logo_path=None):
    """Short con MÚLTIPLES imágenes (cambio cada ~10s) + intro/outro overlay.
    
    Args:
        imagenes: lista de rutas (3-4 imágenes). Si 1 sola, delega a generar_short.
        logo_path: opcional, para overlay de intro/outro.
    
    Fallback: si rot falla con multi-imagen, cae a generar_short() con la primera.
    """
    imagenes = [p for p in imagenes if p and pathlib.Path(p).exists()]
    if not imagenes:
        raise ValueError("Sin imágenes existentes")
    
    if len(imagenes) == 1:
        return generar_short(imagenes[0], texto, voz_path, musica_path, salida)
    
    # Duración total del audio
    dur_total = _dur_audio(voz_path)
    n_img = len(imagenes)
    dur_por_img = dur_total / n_img
    
    try:
        # Construir proyecto con N backgrounds encadenados
        import re
        texto_limpio = re.sub(r"[\r\n]+", " ", texto).replace('"', "").strip()
        theme = CaptionTheme(font="monospace", font_size=44, position=Placement(0.5, 0.85, anchor="center"))
        
        project = (
            Project(settings=RenderSettings(captions=True))
            .short_form()
            .add_speaker("narrator")
        )
        
        # Encadenar N imágenes con duration cada una
        for i, img in enumerate(imagenes):
            project = project.background(
                str(img),
                duration=dur_por_img,
                fit="cover",
                loop=True,
                clip_id=f"bg_{i}"
            )
        
        # Script de voz
        project = project.script(f"@narrator [audio={voz_path}]: {texto_limpio}")
        project = project.captions(theme=theme)
        
        # Intro overlay (logo 0.8s)
        if logo_path and pathlib.Path(logo_path).exists():
            try:
                project = project.overlay_image(
                    str(logo_path),
                    at=0.0,
                    duration=0.8,
                    position=Placement(0.5, 0.4, anchor="center"),
                    opacity=1.0,
                    animation="pop",
                )
            except Exception as _e:
                print(f"  ⚠️ Intro overlay falló: {_e}", flush=True)
        
        # Outro overlay (CTA últimos 3s)
        try:
            project = project.overlay_text(
                "SUSCRÍBETE",
                at=max(0.0, dur_total - 3.0),
                duration=3.0,
                position="center",
                font_size=72,
                color="#e63946",
                outline_color="#000000",
                outline_width=4,
                bold=True,
            )
        except Exception as _e:
            print(f"  ⚠️ Outro overlay falló: {_e}", flush=True)
        
        # Música
        if musica_path and pathlib.Path(musica_path).exists():
            project = project.soundtrack(str(musica_path), volume=0.15, ducking=True, fade_out=1.0)
        
        project.render(str(salida), overwrite=True)
        return salida
    
    except Exception as e:
        print(f"  ⚠️ Multi-imagen falló: {e}. Fallback a single.", flush=True)
        return generar_short(imagenes[0], texto, voz_path, musica_path, salida)


if __name__ == "__main__":
    # Ejemplo de uso rápido
    print("✅ Contrato guardado y script base creado. Listo para integrar en Fase 2.")
