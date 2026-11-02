#!/usr/bin/env python3
"""lofi_largo_del_dia.py - Rotador de lofi largo. Descarga 1 link/día del pool CC."""
import json, subprocess, sys
from pathlib import Path
from datetime import date

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
POOL = ROOT / "config" / "lofi_largo_pool.json"
COUNTER = ROOT / "data" / "agent" / "lofi_largo_counter.txt"
MUSICA_TEMP = ROOT / "output" / "musica_temp"
MUSICA_TEMP.mkdir(parents=True, exist_ok=True)

def _leer_counter():
    if COUNTER.exists():
        try: return int(COUNTER.read_text().strip())
        except: pass
    return 0

def _guardar_counter(n):
    COUNTER.parent.mkdir(parents=True, exist_ok=True)
    COUNTER.write_text(str(n))

def limpiar_lofi_viejo():
    for f in MUSICA_TEMP.glob("lofi_largo_*.mp3"):
        f.unlink()
        print(f"  🗑️ Borrado: {f.name}")

def elegir_link():
    if not POOL.exists(): return None
    pool = json.loads(POOL.read_text())
    activos = [t for t in pool if t.get("activo", True)]
    if not activos: return None
    idx = _leer_counter() % len(activos)
    track = activos[idx]
    _guardar_counter(idx + 1)
    print(f"  📀 Link #{idx+1}/{len(activos)}: {track.get('titulo','?')[:60]}")
    print(f"     Duración: {track['duracion']//60}min | Score: {track['score']}")
    return track

def descargar(track, salida):
    if not track: return None
    try:
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--audio-quality", "128k",
               "--no-playlist", "--no-warnings", "--max-filesize", "50M",
               "-o", str(salida.with_suffix(".%(ext)s")), track["url"]]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and salida.with_suffix(".mp3").exists():
            print(f"  ✅ Descargado: {salida.with_suffix('.mp3').name} ({salida.with_suffix('.mp3').stat().st_size//1024//1024}MB)")
            return salida.with_suffix(".mp3")
        print(f"  ⚠️ yt-dlp: {r.stderr[:150]}")
    except Exception as e:
        print(f"  ⚠️ {e}")
    return None

def preparar():
    print("🎵 Preparando lofi largo del día")
    limpiar_lofi_viejo()
    hoy = date.today().isoformat()
    salida_final = MUSICA_TEMP / f"lofi_largo_{hoy}.mp3"
    if salida_final.exists():
        print(f"  ♻️ Ya existe: {salida_final.name}")
        return str(salida_final)

    for intento in range(3):
        track = elegir_link()
        if not track: break
        temp = MUSICA_TEMP / f"lofi_temp_{intento}.mp3"
        src = descargar(track, temp)
        if src:
            # Renombrar a lofi_largo_FECHA.mp3
            try:
                src.rename(salida_final)
                return str(salida_final)
            except Exception as e:
                print(f"  ⚠️ rename: {e}")
    print("  ❌ Sin lofi largo")
    return None

if __name__ == "__main__":
    r = preparar()
    print(f"\nResultado: {r}")
