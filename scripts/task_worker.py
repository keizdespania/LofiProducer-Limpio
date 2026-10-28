"""Worker que procesa la cola: chat (dios.py) o video (kaggle_manager.py)."""
import sqlite3, subprocess, sys, time, pathlib, json
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "agent" / "cola.db"
LOGS_DIR = ROOT / "data" / "logs" / "tasks"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def health_check_zombies():
    """Marca como error tareas running >2h (evita zombies)."""
    import sqlite3, datetime
    try:
        with sqlite3.connect(DB_PATH) as c:
            hace_2h = (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat()
            res = c.execute("UPDATE tareas SET estado='error', salida='Zombie: +2h sin terminar', actualizada=? WHERE estado='running' AND actualizada < ?", (datetime.datetime.now().isoformat(), hace_2h))
            c.commit()
            if res.rowcount > 0:
                print(f'[Worker] {res.rowcount} tareas zombie limpiadas', flush=True)
    except Exception as e:
        print(f'[Worker] health_check fallo: {e}', flush=True)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                prompt TEXT,
                estado TEXT,
                log_file TEXT,
                salida TEXT,
                creada TEXT,
                actualizada TEXT
            )
        """)



# ═══ HELPERS BATCH ═══
import sys as _sys
_sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

def _agrupar_tareas(session_id, maximo=5):
    """Saca hasta N tareas pending del mismo tipo y las marca como running."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        tareas = conn.execute(
            "SELECT * FROM tareas WHERE estado='pending' AND session_id=? ORDER BY creada ASC LIMIT ?",
            (session_id, maximo)
        ).fetchall()
        if not tareas:
            return []
        ids = [t["id"] for t in tareas]
        for tid in ids:
            conn.execute("UPDATE tareas SET estado='running', actualizada=? WHERE id=?",
                         (datetime.now().isoformat(), tid))
        conn.commit()
        return [dict(t) for t in tareas]

def _marcar_done(ids, salida):
    with sqlite3.connect(DB_PATH) as conn:
        for tid in ids:
            conn.execute("UPDATE tareas SET estado='done', salida=?, actualizada=? WHERE id=?",
                         (salida, datetime.now().isoformat(), tid))
        conn.commit()

def _marcar_error(ids, msg):
    with sqlite3.connect(DB_PATH) as conn:
        for tid in ids:
            conn.execute("UPDATE tareas SET estado='error', salida=?, actualizada=? WHERE id=?",
                         (msg, datetime.now().isoformat(), tid))
        conn.commit()

def _procesar_musica_batch():
    """Agrupa hasta 5 tareas de música y las procesa en 1 kernel."""
    lote = _agrupar_tareas("musica", maximo=5)
    if not lote:
        return False
    ids = [t["id"] for t in lote]
    captions = [t["prompt"] for t in lote]
    print(f"[Worker] Batch música: {len(captions)} tareas (ids: {[i[:8] for i in ids]})", flush=True)
    try:
        from musica_acestep import generar_batch
        resultado = generar_batch(captions, duration=60, preset="lofi")
        if resultado.startswith("ERROR"):
            _marcar_error(ids, resultado[:500])
        else:
            _marcar_done(ids, resultado[:2000])
        print(f"[Worker] Batch música completo: {resultado[:150]}", flush=True)
    except Exception as e:
        _marcar_error(ids, f"Excepción: {e}")
        print(f"[Worker] Batch música error: {e}", flush=True)
    return True

def _procesar_video_batch():
    """Agrupa hasta 3 tareas de vídeo y las procesa en 1 kernel."""
    lote = _agrupar_tareas("video", maximo=3)
    if not lote:
        return False
    ids = [t["id"] for t in lote]
    prompts = [t["prompt"] for t in lote]
    print(f"[Worker] Batch vídeo: {len(prompts)} clips (ids: {[i[:8] for i in ids]})", flush=True)
    try:
        from wan22_batch import generar_video_batch
        resultado = generar_video_batch(prompts)
        if resultado.startswith("ERROR"):
            _marcar_error(ids, resultado[:500])
        else:
            _marcar_done(ids, resultado[:2000])
        print(f"[Worker] Batch vídeo completo: {resultado[:150]}", flush=True)
    except Exception as e:
        _marcar_error(ids, f"Excepción: {e}")
        print(f"[Worker] Batch vídeo error: {e}", flush=True)
    return True


def procesar_cola():
    _iteracion = 0
    init_db()
    print("[Worker] Cola de tareas iniciada. Esperando tareas...", flush=True)
    while True:
        _iteracion += 1
        if _iteracion % 10 == 1:
            health_check_zombies()
        try:
            # Primero, intentar procesar lotes de música y vídeo
            if _procesar_musica_batch():
                time.sleep(1)
                continue
            if _procesar_video_batch():
                time.sleep(1)
                continue
            # Si no hay lotes, procesar 1 tarea individual (chat o legacy)
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                tarea = conn.execute("SELECT * FROM tareas WHERE estado = 'pending' ORDER BY creada ASC LIMIT 1").fetchone()
                
                if tarea:
                    task_id = tarea["id"]
                    prompt = tarea["prompt"]
                    session_id = tarea["session_id"]
                    log_file = LOGS_DIR / f"{task_id}.log"
                    
                    print(f"[Worker] Ejecutando tarea {task_id[:8]} ({session_id})...", flush=True)
                    conn.execute("UPDATE tareas SET estado = 'running', actualizada = ? WHERE id = ?", 
                                 (datetime.now().isoformat(), task_id))
                    conn.commit()
                    
                    # Detectar si es video
                    # Solo es_video si la sesión es explícitamente "video" (la web ya decidió)
                    # Frases complejas → session_id="default" → dios.py
                    es_video = (session_id == "video")
                    
                    if es_video:
                        # Lanzar el notebook en Kaggle
                        with open(log_file, "w") as f:
                            subprocess.run([sys.executable, "scripts/kaggle_manager.py", prompt, task_id], 
                                           stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT), timeout=180)
                        # La tarea se queda en 'running'. El checker la descargara cuando Kaggle termine.
                        print(f"[Worker] Tarea {task_id[:8]} lanzada en Kaggle. En espera de descarga.", flush=True)
                    else:
                        # Chat normal: ejecutar dios.py
                        with open(log_file, "w") as f:
                            subprocess.run([sys.executable, "scripts/dios.py", prompt], 
                                           stdout=f, stderr=subprocess.STDOUT, cwd=str(ROOT))
                        # Leer salida
                        salida = ""
                        if log_file.exists():
                            texto = log_file.read_text()
                            if "[dios] Tarea completada. Resumen:" in texto:
                                salida = texto.split("[dios] Tarea completada. Resumen:")[1].strip()
                            else:
                                salida = texto[-500:]
                        conn.execute("UPDATE tareas SET estado = 'done', salida = ?, actualizada = ? WHERE id = ?",
                                     (salida, datetime.now().isoformat(), task_id))
                        conn.commit()
                        print(f"[Worker] Tarea {task_id[:8]} completada.", flush=True)
        except Exception as e:
            print(f"[Worker] Error: {e}", flush=True)
        time.sleep(2)

if __name__ == "__main__":
    procesar_cola()
