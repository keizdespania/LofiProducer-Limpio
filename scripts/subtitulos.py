import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'brain'))
from especialistas import pedir_a_especialista
"""subtitulos.py — Genera SRT desde audio + texto.
Estrategia: 1) Groq Whisper (rápido, cloud) 2) Fallback: distribución proporcional por duración.
"""
import os, sys, json, pathlib, subprocess, urllib.request, mimetypes

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _leer_env(k):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _dur_audio(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def _format_time(seg):
    h = int(seg // 3600)
    m = int((seg % 3600) // 60)
    s = int(seg % 60)
    ms = int((seg - int(seg)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _transcribir_groq(audio_path):
    """Transcribe con Groq Whisper. Devuelve lista de segmentos o None."""
    key = _leer_env("GROQ_API_KEY")
    if not key:
        return None
    try:
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        audio_bytes = pathlib.Path(audio_path).read_bytes()
        # multipart manual
        parts = []
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"model\"\r\n\r\nwhisper-large-v3\r\n".encode())
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"response_format\"\r\n\r\nverbose_json\r\n".encode())
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\nsegment\r\n".encode())
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"audio.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode() + audio_bytes + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST")
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
        return r.get("segments", [])
    except Exception as e:
        print(f"[subtitulos] Groq fallo: {e}", flush=True)
        return None


def _fallback_srt(texto, dur_total):
    """Divide el texto en bloques proporcionales a la duración."""
    palabras = texto.split()
    if not palabras:
        return ""
    # 10 palabras por bloque aprox (lectura ágil)
    por_bloque = 8
    bloques = [" ".join(palabras[i:i+por_bloque]) for i in range(0, len(palabras), por_bloque)]
    seg_por_bloque = dur_total / max(1, len(bloques))
    srt = []
    for i, b in enumerate(bloques):
        ini = i * seg_por_bloque
        fin = (i + 1) * seg_por_bloque
        srt.append(f"{i+1}\n{_format_time(ini)} --> {_format_time(fin)}\n{b}\n")
    return "\n".join(srt)


def generar_srt(audio_path, texto, salida_srt):
    """Genera SRT. Devuelve ruta."""
    audio_path = pathlib.Path(audio_path)
    salida_srt = pathlib.Path(salida_srt)
    salida_srt.parent.mkdir(parents=True, exist_ok=True)
    dur = _dur_audio(audio_path) or 60.0

    print(f"[subtitulos] Audio: {dur:.1f}s · {len(texto.split())} palabras", flush=True)
    segs = _transcribir_groq(audio_path)

    if segs:
        srt = []
        for i, s in enumerate(segs, 1):
            ini = float(s.get("start", 0))
            fin = float(s.get("end", ini + 1))
            txt = (s.get("text") or "").strip()
            if not txt:
                continue
            srt.append(f"{i}\n{_format_time(ini)} --> {_format_time(fin)}\n{txt}\n")
        salida_srt.write_text("\n".join(srt), encoding="utf-8")
        print(f"[subtitulos] OK Groq Whisper: {len(srt)} segmentos", flush=True)
        return str(salida_srt)

    # Fallback
    salida_srt.write_text(_fallback_srt(texto, dur), encoding="utf-8")
    print(f"[subtitulos] OK fallback proporcional", flush=True)
    return str(salida_srt)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: subtitulos.py <audio.mp3> <texto.txt> <salida.srt>")
        sys.exit(1)
    texto = pathlib.Path(sys.argv[2]).read_text()
    print(generar_srt(sys.argv[1], texto, sys.argv[3]))
