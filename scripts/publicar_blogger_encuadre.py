"""publicar_blogger_encuadre.py - Publica el post corto en Blogger."""
import sys, pathlib, json, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _leer_env(k):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39))
    return None

def publicar(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    p = ROOT / "output" / "encuadre" / f"post_corto_{fecha}.html"
    if not p.exists():
        print(f"[blogger] No existe {p}")
        return None
    html = p.read_text(encoding="utf-8")
    titulo = f"El Encuadre — Análisis de medios {fecha}"
    try:
        from publicar_blogger import publicar as pub
        blog_id = _leer_env("EL_ENCUADRE_BLOG_ID")
        r = pub(titulo, html, blog_id=blog_id)
        print(f"[blogger] {r}")
        return r
    except Exception as e:
        print(f"[blogger] ERROR: {e}")
        return f"ERROR: {e}"

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    print(publicar(fecha))