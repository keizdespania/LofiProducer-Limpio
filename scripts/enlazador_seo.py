"""enlazador_seo.py - Añade enlaces a posts anteriores para SEO."""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "web" / "docs" / "posts"

def enlazar(fecha_actual):
    posts_hoy = list(POSTS_DIR.glob(f"*{fecha_actual}*.md"))
    posts_antiguos = [p for p in POSTS_DIR.glob("*.md") if fecha_actual not in p.name]
    
    if not posts_antiguos: return
    enlaces_html = "<hr><h3>Tambien te puede interesar:</h3><ul>"
    for p in posts_antiguos[-3:]:
        titulo = p.stem.replace("-", " ").title()
        enlaces_html += f'<li><a href="/posts/{p.stem}/">{titulo}</a></li>'
    enlaces_html += "</ul>"
    
    for post in posts_hoy:
        contenido = post.read_text()
        if "Tambien te puede interesar" not in contenido:
            post.write_text(contenido + "\n\n" + enlaces_html)
            print(f"Enlaces añadidos a {post.name}")

if __name__ == "__main__":
    enlazar(sys.argv[1] if len(sys.argv) > 1 else "")
