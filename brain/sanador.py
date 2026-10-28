"""Auto-sanacion del ecosistema (Flask, OmniRoute)."""
import subprocess, time, requests, os, pathlib

def _ping(url, timeout=3):
    try:
        r = requests.get(url, timeout=timeout)
        return r.status_code < 500
    except Exception:
        return False

ROOT = pathlib.Path(__file__).resolve().parent.parent

def sanar():
    reporte = []
    if not _ping("http://127.0.0.1:8001/"):
        reporte.append("Flask caido. Reiniciando...")
        subprocess.run("pkill -9 -f web_dashboard.py", shell=True)
        time.sleep(2)
        subprocess.Popen("nohup python web_dashboard.py > data/logs/web.log 2>&1 &", shell=True, cwd=str(ROOT))
        time.sleep(5)
        if _ping("http://127.0.0.1:8001/"):
            reporte.append("OK: Flask revivido.")
        else:
            reporte.append("FALLO: Flask no arranca.")
    else:
        reporte.append("OK: Flask vivo.")

    if not _ping("http://localhost:20128/api/monitoring/health"):
        reporte.append("OmniRoute caido. Reiniciando...")
        subprocess.run("pkill -9 -f omniroute", shell=True)
        time.sleep(3)
        env_file = ROOT / "data" / ".env"
        key = ""
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("STORAGE_ENCRYPTION_KEY="):
                    key = line.split("=",1)[1].strip().strip('"').strip("'")
                    break
        env = os.environ.copy()
        env["STORAGE_ENCRYPTION_KEY"] = key
        subprocess.Popen("nohup omniroute serve > data/logs/omniroute.log 2>&1 &", shell=True, env=env, cwd=str(ROOT))
        time.sleep(20)
        if _ping("http://localhost:20128/api/monitoring/health"):
            reporte.append("OK: OmniRoute revivido.")
        else:
            reporte.append("FALLO: OmniRoute no arranca.")
    else:
        reporte.append("OK: OmniRoute vivo.")
    return "\n".join(reporte)
