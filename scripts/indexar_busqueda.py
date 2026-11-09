#!/usr/bin/env python3
"""Indexa output/ y web/docs/ en SQLite FTS5 para búsqueda full-text."""
import sqlite3, pathlib, json, re, datetime, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "agent" / "busqueda_fts.db"
DB.parent.mkdir(parents=True, exist_ok=True)

con = sqlite3.connect(str(DB))
con.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
    tipo, fecha, titulo, contenido, path UNINDEXED, ts UNINDEXED
)""")
con.commit()

# Limpiar e indexar de nuevo (rápido, ~30s)
con.execute("DELETE FROM docs")

def add(tipo, fecha, titulo, contenido, path):
    if not contenido or len(contenido) < 50: return
    contenido = re.sub(r"<[^>]+>", " ", contenido)[:50000]
    contenido = re.sub(r"\s+", " ", contenido).strip()
    con.execute("INSERT INTO docs (tipo, fecha, titulo, contenido, path, ts) VALUES (?,?,?,?,?,?)",
                (tipo, fecha, titulo[:200], contenido, str(path), datetime.datetime.now().isoformat()))

n = 0
# 1. Posts .md
for md in (ROOT / "web" / "docs" / "analisis").glob("*.md"):
    txt = md.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^date:\s*(\d{4}-\d{2}-\d{2})", txt, re.MULTILINE)
    fecha = m.group(1) if m else ""
    t = re.search(r"^title:\s*\"?([^\"]+)\"?", txt, re.MULTILINE)
    titulo = t.group(1) if t else md.stem
    add("post", fecha, titulo, txt, md); n += 1

# 2. Producción diaria (JSONs)
for jf in (ROOT / "output" / "encuadre").glob("produccion_*.json"):
    fecha = jf.stem.replace("produccion_", "")
    try:
        d = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
        contenido = d.get("texto_voz_largo", "") + " " + (d.get("articulo_html") or "")[:5000]
        titulo = (d.get("dossier") or {}).get("titular_brutal", f"Producción {fecha}")
        add("produccion", fecha, titulo, contenido, jf); n += 1
    except: pass

# 3. Dossiers
for jf in (ROOT / "output" / "encuadre").glob("dossier_*_enriquecido.json"):
    fecha = jf.stem.replace("dossier_", "").replace("_enriquecido", "")
    try:
        d = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
        contenido = json.dumps(d, ensure_ascii=False)
        add("dossier", fecha, "Dossier enriquecido " + fecha, contenido, jf); n += 1
    except: pass

con.commit()
con.execute("INSERT INTO docs (docs) VALUES ('optimize')")
con.commit()
con.close()
print(f"OK {n} docs indexados en {DB}")
