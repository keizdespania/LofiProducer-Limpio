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
MUSICA_TEMP = ROOT / "output" / "musica_temp"
MUSICA_TEMP.mkdir(parents=True, exist_ok=True)

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
    """Borra la música de días anteriores (short_dia_*.mp3)."""
    for f in MUSICA_TEMP.glob("short_dia_*.mp3"):
        f.unlink()
        print(f"  🗑️ Borrado: {f.name}")

def elegir_link():
    if not POOL.exists():
        print(f"⚠️ Pool no existe: {POOL}. Ejecuta cazar_links_musica.py primero.")
        return None
    pool = json.loads(POOL.read_text())
    if not pool:
        print("⚠️ Pool vacío")
        return None
    idx = _leer_counter() % len(pool)
    track = pool[idx]
    _guardar_counter(idx + 1)
    print(f"  📀 Link #{idx+1}/{len(pool)}: {track.get('titulo','?')[:60]}")
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

def preparar():
    print("🎵 Preparando música del día para shorts")
    limpiar_musica_vieja()
    track = elegir_link()
    if not track:
        return None
    hoy = date.today().isoformat()
    salida_final = MUSICA_TEMP / f"short_dia_{hoy}.mp3"
    if salida_final.exists():
        print(f"  ♻️ Ya existe: {salida_final.name}")
        return str(salida_final)

    # Descargar (con reintentos: si falla, prueba el siguiente del pool)
    pool = json.loads(POOL.read_text())
    for intento in range(3):
        track = elegir_link()
        if not track: break
        temp = MUSICA_TEMP / f"temp_{intento}.mp3"
        src = descargar(track, temp)
        if src:
            final = recortar(src, salida_final, 60)
            # Borrar temp
            try: src.unlink()
            except: pass
            if final:
                return str(final)

    print("  ❌ No se pudo descargar ninguna música")
    return None

if __name__ == "__main__":
    r = preparar()
    print(f"\nResultado: {r}")
