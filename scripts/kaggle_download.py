"""Descarga los archivos de salida de un kernel de Kaggle."""
import sys, os, pathlib, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "kaggle_downloads"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _tokens():
    tokens = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#") and "KAGGLE_API_TOKEN" in line:
                tokens.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    at = pathlib.Path.home() / ".kaggle" / "access_token"
    if at.exists() and at.read_text().strip() not in tokens:
        tokens.append(at.read_text().strip())
    return tokens

def descargar(slug):
    for i, token in enumerate(_tokens(), 1):
        url = f"https://www.kaggle.com/api/v1/kernels/output/{slug}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    zip_path = OUT_DIR / f"{slug.replace('/', '_')}.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(r.read())
                    print(f"OK: Descargado con cuenta {i} -> {zip_path}")
                    with zipfile.ZipFile(zip_path, 'r') as z:
                        z.extractall(OUT_DIR / slug.replace('/', '_'))
                    print(f"OK: Extraido en {OUT_DIR / slug.replace('/', '_')}")
                    return True
        except Exception as e:
            print(f"Cuenta {i} fallo: {e}")
    print("ERROR: No se pudo descargar.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python kaggle_download.py usuario/slug")
        sys.exit(1)
    descargar(sys.argv[1])
