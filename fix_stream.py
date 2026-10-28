"""Reemplaza el bloque chat_stream roto por uno funcional (sin escapes problematicos)."""
import pathlib, ast, re

p = pathlib.Path("web_dashboard.py")
t = p.read_text()

# Encontrar el inicio y fin del bloque chat_stream
patron = re.compile(
    r'@app\.route\("/api/chat_stream/<task_id>"\).*?(?=@app\.route|\nif __name__)',
    re.DOTALL
)

# Construir el bloque nuevo con chr() para evitar escapes
NL = chr(10)
Q = chr(34)  # comilla doble
BQ = chr(96) # backtick (por si acaso)

lineas = [
    '@app.route("/api/chat_stream/<task_id>")',
    'def chat_stream(task_id):',
    '    from flask import Response',
    '    import time, json, sqlite3',
    '    log_file = ROOT / "data" / "logs" / "tasks" / (task_id + ".log")',
    '    db_path = ROOT / "data" / "agent" / "cola.db"',
    '',
    '    def generate():',
    '        # Esperar a que el worker empiece',
    '        esperando = 0',
    '        while not log_file.exists():',
    '            yield "data: " + json.dumps("[+] En cola...") + NL2 + NL2',
    '            time.sleep(1)',
    '            esperando += 1',
    '            if esperando > 300:',
    '                yield "data: " + json.dumps("[+] Timeout esperando worker") + NL2 + NL2',
    '                return',
    '',
    '        with open(log_file, "r", encoding="utf-8") as f:',
    '            while True:',
    '                line = f.readline()',
    '                if line:',
    '                    yield "data: " + json.dumps(line.strip()) + NL2 + NL2',
    '                else:',
    '                    try:',
    '                        with sqlite3.connect(db_path) as conn:',
    '                            row = conn.execute("SELECT estado FROM tareas WHERE id=?", (task_id,)).fetchone()',
    '                            if row and row[0] in ("done", "error"):',
    '                                break',
    '                    except Exception:',
    '                        pass',
    '                    time.sleep(0.5)',
    '        yield "data: " + json.dumps("[+] Proceso finalizado.") + NL2 + NL2',
    '',
    '    return Response(generate(), mimetype="text/event-stream")',
    '',
]

# Reemplazar NL2 por el escape real de dos saltos de linea
bloque = NL.join(lineas).replace("NL2", chr(92) + "n" + chr(92) + "n")

if patron.search(t):
    t = patron.sub(bloque, t, count=1)
    p.write_text(t)
    ast.parse(t)
    print("OK: Bloque chat_stream reemplazado")
    print("OK: Sintaxis OK")
else:
    print("ERROR: No se encontro el bloque chat_stream")
