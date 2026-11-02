#!/usr/bin/env python3
"""limpieza_pipeline.py — Limpia assets del pipeline anterior, preserva lo publicado <3 días.
Uso: python3 scripts/limpieza_pipeline.py [--dry-run] [--dias 3]
"""
import sys, os, shutil, time
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

DRY_RUN = "--dry-run" in sys.argv
DIAS_PRESERVAR = 3
for i, arg in enumerate(sys.argv):
    if arg == "--dias" and i+1 < len(sys.argv):
        DIAS_PRESERVAR = int(sys.argv[i+1])

fecha_limite = time.time() - (DIAS_PRESERVAR * 86400)

# ═══ NUNCA BORRAR ═══
PROTEGIDOS = {
    "web/site", "web/docs/assets", "web/docs/analisis", "web/docs/stylesheets",
    "web/docs/javascripts", "web/docs/en", "assets", "data/agent",
    "config", "scripts", "brain", "core", "fases", "kaggle_src", "colab",
    "secrets", "agent", "sandbox", ".git", "web/media/imagenes",
    "web/docs/podcast/feed.xml", "web/docs/podcast/index.md",
}

# ═══ BORRAR SIEMPRE (temporales) ═══
BORRAR_SIEMPRE = [
    "output/tmp_voz",
    "output/render_tmp",
    "output/musica_temp",
    "output/musica_temp/bandcamp_tmp",
    "__pycache__",
]

# ═══ BORRAR SI >DIAS ═══
BORRAR_ANTIGUOS = [
    "output/snapshots",
    "output/imagenes",
    "output/videos",
    "output/merch",
    "output/stock",
    "output/taller",
    "output/keiz_productions",
    "output/encuadre",  # solo .mp4 y .mp3 sueltos
    "web/docs/podcast",  # solo .mp3
    "output",
]

# Extensiones a borrar >DIAS en output/encuadre
EXT_BORRAR = {".mp4", ".mp3", ".wav", ".m4a", ".webm", ".png", ".jpg"}

total_liberado = 0
archivos_borrados = 0
archivos_preservados = 0

def _es_protegido(path):
    rp = str(path.relative_to(ROOT))
    for prot in PROTEGIDOS:
        if rp == prot or rp.startswith(prot + "/"):
            return True
    return False

def _borrar(path, razon):
    global total_liberado, archivos_borrados
    if _es_protegido(path):
        return
    if not path.exists():
        return
    try:
        if path.is_file():
            size = path.stat().st_size
            if DRY_RUN:
                print(f"  [DRY] Borraría {path.relative_to(ROOT)} ({size//1024}KB) — {razon}")
            else:
                path.unlink()
                print(f"  ✅ {path.relative_to(ROOT)} ({size//1024}KB)")
            total_liberado += size
            archivos_borrados += 1
        elif path.is_dir():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            if DRY_RUN:
                print(f"  [DRY] Borraría dir {path.relative_to(ROOT)} ({size//1024//1024}MB) — {razon}")
            else:
                shutil.rmtree(path)
                print(f"  ✅ dir {path.relative_to(ROOT)} ({size//1024//1024}MB)")
            total_liberado += size
            archivos_borrados += 1
    except Exception as e:
        print(f"  ⚠️ {path}: {e}")

def _procesar_dir(dir_path, razon, ext_filter=None):
    global archivos_preservados
    if not dir_path.exists():
        return
    for item in dir_path.iterdir():
        if _es_protegido(item):
            archivos_preservados += 1
            continue
        if item.is_dir():
            _procesar_dir(item, razon, ext_filter)
        elif item.is_file():
            if ext_filter and item.suffix.lower() not in ext_filter:
                archivos_preservados += 1
                continue
            mtime = item.stat().st_mtime
            if mtime < fecha_limite:
                _borrar(item, razon)
            else:
                archivos_preservados += 1

print(f"\n{'='*60}")
print(f"  LIMPIEZA PIPELINE {'(DRY-RUN)' if DRY_RUN else '(REAL)'}")
print(f"  Preservando < {DIAS_PRESERVAR} días: {datetime.fromtimestamp(fecha_limite).strftime('%Y-%m-%d %H:%M')}")
print(f"{'='*60}\n")

# 1. BORRAR SIEMPRE
print("═══ 1. Temporales (borrar siempre) ═══")
for rel in BORRAR_SIEMPRE:
    p = ROOT / rel
    if p.exists():
        _borrar(p, "temporal")

# 2. BORRAR ANTIGUOS
print("\n═══ 2. Assets >3 días (regenerables) ═══")
for rel in BORRAR_ANTIGUOS:
    p = ROOT / rel
    if p.exists() and p.is_dir():
        _procesar_dir(p, ">3 días", EXT_BORRAR)

# 3. __pycache__ y .pyc
print("\n═══ 3. Cachés Python ═══")
for pc in ROOT.rglob("__pycache__"):
    if ".git" not in str(pc) and "site" not in str(pc):
        _borrar(pc, "pycache")
for pyc in ROOT.rglob("*.pyc"):
    if ".git" not in str(pyc):
        _borrar(pyc, "pyc")

# RESUMEN
print(f"\n{'='*60}")
print(f"  RESUMEN {'(SIMULACIÓN)' if DRY_RUN else ''}")
print(f"{'='*60}")
print(f"  Archivos borrados:    {archivos_borrados}")
print(f"  Archivos preservados: {archivos_preservados}")
print(f"  Espacio liberado:     {total_liberado/1024/1024/1024:.2f} GB")
print(f"{'='*60}\n")

if DRY_RUN:
    print("⚠️  Esto fue un DRY-RUN. Nada se borró.")
    print("   Para borrar de verdad: python3 scripts/limpieza_pipeline.py")
