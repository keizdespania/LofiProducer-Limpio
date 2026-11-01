"""subir_imagenes_github.py - Devuelve URLs públicas de imágenes ya en el repo."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
GITHUB_USER = "keizdespania"
GITHUB_REPO = "LofiProducer-Limpio"
GITHUB_BRANCH = "main"
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/web/media/imagenes"

def url_imagen(nombre):
    """Devuelve la URL pública de una imagen del repo."""
    return f"{BASE_URL}/{nombre}"

def escenas_disponibles():
    """Devuelve lista de escenas disponibles."""
    imgs = sorted((ROOT / "web" / "media" / "imagenes").glob("escena_*.png"))
    return [img.name for img in imgs]

def obtener_hero_y_secundarias():
    """Devuelve 1 hero + 4 secundarias para los 5 posts."""
    escenas = escenas_disponibles()
    if len(escenas) < 5:
        return None
    return {
        "hero": escenas[0],
        "posts": [
            escenas[0],  # post 1 (principal)
            escenas[3],  # post 2
            escenas[7],  # post 3
            escenas[11], # post 4
            escenas[15], # post 5
        ]
    }

if __name__ == "__main__":
    escenas = escenas_disponibles()
    print(f"Escenas disponibles: {len(escenas)}")
    for e in escenas[:5]:
        print(f"  {url_imagen(e)}")
