"""
Cajon 13b - Subida a YouTube con OAuth 2.0 (v2).

Cambios v2:
  - Declara 'containsSyntheticMedia: True' (uso de IA obligatorio desde 2024)
  - Mantiene: programacion, paleta alterna, atribuciones, tracklist
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from config.youtube import (
    UPLOADS_LOG, DEFAULT_PRIVACY, DEFAULT_CATEGORY, DEFAULT_LANGUAGE,
    DEFAULT_MADE_FOR_KIDS, DEFAULT_TAGS_FALLBACK,
    MAX_RETRY, RETRY_BACKOFF,
)
from core.attributions import (
    formatear_tracklist, formatear_atribuciones, formatear_chapters,
)
from core.config import DATA_DIR, OUTPUT_DIR
from core.logger import get_logger
from core.youtube_auth import obtener_youtube


log = get_logger("fases.subida")


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _cargar_log() -> dict:
    if UPLOADS_LOG.exists():
        return json.loads(UPLOADS_LOG.read_text(encoding="utf-8"))
    return {"uploads": [], "ultima_paleta": "oscuro"}


def _guardar_log(data: dict) -> None:
    UPLOADS_LOG.parent.mkdir(parents=True, exist_ok=True)
    UPLOADS_LOG.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                          encoding="utf-8")


def _ya_subido(sha: str) -> dict | None:
    data = _cargar_log()
    for up in data.get("uploads", []):
        if up.get("sha256") == sha:
            return up
    return None


def _registrar_subida(sha: str, video_id: str, url: str, titulo: str,
                     publish_at: str | None = None,
                     paleta_usada: str | None = None) -> None:
    data = _cargar_log()
    data.setdefault("uploads", []).append({
        "sha256": sha, "video_id": video_id, "url": url, "titulo": titulo,
        "subido": datetime.now(timezone.utc).isoformat(),
        "publish_at": publish_at, "paleta": paleta_usada,
    })
    if paleta_usada:
        data["ultima_paleta"] = paleta_usada
    _guardar_log(data)


def _proxima_paleta() -> str:
    data = _cargar_log()
    return "claro" if data.get("ultima_paleta", "oscuro") == "oscuro" else "oscuro"


def _miniatura_para_paleta(paleta: str) -> Path:
    archivos = sorted(OUTPUT_DIR.glob(f"portada_final_horizontal_{paleta}_*.jpg"))
    if archivos:
        return archivos[-1]
    archivos = sorted(OUTPUT_DIR.glob("portada_final_horizontal_*.jpg"))
    if archivos:
        return archivos[-1]
    raise FileNotFoundError("No hay portadas horizontales")


def _ultimo_seo_pack() -> Path | None:
    packs = sorted(DATA_DIR.glob("seo_pack_*.json"))
    return packs[-1] if packs else None


def _cargar_timeline() -> list[dict]:
    p = DATA_DIR / "last_timeline.json"
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return []


def _construir_descripcion(titulo_youtube: str, hashtags: list[str]) -> str:
    timeline = _cargar_timeline()

    from core.attributions import _cargar as _cargar_attr
    attr_data = _cargar_attr()
    attr_by_id = {str(a["track_id"]): a for a in attr_data.get("tracks", [])}

    entries = []
    for t in timeline:
        entry = attr_by_id.get(str(t["track_id"]), {})
        entries.append({
            "track_id": t["track_id"],
            "titulo": t["titulo"],
            "artista": t["artista"],
            "inicio": t["inicio"],
            "duracion_seg": t["duracion_seg"],
            "file_page_url": t.get("file_page_url", ""),
            "url_descarga": t.get("url_descarga", ""),
            "licencia": t.get("licencia", entry.get("licencia", "?")),
            "licencia_url": t.get("licencia_url", entry.get("licencia_url", "")),
            "atribucion_requerida": entry.get("atribucion_requerida", True),
        })

    tracklist_bloque = formatear_tracklist(entries)
    atribuciones_bloque = formatear_atribuciones(entries)

    hashtags_txt = " ".join(hashtags[:15]) if hashtags else "#lofi #chillhop"

    partes = [
        titulo_youtube,
        "",
        "Relax, study or sleep with this lofi mix.",
        "",
        "🔔 Subscribe for more beats.",
        "",
        tracklist_bloque,
    ]
    if atribuciones_bloque:
        partes.append(atribuciones_bloque)

    partes.extend([
        "═══════════════════════════════════",
        "🌐 SÍGUENOS",
        "═══════════════════════════════════",
        "",
        "YouTube: https://www.youtube.com/@keizproductions",
        "Instagram: (próximamente)",
        "TikTok: (próximamente)",
        "Web: (próximamente)",
        "",
        hashtags_txt,
    ])

    return "\n".join(p for p in partes if p is not None)[:5000]


def _metadatos_desde_pack() -> dict:
    pack_path = _ultimo_seo_pack()
    if not pack_path:
        log.warning("Sin seo_pack. Usando metadatos genericos.")
        return {
            "titulo": "Lofi Beats - Relax & Study",
            "descripcion": "Relaxing lofi beats to study and chill.",
            "tags": DEFAULT_TAGS_FALLBACK,
        }

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    titulo = pack.get("titulo_youtube") or (pack.get("titulos") or ["Lofi Beats"])[0]
    hashtags = pack.get("hashtags") or []
    tags = [h.lstrip("#") for h in hashtags][:15] or DEFAULT_TAGS_FALLBACK

    descripcion = _construir_descripcion(titulo, hashtags)

    log.info("Descripcion construida: %d chars", len(descripcion))
    return {"titulo": titulo[:100], "descripcion": descripcion, "tags": tags}


def _calcular_publish_at() -> str | None:
    from config.youtube import PUBLISH_AT_HOUR, PUBLISH_MIN_DIAS_ESPERA
    if not PUBLISH_AT_HOUR:
        return None
    try:
        hora, minuto = map(int, PUBLISH_AT_HOUR.split(":"))
    except Exception:
        return None
    ahora = datetime.now(timezone.utc)
    objetivo = ahora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    objetivo += timedelta(days=PUBLISH_MIN_DIAS_ESPERA - 1)
    return objetivo.isoformat().replace("+00:00", "Z")


def _subir_reanudable(yt, path: Path, body: dict, intento: int = 1):
    media = MediaFileUpload(str(path), chunksize=5 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    log.info("Subiendo %s (intento %d/%d)...", path.name, intento, MAX_RETRY)
    response = None
    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                log.info("  Progreso: %d%%", int(status.progress() * 100))
        except HttpError as e:
            if e.resp.status in (500, 502, 503, 504) and intento < MAX_RETRY:
                espera = RETRY_BACKOFF * (2 ** (intento - 1))
                log.warning("  Error %s. Reintentando en %ds...", e.resp.status, espera)
                time.sleep(espera)
                return _subir_reanudable(yt, path, body, intento + 1)
            raise
        except Exception as e:
            if intento < MAX_RETRY:
                espera = RETRY_BACKOFF * (intento ** 2)
                log.warning("  Error red: %s. Reintentando en %ds...", e, espera)
                time.sleep(espera)
                return _subir_reanudable(yt, path, body, intento + 1)
            raise
    return response


def _subir_miniatura(yt, video_id: str, thumb: Path) -> None:
    if not thumb.exists():
        return
    try:
        yt.thumbnails().set(videoId=video_id,
                           media_body=MediaFileUpload(str(thumb))).execute()
        log.info("Miniatura subida: %s", thumb.name)
    except HttpError as e:
        log.warning("No se pudo subir la miniatura: %s", e)


def subir(video_path: Path | None = None,
          miniatura: Path | None = None,
          privacidad: str | None = None,
          paleta: str | None = None) -> dict:
    if video_path is None:
        candidatos = sorted(OUTPUT_DIR.glob("video_final_*.mp4"))
        if not candidatos:
            raise FileNotFoundError("No hay video_final_*.mp4.")
        video_path = candidatos[-1]

    if not video_path.exists():
        raise FileNotFoundError(f"No existe {video_path}")

    log.info("Video a subir: %s (%.1f MB)",
             video_path.name, video_path.stat().st_size / 1024 / 1024)

    sha = _sha256(video_path)
    dup = _ya_subido(sha)
    if dup:
        log.warning("Este archivo YA fue subido el %s", dup["subido"])
        return dup

    meta = _metadatos_desde_pack()
    privacidad = privacidad or DEFAULT_PRIVACY
    paleta = paleta or _proxima_paleta()
    log.info("Paleta: %s", paleta)

    if miniatura is None:
        miniatura = _miniatura_para_paleta(paleta)
    log.info("Miniatura: %s", miniatura.name)

    publish_at = _calcular_publish_at()
    if publish_at:
        log.info("Programado para: %s", publish_at)

    status_block = {
        "privacyStatus": privacidad,
        "selfDeclaredMadeForKids": DEFAULT_MADE_FOR_KIDS,
        "containsSyntheticMedia": True,  # <-- MARCA DE IA OBLIGATORIA
    }
    if publish_at and privacidad == "private":
        status_block["publishAt"] = publish_at
    elif publish_at:
        log.warning("publishAt ignorado (requiere privacidad=private)")
        publish_at = None

    body = {
        "snippet": {
            "title": meta["titulo"],
            "description": meta["descripcion"],
            "tags": meta["tags"],
            "categoryId": DEFAULT_CATEGORY,
            "defaultLanguage": DEFAULT_LANGUAGE,
        },
        "status": status_block,
    }

    log.info("Titulo         : %s", meta["titulo"])
    log.info("Privacidad     : %s", privacidad)
    log.info("Marca IA       : SI (containsSyntheticMedia)")

    yt = obtener_youtube()
    resp = _subir_reanudable(yt, video_path, body)
    video_id = resp["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"

    log.info("VIDEO SUBIDO OK")
    log.info("  ID  : %s", video_id)
    log.info("  URL : %s", url)

    _subir_miniatura(yt, video_id, miniatura)
    _registrar_subida(sha, video_id, url, meta["titulo"], publish_at, paleta)

    return {
        "video_id": video_id,
        "url": url,
        "titulo": meta["titulo"],
        "privacidad": privacidad,
        "publish_at": publish_at,
        "paleta": paleta,
    }


if __name__ == "__main__":
    log.info("--- Cajon 13b v2: subida a YouTube con marca IA ---")
    resultado = subir()

    print()
    print("=" * 60)
    print(f"[OK] SUBIDA COMPLETADA")
    print(f"     Titulo    : {resultado['titulo']}")
    print(f"     Video ID  : {resultado['video_id']}")
    print(f"     URL       : {resultado['url']}")
    print(f"     Privacidad: {resultado['privacidad']}")
    print(f"     Paleta    : {resultado['paleta']}")
    if resultado.get("publish_at"):
        print(f"     Programado: {resultado['publish_at']}")
    print("=" * 60)
