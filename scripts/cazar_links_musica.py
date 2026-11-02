#!/usr/bin/env python3
"""cazar_links_musica.py v2 - Cazador de links CC para YouTube.
Uso:
  python3 cazar_links_musica.py                # caza shorts (30-180s)
  python3 cazar_links_musica.py --tipo largo   # caza lofi largo (900-3600s)
"""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
POOL_SHORT = ROOT / "config" / "musica_shorts_pool.json"
POOL_LARGO = ROOT / "config" / "lofi_largo_pool.json"

# Queries por tipo
QUERIES = {
    "short": [
        ("tension",    "lofi type beat dark hook no copyright"),
        ("epico",      "cinematic epic trailer music creative commons"),
        ("relax",      "lofi chill beat vinyl creative commons"),
        ("electronico","techno hook drop 30s creative commons"),
        ("misterio",   "dark ambient mystery music creative commons"),
        ("inspirador","inspiring cinematic short music creative commons"),
    ],
    "largo": [
        ("lofi",       "lofi hip hop mix 1 hour creative commons"),
        ("chillhop",   "chillhop music mix creative commons"),
        ("jazzhop",    "jazz hop cafe mix creative commons"),
        ("study",      "lofi beats to study creative commons"),
        ("sleep",      "lofi sleep music creative commons"),
        ("ambient",    "ambient lofi mix creative commons"),
    ],
}

def buscar_youtube(query, tipo, max_results=25):
    """Busca con filtro CC. Duración según tipo."""
    if tipo == "largo":
        filtro = "license=creativeCommon & duration>900 & duration<3600"
    else:
        filtro = "license=creativeCommon & duration>20 & duration<180"

    cmd = [
        "yt-dlp", "--flat-playlist", "--dump-json",
        "--no-warnings",
        "--match-filter", filtro,
        f"ytsearch{max_results}:{query}"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
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

def puntuar(track, mood, tipo="short"):
    score = 50
    titulo = track["titulo"].lower()
    dur = track.get("duracion") or 0
    vistas = track.get("vistas") or 0

    if tipo == "largo":
        # Duración óptima: 15-25 min
        if 900 <= dur <= 1500: score += 25
        elif 1500 < dur <= 2400: score += 15
        elif dur > 2400 or dur < 900: score -= 20
    else:
        if 30 <= dur <= 90: score += 20
        elif 90 < dur <= 180: score += 10
        elif dur < 20: score -= 30

    # Keywords
    if tipo == "largo":
        for kw in ["mix", "hour", "chillhop", "study", "relax", "beats"]:
            if kw in titulo: score += 6
    else:
        for kw in ["hook", "drop", "type beat", "free", "instrumental", "beat"]:
            if kw in titulo: score += 8

    if vistas > 1_000_000: score += 15
    elif vistas > 100_000: score += 10
    elif vistas > 10_000: score += 5

    return max(0, min(100, score))

def _cargar_pool(path):
    if not path.exists(): return []
    try: return json.loads(path.read_text())
    except: return []

def _guardar_pool(path, pool):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pool, indent=2, ensure_ascii=False))

def _dedup(pool):
    vistos = set()
    limpio = []
    for t in pool:
        if t.get("id") not in vistos:
            vistos.add(t["id"])
            limpio.append(t)
    return limpio

def cazar(tipo="short", score_min=None, modo_renovacion=False):
    """Caza links.
    - tipo: short | largo
    - score_min: puntuación mínima (65 short, 60 largo)
    - modo_renovacion: caza solo 10-20 nuevos (mantiene existentes)
    """
    if score_min is None:
        score_min = 60 if tipo == "largo" else 65

    pool_path = POOL_LARGO if tipo == "largo" else POOL_SHORT
    pool_existente = _cargar_pool(pool_path)

    if modo_renovacion:
        print(f"🔄 Modo renovación (mantener {len(pool_existente)} existentes)")
        existentes_ids = {t["id"] for t in pool_existente}
        max_por_mood = 3  # pocos nuevos por mood
    else:
        print(f"🎯 Modo caza completa ({tipo})")
        existentes_ids = set()
        max_por_mood = 30

    pool_nuevo = []
    queries = QUERIES.get(tipo, QUERIES["short"])

    for mood, query in queries:
        print(f"\n=== {mood} ===")
        tracks = buscar_youtube(query, tipo, max_results=25)
        print(f"  {len(tracks)} encontrados")
        count = 0
        for t in tracks:
            if t["id"] in existentes_ids: continue
            s = puntuar(t, mood, tipo)
            if s >= score_min and count < max_por_mood:
                t["mood"] = mood
                t["score"] = s
                t["fecha_cazado"] = datetime.now().isoformat()
                t["activo"] = True
                pool_nuevo.append(t)
                count += 1

    # Fusionar: existentes + nuevos
    pool_final = _dedup(pool_existente + pool_nuevo)
    _guardar_pool(pool_path, pool_final)

    print(f"\n✅ Pool {tipo}: {len(pool_final)} links ({len(pool_nuevo)} nuevos)")
    print(f"   Guardado en: {pool_path}")
    return pool_final

def verificar_links(pool_path):
    """Verifica qué links del pool siguen vivos (--flat-playlist, rápido)."""
    pool = _cargar_pool(pool_path)
    if not pool: return pool
    print(f"🔍 Verificando {len(pool)} links...")
    vivos, muertos = 0, 0
    for t in pool:
        try:
            r = subprocess.run(
                ["yt-dlp", "--flat-playlist", "--dump-json", "--no-warnings", t["url"]],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0 and r.stdout.strip():
                t["activo"] = True
                vivos += 1
            else:
                t["activo"] = False
                muertos += 1
        except Exception:
            t["activo"] = False
            muertos += 1
    print(f"  Vivos: {vivos} | Muertos: {muertos}")
    _guardar_pool(pool_path, pool)
    return pool

def mantener_pool(tipo="short"):
    """Modo mantenimiento semanal: verifica + repone muertos."""
    pool_path = POOL_LARGO if tipo == "largo" else POOL_SHORT
    pool = verificar_links(pool_path)
    activos = [t for t in pool if t.get("activo")]
    print(f"\n🔄 Pool tras verificación: {len(activos)} activos de {len(pool)}")
    if len(activos) < 20:
        print(f"⚠️ Pool bajo (<20), cazando 30 más...")
        cazar(tipo=tipo, modo_renovacion=True)
    else:
        print(f"✅ Pool OK (>=20 activos)")

if __name__ == "__main__":
    tipo = "short"
    modo = "cazar"
    for i, arg in enumerate(sys.argv):
        if arg == "--tipo" and i+1 < len(sys.argv):
            tipo = sys.argv[i+1]
        if arg == "--mantener":
            modo = "mantener"

    if modo == "mantener":
        mantener_pool(tipo)
    else:
        cazar(tipo=tipo)
