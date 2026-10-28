"""pipeline_encuadre.py - Orquestador Maestro Definitivo (Real-Time Logs)."""
import subprocess, sys, pathlib, datetime, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
fecha = datetime.date.today().isoformat()
TOKEN_ENC = ROOT / "data" / "youtube_encuadre_token.json"

def _run(script, args=None, timeout=1200):
    cmd = ["python3", f"scripts/{script}"] + (args or [])
    print(f"\n{'='*60}\n▶️  EJECUTANDO: {script} {' '.join(args or [])}\n{'='*60}", flush=True)
    try:
        # capture_output=False imprime en tiempo real en la terminal
        r = subprocess.run(cmd, cwd=str(ROOT), capture_output=False, text=True, timeout=timeout)
        if r.returncode != 0:
            print(f"⚠️  ATENCIÓN: {script} terminó con código {r.returncode}", flush=True)
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ TIMEOUT: {script} tardó más de {timeout} segundos.", flush=True)
        return False
    except Exception as e:
        print(f"❌ ERROR ejecutando {script}: {e}", flush=True)
        return False

def _subir_youtube(archivo, titulo, desc, publish_at=None):
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import subir
        r = subir(archivo, titulo, desc, privacidad="private", publish_at=publish_at, token_file=TOKEN_ENC)
        print(f"✅ YouTube: https://youtu.be/{r['id']}")
    except Exception as e:
        print(f"❌ Error YouTube: {e}")

def main():
    print(f"🚀 INICIANDO PIPELINE MASIVO - {fecha}", flush=True)
    
    pasos = [
        ("recolector.py", None, 1200),
        ("transcribir_groq.py", None, 1200),
        ("analista_fase1.py", None, 1200),
        ("sintetizador.py", None, 600),
        ("fase2_produccion.py", None, 1200),
        ("preparar_assets.py", None, 600),
        ("voz_edge.py", None, 600),
        ("musica_youtube_cc.py", None, 600),
        ("analizar_musica_cc.py", None, 300),
        ("planificador_montaje.py", None, 300),
        ("generar_blueprint.py", None, 300),
        ("renderizador.py", None, 1200)
    ]
    
    for script, args, t in pasos:
        exito = _run(script, args, t)
        if not exito:
            print(f"\n🛑 PIPELINE DETENIDO: Falló en {script}. Revisa el error arriba.", flush=True)
            return

    # Archivar shorts en Drive (liberar espacio)
    _run("gestor_shorts.py", [fecha])

    # Comprobar que los vídeos existen
    video_path = ROOT / "output" / "encuadre" / f"video_largo_{fecha}.mp4"
    short_path = ROOT / "output" / "encuadre" / f"short_1_{fecha}.mp4"
    
    if not video_path.exists() or not short_path.exists():
        print("\n🛑 PIPELINE DETENIDO: Los vídeos no se generaron correctamente.", flush=True)
        return

    # Publicación masiva
    print("\n" + "="*60 + "\nPUBLICACIÓN MASIVA\n" + "="*60, flush=True)
    _run("generar_web_masiva.py", [fecha])
    _run("generar_blogs_blogger.py", [fecha])
    _run("generar_redes.py", [fecha])
    _run("generar_thumbnail.py", [fecha])
    _run("generar_podcast_rss.py", [fecha])
    _run("enlazador_seo.py", [fecha])
    
    # Subida a YouTube (Programada)
    _subir_youtube(str(video_path), f"Vídeo Largo {fecha}", "Análisis completo.", publish_at=f"{fecha}T18:00:00Z")
    _subir_youtube(str(short_path), f"Short {fecha}", "Análisis rápido.", publish_at=f"{fecha}T13:00:00Z")
    
    # Notificación
    try:
        subprocess.run(["termux-notification", "-t", "🎬 Encuadre " + fecha, "-c", "12 posts Web + 5 Blogger + Vídeos listos.", "--priority", "high"], check=False)
    except: pass
    
    # Guardar estado REAL
    state = {"fecha": fecha, "completado": True, "video": str(video_path), "short": str(short_path)}
    (ROOT / "output" / "encuadre" / f"pipeline_{fecha}.json").write_text(json.dumps(state, indent=2))
    print(f"\n✅ PIPELINE MASIVO {fecha} COMPLETADO CON ÉXITO")

if __name__ == "__main__":
    main()
