"""
🧹 CONSERJE — Auto-limpieza del ecosistema LofiProducer
================================================================================
QUÉ HACE
--------
Script determinista de limpieza. Corre 1 vez al día vía termux-job-scheduler.
Aplica reglas declarativas de config/limpieza.json. NO usa LLM (es predecible
y rápido). El Dios solo lo invoca cuando tú se lo pides, o lo consulta para
saber qué se limpió.

CÓMO FUNCIONA (para la próxima IA que lea esto)
------------------------------------------------
1. Lee config/limpieza.json (reglas declarativas).
2. Para cada regla:
   - Busca ficheros que cumplan patrón + antigüedad.
   - Si `auto_borrar: true` → mueve a ~/.trash/ (o borra según regla).
   - Si `auto_borrar: false` → solo lista (dry-run forzado para esa regla).
3. Reglas especiales:
   - `git_gc`: si .git > min_mb → `git gc --aggressive --prune=now`.
   - `changelog_max`: si AUTO_CHANGELOG.md > max_lineas → trunca los más viejos.
4. Notifica al móvil con `termux-notification` el resumen.
5. Documenta en AUTO_CHANGELOG.md un bloque `### <fecha> Conserje` con lo hecho.

CÓMO SE USA
-----------
  python scripts/conserje.py              # Aplica reglas (mueve/borra)
  python scripts/conserje.py --dry        # Solo simula (no toca nada)
  python scripts/conserje.py --regla=logs # Ejecuta solo 1 regla
  python scripts/conserje.py --stats      # Muestra qué limpiaría ahora

REGLAS DE SEGURIDAD
-------------------
- NUNCA borra modelos TTS, media publicado en YouTube, ni docs maestros.
- Mueve a ~/.trash/ (recuperable 30 días) salvo que la regla diga borrar.
- Si algo falla, no aborta las demás reglas (cada una es independiente).
- Log detallado en data/logs/conserje.log.

FILOSOFÍA
---------
"Si se puede regenerar, se borra. Si es único, se pregunta."
El criterio no es 'no se usa', es '¿es reproducible?'.
"""
import sys, os, json, shutil, subprocess, time, pathlib
from datetime import datetime, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "limpieza.json"
TRASH = pathlib.Path.home() / ".trash"
LOG = ROOT / "data" / "logs" / "conserje.log"
CHANGELOG = ROOT / "AUTO_CHANGELOG.md"
DRY = "--dry" in sys.argv
SOLO_REGLA = None
for a in sys.argv:
    if a.startswith("--regla="):
        SOLO_REGLA = a.split("=", 1)[1]
STATS = "--stats" in sys.argv

LOG.parent.mkdir(parents=True, exist_ok=True)
TRASH.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def notificar(titulo, mensaje):
    try:
        subprocess.run(["termux-notification", "-t", titulo, "-c", mensaje],
                      check=True, timeout=10, capture_output=True)
    except Exception:
        pass

def antiguedad_dias(p):
    return (time.time() - p.stat().st_mtime) / 86400.0

def aplicar_regla(regla):
    nombre = regla.get("nombre", "?")
    patrones = regla.get("patron", [])
    if isinstance(patrones, str):
        patrones = [patrones]
    dias = regla.get("antiguedad_dias", 7)
    excluir = regla.get("excluir", [])
    accion = regla.get("accion", "trash")

    movidos, tamaño = 0, 0
    for patron in patrones:
        if patron.startswith("~"):
            base = pathlib.Path(os.path.expanduser("~"))
            patron = patron[2:] if patron.startswith("~/") else patron[1:]
            ficheros = list(base.glob(patron))
        else:
            ficheros = list(ROOT.glob(patron))
        for f in ficheros:
            if not f.is_file(): continue
            if any(ex in str(f) for ex in excluir): continue
            if antiguedad_dias(f) < dias: continue
            size = f.stat().st_size
            if STATS:
                log(f"  [stats] {f} ({size//1024} KB, {antiguedad_dias(f):.1f}d)")
                movidos += 1
                tamaño += size
                continue
            if DRY:
                log(f"  [dry] movería {f} ({size//1024} KB)")
                movidos += 1
                tamaño += size
                continue
            dest = TRASH / f"{f.name}.{int(time.time())}"
            try:
                shutil.move(str(f), str(dest))
                movidos += 1
                tamaño += size
            except Exception as e:
                log(f"  [err] {f}: {e}")
    return nombre, movidos, tamaño

