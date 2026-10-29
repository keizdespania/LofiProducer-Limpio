"""analista_audio.py v2 - Detecta pico de energía rápido y blindado."""
import subprocess, json, re, pathlib, sys, time


def _duracion(audio_path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, timeout=8)
        return float(r.stdout.strip()) if r.stdout.strip() else 0.0
    except Exception:
        return 0.0


def analizar_pista(audio_path, ventana_max=60):
    audio_path = pathlib.Path(audio_path)
    if not audio_path.exists():
        return {"error": "Archivo no encontrado"}

    t0 = time.time()
    dur_real = _duracion(audio_path)
    dur_analisis = min(ventana_max, dur_real) if dur_real > 0 else ventana_max

    cmd = [
        "ffmpeg", "-t", str(dur_analisis), "-i", str(audio_path),
        "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-"
    ]
    tiempos, rms_max = [], 0.0
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        tiempo_actual = 0.0
        for linea in r.stderr.splitlines():
            m_time = re.search(r"pts_time:([\d\.]+)", linea)
            if m_time:
                try: tiempo_actual = float(m_time.group(1))
                except: pass
            m_rms = re.search(r"lavfi\.astats\.Overall\.RMS_level=([-\d\.]+)", linea)
            if m_rms:
                v = m_rms.group(1)
                if v in ("-", "-inf", "inf", "nan"): continue
                try:
                    r = float(v)
                    tiempos.append({"tiempo": round(tiempo_actual, 1), "rms": r})
                except ValueError:
                    continue
    except subprocess.TimeoutExpired:
        print(f"[analista] timeout ({ventana_max}s) en {audio_path.name}", file=sys.stderr)

    # Fallback: si pocas muestras, usar 40% del track (suele ser el "drop")
    if len(tiempos) < 3:
        dur_ref = dur_real if dur_real > 0 else dur_analisis
        peak_time = round(dur_ref * 0.4, 1)
        print(f"[analista] fallback {audio_path.name}: peak {peak_time}s", file=sys.stderr)
    else:
        peak_time = max(tiempos, key=lambda x: x["rms"])["tiempo"]
        rms_max = max(t["rms"] for t in tiempos)

    elapsed = round(time.time() - t0, 1)
    print(f"[analista] {audio_path.name}: {len(tiempos)} muestras, peak={peak_time}s, {elapsed}s", file=sys.stderr)

    inicio = max(0, peak_time - 10)
    return {
        "pista": audio_path.name,
        "peak_energy_time": peak_time,
        "sugerencia_inicio": inicio,
        "sugerencia_fin": inicio + 30,
        "duracion_sugerida": 30,
        "rms_max": round(rms_max, 2),
        "elapsed_s": elapsed,
        "muestras": len(tiempos),
    }


if __name__ == "__main__":
    audio = sys.argv[1] if len(sys.argv) > 1 else "output/musica_temp/tension_6718.mp3"
    print(json.dumps(analizar_pista(audio), indent=2, ensure_ascii=False))
