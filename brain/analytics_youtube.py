"""Cajon 134 - Obtiene estadisticas del canal de YouTube para el Dashboard."""
from __future__ import annotations
import json
import requests
from pathlib import Path
from core.config import YOUTUBE_API_KEY

ROOT = Path(__file__).resolve().parent.parent

def obtener_stats_canal(nombre_canal="KeiZ Productions") -> dict:
    if not YOUTUBE_API_KEY:
        return {"error": "Falta YOUTUBE_API_KEY en .env"}

    try:
        # 1. Buscar el ID del canal por su nombre
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            "key": YOUTUBE_API_KEY,
            "part": "snippet",
            "q": nombre_canal,
            "type": "channel",
            "maxResults": 1
        }
        r = requests.get(search_url, params=search_params, timeout=15)
        r.raise_for_status()
        items = r.json().get("items", [])
        
        if not items:
            return {"error": f"Canal '{nombre_canal}' no encontrado"}
            
        channel_id = items[0]["id"]["channelId"]

        # 2. Obtener estadísticas del canal
        stats_url = "https://www.googleapis.com/youtube/v3/channels"
        stats_params = {
            "key": YOUTUBE_API_KEY,
            "part": "statistics",
            "id": channel_id
        }
        r_stats = requests.get(stats_url, params=stats_params, timeout=15)
        r_stats.raise_for_status()
        stats = r_stats.json()["items"][0]["statistics"]

        # 3. Obtener los últimos vídeos subidos
        videos_url = "https://www.googleapis.com/youtube/v3/search"
        videos_params = {
            "key": YOUTUBE_API_KEY,
            "channelId": channel_id,
            "part": "snippet",
            "order": "date",
            "maxResults": 3,
            "type": "video"
        }
        r_videos = requests.get(videos_url, params=videos_params, timeout=15)
        r_videos.raise_for_status()
        videos = []
        for v in r_videos.json().get("items", []):
            videos.append(v["snippet"]["title"])

        return {
            "nombre_canal": items[0]["snippet"]["channelTitle"],
            "nombre_canal": items[0]["snippet"]["channelTitle"],
            "suscriptores": f"{int(stats.get('subscriberCount', 0)):,}",
            "visitas_totales": f"{int(stats.get('viewCount', 0)):,}",
            "videos_totales": f"{int(stats.get('videoCount', 0)):,}",
            "ultimos_videos": videos
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print(json.dumps(obtener_stats_canal(), indent=2, ensure_ascii=False))
