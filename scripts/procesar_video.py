"""Convierte cualquier video (.mov, .webm, .mkv) a .mp4 (H.264) para compatibilidad web."""
import sys
import subprocess
from pathlib import Path

def convertir(input_path: Path) -> str:
    """Convierte un video a MP4 con H.264 y AAC."""
    if not input_path.exists():
        return f"ERROR: No existe {input_path}"
    
    output_path = input_path.with_suffix(".mp4")
    if output_path == input_path:
        output_path = input_path.with_name(input_path.stem + "_web.mp4")
    
    print(f"Convirtiendo {input_path.name} -> {output_path.name}...")
    
    try:
        subprocess.run([
            "ffmpeg", "-i", str(input_path),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart",
            str(output_path), "-y"
        ], check=True, capture_output=True, timeout=600)
        
        # Borrar el original si se ha convertido bien
        if output_path.exists():
            input_path.unlink()
            return f"OK: Convertido a {output_path}"
        else:
            return "ERROR: FFmpeg no generó el archivo."
    except subprocess.CalledProcessError as e:
        return f"ERROR FFmpeg: {e.stderr.decode()[:300]}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/procesar_video.py 'ruta/al/video.mov'")
        sys.exit(1)
    print(convertir(Path(sys.argv[1])))
