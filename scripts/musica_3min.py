"""Genera 3 min de música en Kaggle y apaga el kernel automáticamente."""
import sys, time, pathlib, json, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from kaggle_bearer import push_kernel, estado_kernel, stop_kernel
from musica_acestep import _leer_token, _leer_env

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "kaggle_acestep_v11.py"
OUTPUT_DIR = ROOT / "output" / "musica"
USUARIO = "keizproductions"

def generar_3min(caption="solo piano, lofi, chill, 60 bpm, emotional, no drums", duracion=180):
    if not TEMPLATE.exists():
        return f"ERROR: falta {TEMPLATE}"

    code = TEMPLATE.read_text()
    # Inyectar 180s y token github
    code = code.replace("__CAPTION__", caption.replace('"', '\\"'))
    code = code.replace("__DURATION__", str(duracion))
    gtoken = _leer_env("GITHUB_TOKEN")
    code = code.replace('"__GITHUB_TOKEN__"', json.dumps(gtoken))

    slug_temp = f"acestep3m-{int(time.time())}"
    print(f"[Musica] Push -> {USUARIO}/{slug_temp}", flush=True)
    r = push_kernel(f"{USUARIO}/{slug_temp}", code)
    if isinstance(r, dict) and r.get("hasError"):
        return f"ERROR push: {r.get('error', r)}"
    print("[Musica] Push OK. Esperando GPU Kaggle...", flush=True)

    # Poll hasta 'complete' o timeout (3 min de audio puede tardar ~30-40 min)
    candidatos = [f"{USUARIO}/{slug_temp}", f"lofiproducer/{slug_temp}"]
    slug_real, status = None, "queued"
    for i in range(1, 90):
        time.sleep(30)
        for slug in candidatos:
            try:
                est = estado_kernel(slug)
                if isinstance(est, dict) and est.get("status"):
                    status = est["status"]
                    slug_real = slug
                    print(f"[{i}/90] {slug} -> {status}", flush=True)
                    break
            except Exception:
                continue
        if status in ("complete", "error", "failed"):
            break

    if slug_real:
        print(f"[Musica] Apagando kernel {slug_real}...", flush=True)
        stop_kernel(slug_real)

    if status != "complete":
        return f"ERROR: kernel acabó como {status}"

    # Descargar desde GitHub
    from musica_acestep import _descargar_github
    gtoken = _leer_env("GITHUB_TOKEN")
    return _descargar_github(gtoken)

if __name__ == "__main__":
    caption = sys.argv[1] if len(sys.argv) > 1 else "solo piano, lofi, chill, 60 bpm, emotional, no drums"
    print(generar_3min(caption))
