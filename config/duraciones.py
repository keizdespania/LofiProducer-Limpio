"""
Configuracion de tipos de duracion.

Cada tipo define:
  - duracion segundos
  - contador_hasta: segundos donde se muestra el contador
    (None = contador durante toda la duracion)
  - usa_hhmmss: usar formato HH:MM:SS en lugar de MM:SS
"""

from __future__ import annotations

DURACIONES: dict[str, int] = {
    "test":     300,      # 5 min
    "estandar": 1800,     # 30 min
    "largo":    3600,     # 1 h
    "sleep":    14400,    # 4 h
    "deep":     28800,    # 8 h
}

CONTADOR_HASTA: dict[str, int | None] = {
    "test":     None,
    "estandar": None,
    "largo":    None,
    "sleep":    1800,     # solo primeros 30 min
    "deep":     1800,     # solo primeros 30 min
}


def get_duracion(tipo: str) -> int:
    if tipo not in DURACIONES:
        raise ValueError(
            f"Tipo desconocido: '{tipo}'. "
            f"Disponibles: {list(DURACIONES.keys())}"
        )
    return DURACIONES[tipo]


def get_contador_hasta(tipo: str) -> int | None:
    return CONTADOR_HASTA.get(tipo)


def usa_hhmmss(tipo: str) -> bool:
    """True si la duracion requiere formato HH:MM:SS."""
    return get_duracion(tipo) > 3600


def es_tipo_largo(tipo: str) -> bool:
    """True si la duracion supera 1 hora."""
    return get_duracion(tipo) > 3600


def listar_tipos() -> list[tuple[str, int, str]]:
    """Devuelve [(tipo, segundos, descripcion)] para mostrar en CLI."""
    descripciones = {
        "test": "5 min",
        "estandar": "30 min",
        "largo": "1 hora",
        "sleep": "4 horas",
        "deep": "8 horas",
    }
    return [
        (t, DURACIONES[t], descripciones[t])
        for t in DURACIONES
    ]


if __name__ == "__main__":
    print("Tipos de duracion disponibles:")
    print()
    for t, seg, desc in listar_tipos():
        cont = CONTADOR_HASTA[t]
        if cont is None:
            cont_txt = "completo"
        else:
            cont_txt = f"{cont}s ({cont//60} min)"
        print(f"  {t:10} {desc:10} ({seg}s)  contador: {cont_txt}")
