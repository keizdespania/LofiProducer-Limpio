#!/usr/bin/env python3
"""Sube shorts programados cuyo publish_at ya pasó. Cron cada 30 min."""
import sys, json, pathlib, sqlite3, datetime, subprocess
ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "agent" / "cola_publicacion.db"
if not DB.exists():
    print("[cola] sin DB"); sys.exit(0)
ahora = datetime.datetime.now()
con = sqlite3.connect(str(DB)); con.row_factory = sqlite3.Row
cur = con.cursor()
# Schema: id, video_path, titulo, descripcion, tags, publish_at, estado, youtube_id, creada
cur.execute("SELECT id, video_path, titulo, descripcion, tags, publish_at FROM publicaciones WHERE estado = 'pendiente'")
for row in cur.fetchall():
    try:
        pub = datetime.datetime.fromisoformat(row["publish_at"].replace("Z", ""))
    except: continue
    if pub > ahora: continue
    print(f"[cola] subiendo {row['titulo'][:50]}...")
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import subir
        tags = json.loads(row["tags"]) if row["tags"] else []
        r = subir(row["video_path"], row["titulo"], row["descripcion"] or "", tags=tags, privacidad="public", token_file="data/youtube_encuadre_token.json")
        cur.execute("UPDATE publicaciones SET estado='publicado', youtube_id=? WHERE id=?", (r.get("id",""), row["id"]))
        con.commit()
        print(f"  ✅ {r.get('id')}")
    except Exception as e:
        print(f"  ❌ {e}")
con.close()
