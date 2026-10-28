"""
Cajon 15 - Gestor de canales multi-canal.

Carga config/channels.json y permite:
  - Listar todos los canales
  - Seleccionar canal activo (modifica DATA_DIR, OUTPUT_DIR dinamicamente)
  - Devolver rutas por canal

Uso tipico:
    from core.channel_manager import set_active_channel, get_active_channel
    set_active_channel("keiz_productions")
    ch = get_active_channel()
    print(ch["nombre"], ch["data_dir"])
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.logger import get_logger


log = get_logger("core.channel_manager")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHANNELS_FILE = PROJECT_ROOT / "config" / "channels.json"


# Estado global del canal activo
_ACTIVE_CHANNEL: dict[str, Any] | None = None


# -------------------------------------------------------------
# Carga y validacion
# -------------------------------------------------------------
def _cargar_config() -> dict[str, Any]:
    if not CHANNELS_FILE.exists():
        raise FileNotFoundError(
            f"No existe {CHANNELS_FILE}. Crea config/channels.json primero."
        )
    try:
        data = json.loads(CHANNELS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"channels.json invalido: {exc}"
        ) from exc

    if "channels" not in data or not isinstance(data["channels"], list):
        raise RuntimeError("channels.json debe tener una clave 'channels' (lista).")

    return data


def listar_canales(solo_habilitados: bool = True) -> list[dict[str, Any]]:
    """Devuelve la lista de canales."""
    data = _cargar_config()
    canales = data["channels"]
    if solo_habilitados:
        canales = [c for c in canales if c.get("enabled", True)]
    return canales


def obtener_canal(canal_id: str) -> dict[str, Any]:
    """Devuelve la config de un canal por ID. Error si no existe."""
    data = _cargar_config()
    for c in data["channels"]:
        if c.get("id") == canal_id:
            return c
    ids_disponibles = [c.get("id") for c in data["channels"]]
    raise ValueError(
        f"Canal '{canal_id}' no encontrado. "
        f"Disponibles: {ids_disponibles}"
    )


# -------------------------------------------------------------
# Rutas por canal
# -------------------------------------------------------------
def _construir_rutas(canal: dict[str, Any]) -> dict[str, Any]:
    """Anade rutas derivadas a la config del canal."""
    cid = canal["id"]
    canal = dict(canal)  # copia para no mutar el original
    canal["data_dir"] = PROJECT_ROOT / "data" / cid
    canal["output_dir"] = PROJECT_ROOT / "output" / cid
    canal["secrets_dir"] = PROJECT_ROOT / "secrets" / cid
    return canal


def _crear_directorios(canal: dict[str, Any]) -> None:
    for key in ("data_dir", "output_dir", "secrets_dir"):
        canal[key].mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------
# Canal activo (modifica core.config dinamicamente)
# -------------------------------------------------------------
def set_active_channel(canal_id: str | None = None) -> dict[str, Any]:
    """
    Establece el canal activo. Si canal_id es None, usa el primer canal
    habilitado de channels.json.

    Modifica core.config.DATA_DIR y core.config.OUTPUT_DIR.
    """
    global _ACTIVE_CHANNEL

    # 1. Elegir canal
    if canal_id is None:
        habilitados = listar_canales(solo_habilitados=True)
        if not habilitados:
            raise RuntimeError("No hay canales habilitados en channels.json.")
        canal = habilitados[0]
        log.info("Sin --canal, usando el primero habilitado: %s", canal["id"])
    else:
        canal = obtener_canal(canal_id)

    if not canal.get("enabled", True):
        raise RuntimeError(
            f"El canal '{canal['id']}' esta deshabilitado en channels.json."
        )

    # 2. Construir rutas y crear carpetas
    canal = _construir_rutas(canal)
    _crear_directorios(canal)

    # 3. Actualizar core.config dinamicamente
    import core.config as cfg
    cfg.DATA_DIR = canal["data_dir"]
    cfg.OUTPUT_DIR = canal["output_dir"]

    # 4. Guardar como activo
    _ACTIVE_CHANNEL = canal
    log.info(
        "Canal activo: %s (%s) — duracion=%s, paleta=%s",
        canal["nombre"], canal["id"],
        canal.get("duracion_default", "?"),
        canal.get("paleta_default", "?"),
    )
    return canal


def get_active_channel() -> dict[str, Any]:
    """Devuelve el canal activo. Error si no se ha llamado a set_active_channel."""
    if _ACTIVE_CHANNEL is None:
        raise RuntimeError(
            "No hay canal activo. Llama primero a set_active_channel()."
        )
    return _ACTIVE_CHANNEL


# -------------------------------------------------------------
# CLI / auto-test
# -------------------------------------------------------------
if __name__ == "__main__":
    log.info("--- Test channel_manager ---")

    print("\nCanales habilitados:")
    for c in listar_canales():
        marca = "*" if c.get("enabled") else " "
        print(f"  [{marca}] {c['id']:20} {c['nombre']}")

    print("\nActivando el primer canal habilitado...")
    canal = set_active_channel()

    print()
    print("=" * 60)
    print(f"Canal activo : {canal['nombre']}")
    print(f"ID           : {canal['id']}")
    print(f"Nicho        : {canal['nicho']}")
    print(f"DATA_DIR     : {canal['data_dir']}")
    print(f"OUTPUT_DIR   : {canal['output_dir']}")
    print(f"SECRETS_DIR  : {canal['secrets_dir']}")
    print("=" * 60)
