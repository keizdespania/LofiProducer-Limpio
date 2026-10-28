"""Configuracion de subida a YouTube."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Registro de subidas (evita duplicados)
UPLOADS_LOG = DATA_DIR / "uploads.json"

# Defaults de subida
DEFAULT_PRIVACY = "private"      # private | unlisted | public
DEFAULT_CATEGORY = "10"          # 10 = Music
DEFAULT_LANGUAGE = "es"
DEFAULT_MADE_FOR_KIDS = False
DEFAULT_TAGS_FALLBACK = ["lofi", "chillhop", "study music", "relax", "beats"]

# Reintentos
MAX_RETRY = 5
RETRY_BACKOFF = 4

# Hora de publicacion programada (formato "HH:MM", hora local Espana)
# Si es None, se sube sin programar (queda como privado)
PUBLISH_AT_HOUR: str | None = "18:00"

# Dias minimos de espera antes de publicar (por si es muy tarde hoy)
PUBLISH_MIN_DIAS_ESPERA = 1
