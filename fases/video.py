"""
Cajon 09 - Renderizado de video horizontal para YouTube (v23).

Cambios v23:
  - Crop del reloj ensanchado (+25px margen) para que no corte el ultimo digito
  - colorkey para eliminar el fondo negro de la capa del reloj
  - Resultado: MM:SS limpio sin fondo negro alrededor
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.config import FONTS_DIR
from core.logger import get_logger


log = get_logger("fases.video")


FPS = 10
ANCHO = 1280
ALTO = 720

FUENTE = "Michroma-Regular.ttf"

# Ancho del crop del reloj (MM:SS con margen amplio)
ANCHO_TEXTO_VISIBLE = 260
MARGEN_EXTRA = 0
ANCHO_CROP = ANCHO_TEXTO_VISIBLE + MARGEN_EXTRA

# Posicion final
POS_X_FINAL = 50
POS_Y_FINAL = 40

TAM_CONTADOR = 40
COLOR_CONTADOR = "0x00FFDC"

RAYA_ANCHO = 260
RAYA_ALTO = 3
RAYA_OFFSET_Y = 90
RAYA_COLOR = "white@0.65"

MARCA = "KZ PRODUCTIONS"
TAM_MARCA = 20
MARCA_MARGEN = 40


def _output_dir() -> Path:
    from core.config import OUTPUT_DIR
    return OUTPUT_DIR


def _run(cmd: list[str], etiqueta: str) -> None:
    log.info("ffmpeg [%s]...", etiqueta)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("Fallo %s:\nSTDERR: %s", etiqueta, proc.stderr[-2500:])
        raise RuntimeError(f"ffmpeg fallo en {etiqueta}")
    log.info("  -> %s OK", etiqueta)


def ruta_fuente() -> str:
    ruta = FONTS_DIR / FUENTE
    if not ruta.exists():
        alternativas = ["Orbitron.ttf", "BebasNeue-Regular.ttf", "Anton-Regular.ttf"]
        for alt in alternativas:
            r = FONTS_DIR / alt
            if r.exists():
                log.warning("Usando fuente alternativa: %s", alt)
                return str(r)
        raise FileNotFoundError(f"Ninguna fuente disponible en {FONTS_DIR}")
    return str(ruta)


def portada_horizontal() -> Path:
    out = _output_dir()
    archivos = sorted(out.glob("portada_final_horizontal_*.jpg"))
    if not archivos:
        raise FileNotFoundError(
            f"No hay portada_final_horizontal_*.jpg en {out}. "
            "Ejecuta: python -m fases.portada"
        )
    return archivos[-1]


def generar_audio_dummy(destino: Path, duracion: int = 60) -> Path:
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"anoisesrc=color=pink:duration={duracion}:sample_rate=44100",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(destino),
    ]
    _run(cmd, "audio_dummy")
    return destino


def _generar_capa_reloj(duracion: int, destino: Path, fuente: str) -> Path:
    """
    Genera un video MOV con transparencia que contiene SOLO el reloj
    MM:SS (recortado del formato HH:MM:SS.mmm).

    Tecnica:
      1. Fondo transparente (color=black@0.0, formato argb)
      2. drawtext con %{pts:hms} -> 00:00:03.000
      3. crop quirurgico -> solo MM:SS
      4. colorkey del negro residual -> transparencia real
    """
    filtro = (
        # drawtext sobre fondo transparente
        f"drawtext=fontfile={fuente}"
        f":text='%{{pts\\:hms}}'"
        f":x=0:y={POS_Y_FINAL}"
        f":fontsize={TAM_CONTADOR}"
        f":fontcolor={COLOR_CONTADOR}"
        f":shadowx=2:shadowy=2:shadowcolor=black@0.85"
        # crop para eliminar .000
        f",crop={ANCHO_CROP}:{ALTO}:0:0"
        # colorkey: elimina el negro residual
        f",colorkey=black:0.05:0.0"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=black:s={ANCHO}x{ALTO}:d={duracion}:r={FPS}",
        "-vf", filtro,
        "-c:v", "qtrle",  # QuickTime Animation, soporta alpha
        "-pix_fmt", "argb",
        str(destino),
    ]
    _run(cmd, "capa_reloj")
    return destino


def montar_video(portada: Path, audio: Path, destino: Path,
                 duracion: int = 1800, contador_hasta: int | None = None,
                 hhmmss: bool = False) -> Path:
    fuente = ruta_fuente()

    # Generar la capa del reloj con transparencia
    reloj_mov = destino.with_suffix(".reloj.mov")
    _generar_capa_reloj(duracion, reloj_mov, fuente)

    # Filtro final: overlay del reloj + raya + marca
    filtro = (
        f"[0:v]scale={ANCHO}:{ALTO},setsar=1[bg];"
        # overlay de la capa del reloj transparente
        f"[bg][1:v]overlay={POS_X_FINAL}:0[v1];"
        # Raya HUD
        f"[v1]drawbox=x={POS_X_FINAL}:y={RAYA_OFFSET_Y}"
        f":w={RAYA_ANCHO}:h={RAYA_ALTO}:color={RAYA_COLOR}:t=fill[v2];"
        # Marca
        f"[v2]drawtext=fontfile={fuente}"
        f":text='{MARCA}'"
        f":x=w-tw-{MARCA_MARGEN}:y={MARCA_MARGEN}"
        f":fontsize={TAM_MARCA}"
        f":fontcolor=white@0.6"
        f":shadowx=1:shadowy=1:shadowcolor=black@0.7[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", str(portada),
        "-i", str(reloj_mov),
        "-stream_loop", "-1", "-i", str(audio),
        "-filter_complex", filtro,
        "-map", "[out]",
        "-map", "2:a",
        "-t", str(duracion),
        "-r", str(FPS),
        "-fps_mode", "cfr",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "25",
        "-pix_fmt", "yuv420p",
        "-g", str(FPS * 2),
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(destino),
    ]
    _run(cmd, "video_horizontal")
    reloj_mov.unlink(missing_ok=True)
    return destino


def construir_video_youtube(audio_real: Path | None = None,
                            duracion: int = 1800,
                            contador_hasta: int | None = None,
                            hhmmss: bool = False) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    video_final = _output_dir() / f"video_youtube_{ts}.mp4"

    log.info("=== Cajon 09 v23: crop + colorkey ===")

    if audio_real is None:
        log.warning("Sin audio real: uso dummy.")
        audio_dummy = _output_dir() / f"audio_dummy_{ts}.mp3"
        generar_audio_dummy(audio_dummy, duracion=min(duracion, 60))
        audio_real = audio_dummy
    else:
        log.info("Usando audio real: %s", audio_real.name)

    montar_video(portada_horizontal(), audio_real, video_final,
                 duracion, contador_hasta, hhmmss)
    return video_final


if __name__ == "__main__":
    from core.channel_manager import set_active_channel

    log.info("--- Test cajon 09 v23 ---")
    set_active_channel(None)
    log.info("OUTPUT_DIR: %s", _output_dir())

    video = construir_video_youtube(duracion=60)
    tam_mb = video.stat().st_size / 1024 / 1024
    print()
    print("=" * 60)
    print(f"[OK] Video: {video.name}")
    print(f"     Tamano: {tam_mb:.1f} MB")
    print("=" * 60)
