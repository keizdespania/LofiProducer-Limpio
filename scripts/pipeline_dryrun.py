#!/usr/bin/env python3
"""Pipeline Dry-Run: verifica si el pipeline de mañana fallará. NO genera archivos."""
import os, sys, json, subprocess, shutil, time, urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)

checks = []
def add(nombre, ok, detalle, severidad="error"):
    checks.append({"nombre": nombre, "ok": ok, "detalle": detalle, "sev": severidad})

def _env(k):
    for l in (ROOT/".env").read_text().splitlines():
        if l.startswith(k+"="): return l.split("=",1)[1].strip().strip('"').strip("'")
    return ""

# ═══ 1. SERVICIOS ═══
def check_flask():
    try:
        r = urllib.request.urlopen("http://127.0.0.1:8001/api/dashboard", timeout=3)
        add("Flask :8001", r.status==200, f"HTTP {r.status}")
    except Exception as e:
        add("Flask :8001", False, str(e)[:80])

def check_omniroute():
    try:
        r = urllib.request.urlopen("http://localhost:20128/v1/models", timeout=3)
        add("OmniRoute :20128", r.status in (200,401), f"HTTP {r.status}", "warn")
    except Exception as e:
        add("OmniRoute :20128", False, "caído (no crítico, Groq directo)", "warn")

def check_cron():
    try:
        r = subprocess.run(["pgrep","-f","crond"], capture_output=True)
        add("crond", r.returncode==0, "activo" if r.returncode==0 else "NO ACTIVO")
    except: add("crond", False, "no encontrado")

def check_cron_job():
    try:
        r = subprocess.run(["crontab","-l"], capture_output=True, text=True)
        tiene = "pipeline_encuadre.py" in r.stdout
        add("cron 06:00 pipeline", tiene, "configurado" if tiene else "FALTA")
    except: add("cron 06:00", False, "no se pudo leer crontab")

# ═══ 2. APIs EXTERNAS ═══
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"

def check_groq():
    key = _env("GROQ_API_KEY")
    if not key: add("GROQ_API_KEY", False, "vacía"); return
    payload = {"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":"OK"}],"max_tokens":5}
    try:
        req = urllib.request.Request("https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","User-Agent":UA}, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            add("Groq#1 (gpt-oss-20b)", True, "OK")
    except urllib.error.HTTPError as e:
        add("Groq#1", False, f"HTTP {e.code}", "error")
    except Exception as e:
        add("Groq#1", False, str(e)[:60], "error")

def check_youtube_api():
    key = _env("YOUTUBE_API_KEY")
    if not key: add("YOUTUBE_API_KEY", False, "vacía", "warn"); return
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&regionCode=ES&maxResults=1&key={key}"
        urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":UA}), timeout=10)
        add("YouTube API v3", True, "trending OK")
    except urllib.error.HTTPError as e:
        add("YouTube API", False, f"HTTP {e.code}", "warn")
    except Exception as e:
        add("YouTube API", False, str(e)[:60], "warn")

def check_telegram():
    tok = _env("TELEGRAM_BOT_TOKEN")
    if not tok: add("Telegram", False, "sin token", "warn"); return
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/getMe", timeout=5)
        add("Telegram bot", True, "OK")
    except Exception as e:
        add("Telegram", False, str(e)[:60], "warn")

# ═══ 3. FICHEROS CRÍTICOS ═══
criticos = [
    ("config/nichos.json", "config nichos"),
    (".env", ".env"),
    ("scripts/pipeline_encuadre.py", "pipeline_encuadre.py"),
    ("scripts/dios.py", "dios.py"),
    ("scripts/jarvis_listen.py", "jarvis_listen.py"),
    ("brain/especialistas.py", "especialistas.py"),
    ("brain/investigador_redes.py", "investigador_redes.py"),
    ("scripts/actualizar_web_index.py", "actualizar_web_index.py"),
    ("BOOT_PROMPT.md", "BOOT_PROMPT.md"),
]
for f, nombre in criticos:
    p = ROOT / f
    add(f"Fichero {nombre}", p.exists() and p.stat().st_size > 0,
        f"{p.stat().st_size//1024}KB" if p.exists() else "NO EXISTE")

