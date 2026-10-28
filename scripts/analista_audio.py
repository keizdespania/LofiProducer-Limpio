"""analista_audio.py - Detecta el pico de energía de una canción (con fix de parseo)."""
import subprocess, json, re, pathlib, sys

def analizar_pista(audio_path):
    audio_path = pathlib.Path(audio_path)
    if not audio_path.exists():
        return {"error": "Archivo no encontrado"}
    
    cmd = [
        "ffmpeg", "-i", str(audio_path),
        "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-"
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    
    lineas = r.stderr.splitlines()
    tiempos = []
    rms_actual = None
    tiempo_actual = 0.0
    
    for linea in lineas:
        m_time = re.search(r"pts_time:([\d\.]+)", linea)
        if m_time:
            tiempo_actual = float(m_time.group(1))
        m_rms = re.search(r"lavfi\.astats\.Overall\.RMS_level=([-\d\.]+)", linea)
        if m_rms:
            valor = m_rms.group(1)
            # FIX: Ignorar valores no numéricos como '-' o '-inf'
            if valor in ("-", "-inf", "inf", "nan"): continue
            try:
                rms_actual = float(valor)
                tiempos.append({"tiempo": round(tiempo_actual, 1), "rms": rms_actual})
            except ValueError:
                continue
    
    if not tiempos:
        return {"error": "No se pudo analizar el audio"}
    
    max_rms = max(tiempos, key=lambda x: x["rms"])
    peak_time = max_rms["tiempo"]
    inicio = max(0, peak_time - 10)
    fin = inicio + 30
    
    return {
        "pista": audio_path.name,
        "peak_energy_time": peak_time,
        "sugerencia_inicio": inicio,
        "sugerencia_fin": fin,
        "duracion_sugerida": 30,
        "rms_max": round(max_rms["rms"], 2)
    }

if __name__ == "__main__":
    audio = sys.argv[1] if len(sys.argv) > 1 else "output/musica_temp/tension_6718.mp3"
    print(json.dumps(analizar_pista(audio), indent=2, ensure_ascii=False))
