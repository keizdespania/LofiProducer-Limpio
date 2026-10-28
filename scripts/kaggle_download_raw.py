"""Descarga el output crudo de Kaggle y detecta que es."""
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

def descargar(slug):
    user, kernel = slug.split("/")
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug={kernel}"
    for i, token in enumerate(_get_tokens(), 1):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    data = r.read()
                    raw_path = OUT_DIR / "wangp_output_raw.bin"
                    raw_path.write_bytes(data)
                    print(f"OK: {len(data)} bytes guardados en {raw_path}")
                    # Detectar tipo por los primeros bytes
                    header = data[:20]
                    print(f"Header: {header}")
                    if header.startswith(b"PK\x03\x04"):
                        print("Es un ZIP.")
                    elif header.startswith(b"\x00\x00\x00") or b"ftyp" in header:
                        print("Parece un MP4.")
                    else:
                        print("Tipo desconocido.")
                    return
        except Exception as e:
            print(f"Cuenta {i} fallo: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python kaggle_download_raw.py 'usuario/slug'")
        sys.exit(1)
    descargar(sys.argv[1])
