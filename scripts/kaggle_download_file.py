"""Descarga un archivo de output de Kaggle a Termux."""
import sys, pathlib, urllib.request, urllib.parse

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

def descargar(slug, file_path):
    encoded_path = urllib.parse.quote(file_path, safe='/')
    url = f"https://www.kaggle.com/api/v1/kernels/output/{slug}/files/{encoded_path}"
    
    for i, token in enumerate(_get_tokens(), 1):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    fname = pathlib.Path(file_path).name
                    dest = OUT_DIR / fname
                    with open(dest, 'wb') as f:
                        f.write(r.read())
                    print(f"✅ Descargado (cuenta {i}): {dest} ({dest.stat().st_size // 1024} KB)")
                    return True
        except Exception as e:
            print(f"Cuenta {i} falló: {e}")
    print("❌ No se pudo descargar el archivo.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python kaggle_download_file.py 'usuario/slug' 'ruta/al/archivo.mp4'")
        sys.exit(1)
    descargar(sys.argv[1], sys.argv[2])
