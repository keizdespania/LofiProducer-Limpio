"""Cajon 110.A - Busqueda web via webless (Termux-friendly, sin Rust)."""
from __future__ import annotations
from webless import search_sync
from core.logger import get_logger

log = get_logger("brain.web_search")


def buscar(query: str, max_results: int = 5) -> str:
    """Busca en la web y devuelve un resumen en texto para el LLM."""
    try:
        result = search_sync(query, limit=max_results)
        if not result.ok:
            return f"Sin resultados para '{query}'. Fallos: {result.failed}"
        lineas = [f"Resultados para '{query}':"]
        for i, hit in enumerate(result.hits[:max_results], 1):
            lineas.append(f"{i}. {hit.title}")
            lineas.append(f"   {hit.snippet[:200]}")
            lineas.append(f"   {hit.url}")
        return "\n".join(lineas)
    except Exception as e:
        log.warning("Error en busqueda web: %s", e)
        return f"Error de busqueda: {e}"


if __name__ == "__main__":
    print(buscar("zapatillas Nike mas vendidas 2026"))
