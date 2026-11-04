#!/usr/bin/env python3
"""musica_short_del_dia.py - Elige 1 link del pool por día, lo descarga, lo recorta.
Rotación automática con counter. Borra la música de ayer antes de descargar la de hoy.
"""
import json, subprocess, sys, os
from pathlib import Path
from datetime import date

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
POOL = ROOT / "config" / "musica_shorts_pool.json"
COUNTER = ROOT / "data" / "agent" / "musica_counter.txt"
USADAS_DIR = ROOT / "data" / "agent" / "musica_usadas"
USADAS_DIR.mkdir(parents=True, exist_ok=True)
MUSICA_TEMP = ROOT / "output" / "musica_temp"
MUSICA_TEMP.mkdir(parents=True, exist_ok=True)

MOODS_SHORT = {
    "dato": "tension",
    "contradiccion": "epico",
    "prediccion": "electronico",
    "tutorial": "relax",
}

def _usadas_path(mood):
    return USADAS_DIR / f"{mood}.json"

def _cargar_usadas(mood):
    p = _usadas_path(mood)
    if p.exists():
        try:
            return set(json.loads(p.read_text()).get("urls", []))
        except: pass
    return set()

def _marcar_usada(mood, url):
    usadas = _cargar_usadas(mood)
    usadas.add(url)
    _usadas_path(mood).write_text(json.dumps({"urls": list(usadas)}, indent=2))

def _leer_counter():
    if COUNTER.exists():
        try:
            return int(COUNTER.read_text().strip())
        except: pass
    return 0

def _guardar_counter(n):
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    COUNTER.write_text(str(n))

def limpiar_musica_vieja():
    """Borra la música de días anteriores, pero NO la del día actual (fix 2026-11-04)."""
    hoy = date.today().isoformat()
    for f in MUSICA_TEMP.glob("short_dia_*.mp3"):
        if hoy in f.name:
            continue  # conservar los del día
        f.unlink()
        print(f"  🗑️ Borrado: {f.name}")

def elegir_link(mood=None):
    if not POOL.exists():
        print(f"⚠️ Pool no existe: {POOL}. Ejecuta cazar_links_musica.py primero.")
        return None
    pool = json.loads(POOL.read_text())
    if not pool:
        print("⚠️ Pool vacío")
        return None
    # Filtrar por mood si se pide
    if mood:
        pool_filtrado = [t for t in pool if t.get("mood") == mood]
        if not pool_filtrado:
            print(f"⚠️ Sin canciones del mood '{mood}', usando cualquier mood")
        else:
            pool = pool_filtrado
    # Filtrar ya usadas
    usadas = _cargar_usadas(mood) if mood else set()
    pool_no_usado = [t for t in pool if t.get("url") not in usadas]
    if not pool_no_usado:
        print(f"⚠️ Todas las canciones de '{mood}' usadas. Reciclando pool completo.")
        pool_no_usado = pool
    idx = _leer_counter() % len(pool_no_usado)
    track = pool_no_usado[idx]
    _guardar_counter(idx + 1)
    print(f"  📀 Link #{idx+1}/{len(pool_no_usado)}: {track.get('titulo','?')[:60]}")
    print(f"     Mood: {track.get('mood')} | Duración: {track.get('duracion')}s | Score: {track.get('score')}")
    return track

def descargar(track, salida):
    """Descarga el audio del link. Si falla, prueba los siguientes del pool."""
    if not track: return None
    try:
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "128k",
            "--no-playlist", "--no-warnings",
            "-o", str(salida.with_suffix(".%(ext)s")),
            track["url"]
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if r.returncode == 0 and salida.with_suffix(".mp3").exists():
            print(f"  ✅ Descargado: {salida.with_suffix('.mp3').name}")
            return salida.with_suffix(".mp3")
        else:
            print(f"  ⚠️ yt-dlp: {r.stderr[:200]}")
    except Exception as e:
        print(f"  ⚠️ {e}")
    return None

def recortar(src, salida, segundos=60):
    """Recorta a 60s."""
    try:
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-i", str(src), "-t", str(segundos), "-c", "copy", str(salida)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if r.returncode == 0 and salida.exists():
            print(f"  ✅ Recortado: {salida.name} ({salida.stat().st_size//1024}KB)")
            return salida
    except Exception as e:
        print(f"  ⚠️ {e}")
    return None

def preparar(mood=None):
    print(f"🎵 Preparando música del día para shorts (mood={mood or 'cualquiera'})")
    limpiar_musica_vieja()
    track = elegir_link(mood)
    if not track:
        return None
    hoy = date.today().isoformat()
    sufijo = f"_{mood}" if mood else ""
    salida_final = MUSICA_TEMP / f"short_dia_{hoy}{sufijo}.mp3"
    if salida_final.exists():
        print(f"  ♻️ Ya existe: {salida_final.name}")
        return str(salida_final)

    # Descargar (con reintentos)
    for intento in range(3):
        track = elegir_link(mood)
        if not track: break
        temp = MUSICA_TEMP / f"temp_{mood or 'x'}_{intento}.mp3"
        src = descargar(track, temp)
        if src:
            final = recortar(src, salida_final, 70)
            # Marcar como usada
            if final and mood and track.get("url"):
                _marcar_usada(mood, track["url"])
                print(f"  ✅ Marcada como usada: {mood}")
            try: src.unlink()
            except: pass
            if final:
                return str(final)

    print("  ❌ No se pudo descargar ninguna música")
    return None

if __name__ == "__main__":
    mood = None
    if "--mood" in sys.argv:
        idx = sys.argv.index("--mood")
        if idx + 1 < len(sys.argv):
            mood = sys.argv[idx + 1]
    r = preparar(mood)
    print(f"\nResultado: {r}")
    sys.exit(0 if r else 1)
