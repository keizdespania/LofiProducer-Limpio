#!/usr/bin/env python3
"""Limpieza rolling-2-dias: mantiene HOY + AYER. Borra todo lo anterior.
NO toca: biblioteca LTX, memoria Dios, código, contratos, config, biblioteca musical."""
import pathlib, time, subprocess, datetime, re, shutil, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
HOY = datetime.date.today().isoformat()
AYER = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
PERMITIDAS = {HOY, AYER}

def fecha_de(fname):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", fname)
    return m.group(1) if m else None

def borrar_por_fecha(subdir):
    """Borra ficheros con fecha < AYER en una carpeta. Mantiene HOY/AYER."""
    n = b = 0
    p = ROOT / subdir
    if not p.exists(): return n, b
    for f in p.rglob("*"):
        if not f.is_file(): continue
        fch = fecha_de(f.name)
        if fch and fch not in PERMITIDAS:
            try: b += f.stat().st_size; f.unlink(); n += 1
            except: pass
    return n, b

total_n = total_b = 0
print(f"=== LIMPIEZA {HOY} (mantiene {HOY} + {AYER}) ===")

# 1. Output con fecha: solo 2 días
for sub in ["output/encuadre", "output/cola_web", "output/cola_blogger",
            "output/musica_temp", "web/docs/analisis", "web/docs/podcast",
            "web/docs/en", "web/media/imagenes"]:
    n, b = borrar_por_fecha(sub)
    total_n += n; total_b += b
    if n: print(f"  {sub}: {n} ({b//1024//1024}MB)")

# 2. Regenerables diarios (siempre se borran)
for patron in ["web/media/imagenes/seg_*.png", "web/media/imagenes/short_*.png"]:
    n = b = 0
    for f in ROOT.glob(patron):
        if f.is_file():
            try: b += f.stat().st_size; f.unlink(); n += 1
            except: pass
    total_n += n; total_b += b
    if n: print(f"  {patron.split('/')[-1]}: {n} ({b//1024//1024}MB)")

# 2b. render_work + clips (siempre, son temporales del render)
for d in ["output/encuadre/render_work", "output/encuadre/clips"]:
    p2 = ROOT / d
    if p2.exists():
        s = sum(f.stat().st_size for f in p2.rglob("*") if f.is_file())
        shutil.rmtree(p2, ignore_errors=True)
        total_b += s
        print(f"  {d}: {s//1024//1024}MB")

# 2c. test_*.mp4/mp3 viejos (>3d, sin fecha en nombre)
corte_test = time.time() - 3 * 86400
n = b = 0
for pat in ["output/encuadre/test_*.mp4", "output/encuadre/test_*.mp3"]:
    for f in ROOT.glob(pat):
        if f.is_file() and f.stat().st_mtime < corte_test:
            try: b += f.stat().st_size; f.unlink(); n += 1
            except: pass
total_n += n; total_b += b
if n: print(f"  test_* (>3d): {n} ({b//1024//1024}MB)")

# 3. Build artefacts (siempre)
for d in ["web/site", "web/web"]:
    p = ROOT / d
    if p.exists():
        s = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        shutil.rmtree(p, ignore_errors=True)
        total_b += s
        print(f"  {d}: {s//1024//1024}MB")

# 4. Logs > 7 días (no > 14, más agresivo ahora)
corte = time.time() - 7 * 86400
n = 0
for f in (ROOT/"data"/"logs").glob("*.log"):
    if f.stat().st_mtime < corte and fecha_de(f.name) not in PERMITIDAS:
        try: f.unlink(); n += 1
        except: pass
if n: print(f"  data/logs (>7d): {n}")

# 5. Git tags > 7 días
try:
    r = subprocess.run(["git", "tag", "-l", "snap-*"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
    for tag in r.stdout.strip().splitlines():
        try:
            fecha = datetime.datetime.strptime(tag.split("-")[1] + "-" + tag.split("-")[2], "%Y%m%d-%H%M%S")
            if (datetime.datetime.now() - fecha).days > 7:
                subprocess.run(["git", "tag", "-d", tag], cwd=str(ROOT), check=False)
                subprocess.run(["git", "push", "origin", ":refs/tags/" + tag], cwd=str(ROOT), capture_output=True, check=False)
                print(f"  git-tag {tag} borrado (> 7d)")
        except: pass
except: pass

# 6. Reindexar FTS5 si > 1 día (siempre al día)
fts = ROOT / "data/agent/busqueda_fts.db"
if fts.exists() and (time.time() - fts.stat().st_mtime) > 86400:
    print("  fts: reindexando...")
    subprocess.run(["python3", "scripts/indexar_busqueda.py"], cwd=str(ROOT), timeout=180, check=False)

# 7. Git gc día 1
if datetime.datetime.now().day == 1:
    subprocess.run(["git", "gc", "--aggressive", "--prune=now"], cwd=str(ROOT), timeout=300, check=False)
    print("  git: gc aggressive")

# Resumen
print(f"\nLIMPIEZA OK: {total_n} ficheros, {total_b/1024/1024:.1f}MB liberados")
du = subprocess.run(["du", "-sh", "output", "data/agent", "web/media", ".git"], cwd=str(ROOT), capture_output=True, text=True)
print(du.stdout)
