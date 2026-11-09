#!/usr/bin/env python3
"""Sincroniza podcasts: copia de output/ a web/ + regenera feed.xml + index.md."""
import pathlib, shutil, subprocess, sys, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
PODCAST = ROOT / "web" / "docs" / "podcast"
OUT_POD = ROOT / "output" / "encuadre" / "podcast"
PODCAST.mkdir(parents=True, exist_ok=True)

nuevos = 0
# 1. Copiar de output/encuadre/podcast/ si existe
if OUT_POD.exists():
    for mp3 in OUT_POD.glob("*.mp3"):
        dst = PODCAST / mp3.name
        if not dst.exists() or dst.stat().st_size < mp3.stat().st_size:
            shutil.copy2(mp3, dst); nuevos += 1
            print(f"  [copy] {mp3.name}")

# 2. Regenerar index + feed
try:
    from generar_podcast import _regenerar_index, _regenerar_feed
    _regenerar_index()
    _regenerar_feed()
    print("OK index + feed regenerados")
except Exception as e:
    print(f"WARN regenerar: {e}")

# 3. Stats
mp3s = sorted(PODCAST.glob("*.mp3"))
print(f"OK {len(mp3s)} episodios, {nuevos} nuevos copiados")
if mp3s:
    print(f"   desde {mp3s[0].stem} hasta {mp3s[-1].stem}")
