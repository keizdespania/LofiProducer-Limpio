"""Comprueba kernels de video, descarga el MP4 y notifica al movil."""
import sys, pathlib, json, sqlite3, subprocess, shutil, time
sys.path.insert(0, "scripts")
from kaggle_bearer import estado_kernel

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "agent" / "cola.db"
OUT_DIR = ROOT / "output" / "videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def notificar(titulo, mensaje):
    try:
        subprocess.run(["termux-notification", "-t", titulo, "-c", mensaje], check=True, timeout=10)
    except Exception as e:
        print(f"Notificacion fallo: {e}", flush=True)

def procesar_pendientes():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        tareas = conn.execute("SELECT * FROM tareas WHERE session_id='video' AND estado='running'").fetchall()
    
    if not tareas:
        print("[Checker] Sin tareas pendientes.", flush=True)
        return
    
    for t in tareas:
        # El slug real que usa kaggle_manager.py es: kaggle-auto-{timestamp}
        # Pero no lo guardamos en la DB, asi que usamos el task_id como aproximacion
        slug = f"keizproductions/kaggle-auto-video-{t['id']}"
        print(f"[Checker] Comprobando {slug}...", flush=True)
        # Probar en cuenta 1 primero
        r1 = estado_kernel(slug)
        status = r1.get('status', '?') if isinstance(r1, dict) else 'error'
        
        # Si da 403 o no encontrado, probar cuenta 2
        if status == '?' or (isinstance(r1, dict) and '403' in str(r1.get('error', ''))):
            slug2 = f"lofiproducer/kaggle-auto-video-{t['id']}"
            print(f"[Checker] Probando cuenta 2: {slug2}...", flush=True)
            r2 = estado_kernel(slug2)
            status = r2.get('status', '?') if isinstance(r2, dict) else 'error'
            if status != '?':
                slug = slug2  # Usar el slug de la cuenta 2 para descargar
        
        print(f"[Checker] Estado: {status}", flush=True)
        
        if status == 'complete':
            print(f"[Checker] ✅ Listo. Descargando...", flush=True)
            try:
                import kagglehub
                path = kagglehub.notebook_output_download(f"{slug}/versions/1")
                for f in pathlib.Path(path).rglob("*.mp4"):
                    dest = OUT_DIR / f"video_{t['id']}.mp4"
                    shutil.copy2(f, dest)
                    print(f"[Checker] ✅ Video descargado: {dest} ({dest.stat().st_size // 1024} KB)", flush=True)
                    notificar("Video listo", f"Tu video esta en el Media Center ({dest.stat().st_size // 1024} KB)")
                    break
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("UPDATE tareas SET estado='done', ruta_video=? WHERE id=?", (str(dest), t['id']))
                    conn.commit()
            except Exception as e:
                print(f"[Checker] ❌ Error descargando: {e}", flush=True)
        elif status == 'error':
            print(f"[Checker] ❌ Kernel fallo.", flush=True)
            notificar("Video fallo", f"El kernel {t['id']} ha fallado.")
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("UPDATE tareas SET estado='error' WHERE id=?", (t['id'],))
                conn.commit()

if __name__ == "__main__":
    procesar_pendientes()
