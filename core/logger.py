"""
Cajon 03 - Logger centralizado.

Uso desde cualquier cajon:

    from core.logger import get_logger
    log = get_logger(__name__)
    log.info("Arrancando fase 1")
    log.error("Fallo en la peticion", exc_info=True)

Salida:
  - Terminal: con colores ANSI (nivel coloreado, resto normal).
  - Archivo : data/logs/lofiproducer.log con rotacion a 2 MB x 5 backups.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from core.config import PROJECT_ROOT


# -------------------------------------------------------------
# 1. Rutas y constantes
# -------------------------------------------------------------
LOG_DIR: Path = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE: Path = LOG_DIR / "lofiproducer.log"

LOG_FORMAT_FILE = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
LOG_FORMAT_TERM = "%(asctime)s | %(levelname)-8s | %(name)-24s | %(message)s"
DATE_FORMAT     = "%Y-%m-%d %H:%M:%S"


# -------------------------------------------------------------
# 2. Codigos ANSI (colores de terminal)
# -------------------------------------------------------------
class Color:
    RESET   = "\033[0m"
    GREY    = "\033[90m"
    CYAN    = "\033[36m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    RED     = "\033[31m"
    BOLD_RED = "\033[1;31m"


_LEVEL_COLORS = {
    logging.DEBUG:    Color.GREY,
    logging.INFO:     Color.CYAN,
    logging.WARNING:  Color.YELLOW,
    logging.ERROR:    Color.RED,
    logging.CRITICAL: Color.BOLD_RED,
}


# -------------------------------------------------------------
# 3. Formatter con color para la terminal
# -------------------------------------------------------------
class ColorFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, Color.RESET)
        # Reemplazamos solo el nivel por su version coloreada
        record.levelname = f"{color}{record.levelname:<8}{Color.RESET}"
        return super().format(record)


# -------------------------------------------------------------
# 4. Configuracion global (idempotente)
# -------------------------------------------------------------
_CONFIGURED = False


def _configure_root() -> None:
    """Configura el logger raiz solo una vez."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    # --- Handler 1: terminal con color (solo INFO+) ---
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(ColorFormatter(LOG_FORMAT_TERM, DATE_FORMAT))
    root.addHandler(console)

    # --- Handler 2: archivo rotativo (DEBUG+, todo) ---
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2 * 1024 * 1024,   # 2 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT_FILE, DATE_FORMAT))
    root.addHandler(file_handler)

    # --- Silenciar ruido de librerias externas ---
    for noisy in ("urllib3", "requests", "charset_normalizer", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


# -------------------------------------------------------------
# 5. API publica
# -------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger listo para usar con el nombre dado."""
    _configure_root()
    return logging.getLogger(name)


# -------------------------------------------------------------
# 6. Auto-test
# -------------------------------------------------------------
if __name__ == "__main__":
    log = get_logger("core.logger.test")

    log.debug("Esto es DEBUG (solo va al archivo, no a terminal)")
    log.info("Esto es INFO (visible en terminal y archivo)")
    log.warning("Esto es WARNING (amarillo)")
    log.error("Esto es ERROR (rojo)")
    log.critical("Esto es CRITICAL (rojo intenso)")

    try:
        1 / 0
    except ZeroDivisionError:
        log.error("Ejemplo con traza:", exc_info=True)

    print()
    print(f"[OK] Log escrito en: {LOG_FILE}")
    print(f"[OK] Tamano actual  : {LOG_FILE.stat().st_size} bytes")
