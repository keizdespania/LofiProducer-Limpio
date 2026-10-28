"""cola_publicacion.py - Gestiona la programacion de subidas a YouTube."""
import sqlite3, datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "agent" / "cola_publicacion.db"

def _init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as c:
        c.execute("CREATE TABLE IF NOT EXISTS publicaciones (id INTEGER PRIMARY KEY AUTOINCREMENT, video_path TEXT, titulo TEXT, descripcion TEXT, tags TEXT, publish_at TEXT, estado TEXT DEFAULT 'pending', youtube_id TEXT, creada TEXT)")

def proximo_hueco():
    _init_db()
    with sqlite3.connect(DB_PATH) as c:
        row = c.execute("SELECT MAX(publish_at) FROM publicaciones WHERE estado = 'pending'").fetchone()
        ahora = datetime.datetime.now(datetime.timezone.utc)
        if row and row[0]:
            base = datetime.datetime.fromisoformat(row[0].replace("Z", "+00:00"))
            if base < ahora: base = ahora
        else:
            base = ahora
        while True:
            base += datetime.timedelta(days=1)
            if base.weekday() < 5:
                base = base.replace(hour=13, minute=0, second=0, microsecond=0)
                return base.isoformat().replace("+00:00", "Z")

def encolar(video_path, titulo, desc="", tags=""):
    _init_db()
    fecha = proximo_hueco()
    ahora = datetime.datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as c:
        c.execute("INSERT INTO publicaciones (video_path, titulo, descripcion, tags, publish_at, creada) VALUES (?,?,?,?,?,?)", (str(video_path), titulo, desc, tags, fecha, ahora))
    print(f"[cola] Encolado: {titulo} -> {fecha}")
    return fecha

def procesar_cola():
    _init_db()
    ahora = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    with sqlite3.connect(DB_PATH) as c:
        rows = c.execute("SELECT id, video_path, titulo, descripcion, tags FROM publicaciones WHERE estado = 'pending' AND publish_at <= ?", (ahora,)).fetchall()
    if not rows:
        print("[cola] No hay nada para publicar ahora.")
        return
    from subir_youtube import subir
    for r in rows:
        vid_id, path, titulo, desc, tags = r
        print(f"[cola] Subiendo {titulo}...")
        try:
            res = subir(path, titulo, desc, tags, privacidad="private")
            yt_id = res.get("id")
            with sqlite3.connect(DB_PATH) as c2:
                c2.execute("UPDATE publicaciones SET estado = 'done', youtube_id = ? WHERE id = ?", (yt_id, vid_id))
            print(f"[cola] OK subido: {yt_id}")
        except Exception as e:
            print(f"[cola] Error {titulo}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    if sys.argv[1] == "procesar": procesar_cola()