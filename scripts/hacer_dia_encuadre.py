"""hacer_dia_encuadre.py - Cron diario 06:00 para Somos El Encuadre."""
import sys, subprocess, pathlib, datetime, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from subir_youtube import subir

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOKEN_ENC = ROOT / "data/youtube_encuadre_token.json"
fecha = datetime.date.today().isoformat()

def _run(script, *args, timeout=600):
    cmd = ["python3", f"scripts/{script}"] + list(args)
    print(f"[dia] Ejecutando {script}...", flush=True)
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=timeout)
    salida = (r.stdout or r.stderr or "").strip()
    print(salida[-300:], flush=True)
    # Buscar ruta de archivo generado (última línea que empiece por / o contenga .mp4)
    for linea in reversed(salida.splitlines()):
        linea = linea.strip()
        if (linea.startswith("/") or linea.startswith("output/")) and ".mp4" in linea:
            p = ROOT / linea.lstrip("/")
            if p.exists():
                return str(p)
    return None

print(f"[dia] {fecha} — Iniciando pipeline completo", flush=True)

# 1. Comparar medios
_run("comparar_medios.py", "noticias de inteligencia artificial", timeout=300)

# 2. Generar post + auto-publicar web
_run("generar_post_encuadre.py", fecha, timeout=600)

# 3. Generar shorts
short_paths = _run("short_engine_encuadre.py", fecha, timeout=600)

# 4. Notificar móvil
print("[dia] Notificando...", flush=True)
try:
    subprocess.run(["termux-notification", "-t", "📊 El Encuadre " + fecha,
                    "-c", "Post + short listos.", "--priority", "high"], check=False, timeout=5)
except: pass

# 5. Subir short
if short_paths:
    for sp in short_paths:
        print(f"[dia] Subiendo {sp} a YouTube...", flush=True)
        try:
            r = subir(sp, f"Short {fecha} - Somos El Encuadre", "Análisis del encuadre.", privacidad="private", token_file=TOKEN_ENC)
            print(f"[dia] ✅ Subido: https://youtu.be/{r['id']}", flush=True)
        except Exception as e:
            print(f"[dia] ❌ Error subiendo {sp}: {e}", flush=True)
else:
    print("[dia] ⚠️  No se generaron shorts", flush=True)

# 6. Generar vídeo largo
video_path = _run("video_largo_encuadre.py", fecha, timeout=900)

# 7. Subir vídeo largo
if video_path:
    print(f"[dia] Subiendo vídeo largo a YouTube...", flush=True)
    try:
        r = subir(video_path, f"Vídeo largo {fecha} - Somos El Encuadre", "Análisis completo del encuadre.", privacidad="private", token_file=TOKEN_ENC)
        print(f"[dia] ✅ Vídeo largo subido: https://youtu.be/{r['id']}", flush=True)
    except Exception as e:
        print(f"[dia] ❌ Error subiendo vídeo largo: {e}", flush=True)
else:
    print("[dia] ⚠️  No se generó vídeo largo", flush=True)

# 8. Generar copys para redes
_run("generar_redes.py", fecha, timeout=120)

# 9. Guardar estado
state = {"fecha": fecha, "completado": True, "short": short_path, "video": video_path}
(ROOT / "output" / "encuadre").mkdir(parents=True, exist_ok=True)
(ROOT / "output" / "encuadre" / f"dia_{fecha}.json").write_text(json.dumps(state, indent=2))
print(f"[dia] ✅ Pipeline {fecha} completado", flush=True)
