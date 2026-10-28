"""
Cajon 13a - OAuth 2.0 con YouTube Data API v3 (multi-canal).

Rutas de credenciales:
  1. secrets/<canal>/client_secret.json  (prioridad si hay canal activo)
  2. secrets/client_secret.json           (fallback global)

Mismo patron para token.json.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse, parse_qs

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.logger import get_logger


log = get_logger("core.youtube_auth")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]


def _rutas_credenciales() -> tuple[Path, Path]:
    """
    Devuelve (client_secret_path, token_path).
    Prioriza secrets/<canal>/ si hay canal activo.
    """
    # 1. Intentar canal activo
    try:
        from core.channel_manager import get_active_channel
        canal = get_active_channel()
        secrets_dir = canal["secrets_dir"]
        cs = secrets_dir / "client_secret.json"
        tk = secrets_dir / "token.json"
        if cs.exists():
            log.info("Usando credenciales del canal: %s", secrets_dir.name)
            return cs, tk
    except Exception:
        pass

    # 2. Fallback global
    secrets_dir = PROJECT_ROOT / "secrets"
    cs = secrets_dir / "client_secret.json"
    tk = secrets_dir / "token.json"
    log.info("Usando credenciales globales: %s", secrets_dir)
    return cs, tk


def _flow() -> InstalledAppFlow:
    client_secret, _ = _rutas_credenciales()
    if not client_secret.exists():
        raise FileNotFoundError(
            f"No existe {client_secret}. "
            f"Descarga el JSON OAuth de Google Cloud y colocalo ahi."
        )
    return InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)


def _guardar_token(creds: Credentials) -> None:
    _, token_file = _rutas_credenciales()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    token_file.chmod(0o600)
    log.info("Token guardado en %s", token_file)


def _cargar_token() -> Credentials | None:
    _, token_file = _rutas_credenciales()
    if not token_file.exists():
        return None
    try:
        return Credentials.from_authorized_user_file(str(token_file), SCOPES)
    except Exception as exc:
        log.warning("Token existente invalido: %s", exc)
        return None


def autorizar_interactivo() -> Credentials:
    flow = _flow()
    flow.redirect_uri = "http://localhost"

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    print()
    print("=" * 70)
    print("PASO 1: Abre esta URL en el navegador del movil:")
    print("=" * 70)
    print()
    print(auth_url)
    print()
    print("=" * 70)
    print("PASO 2: Autoriza con la cuenta del canal.")
    print("PASO 3: El navegador redirigira a una pagina que no cargara.")
    print("PASO 4: Copia la URL COMPLETA de la barra de direcciones")
    print("        (empieza por http://localhost/?code=...)")
    print("        y pegala aqui abajo.")
    print("=" * 70)
    print()

    redir = input("Pega la URL de redireccion completa: ").strip()

    if "code=" not in redir:
        raise RuntimeError("La URL no contiene 'code='. Vuelve a intentarlo.")

    qs = parse_qs(urlparse(redir).query)
    code = qs.get("code", [None])[0]
    if not code:
        raise RuntimeError("No se encontro 'code' en la URL.")

    log.info("Canjeando codigo por token...")
    flow.fetch_token(code=code)
    creds = flow.credentials
    _guardar_token(creds)
    log.info("Autorizacion completada.")
    return creds


def obtener_credenciales() -> Credentials:
    creds = _cargar_token()

    if creds and creds.valid:
        log.info("Token valido reutilizado.")
        return creds

    if creds and creds.expired and creds.refresh_token:
        log.info("Token expirado. Refrescando...")
        creds.refresh(Request())
        _guardar_token(creds)
        return creds

    log.info("Sin token valido. Iniciando autorizacion interactiva.")
    return autorizar_interactivo()


def obtener_youtube():
    creds = obtener_credenciales()
    return build("youtube", "v3", credentials=creds)


if __name__ == "__main__":
    log.info("--- Test autorizacion YouTube ---")
    yt = obtener_youtube()
    log.info("Cliente YouTube OK.")

    resp = yt.channels().list(part="snippet,statistics", mine=True).execute()

    if not resp.get("items"):
        print("[!] No se encontro ningun canal asociado.")
    else:
        ch = resp["items"][0]
        print()
        print("=" * 60)
        print(f"Canal        : {ch['snippet']['title']}")
        print(f"Subscriptores: {ch['statistics'].get('subscriberCount', '?')}")
        print(f"Videos       : {ch['statistics'].get('videoCount', '?')}")
        print("=" * 60)
