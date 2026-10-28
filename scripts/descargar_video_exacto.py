"""Descarga el video de Kaggle usando la ruta exacta del log."""
import sys, pathlib, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "videos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def _tokens():
    tokens = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("KAGGLE_API_TOKEN"):
                tokens.append(line.split("=", 1)[1].strip().strip('"').strip("'"))
    return tokens

def descargar(user, kernel, ruta):
    ruta_encoded = urllib.parse.quote(ruta, safe='')
    url = f"https://www.kaggle.com/api/v1/kernels/output/{user}/{kernel}/files/{ruta_encoded}"
    
    for i, token in enumerate(_tokens(), 1):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    data = r.read()
                    if data.startswith(b"PK\x03\x04"):
                        # Es un ZIP, extraer el mp4
                        import io, zipfile
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            for f in z.namelist():
                                if f.endswith('.mp4'):
                                    dest = OUT_DIR / pathlib.Path(f).name
                                    dest.write_bytes(z.read(f))
                                    print(f"✅ Video extraido: {dest} ({dest.stat().st_size // 1024} KB)")
                                    return
                    elif b"ftyp" in data[:100]:
                        # Es un MP4 directo
                        fname = pathlib.Path(ruta).name
                        dest = OUT_DIR / fname
                        dest.write_bytes(data)
                        print(f"✅ Video descargado: {dest} ({dest.stat().st_size // 1024} KB)")
                        return
                    else:
                        print(f"Cuenta {i}: tipo desconocido ({len(data)} bytes)")
        except Exception as e:
            print(f"Cuenta {i} fallo: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python descargar_video_exacto.py 'user' 'kernel' 'ruta/archivo.mp4'")
        sys.exit(1)
    descargar(sys.argv[1], sys.argv[2], sys.argv[3])
