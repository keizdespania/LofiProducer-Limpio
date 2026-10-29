"""limpiar_musica_render.py - Borra música de fuentes externas tras renderizar.
Conserva ACE-Step (propia) para hacer álbumes en Spotify.
Uso: python limpiar_musica_render.py [fecha]
"""
import json, pathlib, sys, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
MUSICA = ROOT / "output" / "musica_temp"
ACE_ARCHIVO = ROOT / "output" / "musica_propia" / "ace_step"
ACE_ARCHIVO.mkdir(parents=True, exist_ok=True)
ROT = MUSICA / "rotacion_musica.json"
HIST = MUSICA / "historial_yt_cc.json"


def limpiar(fecha=None):
    """Borra todo excepto ACE-Step (que se archiva)."""
    fecha = fecha or __import__("datetime").date.today().isoformat()
    borrados = 0
    conservados = 0
    archivados = 0

    # 1. yt_cc_*.mp3 (YouTube CC, de paso) → borrar
    for f in MUSICA.glob("yt_cc_*.mp3"):
        f.unlink(); borrados += 1; print(f"  🗑️ {f.name}")

    # 2. Tunetank (nombre_mood_NNNN.mp3) → borrar
    for f in MUSICA.glob("*_*.mp3"):
        if f.name.startswith("yt_") or f.name.startswith("ace_") or "propia" in f.name:
            continue
        # Tunetank: tension_6718.mp3, epico_1458.mp3, etc.
        if any(m in f.name for m in ["tension_","relax_","epico_","inspirador_","misterio_","electronico_","sarcasmo_","dramatico_","calm_"]):
            f.unlink(); borrados += 1; print(f"  🗑️ {f.name}")

    # 3. ACE-Step (ace_*.mp3 o *_acestep_*) → archivar para Spotify
    for f in MUSICA.glob("ace_*.mp3"):
        if f.exists():
            dst = ACE_ARCHIVO / f.name
            shutil.move(str(f), str(dst)); archivados += 1; print(f"  📀 {f.name} → {dst}")
    for f in MUSICA.glob("*acestep*.mp3"):
        if f.exists():
            dst = ACE_ARCHIVO / f.name
            shutil.move(str(f), str(dst)); archivados += 1; print(f"  📀 {f.name} → {dst}")

    # 4. Limpiar rotación (los ya borrados)
    if ROT.exists():
        try:
            rot = json.loads(ROT.read_text())
            rot["usos"] = {}
            ROT.write_text(json.dumps(rot, indent=2, ensure_ascii=False))
        except: pass

    # 5. Limpiar historial de YT CC (los archivos ya no existen)
    if HIST.exists():
        try:
            h = json.loads(HIST.read_text())
            h["descargados"] = [x for x in h.get("descargados", []) if (MUSICA / x).exists()]
            HIST.write_text(json.dumps(h, indent=2, ensure_ascii=False))
        except: pass

    print(f"\n✅ {borrados} borrados, {archivados} archivados (ACE-Step → {ACE_ARCHIVO})")
    return {"borrados": borrados, "archivados": archivados}


if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    limpiar(fecha)
