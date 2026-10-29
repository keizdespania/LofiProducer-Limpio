"""descargar_y_borrar_github.py - Polling de GitHub, descarga mp4s, borra del repo.
Uso: python descargar_y_borrar_github.py [prefijo] [destino] [timeout_min]
Ejemplo: python descargar_y_borrar_github.py render_2026 output/encuadre 60"""
import sys, json, base64, requests, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
TOKEN = ""
if ENV.exists():
    for line in ENV.read_text().splitlines():
        if line.startswith("GITHUB_TOKEN="):
            TOKEN = line.split("=", 1)[1].strip().strip('"').strip("'"); break
if not TOKEN:
    print("ERROR: falta GITHUB_TOKEN"); sys.exit(1)

REPO = "keizdespania/LofiProducer-backup"
BRANCH = "main"
API = f"https://api.github.com/repos/{REPO}/contents"
H = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}


def listar(carpeta="output/videos"):
    r = requests.get(f"{API}/{carpeta}?ref={BRANCH}", headers=H, timeout=30)
    if r.status_code != 200: return []
    return r.json() if isinstance(r.json(), list) else []


def descargar(carpeta, nombre, destino):
    r = requests.get(f"{API}/{carpeta}/{nombre}?ref={BRANCH}", headers=H, timeout=30)
    if r.status_code != 200: return None
    d = r.json()
    contenido = base64.b64decode(d["content"])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(contenido)
    print(f"  descargado {destino.name} ({len(contenido)//1024//1024}MB)", flush=True)
    return d.get("sha")


def borrar(carpeta, nombre, sha):
    payload = {"message": f"cleanup {nombre}", "sha": sha, "branch": BRANCH}
    r = requests.delete(f"{API}/{carpeta}/{nombre}", headers=H, json=payload, timeout=30)
    if r.status_code in (200, 204):
        print(f"  borrado GitHub {nombre}", flush=True); return True
    print(f"  error borrar {r.status_code}: {r.text[:100]}", flush=True); return False


def main(prefijo="render_", destino_dir="output/encuadre", timeout_min=60, carpeta="output/videos"):
    destino_dir = ROOT / destino_dir
    t0 = time.time()
    vistos = set()
    print(f"[poll] prefijo='{prefijo}' timeout={timeout_min}min", flush=True)
    while time.time() - t0 < timeout_min * 60:
        for f in listar(carpeta):
            n = f.get("name", "")
            if not n.startswith(prefijo) or not n.endswith(".mp4"): continue
            if n in vistos: continue
            vistos.add(n)
            sha = descargar(carpeta, n, destino_dir / n)
            if sha: borrar(carpeta, n, sha)
        # Si ya bajamos algo, salir al siguiente ciclo sin más ficheros
        if vistos and not any(f.get("name","").startswith(prefijo) and f.get("name","").endswith(".mp4") for f in listar(carpeta)):
            print(f"[poll] OK {len(vistos)} archivos", flush=True); return True
        time.sleep(20)
    print(f"[poll] timeout sin nuevos archivos", flush=True)
    return False


if __name__ == "__main__":
    prefijo = sys.argv[1] if len(sys.argv) > 1 else "render_"
    dest = sys.argv[2] if len(sys.argv) > 2 else "output/encuadre"
    tmin = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    sys.exit(0 if main(prefijo, dest, tmin) else 1)