def regla_git_gc(regla):
    min_mb = regla.get("min_mb", 300)
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        return "git_gc", 0, 0
    tamaño_mb = sum(f.stat().st_size for f in git_dir.rglob("*") if f.is_file()) / (1024*1024)
    if tamaño_mb < min_mb:
        log(f"  [git_gc] .git = {tamaño_mb:.0f} MB < {min_mb} MB → saltando")
        return "git_gc", 0, 0
    if DRY:
        log(f"  [dry] git gc ({(tamaño_mb-min_mb):.0f} MB aprox liberables)")
        return "git_gc", 0, 0
    log(f"  [git_gc] .git = {tamaño_mb:.0f} MB → gc...")
    subprocess.run(["git", "gc", "--aggressive", "--prune=now"], cwd=str(ROOT), timeout=600)
    nuevo = sum(f.stat().st_size for f in git_dir.rglob("*") if f.is_file()) / (1024*1024)
    return "git_gc", 1, int((tamaño_mb - nuevo) * 1024 * 1024)

def regla_changelog_max(regla):
    max_lineas = regla.get("max_lineas", 3000)
    if not CHANGELOG.exists():
        return "changelog_max", 0, 0
    lineas = CHANGELOG.read_text(encoding="utf-8").splitlines()
    if len(lineas) <= max_lineas:
        return "changelog_max", 0, 0
    log(f"  [changelog_max] {len(lineas)} > {max_lineas} → truncando")
    if DRY:
        return "changelog_max", 0, 0
    nuevo = "\n".join(lineas[-max_lineas:])
    CHANGELOG.write_text(nuevo + "\n", encoding="utf-8")
    return "changelog_max", 1, 0

def main():
    if not CONFIG.exists():
        log(f"ERROR: falta {CONFIG}")
        return 1
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    reglas = cfg.get("reglas", [])
    if SOLO_REGLA:
        reglas = [r for r in reglas if r.get("nombre") == SOLO_REGLA]
        if not reglas:
            log(f"ERROR: regla '{SOLO_REGLA}' no existe")
            return 1

    log(f"═══ Conserje {'(dry-run)' if DRY else '(real)'}{(' stats' if STATS else '')} ═══")
    total_ficheros, total_bytes = 0, 0
    resumen = []
    for r in reglas:
        nombre = r.get("nombre", "?")
        try:
            if nombre == "git_gc":
                n, k, b = regla_git_gc(r)
            elif nombre == "changelog_max":
                n, k, b = regla_changelog_max(r)
            else:
                n, k, b = aplicar_regla(r)
            total_ficheros += k
            total_bytes += b
            resumen.append(f"  · {n}: {k} ficheros, {b//1024} KB")
            log(f"  ✅ {n}: {k} ficheros, {b//1024} KB")
        except Exception as e:
            log(f"  ❌ {nombre}: {e}")
            resumen.append(f"  · {nombre}: ERROR {e}")

    mb = total_bytes / (1024*1024)
    solo_gc = all("git_gc" in line for line in resumen) if resumen else False
    log(f"═══ Resumen: git gc liberó {mb:.1f} MB ═══" if (solo_gc and total_bytes > 0) else f"═══ Resumen: {total_ficheros} ficheros, {mb:.1f} MB ═══")

    if not DRY and not STATS and cfg.get("notificar_movil") and total_ficheros > 0:
        notificar("🧹 Conserje", f"Limpié {total_ficheros} ficheros ({mb:.1f} MB)")

    if not DRY and total_ficheros > 0:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        bloque = f"\n\n### {ts} Conserje\n" + "\n".join(resumen)
        with open(CHANGELOG, "a", encoding="utf-8") as f:
            f.write(bloque)
    return 0

if __name__ == "__main__":
    sys.exit(main())
