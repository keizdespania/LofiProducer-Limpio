import sys
import subprocess
from pathlib import Path

def producir(video: str, audio: str, nombre_final: str):
    v = Path(video)
    a = Path(audio)
    out_dir = Path("output/produccion_final")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_final = out_dir / nombre_final

    if not v.exists() or not a.exists():
        return f"ERROR: No existe {v} o {a}"

    cmd_ensamblar = [
        "ffmpeg", "-y", "-i", str(v), "-i", str(a),
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        "-map", "0:v:0", "-map", "1:a:0",
        str(out_final)
    ]
    try:
        subprocess.run(cmd_ensamblar, check=True, capture_output=True, timeout=300)
    except Exception as e:
        return f"ERROR en ensamblaje: {e}"

    temp_fade = out_dir / f"temp_{nombre_final}"
    cmd_fade = [
        "ffmpeg", "-y", "-i", str(out_final),
        "-vf", "fade=t=in:st=0:d=1,fade=t=out:st=end-1:d=1",
        "-af", "afade=t=in:st=0:d=1,afade=t=out:st=end-1:d=1",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac",
        str(temp_fade)
    ]
    try:
        subprocess.run(cmd_fade, check=True, capture_output=True, timeout=300)
        out_final.unlink()
        temp_fade.rename(out_final)
    except Exception as e:
        return f"ERROR en fade: {e}"

    cmd_probe = ["ffprobe", "-v", "error", "-show_entries",
                 "format=duration,size", "-of", "default=noprint_wrappers=1:nokey=1",
                 str(out_final)]
    try:
        resultado = subprocess.run(cmd_probe, check=True, capture_output=True, text=True, timeout=30).stdout.strip().split("\n")
        duracion = float(resultado[0])
        tamaño_mb = int(resultado[1]) / (1024 * 1024)
        return f"OK: Video listo en {out_final} (Duracion: {duracion:.1f}s, Tamaño: {tamaño_mb:.1f} MB)"
    except Exception as e:
        return f"OK: Video creado, pero fallo la validacion: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python scripts/producir_video.py <video.mp4> <audio.mp3> <nombre_final.mp4>")
        sys.exit(1)
    print(producir(sys.argv[1], sys.argv[2], sys.argv[3]))
