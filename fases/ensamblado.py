"""
Cajon 12 - Ensamblado final: intro + video + outro.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path

from core.config import OUTPUT_DIR
from core.logger import get_logger


log = get_logger("fases.ensamblado")

INTRO_PATH = Path.home() / "LofiProducer/assets/intro/intro_kz.mp4"
OUTRO_PATH = Path.home() / "LofiProducer/assets/outro/outro_kz.mp4"

AUDIO_PARAMS = ["-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2"]


def _run(cmd: list[str], etiqueta: str) -> None:
    log.info("ffmpeg [%s]...", etiqueta)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("STDERR:\n%s", proc.stderr[-2000:])
        raise RuntimeError(f"Fallo en {etiqueta}")
    log.info("  -> %s OK", etiqueta)


def _duracion(path: Path) -> float:
    if not path.exists():
        raise FileNotFoundError(f"Falta archivo: {path}")
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    salida = proc.stdout.strip()
    if not salida:
        raise RuntimeError(
            f"ffprobe devolvio vacio para {path.name}. "
            f"stderr: {proc.stderr.strip()[:200]}"
        )
    return float(salida)


def _tiene_audio(path: Path) -> bool:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    )
    return bool(proc.stdout.strip())


def anadir_audio_silencioso(src: Path, dst: Path) -> Path:
    dur = _duracion(src)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-f", "lavfi", "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t", str(dur),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "copy",
        *AUDIO_PARAMS,
        "-shortest",
        str(dst),
    ]
    _run(cmd, f"silent_audio {src.name}")

    if not dst.exists() or dst.stat().st_size < 10_000:
        raise RuntimeError(f"Temporal invalido: {dst}")

    _duracion(dst)  # verifica que se puede leer
    return dst


def ensamblar(video_principal: Path | None = None) -> Path:
    if video_principal is None:
        videos = sorted(OUTPUT_DIR.glob("video_youtube_*.mp4"))
        if not videos:
            raise FileNotFoundError(
                "No hay video_youtube_*.mp4 en output/. Ejecuta fases.video"
            )
        video_principal = videos[-1]

    if not INTRO_PATH.exists():
        raise FileNotFoundError(f"Falta intro: {INTRO_PATH}")
    if not OUTRO_PATH.exists():
        raise FileNotFoundError(f"Falta outro: {OUTRO_PATH}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    work = OUTPUT_DIR / f"_ensamblado_{ts}"
    work.mkdir(parents=True, exist_ok=True)

    log.info("Video principal: %s (%.1fs)",
             video_principal.name, _duracion(video_principal))

    # 1. Intro con audio silencioso
    intro_a = work / "intro_a.mp4"
    if _tiene_audio(INTRO_PATH):
        log.info("Intro ya tiene audio, copiando tal cual")
        intro_a.write_bytes(INTRO_PATH.read_bytes())
    else:
        anadir_audio_silencioso(INTRO_PATH, intro_a)

    # 2. Outro con audio silencioso
    outro_a = work / "outro_a.mp4"
    if _tiene_audio(OUTRO_PATH):
        log.info("Outro ya tiene audio, copiando tal cual")
        outro_a.write_bytes(OUTRO_PATH.read_bytes())
    else:
        anadir_audio_silencioso(OUTRO_PATH, outro_a)

    # 3. Lista de concatenacion
    lista = work / "lista.txt"
    lista.write_text(
        f"file '{intro_a.resolve()}'\n"
        f"file '{video_principal.resolve()}'\n"
        f"file '{outro_a.resolve()}'\n",
        encoding="utf-8",
    )

    # 4. Concatenar
    destino = OUTPUT_DIR / f"video_final_{ts}.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(lista),
        "-c", "copy",
        "-movflags", "+faststart",
        str(destino),
    ]
    _run(cmd, "concat_final")

    # 5. Verificar
    dur_final = _duracion(destino)
    dur_esperada = (_duracion(INTRO_PATH)
                    + _duracion(video_principal)
                    + _duracion(OUTRO_PATH))
    log.info("Duracion final: %.2fs (esperada ~%.2fs)",
             dur_final, dur_esperada)

    # 6. Limpiar temporales
    for f in work.iterdir():
        f.unlink()
    work.rmdir()

    return destino


if __name__ == "__main__":
    log.info("--- Cajon 12: ensamblado final ---")
    ruta = ensamblar()
    dur = _duracion(ruta)
    tam_mb = ruta.stat().st_size / 1024 / 1024

    print()
    print("=" * 60)
    print(f"[OK] Video final: {ruta.name}")
    print(f"     Duracion   : {dur:.1f}s ({dur/60:.1f} min)")
    print(f"     Tamano     : {tam_mb:.1f} MB")
    print("=" * 60)
