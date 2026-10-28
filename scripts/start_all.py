"""
Arranque total del ecosistema LofiProducer.
- Verifica el .env.
- Arranca OmniRoute (si no está vivo).
- Mata cualquier Flask zombi y arranca el nuevo en el puerto 8001.
- Comprueba los Jobs de Android.
"""
from __future__ import annotations
import os
import subprocess
import time
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
OMNIROUTE_URL = "http://localhost:20128"
WEB_PORT = 8001

def log(msg: str) -> None:
    print(f"[sistema] {msg}")


def _check_ram():
    """Si RAM libre <500MB, matar procesos secundarios antes de lanzar pesados."""
    try:
        import subprocess
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                if ":" in line:
                    k, v = line.split(":", 1)
                    mem[k.strip()] = int(v.strip().split()[0]) // 1024
        libre = mem.get("MemAvailable", 0)
        if libre < 500:
            log(f"⚠️ RAM baja: {libre}MB libres. Matando procesos secundarios...")
            subprocess.run(["pkill", "-f", "task_worker.py"], check=False)
            subprocess.run(["pkill", "-f", "ollama"], check=False)
            log("✅ Procesos secundarios detenidos (se relanzarán tras arrancar Flask)")
            return False
        log(f"✅ RAM disponible: {libre}MB")
        return True
    except Exception as e:
        log(f"⚠️ No se pudo comprobar RAM: {e}")
        return True

def check_env() -> None:
    if not ENV_FILE.exists():
        raise SystemExit("❌ Falta el archivo .env")
    log("✅ .env cargado correctamente.")

def is_omniroute_alive() -> bool:
    try:
        r = requests.get(f"{OMNIROUTE_URL}/v1/models", timeout=2)
        return r.status_code in (200, 401, 403)
    except requests.RequestException:
        return False

def start_omniroute() -> None:
    if is_omniroute_alive():
        log("✅ OmniRoute ya está corriendo.")
        return
    log("⏳ OmniRoute no responde. Intentando arrancarlo...")
    if subprocess.run(["which", "omniroute"], capture_output=True).returncode != 0:
        log("❌ OmniRoute no está instalado. Instálalo con: npm install -g omniroute")
        log("⚠️ Mientras tanto, el Dios usará OpenRouter (funciona igual).")
        return
    log_file = PROJECT_ROOT / "data" / "logs" / "omniroute.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "w") as f:
        # Leer STORAGE_ENCRYPTION_KEY del data/.env
        data_env_path = PROJECT_ROOT / "data" / ".env"
        storage_key = ""
        if data_env_path.exists():
            for line in data_env_path.read_text().splitlines():
                if line.startswith("STORAGE_ENCRYPTION_KEY="):
                    storage_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        if not storage_key:
            log("⚠️ No se encontro STORAGE_ENCRYPTION_KEY en data/.env")
        env = os.environ.copy()
        env["STORAGE_ENCRYPTION_KEY"] = storage_key
        subprocess.Popen(["omniroute"], stdout=f, stderr=subprocess.STDOUT, start_new_session=True, env=env)
    
    # Esperar hasta 20 segundos (en vez de 10)
    for _ in range(90):
        time.sleep(1)
        if is_omniroute_alive():
            log("✅ OmniRoute arrancado correctamente.")
            return
    log("⚠️ OmniRoute no responde tras 20s. Revisa omniroute.log")
    log("⚠️ La web y el Dios seguirán funcionando con OpenRouter.")

def start_web() -> None:
    log("🔪 Matando Flask antiguo...")
    subprocess.run(["pkill", "-9", "-f", "web_dashboard.py"], capture_output=True)
    time.sleep(3)
    
    # --- Arrancar el Worker de Tareas en background ---
    log("⚙️ Arrancando Worker de tareas (cola)...")
    subprocess.Popen(
        ["python", "scripts/task_worker.py"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT), start_new_session=True
    )
    log("✅ Worker de tareas iniciado.")
    
    log(f"🚀 Arrancando Flask en el puerto {WEB_PORT}...")
    log_file = PROJECT_ROOT / "data" / "logs" / "web.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_file, "w") as f:
        subprocess.Popen(
            ["python", "web_dashboard.py"],
            cwd=str(PROJECT_ROOT),
            stdout=f, stderr=subprocess.STDOUT,
            start_new_session=True
        )
    
    time.sleep(3)
    try:
        r = requests.get(f"http://127.0.0.1:{WEB_PORT}/", timeout=3)
        if r.status_code == 200:
            log(f"✅ Web arrancada en http://127.0.0.1:{WEB_PORT}")
        else:
            log(f"⚠️ Web responde con HTTP {r.status_code}")
    except Exception:
        log("❌ La web no responde. Revisa data/logs/web.log")

def check_jobs() -> None:
    log("🤖 Comprobando Jobs de Android...")
    r = subprocess.run(["termux-job-scheduler", "-p"], capture_output=True, text=True)
    jobs = r.stdout.count("Pending Job")
    if jobs > 0:
        log(f"✅ {jobs} Jobs activos.")
    else:
        log("⚠️ No hay Jobs activos. Ejecuta termux-job-scheduler -p para verlos.")

def main() -> None:
    _check_ram()
    print("=" * 60)
    print("🚀 ARRANQUE TOTAL DEL ECOSISTEMA")
    print("=" * 60)
    check_env()
    start_omniroute()
    start_web()
    check_jobs()
    print("=" * 60)
    print("✨ TODO LISTO. Abre http://127.0.0.1:8001 en tu navegador.")

if __name__ == "__main__":
    main()
