"""validar_video.py - Valida que el vídeo largo sea apto para YouTube.

Checks:
- Existe
- Duración: entre 60s (no es Short) y 15 min (retención YouTube)
- Formato: 16:9 (width/height ratio ~1.77)
- Tamaño: < 2 GB (límite YouTube)
- Tiene audio (stream de audio)
"""
import json, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"

MIN_SEG = 60       # si <60s, es Short
MAX_SEG = 900      # 15 min, YouTube penaliza retención >15 min
RATIO_MIN = 1.70   # 16:9 = 1.777
RATIO_MAX = 1.85
MAX_MB = 2048      # límite YouTube


def _ffprobe(path, field):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", field,
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        return r.stdout.strip().split("\n")[0] if r.stdout.strip() else ""
    except Exception:
        return ""


def _streams(path):
    """Devuelve lista de tipos de streams (video, audio, etc)."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        return [s.strip() for s in r.stdout.strip().split("\n") if s.strip()]
    except Exception:
        return []


def validar(fecha=None):
    fecha = fecha or FECHA
    video = OUT / f"video_largo_{fecha}.mp4"
    errores = []
    warnings = []

    # 1. Existe
    if not video.exists():
        print(f"❌ NO EXISTE: {video}")
        return False, {"error": "no existe", "path": str(video)}

    size_mb = video.stat().st_size / 1024 / 1024

    # 2. Duración
    dur_str = _ffprobe(video, "format=duration")
    try:
        dur = float(dur_str)
    except Exception:
        dur = 0

    if dur < MIN_SEG:
        errores.append(f"Duración {dur:.1f}s < {MIN_SEG}s (parece un Short, no vídeo largo)")
    elif dur > MAX_SEG:
        warnings.append(f"Duración {dur:.1f}s > {MAX_SEG}s (15 min, puede bajar retención)")

    # 3. Formato 16:9
    width_str = _ffprobe(video, "stream=width")
    height_str = _ffprobe(video, "stream=height")
    try:
        width = int(width_str)
        height = int(height_str)
        ratio = width / height if height > 0 else 0
    except Exception:
        width = height = 0
        ratio = 0

    if not (RATIO_MIN <= ratio <= RATIO_MAX):
        errores.append(f"Formato {width}x{height} ratio={ratio:.2f} (YouTube largo pide 16:9 ≈ 1.78)")

    # 4. Tamaño
    if size_mb > MAX_MB:
        errores.append(f"Tamaño {size_mb:.0f}MB > {MAX_MB}MB (límite YouTube)")

    # 5. Audio presente
    streams = _streams(video)
    has_video = "video" in streams
    has_audio = "audio" in streams

    if not has_video:
        errores.append("Sin stream de vídeo")
    if not has_audio:
        errores.append("Sin stream de audio (no sonaría)")

    # Resultado
    metrics = {
        "path": str(video),
        "size_mb": round(size_mb, 1),
        "duracion_seg": round(dur, 1),
        "duracion_min": round(dur / 60, 2),
        "width": width,
        "height": height,
        "ratio": round(ratio, 2),
        "streams": streams,
        "errores": errores,
        "warnings": warnings,
        "ok": len(errores) == 0,
    }

    print(f"=== VALIDACIÓN VÍDEO: {video.name} ===")
    print(f"  Tamaño: {metrics['size_mb']} MB")
    print(f"  Duración: {metrics['duracion_seg']}s ({metrics['duracion_min']} min)")
    print(f"  Formato: {width}x{height} ratio={ratio:.2f}")
    print(f"  Streams: {streams}")
    print()
    if errores:
        print(f"❌ {len(errores)} ERRORES (bloqueantes):")
        for e in errores:
            print(f"  · {e}")
    if warnings:
        print(f"⚠️ {len(warnings)} WARNINGS (no bloqueantes):")
        for w in warnings:
            print(f"  · {w}")
    if not errores and not warnings:
        print("✅ VÍDEO VÁLIDO para YouTube")

    # Guardar resultado
    out = OUT / f"validacion_video_{fecha}.json"
    out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    return metrics["ok"], metrics


if __name__ == "__main__":
    ok, _ = validar(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)
