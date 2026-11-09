#!/usr/bin/env python3
"""Watchdog: si el pipeline corre >90min sin log nuevo o el cron 06:00 no arrancó, alerta Telegram."""
import pathlib, time, subprocess, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "logs" / "pipeline.log"
TOKEN = ""
CHAT = ""
for line in (ROOT/".env").read_text().splitlines():
    if line.startswith("TELEGRAM_BOT_TOKEN="): TOKEN = line.split("=",1)[1].strip().strip('"').strip("'")
    if line.startswith("TELEGRAM_CHAT_ID="): CHAT = line.split("=",1)[1].strip().strip('"').strip("'")

def alerta(msg):
    if not TOKEN or not CHAT: return
    try:
        import requests
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT, "text": msg}, timeout=10)
    except: pass

hoy = datetime.date.today().isoformat()
hora = datetime.datetime.now().hour

# 1. ¿Cron 06:00 arrancó?
if 7 <= hora <= 9:
    marca = ROOT / "data" / "agent" / f"cron_arrancado_{hoy}.flag"
    if not marca.exists():
        # ¿Hay algo en el log de hoy?
        if LOG.exists() and LOG.stat().st_mtime < time.time() - 3600:
            alerta(f"⚠️ Pipeline {hoy} NO arrancó a las 06:00 (log sin actualizar desde {(time.time()-LOG.stat().st_mtime)/60:.0f}min)")
        else:
            alerta(f"⚠️ Pipeline {hoy} NO arrancó a las 06:00 (no existe flag arranque)")

# 2. ¿Pipeline zombie?
try:
    r = subprocess.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    if r.stdout.strip():
        if LOG.exists():
            sin_cambios = (time.time() - LOG.stat().st_mtime) / 60
            if sin_cambios > 90:
                alerta(f"🚨 Pipeline lleva {sin_cambios:.0f}min sin escribir en log. Posible zombie. Revisa: pgrep -af pipeline")
except: pass
