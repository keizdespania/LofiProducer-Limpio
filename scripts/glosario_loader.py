"""glosario_loader.py - Lee web/docs/glosario.md y expone el glosario estructurado.
Fuente única de verdad para todos los scripts y agentes.
"""
from pathlib import Path
import re
from functools import lru_cache

GLOSARIO_MD = Path(__file__).resolve().parent.parent / "web" / "docs" / "glosario.md"

@lru_cache(maxsize=1)
def cargar_glosario():
    """Devuelve dict {nombre_normalizado: {nombre, en, categoria, autor, definicion}}."""
    s = GLOSARIO_MD.read_text(encoding="utf-8")
    rows = re.findall(
        r'<div class="glossary-row" data-category="([^"]+)"[^>]*>.*?'
        r'<span class="glossary-term"><strong>([^<]+)</strong>\s*'
        r'<span class="glossary-term-en">/\s*([^<]+)</span>.*?'
        r'<span class="glossary-author">([^<]+)</span>.*?'
        r'<div class="glossary-definition">\s*<div><p>([^<]+)</p>',
        s, re.DOTALL
    )
    out = {}
    for cat, nombre, en, autor, defi in rows:
        out[nombre.strip()] = {
            "nombre": nombre.strip(),
            "en": en.strip(),
            "categoria": cat,
            "autor": autor.strip(),
            "definicion": defi.strip(),
        }
    return out

def buscar(tecnica):
    """Busca por nombre exacto o por coincidencia parcial en ES/EN."""
    g = cargar_glosario()
    if tecnica in g:
        return g[tecnica]
    t = tecnica.lower().strip()
    for k, v in g.items():
        if t == k.lower() or t == v["en"].lower():
            return v
    for k, v in g.items():
        if t in k.lower() or t in v["en"].lower():
            return v
    return None

def definiciones(tecnicas):
    """Devuelve dict {tecnica: {definicion, autor}} para una lista de nombres."""
    out = {}
    for t in tecnicas:
        hit = buscar(t)
        if hit:
            out[hit["nombre"]] = {"definicion": hit["definicion"], "autor": hit["autor"]}
    return out

if __name__ == "__main__":
    g = cargar_glosario()
    print(f"Cargadas {len(g)} técnicas de {GLOSARIO_MD}")
    import json
    print(json.dumps(list(g.items())[:3], ensure_ascii=False, indent=2))