# ═══ 4. NICHOS VÁLIDOS ═══
try:
    d = json.loads((ROOT/"config/nichos.json").read_text())
    nichos = [k for k in d if not k.startswith("_")]
    add("Nichos JSON", len(nichos)>=1, f"{len(nichos)} nichos: {','.join(nichos[:4])}...")
except Exception as e:
    add("Nichos JSON", False, str(e)[:60])

# ═══ 5. DISCO Y RAM ═══
try:
    st = shutil.disk_usage(str(ROOT))
    libre_gb = st.free / (1024**3)
    add("Disco libre", libre_gb > 1, f"{libre_gb:.1f}GB libres", "warn" if libre_gb < 3 else "error")
except: pass

try:
    with open("/proc/meminfo") as f:
        for l in f:
            if "MemAvailable" in l:
                mb = int(l.split()[1])//1024
                add("RAM libre", mb > 300, f"{mb}MB", "warn" if mb < 500 else "error")
                break
except: pass

# ═══ 6. MARKERS / DUPLICADOS ═══
hoy = datetime.now().strftime("%Y-%m-%d")
manana = (datetime.now().replace(day=datetime.now().day+1)).strftime("%Y-%m-%d")
marker_hoy = ROOT/f"data/agent/pipeline_done_{hoy}.txt"
add(f"Marker {hoy}", True, "existe (hoy ya corrió)" if marker_hoy.exists() else "no existe (mañana correrá) ✅", "info")

# ═══ 7. PROCESOS BLOQUEANTES ═══
for proc, nombre in [("jarvis_wake.py","jarvis_wake (daemon viejo)"),("pipeline_encuadre.py","pipeline corriendo")]:
    r = subprocess.run(["pgrep","-f",proc], capture_output=True)
    vivo = r.returncode == 0
    if proc == "jarvis_wake.py":
        add(nombre, not vivo, "MATA ESTE PROCESO" if vivo else "no activo", "warn" if vivo else "info")
    else:
        add(nombre, True, "corriendo (normal si toca)" if vivo else "no activo", "info")

# ═══ 8. WEB MKODCS ═══
index_md = ROOT/"web/docs/index.md"
add("web/docs/index.md", index_md.exists(), f"{index_md.stat().st_size//1024}KB" if index_md.exists() else "NO EXISTE")

# ═══ 9. MODELOS GROQ VÁLIDOS EN DIOS.PY ═══
dios = (ROOT/"scripts/dios.py").read_text()
modelos_validos = ["gpt-oss-120b","gpt-oss-20b","qwen3.8-27b"]
invalidos = ["llama-3.3-70b","llama-3.1-8b"]
malos = [m for m in invalidos if m in dios]
add("Modelos Groq en dios.py", not malos, "válidos" if not malos else f"contiene inválidos: {malos}")

# ═══ 10. USER-AGENT ═══
add("User-Agent Chrome en dios.py", "CHROME_UA" in dios, "✅" if "CHROME_UA" in dios else "FALTA (403 Cloudflare)")

# ═══ EJECUTAR CHECKS DE SERVICIOS Y APIS ═══
check_flask()
check_omniroute()
check_cron()
check_cron_job()
check_groq()
check_youtube_api()
check_telegram()

# ═══ REPORTE ═══
print("\n" + "="*62)
print(f"  PIPELINE DRY-RUN — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print("="*62)
errores = [c for c in checks if not c["ok"] and c["sev"]=="error"]
warns = [c for c in checks if not c["ok"] and c["sev"]=="warn"]
oks = [c for c in checks if c["ok"]]
for c in checks:
    icon = "✅" if c["ok"] else ("❌" if c["sev"]=="error" else "⚠️")
    print(f"  {icon} {c['nombre']:<32} {c['detalle']}")
print("="*62)
if errores:
    print(f"🔴 {len(errores)} ERRORES CRÍTICOS — pipeline PUEDE fallar")
    for e in errores: print(f"   • {e['nombre']}: {e['detalle']}")
elif warns:
    print(f"🟡 {len(warns)} warnings — pipeline correrá con avisos")
    for w in warns: print(f"   • {w['nombre']}: {w['detalle']}")
else:
    print(f"🟢 TODO OK — {len(oks)} checks pasados. Pipeline listo.")
print("="*62)
print(f"  Resumen: {len(oks)} OK · {len(warns)} warn · {len(errores)} error")
print("="*62)
