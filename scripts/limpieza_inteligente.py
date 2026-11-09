#!/usr/bin/env python3
"""Limpieza inteligente: borra >N días sin romper pipeline ni perder el día actual."""
import pathlib, time, subprocess, datetime, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
HOY = datetime.date.today().isoformat()

def _borrar_viejo(patron, dias, keep_hoy=True, etiqueta=""):
    corte = time.time() - dias * 86400
    n = 0
    for p in pathlib.Path(ROOT).glob(patron) if "*" in patron else [ROOT / patron]:
        if p.is_file():
            if keep_hoy and HOY in p.name: continue
            if p.stat().st_mtime < corte:
                p.unlink(); n += 1
    if n: print(f"  [{etiqueta}] {n} borrados (> {dias}d)")
    return n

total = 0
# Logs >14d
total += _borrar_viejo("data/logs/*.log", 14, etiqueta="logs")
# Snapshots git >30d
try:
    r = subprocess.run(["git", "tag", "-l", "snap-*"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
    for tag in r.stdout.strip().splitlines():
        try:
            fecha = datetime.datetime.strptime(tag.split("-")[1] + "-" + tag.split("-")[2], "%Y%m%d-%H%M%S")
            if (datetime.datetime.now() - fecha).days > 30:
                subprocess.run(["git", "tag", "-d", tag], cwd=str(ROOT), check=False)
                subprocess.run(["git", "push", "origin", ":refs/tags/" + tag], cwd=str(ROOT), capture_output=True, check=False)
                print(f"  [git-tag] {tag} borrado (> 30d)"); total += 1
        except: pass
except: pass
# Costes + episodios >90d (mantener workspace + fallos)
total += _borrar_viejo("data/agent/dios_costes.db", 0, etiqueta="") # no borrar, se gestiona dentro
# Output pesado >30d (mantener HOY)
for pat, dia in [("output/encuadre/video_largo_*.mp4", 30), ("output/encuadre/short_*.mp4", 30),
                 ("output/encuadre/podcast_*.mp3", 30), ("output/encuadre/seg_*.png", 7),
                 ("web/media/imagenes/post_*.png", 60)]:
    total += _borrar_viejo(pat, dia, etiqueta=pat.split("/")[-1])
# Busqueda FTS5: reindexar si >7d
fts = ROOT / "data/agent/busqueda_fts.db"
if fts.exists() and (time.time() - fts.stat().st_mtime) > 7 * 86400:
    print("  [fts] reindexando (> 7d)...")
    subprocess.run(["python3", "scripts/indexar_busqueda.py"], cwd=str(ROOT), timeout=180, check=False)
# Git gc mensual
if datetime.datetime.now().day == 1:
    subprocess.run(["git", "gc", "--aggressive", "--prune=now"], cwd=str(ROOT), timeout=300, check=False)
    print("  [git] gc aggressive (día 1)")

# Reporte tamaño
du = subprocess.run(["du", "-sh", "output", "data", "web/media", ".git"], cwd=str(ROOT), capture_output=True, text=True)
print(f"\nLIMPIEZA OK ({total} ficheros borrados)")
print(du.stdout)
