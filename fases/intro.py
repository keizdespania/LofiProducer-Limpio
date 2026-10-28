"""
Cajon 10 - Intro KZ de 5 segundos.

Secuencia:
  0.0-0.7s  fade in desde negro (fondo con blur)
  0.5-2.0s  logo aparece con fade (alpha)
  2.0-4.2s  logo mantenido
  4.2-4.8s  logo fade out
  4.5-5.0s  fade out global a negro

Inputs FFmpeg:
  [0:v] portada (loop, imagen estatica)
  [1:v] logo RGBA (loop, imagen estatica)

Salida: assets/intro/intro_kz.mp4
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image

from config.intro import (
    LOGO_PATH, PORTADA_PATH, INTRO_OUTPUT, INTRO_DIR,
    ANCHO, ALTO, FPS, DURACION,
    BLUR_RADIUS, BLUR_POWER, OSCURECER,
    LOGO_ANCHO, LOGO_FADE_IN_START, LOGO_FADE_IN_DUR,
    LOGO_FADE_OUT_START, LOGO_FADE_OUT_DUR,
    VINETA, VINETA_ANGULO,
    FADE_IN_DUR, FADE_OUT_DUR,
    AUDIO_INTRO,
)
from core.logger import get_logger


log = get_logger("fases.intro")


def verificar_assets() -> None:
    """Comprueba que el logo tiene alpha y que la portada existe."""
    if not LOGO_PATH.exists():
        raise FileNotFoundError(f"Logo no encontrado: {LOGO_PATH}")
    if not PORTADA_PATH.exists():
        raise FileNotFoundError(f"Portada no encontrada: {PORTADA_PATH}")

    img = Image.open(LOGO_PATH)
    log.info("Logo: %dx%d, modo=%s", img.size[0], img.size[1], img.mode)

    if img.mode not in ("RGBA", "LA"):
        log.warning("Logo SIN canal alpha (modo=%s).", img.mode)
        log.warning("Se superpondra como rectangulo opaco.")
    else:
        log.info("  -> Logo con transparencia OK")


def construir_filtro() -> str:
    """Construye el filter_complex completo."""
    # 1. Fondo: portada escalada + blur + correccion + vineta
    fondo = (
        f"[0:v]scale={ANCHO}:{ALTO},setsar=1,"
        f"boxblur={BLUR_RADIUS}:{BLUR_POWER},"
        f"eq=brightness=-{OSCURECER}:saturation=0.85"
    )
    if VINETA:
        fondo += f",vignette={VINETA_ANGULO}"
    fondo += "[bg];"

    # 2. Logo: escalado + alpha garantizado + fade in/out propio
    logo = (
        f"[1:v]scale={LOGO_ANCHO}:-1,format=rgba,"
        f"fade=t=in:st={LOGO_FADE_IN_START}:d={LOGO_FADE_IN_DUR}:alpha=1,"
        f"fade=t=out:st={LOGO_FADE_OUT_START}:d={LOGO_FADE_OUT_DUR}:alpha=1"
        f"[logo];"
    )

    # 3. Overlay centrado
    overlay = (
        f"[bg][logo]overlay=x=(W-w)/2:y=(H-h)/2:format=auto[with_logo];"
    )

    # 4. Fade global entrada/salida
    fade_global = (
        f"[with_logo]"
        f"fade=t=in:st=0:d={FADE_IN_DUR},"
        f"fade=t=out:st={DURACION - FADE_OUT_DUR}:d={FADE_OUT_DUR}"
        f"[out]"
    )

    return fondo + logo + overlay + fade_global


def generar_intro() -> Path:
    verificar_assets()
    INTRO_DIR.mkdir(parents=True, exist_ok=True)
    filtro = construir_filtro()

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(DURACION), "-i", str(PORTADA_PATH),
        "-loop", "1", "-t", str(DURACION), "-i", str(LOGO_PATH),
        "-filter_complex", filtro,
        "-map", "[out]",
    ]

    if AUDIO_INTRO and Path(AUDIO_INTRO).exists():
        cmd += ["-i", str(AUDIO_INTRO),
                "-map", "2:a", "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]

    cmd += [
        "-t", str(DURACION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),
        str(INTRO_OUTPUT),
    ]

    log.info("Renderizando intro %.1fs a %dx%d@%dfps",
             DURACION, ANCHO, ALTO, FPS)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("ffmpeg STDERR:\n%s", proc.stderr[-3000:])
        raise RuntimeError("Fallo al renderizar la intro")

    tam_kb = INTRO_OUTPUT.stat().st_size / 1024
    log.info("Intro generada: %s (%.1f KB)", INTRO_OUTPUT.name, tam_kb)
    return INTRO_OUTPUT


def duracion_real() -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of", "csv=p=0", str(INTRO_OUTPUT)],
        capture_output=True, text=True,
    )
    return float(proc.stdout.strip())


if __name__ == "__main__":
    log.info("--- Cajon 10: intro KZ ---")

    ruta = generar_intro()
    dur = duracion_real()

    print()
    print("=" * 60)
    print(f"[OK] Intro generada: {ruta}")
    print(f"     Duracion real : {dur:.2f}s (objetivo {DURACION}s)")
    print(f"     Resolucion    : {ANCHO}x{ALTO} @ {FPS}fps")
    print(f"     Tamano        : {ruta.stat().st_size / 1024:.1f} KB")
    print("=" * 60)
