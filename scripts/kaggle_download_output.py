"""Descarga el output completo de un kernel y extrae los archivos."""
import sys, pathlib, urllib.request, urllib.parse, zipfile, io

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

def descargar_output(slug):
    partes = slug.split("/")
    if len(partes) != 2:
        print("Slug invalido. Usa 'usuario/nombre-kernel'")
        return
    user, kernel = partes
    
    # Endpoint correcto segun la doc: /kernels/output con query params
    url = f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug={kernel}"
    
    for i, token in enumerate(_get_tokens(), 1):
        req = urllib.request.Request(url)
        req.add_header("Authorization", "Bearer " + token)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if r.status == 200:
                    data = r.read()
                    print(f"✅ Output descargado (cuenta {i}): {len(data)} bytes")
                    # Es un ZIP, extraer
                    try:
                        with zipfile.ZipFile(io.BytesIO(data)) as z:
                            # Buscar archivos .mp4
                            mp4_files = [n for n in z.namelist() if n.endswith('.mp4')]
                            if not mp4_files:
                                print("❌ No hay archivos .mp4 en el output.")
                                print("Archivos encontrados:", z.namelist()[:20])
                                return
                            for mp4 in mp4_files:
                                # Extraer solo el nombre del archivo, sin carpetas
                                fname = pathlib.Path(mp4).name
                                dest = OUT_DIR / fname
                                with open(dest, 'wb') as f:
                                    f.write(z.read(mp4))
                                print(f"✅ Video extraido: {dest} ({dest.stat().st_size // 1024} KB)")
                            return
                    except zipfile.BadZipFile:
                        print("❌ El output no es un ZIP valido.")
                        return
        except Exception as e:
            print(f"Cuenta {i} fallo: {e}")
    print("❌ No se pudo descargar el output.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python kaggle_download_output.py 'usuario/nombre-kernel'")
        sys.exit(1)
    descargar_output(sys.argv[1])
