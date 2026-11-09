#!/usr/bin/env python3
"""Watchdog v2 - Solo alerta errores REALES. Sin falsos positivos.
Usa notificador_top1 (throttle + dedupe).
Reglas:
  1. Si pipeline no arrancó HOY a las 06:00 (log sin entradas nuevas >2h)
  2. Si pipeline zombie (>90min corriendo sin log nuevo)
  3. Si YouTube falló hoy (falta youtube_urls_{fecha}.json y ya son >10AM)
  4. Si disco >95% lleno
"""
import sys, pathlib, time, subprocess, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from notificador_top1 import alerta

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "logs" / "pipeline.log"
YT_JSON = ROOT / "data" / "agent"

ahora = datetime.datetime.now()
hoy = ahora.date().isoformat()
hora = ahora.hour

def _log_tiene_entradas_hoy():
    """¿Hay algún log de hoy con contenido?"""
    if not LOG.exists(): return False
    if datetime.datetime.fromtimestamp(LOG.stat().st_mtime).date() == ahora.date():
        return True
    return False

def _log_hace_cuanto_min():
    if not LOG.exists(): return 9999
    return (time.time() - LOG.stat().st_mtime) / 60

# ─── 1. PIPELINE NO ARRANCÓ ───
if 9 <= hora <= 12:
    if not _log_tiene_entradas_hoy():
        mins = _log_hace_cuanto_min()
        if mins > 120:
            alerta("pipeline_no_arranco",
                   f"No hay entradas en pipeline.log hoy {hoy}.\nÚltimo log: hace {int(mins)}min.\n\n"
                   f"Verifica: <code>tail -20 data/logs/pipeline.log</code>",
                   nivel="critico")

# ─── 2. PIPELINE ZOMBIE ───
try:
    r = subprocess.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    if r.stdout.strip():
        mins = _log_hace_cuanto_min()
        if mins > 90:
            alerta("pipeline_zombie",
                   f"Pipeline corriendo pero sin escribir en log hace {int(mins)}min.\n\n"
                   f"Revisa: <code>pgrep -af pipeline_encuadre</code>",
                   nivel="critico")
except: pass

# ─── 3. YOUTUBE FALLÓ ───
if 10 <= hora <= 13:
    yt_file = YT_JSON / f"youtube_urls_{hoy}.json"
    if not yt_file.exists():
        alerta("youtube_fail",
               f"No existe youtube_urls_{hoy}.json.\n\n"
               f"El vídeo largo o los shorts no se subieron.\n"
               f"Revisa: <code>grep -i youtube data/logs/pipeline.log | tail -10</code>",
               nivel="warning")

# ─── 4. DISCO ───
try:
    st = subprocess.run(["df", "-h", str(ROOT)], capture_output=True, text=True, timeout=5)
    lines = st.stdout.strip().split("\n")
    if len(lines) > 1:
        partes = lines[1].split()
        uso = partes[4].replace("%", "")
        if int(uso) >= 95:
            alerta("disco_lleno", f"Disco al {uso}%. Limpia o el pipeline fallará.", nivel="critico")
except: pass

# ─── 5. LIMPIAR throttle de tipos ya resueltos ───
# (opcional: si todo OK hoy, resetea alertas previas)
