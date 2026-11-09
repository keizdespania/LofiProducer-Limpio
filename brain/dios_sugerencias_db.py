"""dios_sugerencias_db.py - SQLite para sugerencias autónomas de Dios."""
import sqlite3, json, datetime, pathlib, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "agent" / "dios_sugerencias.db"
DB.parent.mkdir(parents=True, exist_ok=True)

def _init():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS sugerencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regla TEXT NOT NULL,
            categoria TEXT NOT NULL,
            prioridad REAL DEFAULT 0.5,
            titulo TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            payload TEXT DEFAULT '{}',
            accion_tool TEXT DEFAULT '',
            estado TEXT DEFAULT 'pendiente',
            creada TEXT,
            resuelta TEXT,
            telegram_msg_id INTEGER
        )""")
        c.execute("CREATE INDEX IF NOT EXISTS idx_estado ON sugerencias(estado)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_regla ON sugerencias(regla)")
_init()

def crear(regla, categoria, titulo, mensaje, payload=None, accion_tool="", prioridad=0.5):
    """Crea sugerencia si no hay una igual pendiente en 6h."""
    ahora = datetime.datetime.now()
    with sqlite3.connect(DB) as c:
        # Throttle: misma regla en últimas 6h?
        corte = (ahora - datetime.timedelta(hours=6)).isoformat()
        cur = c.execute("SELECT id FROM sugerencias WHERE regla=? AND creada>? AND estado IN ('pendiente','aceptada') LIMIT 1", (regla, corte))
        if cur.fetchone(): return None
        cur = c.execute("""INSERT INTO sugerencias (regla, categoria, prioridad, titulo, mensaje, payload, accion_tool, creada)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (regla, categoria, prioridad, titulo, mensaje,
                         json.dumps(payload or {}, ensure_ascii=False), accion_tool, ahora.isoformat()))
        return cur.lastrowid

def pendientes(limit=10):
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute("SELECT * FROM sugerencias WHERE estado='pendiente' ORDER BY prioridad DESC, id DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

def por_id(sid):
    with sqlite3.connect(DB) as c:
        c.row_factory = sqlite3.Row
        cur = c.execute("SELECT * FROM sugerencias WHERE id=?", (sid,))
        r = cur.fetchone()
        return dict(r) if r else None

def marcar(sid, estado):
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE sugerencias SET estado=?, resuelta=? WHERE id=?",
                  (estado, datetime.datetime.now().isoformat(), sid))

def guardar_msg_id(sid, msg_id):
    with sqlite3.connect(DB) as c:
        c.execute("UPDATE sugerencias SET telegram_msg_id=? WHERE id=?", (msg_id, sid))

def stats():
    with sqlite3.connect(DB) as c:
        cur = c.execute("SELECT estado, COUNT(*) FROM sugerencias GROUP BY estado")
        return dict(cur.fetchall())

if __name__ == "__main__":
    print("DB:", DB)
    print("Pendientes:", pendientes()[:3])
    print("Stats:", stats())
