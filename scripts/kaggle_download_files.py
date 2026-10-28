"""Prueba varias rutas para descargar archivos de output de Kaggle."""
import sys, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _get_tokens():
    tokens = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("KAGGLE_API_TOKEN"):
                tokens.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    return tokens

def probar_rutas(slug):
    user, kernel = slug.split("/")
    rutas = [
        f"/kernels/output/files?owner={user}&kernel={kernel}",
        f"/kernels/output/{user}/{kernel}/files",
        f"/kernels/output/{user}/{kernel}",
        f"/kernels/output?userName={user}&kernelSlug={kernel}&fileType=output",
    ]
    token = _get_tokens()[0]
    for ruta in rutas:
        url = f"https://www.kaggle.com/api/v1{ruta}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                print(f"{ruta[:60]:60s} -> HTTP {r.status}, {len(data)} bytes, header: {data[:20]}")
                if data.startswith(b"PK\x03\x04"):
                    print(f"  ✅ ¡ZIP encontrado! Guardando...")
                    dest = OUT_DIR / "wangp_output.zip"
                    dest.write_bytes(data)
                    return True
        except Exception as e:
            print(f"{ruta[:60]:60s} -> ERROR: {e}")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python kaggle_download_files.py 'usuario/slug'")
        sys.exit(1)
    probar_rutas(sys.argv[1])
