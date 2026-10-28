"""
Cajon 02 - Configuracion centralizada.

Regla: cada secreto vive en SU PROPIA constante.
Nunca se concatena a mano con URLs.
"""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


def _load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Crea el .env antes de arrancar el proyecto."
        )
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if value.startswith("~"):
            value = str(Path(value).expanduser())
        os.environ.setdefault(key, value)


_load_env(ENV_FILE)


def _get(key: str, default: str | None = None) -> str:
    val = os.environ.get(key, default)
    if val is None:
        raise KeyError(f"Falta variable obligatoria en .env: {key}")
    return val.strip()


# -------------------------------------------------------------
# 2. Secretos y ajustes
# -------------------------------------------------------------
GOOGLE_API_KEY: str     = _get("GOOGLE_API_KEY")
OMNIROUTE_BASE_URL: str = _get("OMNIROUTE_BASE_URL").rstrip("/")
OMNIROUTE_API_KEY: str  = _get("OMNIROUTE_API_KEY")
OMNIROUTE_MANAGE_KEY: str = _get("OMNIROUTE_MANAGE_KEY", "")
MODEL_NAME: str         = _get("MODEL_NAME", "auto/gemini")
YOUTUBE_API_KEY: str    = _get("YOUTUBE_API_KEY")

# Proveedores LLM multi-modelo
DEEPSEEK_API_KEY: str   = _get("DEEPSEEK_API_KEY", "")
OPENROUTER_API_KEY: str = _get("OPENROUTER_API_KEY", "")
NVIDIA_API_KEY: str     = _get("NVIDIA_API_KEY", "")

# Cloudflare Workers AI (imagenes)
CLOUDFLARE_API_TOKEN: str  = _get("CLOUDFLARE_API_TOKEN")
CLOUDFLARE_ACCOUNT_ID: str = _get("CLOUDFLARE_ACCOUNT_ID")

DATA_DIR: Path   = Path(_get("DATA_DIR"))
OUTPUT_DIR: Path = Path(_get("OUTPUT_DIR"))
FONTS_DIR: Path  = PROJECT_ROOT / "assets" / "fonts"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------------
# 3. Validaciones defensivas
# -------------------------------------------------------------
def _validate() -> None:
    if not GOOGLE_API_KEY or " " in GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY vacia o con espacios.")

    if not OMNIROUTE_BASE_URL.startswith(("http://", "https://")):
        raise ValueError(f"OMNIROUTE_BASE_URL invalida: {OMNIROUTE_BASE_URL}")

    if GOOGLE_API_KEY in OMNIROUTE_BASE_URL:
        raise ValueError("La API key se ha colado dentro de la URL.")
    if OMNIROUTE_API_KEY in OMNIROUTE_BASE_URL:
        raise ValueError("OMNIROUTE_API_KEY se ha colado dentro de la URL.")


_validate()


# -------------------------------------------------------------
# 4. Endpoints finales
# -------------------------------------------------------------
GOOGLE_OPENAI_URL: str = (
    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
)

OMNIROUTE_CHAT_URL: str = f"{OMNIROUTE_BASE_URL}/v1/chat/completions"

YOUTUBE_SEARCH_URL: str = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL: str = "https://www.googleapis.com/youtube/v3/videos"

# Cloudflare Workers AI
CLOUDFLARE_IMAGE_URL: str = (
    f"https://api.cloudflare.com/client/v4/accounts/"
    f"{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
)


# -------------------------------------------------------------
# 5. Estrategia multi-combo con fallback
# -------------------------------------------------------------
# Los combos "Planner razonar" y "Executor ejecutar" viven en OmniRoute
# y rotan internamente entre proveedores.
OMNIROUTE_MODELS: list[str] = [
    "mi-groq/qwen/qwen3.8-27b",
    "mi-groq/openai/gpt-oss-120b",
    "mi-groq/openai/gpt-oss-20b",
]

# Modelos de Google directo (fallback si OmniRoute cae)
GOOGLE_MODELS: list[str] = [
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
]


# -------------------------------------------------------------
# 6. Auto-test
# -------------------------------------------------------------
if __name__ == "__main__":
    print("[OK] Configuracion cargada correctamente")
    print(f"   Google key       : {GOOGLE_API_KEY[:8]}...{GOOGLE_API_KEY[-4:]} "
          f"(len={len(GOOGLE_API_KEY)})")
    print(f"   OmniRoute key    : {OMNIROUTE_API_KEY[:8]}... "
          f"(len={len(OMNIROUTE_API_KEY)})")
    print(f"   OmniRoute manage : {OMNIROUTE_MANAGE_KEY[:8]}... "
          f"(len={len(OMNIROUTE_MANAGE_KEY)})")
    print(f"   Modelo           : {MODEL_NAME}")
    print(f"   DeepSeek key     : {'OK' if DEEPSEEK_API_KEY else 'NO'}")
    print(f"   OpenRouter key   : {'OK' if OPENROUTER_API_KEY else 'NO'}")
    print(f"   NVIDIA key       : {'OK' if NVIDIA_API_KEY else 'NO'}")
    print(f"   Cloudflare token : {CLOUDFLARE_API_TOKEN[:8]}... "
          f"(len={len(CLOUDFLARE_API_TOKEN)})")
    print(f"   Cloudflare acc   : {CLOUDFLARE_ACCOUNT_ID[:8]}... "
          f"(len={len(CLOUDFLARE_ACCOUNT_ID)})")
    print(f"   Google URL       : {GOOGLE_OPENAI_URL}")
    print(f"   OmniRoute URL    : {OMNIROUTE_CHAT_URL}")
    print(f"   Cloudflare URL   : {CLOUDFLARE_IMAGE_URL[:80]}...")
    print(f"   DATA_DIR         : {DATA_DIR}")
    print(f"   OUTPUT_DIR       : {OUTPUT_DIR}")
    print(f"   FONTS_DIR        : {FONTS_DIR}")
    print(f"   OMNIROUTE_MODELS : {OMNIROUTE_MODELS}")
