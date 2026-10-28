"""Cajon 122 - Cliente ligero de Kaggle para Termux (Bearer Auth)."""
import json
import urllib.request
import urllib.error
from pathlib import Path

API_URL = "https://www.kaggle.com/api/v1"
TOKEN_FILE = Path.home() / ".kaggle" / "access_token"

def _leer_token() -> str:
    """Lee el token desde .env, con fallback a ~/.kaggle/access_token."""
    import os
    tok = os.environ.get("KAGGLE_API_TOKEN", "").strip()
    if tok:
        return tok
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("KAGGLE_API_TOKEN="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text().strip()
    raise RuntimeError("Falta KAGGLE_API_TOKEN en .env o ~/.kaggle/access_token")

def listar_competiciones() -> None:
    token = _leer_token()
    req = urllib.request.Request(f"{API_URL}/competitions/list")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            print(f"✅ Autenticación OK. Competiciones: {len(data)}")
            for comp in data[:3]:
                print(f" - {comp.get('title')}")
    except urllib.error.HTTPError as e:
        print(f"❌ Error HTTP {e.code}: {e.reason}")
    except Exception as e:
        print(f"❌ Error: {e}")


def crear_kernel(slug: str, codigo_python: str, gpu: bool = True, datasets: list[str] | None = None) -> None:
    """Crea un notebook (Kernel) en Kaggle con el código dado."""
    token = _leer_token()
    
    # Estructura que espera la API de Kaggle
    payload = {
        "slug": slug,
        "newTitle": slug.split("/")[-1],
        "text": codigo_python,
        "language": "python",
        "kernelType": "notebook",
        "isPrivate": True,
        "enableGpu": gpu,
        "enableInternet": True,
        "categoryIds": [],
        "datasetDataSources": datasets or [],
        "competitionDataSources": [],
        "kernelDataSources": [],
        "modelDataSources": []
    }
    
    url = f"{API_URL}/kernels/push"
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            print(f"✅ Kernel creado: {data.get('url', 'URL no devuelta')}")
    except urllib.error.HTTPError as e:
        print(f"❌ Error HTTP {e.code}: {e.reason}")
        print(e.read().decode("utf-8")[:500])
    except Exception as e:
        print(f"❌ Error: {e}")



def activar_kernel(user_name: str, kernel_slug: str) -> bool:
    """
    Activa (lanza) un kernel existente en Kaggle.
    Devuelve True si se ha lanzado con éxito.
    """
    token = _leer_token()
    url = "https://www.kaggle.com/api/v1/kernels/push"
    
    payload = {
        "slug": f"{user_name}/{kernel_slug}",
        "newTitle": kernel_slug,
        "text": "",
        "language": "python",
        "kernelType": "notebook",
        "isPrivate": True,
        "enableGpu": True,
        "enableInternet": True,
        "categoryIds": [],
        "datasetDataSources": [],
        "competitionDataSources": [],
        "kernelDataSources": [],
        "modelDataSources": []
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            print(f"✅ Kernel {kernel_slug} activado.")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Error activando {e.code}: {e.read().decode()[:200]}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Código original de test
    pass
