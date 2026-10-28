"""
Cajon 18 - Base de datos de atribuciones musicales.

Estructura por canal:
    data/<canal>/attributions.json

Contenido:
    {
      "tracks": [
        {
          "track_id": "...",
          "titulo": "...",
          "artista": "...",
          "url_descarga": "...",
          "file_page_url": "...",
          "licencia": "Attribution",
          "licencia_url": "https://creativecommons.org/licenses/by/3.0/",
          "fuente": "ccmixter",
          "atribucion_requerida": true,
          "usado_en": "2026-10-16T..."
        }
      ]
    }

Uso:
    from core.attributions import registrar_atribucion, obtener_por_ids
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from core.logger import get_logger


log = get_logger("core.attributions")


def _attributions_path() -> Path:
    from core.config import DATA_DIR
    return DATA_DIR / "attributions.json"


def _cargar() -> dict:
    p = _attributions_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log.warning("attributions.json corrupto, reiniciando")
    return {"tracks": []}


def _guardar(data: dict) -> None:
    p = _attributions_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _requiere_atribucion(licencia: str, licencia_url: str) -> bool:
    """CC0 y CC-BY-NC (nunca usadas) no requieren, CC-BY si."""
    l = (licencia or "").lower()
    u = (licencia_url or "").lower()
    if "cc0" in l or "cc0" in u or "publicdomain" in u:
        return False
    if "by" in l or "attribution" in l:
        return True
    if "/by" in u:
        return True
    return False


def registrar_atribucion(track: dict) -> None:
    """Registra un track en attributions.json si no estaba ya."""
    data = _cargar()
    tid = str(track.get("track_id"))
    existentes = {str(t.get("track_id")) for t in data["tracks"]}
    if tid in existentes:
        return

    entry = {
        "track_id": track.get("track_id"),
        "titulo": track.get("titulo", "?"),
        "artista": track.get("artista", "?"),
        "url_descarga": track.get("url_descarga", ""),
        "file_page_url": track.get("file_page_url", ""),
        "licencia": track.get("licencia", "?"),
        "licencia_url": track.get("licencia_url", ""),
        "fuente": track.get("fuente", "?"),
        "atribucion_requerida": _requiere_atribucion(
            track.get("licencia", ""), track.get("licencia_url", "")
        ),
        "usado_en": datetime.now(timezone.utc).isoformat(),
    }
    data["tracks"].append(entry)
    _guardar(data)


def obtener_por_ids(track_ids: list) -> list[dict]:
    """Devuelve las entradas de attributions.json para esos IDs."""
    data = _cargar()
    ids = {str(t) for t in track_ids}
    return [t for t in data["tracks"] if str(t["track_id"]) in ids]


# -------------------------------------------------------------
# Formateo de bloques para la descripcion
# -------------------------------------------------------------
def formatear_timecode(segundos: int) -> str:
    h = segundos // 3600
    m = (segundos // 60) % 60
    s = segundos % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def formatear_tracklist(tracks_con_tiempos: list[dict]) -> str:
    """
    tracks_con_tiempos: [{ 'inicio': 0, 'titulo': '...', 'artista': '...' }]
    Devuelve el bloque TRACKLIST formateado.
    """
    if not tracks_con_tiempos:
        return ""

    lineas = [
        "═══════════════════════════════════",
        "📻 TRACKLIST",
        "═══════════════════════════════════",
        "",
    ]
    for t in tracks_con_tiempos:
        tc = formatear_timecode(t["inicio"])
        lineas.append(f"{tc} - {t['titulo']} — {t['artista']}")
    lineas.append("")
    return "\n".join(lineas)


def formatear_atribuciones(entries: list[dict]) -> str:
    """Bloque de atribuciones completo para la descripcion."""
    con_attr = [e for e in entries if e.get("atribucion_requerida")]
    if not con_attr:
        return ""

    lineas = [
        "═══════════════════════════════════",
        "🎵 MUSICA - ATRIBUCIONES (Creative Commons)",
        "═══════════════════════════════════",
        "",
        "Las siguientes pistas requieren atribución:",
        "",
    ]
    for i, e in enumerate(con_attr, 1):
        lineas.append(f'{i}. "{e["titulo"]}" by {e["artista"]}')
        if e.get("file_page_url"):
            lineas.append(f'   Fuente: {e["file_page_url"]}')
        elif e.get("url_descarga"):
            lineas.append(f'   Fuente: {e["url_descarga"]}')
        if e.get("licencia_url"):
            lineas.append(f'   Licencia: {e.get("licencia", "?")} ({e["licencia_url"]})')
        else:
            lineas.append(f'   Licencia: {e.get("licencia", "?")}')
        lineas.append("")
    return "\n".join(lineas)


def formatear_chapters(tracks_con_tiempos: list[dict],
                       segundos_intro: int = 0,
                       offset_principal: int = 0) -> str:
    """
    Genera chapters para YouTube.
    Primer chapter DEBE empezar en 00:00.
    Minimo 3 chapters, cada uno > 10s.
    """
    if len(tracks_con_tiempos) < 2:
        return ""

    lineas = []

    # Intro
    if segundos_intro > 0:
        lineas.append("00:00 Intro")
        primer_track_inicio = segundos_intro + tracks_con_tiempos[0]["inicio"]
    else:
        primer_track_inicio = tracks_con_tiempos[0]["inicio"]

    # Tracks
    for t in tracks_con_tiempos:
        seg = t["inicio"] + segundos_intro
        tc = formatear_timecode(seg)
        lineas.append(f"{tc} {t['titulo'][:60]} — {t['artista'][:40]}")

    return "\n".join(lineas)


if __name__ == "__main__":
    log.info("--- Test attributions ---")
    from core.channel_manager import set_active_channel
    set_active_channel("keiz_productions")

    # Ejemplo
    tracks_demo = [
        {"inicio": 0, "titulo": "Midnight Rain", "artista": "BOCrew"},
        {"inicio": 234, "titulo": "Lost in Thought", "artista": "Air Tone"},
    ]
    print("\n--- TRACKLIST ---")
    print(formatear_tracklist(tracks_demo))
    print("\n--- CHAPTERS ---")
    print(formatear_chapters(tracks_demo, segundos_intro=5))
