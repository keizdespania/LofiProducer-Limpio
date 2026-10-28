"""Modifica Flask para usar la cola SQLite."""
import pathlib, ast, re

p = pathlib.Path("web_dashboard.py")
t = p.read_text()

# 1. Nueva ruta /api/chat (encola)
nueva_ruta_chat = '''
@app.route("/api/chat", methods=["POST"])
def chat():
    import sqlite3, uuid
    from datetime import datetime
    msg = request.json.get("mensaje", "")
    if not msg: return jsonify({"status": "error", "mensaje": "Mensaje vacio"})
    
    task_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    db_path = ROOT / "data" / "agent" / "cola.db"
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT INTO tareas (id, session_id, prompt, estado, creada, actualizada) VALUES (?, ?, ?, ?, ?, ?)",
                     (task_id, "default", msg, "pending", now, now))
        conn.commit()
    
    return jsonify({"status": "processing", "task_id": task_id})
'''

# 2. Nueva ruta /api/chat_stream/<task_id> (lee el archivo de log)
nueva_ruta_stream = '''
@app.route("/api/chat_stream/<task_id>")
def chat_stream(task_id):
    from flask import Response
    import time, json, sqlite3
    log_file = ROOT / "data" / "logs" / "tasks" / f"{task_id}.log"
    db_path = ROOT / "data" / "agent" / "cola.db"

    def generate():
        # Esperar a que el worker empiece
        while not log_file.exists():
            yield f"data: {json.dumps('[+] En cola...')}\\n\\n"
            time.sleep(1)
            
        with open(log_file, "r", encoding="utf-8") as f:
            while True:
                line = f.readline()
                if line:
                    yield f"data: {json.dumps(line.strip())}\\n\\n"
                else:
                    # Comprobar si ha terminado en la DB
                    try:
                        with sqlite3.connect(db_path) as conn:
                            row = conn.execute("SELECT estado FROM tareas WHERE id=?", (task_id,)).fetchone()
                            if row and row[0] in ("done", "error"):
                                break
                    except: pass
                    time.sleep(0.5)
        yield f"data: {json.dumps('[+] Proceso finalizado.')}\\n\\n"

    return Response(generate(), mimetype='text/event-stream')
'''

# Eliminar ruta /api/chat vieja
patron_chat = re.compile(r'@app\.route\("/api/chat".*?return jsonify\(\{"status": "processing", "task_id": task_id\}\).*?return jsonify\(\{"status": "error".*?\}', re.DOTALL)
t = patron_chat.sub(nueva_ruta_chat, t)

# Eliminar ruta /api/chat_stream vieja (si existe)
patron_stream = re.compile(r'@app\.route\("/api/chat_stream/<task_id>".*?return Response\(generate\(\), mimetype=\'text/event-stream\'\)', re.DOTALL)
t = patron_stream.sub(nueva_ruta_stream, t)

p.write_text(t)
ast.parse(t)
print("OK: Flask modificado para usar la cola de tareas")
