#!/usr/bin/env python3
"""limpieza_pipeline.py v2 - Reset diario TOTAL. Mantiene solo HOY + AYER.
Protege: memoria Dios, contratos, config, scripts, brain, web/dashboard, biblioteca LTX, nichos.
Borra: todo lo demás con fecha < AYER."""
import sys, os, shutil, time, re
from pathlib import Path
from datetime import datetime, timedelta, date

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

DRY_RUN = "--dry-run" in sys.argv
HOY = date.today().isoformat()
AYER = (date.today() - timedelta(days=1)).isoformat()
PERMITIDAS = {HOY, AYER}

# ═══ NUNCA BORRAR (rutas protegidas) ═══
PROTEGIDAS = [
    "data/agent",              # memoria Dios + contratos + cola DBs
    "config", "scripts", "brain", "core", "fases",
    "web/dashboard",           # Factory OS (código)
    "web/hooks", "web/overrides", "web/assets",
    "web/docs",                # BLOG COMPLETO - INTOCABLE (posts, podcast, glosario, home)
    "web/mkdocs.yml",          # build config - INTOCABLE
    "web/media",               # imágenes que usa la web activamente - INTOCABLE
    "docs",                    # MANUAL_ECOSISTEMA
    ".git", "sandbox", "secrets", "agent",
    "output/videos/biblioteca", # BIBLIOTECA LTX - INTOCABLE
    "output/nichos",           # configuración de nichos
]

# ═══ BORRAR SIEMPRE (temporales regenerables) ═══
BORRAR_SIEMPRE = [
    "output/tmp_voz",
    "output/render_tmp",
    "output/musica_temp",
    "output/encuadre/render_work",
    "output/encuadre/clips",
    "output/encuadre/audios",   # audios transcritos
    "web/site", "web/web",       # build artefacts
    "__pycache__",
]

# ═══ BORRAR CON FECHA < AYER (por nombre) ═══
DIRS_FECHA = [
    "output/encuadre",
    "output/cola_web",
    "output/cola_blogger",
    "output/podcast",
    "output/shorts",
    "data/logs",
    # web/docs/* PROTEGIDOS - ya no se limpian automáticamente.
    # Los posts viejos se borran manualmente con scripts específicos si hace falta.
]

EXT_BORRAR = {".mp4", ".mp3", ".wav", ".m4a", ".webm", ".png", ".jpg", ".jpeg", ".json", ".md", ".pdf", ".ass", ".srt"}

def _es_protegida(path):
    rp = str(path.relative_to(ROOT)).replace("\\", "/")
    # FIX flash5b: NUNCA borrar JSONs de output/encuadre
    if rp.startswith("output/encuadre/") and rp.endswith(".json"):
        return True
    for prot in PROTEGIDAS:
        if rp == prot or rp.startswith(prot + "/"):
            return True
    return False

def _fecha_de(nombre):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", nombre)
    return m.group(1) if m else None

def borrar_dir(ruta, forzar=False):
    p = ROOT / ruta
    if not p.exists() or _es_protegida(p): return 0, 0
    n = b = 0
    if forzar:
        for f in p.rglob("*"):
            if f.is_file() and not _es_protegida(f):
                b += f.stat().st_size; n += 1
                if not DRY_RUN:
                    try: f.unlink()
                    except: pass
        # Borrar subdirectorios vacíos
        for d in sorted(p.rglob("*"), reverse=True):
            if d.is_dir() and not any(d.iterdir()):
                try: d.rmdir()
                except: pass
    else:
        for f in p.rglob("*"):
            if not f.is_file() or _es_protegida(f): continue
            fch = _fecha_de(f.name)
            if fch and fch not in PERMITIDAS and f.suffix.lower() in EXT_BORRAR:
                b += f.stat().st_size; n += 1
                if not DRY_RUN:
                    try: f.unlink()
                    except: pass
    return n, b

total_n = total_b = 0

# 0. BACKUP pre-limpieza de web/docs (safety net)
import tarfile as _tar
_bk_dir = ROOT / "output" / "web_backups"
_bk_dir.mkdir(parents=True, exist_ok=True)
_bk_file = _bk_dir / f"web_docs_{datetime.now().strftime('%Y%m%d_%H%M')}.tar.gz"
try:
    with _tar.open(_bk_file, "w:gz") as _tar_obj:
        _tar_obj.add(ROOT / "web" / "docs", arcname="docs")
        _tar_obj.add(ROOT / "web" / "mkdocs.yml", arcname="mkdocs.yml")
        if (ROOT / "web" / "media").exists():
            _tar_obj.add(ROOT / "web" / "media", arcname="media")
    print(f"  [backup] {_bk_file.name} ({_bk_file.stat().st_size//1024}KB)")
    # Rotar: máx 7 backups
    _bks = sorted(_bk_dir.glob("web_docs_*.tar.gz"), reverse=True)
    for _old in _bks[7:]:
        _old.unlink()
except Exception as _e:
    print(f"  [backup] ERROR: {_e}")

# 1. BORRAR_SIEMPRE
for ruta in BORRAR_SIEMPRE:
    n, b = borrar_dir(ruta, forzar=True)
    total_n += n; total_b += b
    if n: print(f"  [siempre] {ruta}: {n} ({b//1024//1024}MB)")

# 2. DIRS_FECHA
for ruta in DIRS_FECHA:
    n, b = borrar_dir(ruta, forzar=False)
    total_n += n; total_b += b
    if n: print(f"  [fecha<{AYER}] {ruta}: {n} ({b//1024//1024}MB)")

# 3. output/ raíz (ficheros sueltos con fecha vieja, excl. protegidos)
for f in (ROOT / "output").iterdir():
    if f.is_file() and not _es_protegida(f):
        fch = _fecha_de(f.name)
        if fch and fch not in PERMITIDAS:
            total_b += f.stat().st_size; total_n += 1
            if not DRY_RUN:
                try: f.unlink()
                except: pass

# 4. .tmp.mp4 ocultos en output/encuadre
for f in (ROOT / "output" / "encuadre").glob(".*.tmp.mp4"):
    try:
        total_b += f.stat().st_size; total_n += 1
        if not DRY_RUN: f.unlink()
    except: pass

# 5. test_*.mp4/mp3 huérfanos >3d
corte_test = time.time() - 3*86400
for pat in ["output/encuadre/test_*.mp4", "output/encuadre/test_*.mp3"]:
    for f in ROOT.glob(pat):
        if f.is_file() and f.stat().st_mtime < corte_test:
            total_b += f.stat().st_size; total_n += 1
            if not DRY_RUN:
                try: f.unlink()
                except: pass

mode = "[DRY-RUN]" if DRY_RUN else "[OK]"
print(f"\n{mode} LIMPIEZA v2: {total_n} ficheros, {total_b/1024/1024:.1f}MB liberados (mantuvo {HOY}+{AYER})")
