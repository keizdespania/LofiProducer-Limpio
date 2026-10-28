"""monitor_salud.py - Vigila que todo el ecosistema esté vivo."""
import requests, subprocess, sys

def check():
    errores = []
    # 1. OmniRoute
    try:
        r = requests.get("http://localhost:20128/v1/models", timeout=5)
        if r.status_code != 200: errores.append("OmniRoute no responde")
    except: errores.append("OmniRoute caído")
    
    # 2. Disco
    st = subprocess.run(["df", "-h", "/data"], capture_output=True, text=True).stdout
    if "100%" in st: errores.append("Disco lleno")
    
    if errores:
        msg = " | ".join(errores)
        print(f"❌ ALERTA: {msg}")
        subprocess.run(["termux-notification", "-t", "⚠️ Alerta Sistema", "-c", msg, "--priority", "max"], check=False)
        sys.exit(1)
    print("✅ Todo OK")

if __name__ == "__main__": check()
