"""renderizar_en_kaggle.py - Orquesta: sube assets a Kaggle, lanza kernel T4, descarga mp4."""
import sys, json, pathlib, subprocess, shutil, time, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from kaggle_bearer import push_kernel, estado_kernel, output_kernel, stop_kernel

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
KERNEL_SLUG = "keizproductions/render-encuadre"
DS_OWNER = "keizproductions"
DS_SLUG = "encuadre-assets"  # ajustar si cuenta 2


def _preparar_assets(fecha, dest):
    """Copia 18 escenas + voz + ass + musica + timeline a una carpeta plana."""
    dest.mkdir(parents=True, exist_ok=True)
    tl = json.loads((OUT / f"timeline_{fecha}.json").read_text())
    faltan = []
    for item in tl:
        n = item["id"]
        for ext in ("mp4", "png"):
            src = MEDIA / f"escena_{n:02d}.{ext}"
            if src.exists(): shutil.copy2(src, dest / src.name)
        mus = MUSICA / f"escena_{n:02d}.mp3"
        if mus.exists(): shutil.copy2(mus, dest / mus.name)
        else: faltan.append(f"escena_{n:02d}.mp3")
    for f in ("voz_largo_", "intro", "outro"):
        for ext in ("mp3", "ass", "mp4"):
            src = OUT / f"{f}{fecha}.{ext}" if f == "voz_largo_" else OUT / f"{f}.{ext}"
            if src.exists(): shutil.copy2(src, dest / src.name)
    shutil.copy2(OUT / f"timeline_{fecha}.json", dest / "timeline.json")
    if faltan: print(f"⚠️ Faltan {len(faltan)} audios: {faltan[:3]}")
    return dest


def _subir_dataset(assets_dir, dataset_slug):
    """Sube assets a Kaggle Dataset vía CLI (kaggle datasets create/version)."""
    print(f"[orq] Preparando dataset {dataset_slug}...")
    meta = {
        "title": "Encuadre Assets",
        "id": dataset_slug,
        "licenses": [{"name": "CC0-1.0"}],
    }
    (assets_dir / "dataset-metadata.json").write_text(json.dumps(meta, indent=2))
    r = subprocess.run(["kaggle", "datasets", "create", "-p", str(assets_dir)],
                       capture_output=True, text=True, timeout=900)
    if "already exists" in (r.stdout + r.stderr).lower() or r.returncode != 0:
        print("[orq] Existe, subiendo nueva versión...")
        r = subprocess.run(["kaggle", "datasets", "version", "-p", str(assets_dir), "-m", "update"],
                           capture_output=True, text=True, timeout=900)
    out = (r.stdout or "") + (r.stderr or "")
    print(f"[orq] kaggle exit={r.returncode}")
    print(f"[orq] ultimas lineas: {out.strip().splitlines()[-3:] if out.strip() else 'vacio'}")
    if r.returncode != 0:
        return False
    # Kaggle tarda 60-180s en procesar dataset. Esperar explícitamente.
    print("[orq] esperando procesado Kaggle (90s)...")
    import time as _t; _t.sleep(90)
    return True


def _renderizar_kernel(fecha):
    """Lee template y lo sube como kernel."""
    tpl = (ROOT / "scripts" / "kernel_render_encuadre.py").read_text()
    # Inyectar FECHA + GITHUB_TOKEN reales (como Wan)
    import re as _re
    _env = (ROOT / ".env").read_text()
    _tok = ""
    for _l in _env.splitlines():
        if _l.startswith("GITHUB_TOKEN="):
            _tok = _l.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39)); break
    tpl = tpl.replace("__FECHA__", fecha).replace("__GITHUB_TOKEN__", _tok)
    print(f"[orq] push_kernel({KERNEL_SLUG})...")
    # Pasar el dataset como source (monta /kaggle/input/<slug>/)
    ds_sources = [f"{DS_OWNER}/{DS_SLUG}"] if DS_OWNER and DS_SLUG else []
    print(f"[orq] dataset_sources: {ds_sources}")
    res = push_kernel(KERNEL_SLUG, tpl, enable_gpu=True, enable_internet=True, dataset_sources=ds_sources)
    print(f"[orq] push result: {str(res)[:200]}")
    return not (isinstance(res, dict) and res.get("hasError"))


