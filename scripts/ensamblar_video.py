"""Ensambla un vídeo final mezclando un MP4 (visual) y un MP3 (audio)."""
import sys
import subprocess
from pathlib import Path

def ensamblar(video_path: str, audio_path: str, output_path: str):
    v = Path(video_path)
    a = Path(audio_path)
    o = Path(output_path)
    
    if not v.exists() or not a.exists():
        return f"ERROR: No existe {v} o {a}"
    
    print(f"Mezclando {v.name} + {a.name} -> {o.name}...")
    try:
        # FFmpeg: Coge el vídeo, le pone el audio, y lo deja listo
        cmd = [
            "ffmpeg", "-y",
            "-i", str(v),
            "-i", str(a),
            "-c:v", "copy",          # No reencodeamos el vídeo (más rápido)
            "-c:a", "aac",           # Audio en AAC (compatible)
            "-shortest",             # Si el audio es más corto, corta el vídeo
            "-map", "0:v:0",         # Coge el primer stream de vídeo
            "-map", "1:a:0",         # Coge el primer stream de audio
            str(o)
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)
        return f"OK: Vídeo ensamblado en {o}"
    except subprocess.CalledProcessError as e:
        return f"ERROR FFmpeg: {e.stderr.decode()[:300]}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python scripts/ensamblar_video.py <video.mp4> <audio.mp3> <output.mp4>")
        sys.exit(1)
    print(ensamblar(sys.argv[1], sys.argv[2], sys.argv[3]))
