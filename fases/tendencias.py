"""
Cajon 05 - Tendencias de YouTube.

Flujo:
  1. search.list  -> descubre videos del nicho en los ultimos N dias.
  2. videos.list  -> trae stats + snippet completo.
  3. Guarda resultado en data/tendencias.json.

Coste: ~101 unidades por ejecucion (limite diario 10.000).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import requests

from core.config import (
    DATA_DIR,
    YOUTUBE_API_KEY,
    YOUTUBE_SEARCH_URL,
    YOUTUBE_VIDEOS_URL,
)
from core.logger import get_logger


log = get_logger("fases.tendencias")


# -------------------------------------------------------------
# Configuracion del nicho
# -------------------------------------------------------------
QUERIES_NICHO = [
    "lofi hip hop",
    "relaxing lofi beats",
    "chillhop study",
]

DIAS_ANTIGUEDAD = 30
MAX_RESULTADOS   = 10
MIN_VISTAS       = 5_000


# -------------------------------------------------------------
# 1. Buscar videos por query
# -------------------------------------------------------------
def buscar_videos(query: str, dias: int = DIAS_ANTIGUEDAD,
                  max_results: int = MAX_RESULTADOS) -> list[str]:
    fecha_limite = (
        datetime.now(timezone.utc) - timedelta(days=dias)
    ).isoformat(timespec="seconds").replace("+00:00", "Z")

    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet",
        "q": query,
        "type": "video",
        "order": "viewCount",
        "publishedAfter": fecha_limite,
        "maxResults": max_results,
        "relevanceLanguage": "en",
        "videoDuration": "long",
    }

    log.info("YouTube search: q=%r (desde %s)", query, fecha_limite[:10])
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=30)

    if resp.status_code >= 400:
        log.error("YouTube search HTTP %s -> %s",
                  resp.status_code, resp.text[:400])
        raise RuntimeError(f"YouTube search error {resp.status_code}")

    data = resp.json()
    ids = [item["id"]["videoId"]
           for item in data.get("items", [])
           if item.get("id", {}).get("videoId")]

    log.info("  -> %d videos encontrados para %r", len(ids), query)
    return ids


# -------------------------------------------------------------
# 2. Obtener detalles de los videos
# -------------------------------------------------------------
def detalle_videos(video_ids: list[str]) -> list[dict[str, Any]]:
    if not video_ids:
        return []

    params = {
        "key": YOUTUBE_API_KEY,
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids[:50]),
    }

    log.info("YouTube videos.list para %d ids", len(video_ids))
    resp = requests.get(YOUTUBE_VIDEOS_URL, params=params, timeout=30)

    if resp.status_code >= 400:
        log.error("YouTube videos HTTP %s -> %s",
                  resp.status_code, resp.text[:400])
        raise RuntimeError(f"YouTube videos error {resp.status_code}")

    data = resp.json()
    return data.get("items", [])


# -------------------------------------------------------------
# 3. Normalizar cada video
# -------------------------------------------------------------
def normalizar(item: dict[str, Any]) -> dict[str, Any]:
    snippet = item.get("snippet", {})
    stats   = item.get("statistics", {})
    detalles = item.get("contentDetails", {})

    return {
        "id":           item.get("id"),
        "titulo":       snippet.get("title", ""),
        "canal":        snippet.get("channelTitle", ""),
        "publicado":    snippet.get("publishedAt", ""),
        "descripcion":  (snippet.get("description", "") or "")[:500],
        "tags":         snippet.get("tags", []),
        "vistas":       int(stats.get("viewCount", 0)),
        "likes":        int(stats.get("likeCount", 0)),
        "comentarios":  int(stats.get("commentCount", 0)),
        "duracion_iso": detalles.get("duration", ""),
        "url":          f"https://www.youtube.com/watch?v={item.get('id')}",
    }


# -------------------------------------------------------------
# 4. Orquestador
# -------------------------------------------------------------
def recoger_tendencias() -> list[dict[str, Any]]:
    todos_ids: set[str] = set()

    for q in QUERIES_NICHO:
        try:
            todos_ids.update(buscar_videos(q))
        except Exception as exc:
            log.warning("Fallo en query %r: %s", q, exc)

    if not todos_ids:
        log.warning("No se encontraron videos en ninguna query.")
        return []

    items = detalle_videos(list(todos_ids))
    videos = [normalizar(it) for it in items]

    videos = [v for v in videos if v["vistas"] >= MIN_VISTAS]
    videos.sort(key=lambda v: v["vistas"], reverse=True)

    log.info("Tendencias finales: %d videos (filtro vistas>=%d)",
             len(videos), MIN_VISTAS)
    return videos


# -------------------------------------------------------------
# 5. Guardar a JSON
# -------------------------------------------------------------
def guardar_json(videos: list[dict[str, Any]]) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta = DATA_DIR / f"tendencias_{timestamp}.json"

    payload = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "queries": QUERIES_NICHO,
        "dias_antiguedad": DIAS_ANTIGUEDAD,
        "total": len(videos),
        "videos": videos,
    }

    ruta.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Guardado en %s", ruta)
    return str(ruta)


# -------------------------------------------------------------
# 6. Auto-test
# -------------------------------------------------------------
if __name__ == "__main__":
    log.info("--- Test cajon 05: tendencias de YouTube ---")
    videos = recoger_tendencias()

    if not videos:
        print("\n[!] No se han encontrado videos. Revisa la key o la cuota.")
    else:
        ruta = guardar_json(videos)
        print()
        print("=" * 60)
        print(f"TOP {min(5, len(videos))} TENDENCIAS")
        print("=" * 60)
        for v in videos[:5]:
            print(f"  {v['vistas']:>10,} vistas | {v['titulo'][:60]}")
            print(f"             canal: {v['canal']}")
        print("=" * 60)
        print(f"[OK] JSON guardado: {ruta}")