def _esperar_fin(slug, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = estado_kernel(slug)
        s = st.get("status", "?") if isinstance(st, dict) else "?"
        print(f"[orq] {s} ({int(time.time()-t0)}s)", flush=True)
        if s in ("complete", "error", "cancelAcknowledged"): return s == "complete"
        time.sleep(30)
    return False


def _descargar(slug, fecha, dest):
    r = output_kernel(slug)
    files = r.get("files", []) if isinstance(r, dict) else []
    print(f"[orq] outputs: {[f.get('name','?') for f in files]}")
    target = OUT / f"video_largo_{fecha}_kaggle.mp4"
    for f in files:
        if f.get("name", "").endswith(".mp4"):
            url = f.get("url") or f.get("downloadUrl")
            if url:
                import urllib.request
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=300) as resp, open(target, "wb") as out:
                    shutil.copyfileobj(resp, out)
                print(f"[orq] OK {target} ({target.stat().st_size//1024//1024}MB)")
                return target
    print("[orq] No se descargó mp4"); return None




def _limpiar_kaggle(dataset_slug, kernel_slug, borrar_dataset=True):
    """Para el kernel (si sigue vivo) y opcionalmente borra el dataset."""
    print("[cleanup] parando kernel...", flush=True)
    try:
        r = stop_kernel(kernel_slug)
        print(f"[cleanup] stop_kernel: {str(r)[:150]}", flush=True)
    except Exception as e:
        print(f"[cleanup] stop error: {e}", flush=True)
    if borrar_dataset:
        print(f"[cleanup] borrando dataset {dataset_slug}...", flush=True)
        try:
            r = subprocess.run(
                ["kaggle", "datasets", "delete", dataset_slug, "--yes"],
                capture_output=True, text=True, timeout=60)
            print(f"[cleanup] delete exit={r.returncode} {r.stdout.strip()[:100]}", flush=True)
        except Exception as e:
            print(f"[cleanup] delete error: {e}", flush=True)


def main(fecha, dataset_slug=None, borrar_dataset=True):
    global DS_OWNER, DS_SLUG
    if not dataset_slug:
        dataset_slug = f"{DS_OWNER}/{DS_SLUG}"
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="kaggle_render_"))
    print(f"[orq] tmp: {tmp}")
    exito = False
    try:
        assets = _preparar_assets(fecha, tmp / "assets")
        if not _subir_dataset(assets, dataset_slug):
            print("[orq] FALLO subir dataset"); return
        if not _renderizar_kernel(fecha):
            print("[orq] FALLO push_kernel"); return
        if not _esperar_fin(KERNEL_SLUG):
            print("[orq] FALLO o timeout"); return
        print("[orq] esperando subida a GitHub...", flush=True)
        sys.path.insert(0, str(ROOT / "scripts"))
        from descargar_y_borrar_github import main as _dl_git
        _dl_git(prefijo=f"render_{fecha}", destino_dir="output/encuadre", timeout_min=55)
        target = OUT / f"render_{fecha}.mp4"
        if target.exists():
            video = OUT / f"video_largo_{fecha}_kaggle.mp4"
            target.rename(video)
            print(f"[orq] COMPLETADO {video}")
            exito = True
        else:
            print("[orq] SIN VIDEO")
    finally:
        # SIEMPRE: parar kernel y borrar dataset (salvo que falle y quieras debug)
        _limpiar_kaggle(dataset_slug, KERNEL_SLUG, borrar_dataset=borrar_dataset and exito)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-10-29")
