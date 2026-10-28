"""
Cajon 11 - Outro KZ de 6 segundos (v2).

Cambio clave v2:
  - El texto se renderiza con Pillow a un PNG transparente.
  - FFmpeg solo hace fade + overlay (sin expresiones dinamicas).
  - Esto elimina los errores de escape del filtergraph.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config.outro import (
    LOGO_PATH, PORTADA_PATH, TEXTO_PNG, OUTRO_OUTPUT, OUTRO_DIR,
    ANCHO, ALTO, FPS, DURACION,
    BLUR_RADIUS, BLUR_POWER, OSCURECER,
    LOGO_ANCHO, LOGO_Y_OFFSET,
    LOGO_FADE_IN_START, LOGO_FADE_IN_DUR,
    LOGO_FADE_OUT_START, LOGO_FADE_OUT_DUR,
    TEXTO_1, TEXTO_2, FUENTE, TAM_TEXTO_1, TAM_TEXTO_2,
    Y_TEXTO_1, Y_TEXTO_2,
    TEXTO_FADE_IN_START, TEXTO_FADE_IN_DUR,
    VINETA, VINETA_ANGULO,
    FADE_IN_DUR, FADE_OUT_DUR,
    AUDIO_OUTRO,
)
from core.config import FONTS_DIR
from core.logger import get_logger


log = get_logger("fases.outro")


def verificar_assets() -> None:
    if not LOGO_PATH.exists():
        raise FileNotFoundError(f"Logo no encontrado: {LOGO_PATH}")
    if not PORTADA_PATH.exists():
        raise FileNotFoundError(f"Portada no encontrada: {PORTADA_PATH}")
    if not (FONTS_DIR / FUENTE).exists():
        raise FileNotFoundError(f"Fuente no encontrada: {FONTS_DIR / FUENTE}")


def generar_texto_png(destino: Path) -> Path:
    """
    Genera un PNG transparente 1920x1080 con los dos textos
    dibujados en las posiciones definidas.
    """
    img = Image.new("RGBA", (ANCHO, ALTO), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    fuente_path = str(FONTS_DIR / FUENTE)
    f1 = ImageFont.truetype(fuente_path, TAM_TEXTO_1)
    f2 = ImageFont.truetype(fuente_path, TAM_TEXTO_2)

    # Texto principal (con sombra)
    bbox = draw.textbbox((0, 0), TEXTO_1, font=f1)
    w = bbox[2] - bbox[0]
    x = (ANCHO - w) // 2
    draw.text((x + 3, Y_TEXTO_1 + 3), TEXTO_1, font=f1, fill=(0, 0, 0, 200))
    draw.text((x, Y_TEXTO_1), TEXTO_1, font=f1, fill=(255, 255, 255, 255))

    # Subtexto (con sombra)
    bbox = draw.textbbox((0, 0), TEXTO_2, font=f2)
    w = bbox[2] - bbox[0]
    x = (ANCHO - w) // 2
    draw.text((x + 2, Y_TEXTO_2 + 2), TEXTO_2, font=f2, fill=(0, 0, 0, 200))
    draw.text((x, Y_TEXTO_2), TEXTO_2, font=f2, fill=(255, 255, 255, 220))

    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "PNG")
    log.info("Texto PNG generado: %s", destino.name)
    return destino


def construir_filtro() -> str:
    """Filtro limpio, sin expresiones dinamicas."""

    # 1. Fondo
    fondo = (
        f"[0:v]scale={ANCHO}:{ALTO},setsar=1,"
        f"boxblur={BLUR_RADIUS}:{BLUR_POWER},"
        f"eq=brightness=-{OSCURECER}:saturation=0.7"
    )
    if VINETA:
        fondo += f",vignette={VINETA_ANGULO}"
    fondo += "[bg];"

    # 2. Logo con fade propio
    logo = (
        f"[1:v]scale={LOGO_ANCHO}:-1,format=rgba,"
        f"fade=t=in:st={LOGO_FADE_IN_START}:d={LOGO_FADE_IN_DUR}:alpha=1,"
        f"fade=t=out:st={LOGO_FADE_OUT_START}:d={LOGO_FADE_OUT_DUR}:alpha=1"
        f"[logo];"
    )

    # 3. Overlay logo sobre fondo
    overlay_logo = (
        f"[bg][logo]overlay=x=(W-w)/2:y=(H-h)/2{LOGO_Y_OFFSET:+d}"
        f"[v1];"
    )

    # 4. Texto con fade propio
    texto = (
        f"[2:v]format=rgba,"
        f"fade=t=in:st={TEXTO_FADE_IN_START}:d={TEXTO_FADE_IN_DUR}:alpha=1"
        f"[txt];"
    )

    # 5. Overlay texto
    overlay_texto = f"[v1][txt]overlay=0:0[v2];"

    # 6. Fade global
    fade_global = (
        f"[v2]fade=t=in:st=0:d={FADE_IN_DUR},"
        f"fade=t=out:st={DURACION - FADE_OUT_DUR}:d={FADE_OUT_DUR}"
        f"[out]"
    )

    return fondo + logo + overlay_logo + texto + overlay_texto + fade_global


def generar_outro() -> Path:
    verificar_assets()
    OUTRO_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generar el PNG del texto con Pillow
    generar_texto_png(TEXTO_PNG)

    # 2. Construir y ejecutar FFmpeg
    filtro = construir_filtro()

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(DURACION), "-i", str(PORTADA_PATH),
        "-loop", "1", "-t", str(DURACION), "-i", str(LOGO_PATH),
        "-loop", "1", "-t", str(DURACION), "-i", str(TEXTO_PNG),
        "-filter_complex", filtro,
        "-map", "[out]",
    ]

    if AUDIO_OUTRO and Path(AUDIO_OUTRO).exists():
        cmd += ["-i", str(AUDIO_OUTRO),
                "-map", "3:a", "-c:a", "aac", "-b:a", "192k"]
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
        str(OUTRO_OUTPUT),
    ]

    log.info("Renderizando outro %.1fs a %dx%d@%dfps",
             DURACION, ANCHO, ALTO, FPS)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("ffmpeg STDERR:\n%s", proc.stderr[-3000:])
        raise RuntimeError("Fallo al renderizar el outro")

    log.info("Outro generado: %s (%.1f KB)",
             OUTRO_OUTPUT.name, OUTRO_OUTPUT.stat().st_size / 1024)
    return OUTRO_OUTPUT


if __name__ == "__main__":
    log.info("--- Cajon 11: outro KZ (v2) ---")
    ruta = generar_outro()

    print()
    print("=" * 60)
    print(f"[OK] Outro: {ruta}")
    print(f"     Duracion: {DURACION}s @ {ANCHO}x{ALTO}")
    print(f"     Tamano  : {ruta.stat().st_size / 1024:.1f} KB")
    print("=" * 60)
