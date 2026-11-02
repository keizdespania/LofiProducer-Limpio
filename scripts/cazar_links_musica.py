#!/usr/bin/env python3
"""cazar_links_musica.py - Cazador de links de YouTube para música de shorts.
Filtra por Creative Commons (license=creativeCommon), duración 20-180s, score 0-100.
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
POOL_FILE = ROOT / "config" / "musica_shorts_pool.json"

QUERIES = [
    ("tension",    "lofi type beat dark hook no copyright"),
    ("epico",      "cinematic epic trailer music creative commons"),
    ("relax",      "lofi chill beat vinyl creative commons"),
    ("electronico","techno hook drop 30s creative commons"),
    ("misterio",   "dark ambient mystery music creative commons"),
    ("inspirador","inspiring cinematic short music creative commons"),
]

def buscar_youtube(query, max_results=15):
    """Busca con filtro CC y duración 20-180s."""
    cmd = [
        "yt-dlp", "--flat-playlist", "--dump-json",
        "--no-warnings",
        "--match-filter", "license=creativeCommon & duration>20 & duration<180",
        f"ytsearch{max_results}:{query}"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        resultados = []
        for line in r.stdout.strip().split("\n"):
            if not line.strip(): continue
            try:
                d = json.loads(line)
                resultados.append({
                    "id": d.get("id"),
                    "titulo": d.get("title", ""),
                    "canal": d.get("channel", ""),
                    "duracion": int(d.get("duration") or 0),
                    "vistas": int(d.get("view_count") or 0),
                    "url": f"https://www.youtube.com/watch?v={d.get('id')}",
                    "licencia": "creativeCommon",
                })
            except Exception:
                pass
        return resultados
    except Exception as e:
        print(f"  ⚠️ yt-dlp: {e}")
        return []

def puntuar(track, mood):
    score = 50
    titulo = track["titulo"].lower()
    dur = track.get("duracion") or 0
    vistas = track.get("vistas") or 0

    # Duración óptima: 30-90s
    if 30 <= dur <= 90: score += 20
    elif 90 < dur <= 180: score += 10
    elif dur < 20: score -= 30

    # Keywords
    for kw in ["hook", "drop", "type beat", "free", "instrumental", "beat", "no copyright"]:
        if kw in titulo: score += 8

    # Vistas
    if vistas > 1_000_000: score += 15
    elif vistas > 100_000: score += 10
    elif vistas > 10_000: score += 5

    # Mood
    mood_kw = {
        "tension": ["dark", "tense", "suspense", "dramatic"],
        "epico": ["epic", "cinematic", "trailer", "powerful"],
        "relax": ["chill", "relax", "calm", "lofi"],
        "electronico": ["techno", "electronic", "synth", "edm"],
        "misterio": ["mystery", "dark", "ambient", "eerie"],
        "inspirador": ["inspiring", "uplifting", "motivational"],
    }
    for kw in mood_kw.get(mood, []):
        if kw in titulo: score += 5

    return max(0, min(100, score))

def cazar(max_por_mood=30, score_min=65):
    print("🎯 Cazador de links CC para música de shorts")
    pool = []
    for mood, query in QUERIES:
        print(f"\n=== {mood} ===")
        tracks = buscar_youtube(query, max_results=25)
        print(f"  {len(tracks)} con CC y 20-180s")
        for t in tracks:
            s = puntuar(t, mood)
            if s >= score_min:
                t["mood"] = mood
                t["score"] = s
                t["fecha_cazado"] = datetime.now().isoformat()
                pool.append(t)

    # Dedup + ordenar
    vistos = set()
    pool_limpio = []
    for t in sorted(pool, key=lambda x: x["score"], reverse=True):
        if t["id"] not in vistos:
            vistos.add(t["id"])
            pool_limpio.append(t)

    POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
    POOL_FILE.write_text(json.dumps(pool_limpio, indent=2, ensure_ascii=False))
    print(f"\n✅ Pool: {len(pool_limpio)} links CC en {POOL_FILE}")

    # Resumen por mood
    print("\n=== Resumen por mood ===")
    for mood in ["tension", "epico", "relax", "electronico", "misterio", "inspirador"]:
        n = sum(1 for t in pool_limpio if t["mood"] == mood)
        print(f"  {mood}: {n}")
    return pool_limpio

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    cazar(max_por_mood=n)
