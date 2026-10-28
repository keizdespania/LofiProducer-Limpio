"""
Cajon 16 - Limpieza automatica de archivos antiguos (v2).

Cambios v2:
  - Anade playlist_*.mp3, polli_*.mp3 y polli_playlist_*.mp3 (1 dia)
  - Anade test_*.ass (0 dia = inmediato)
"""

from __future__ import annotations

import time
from pathlib import Path

from core.logger import get_logger


log = get_logger("fases.limpieza")


RETENCION = {
    # Videos
    "video_youtube_*.mp4": 3,
    "video_final_*.mp4": 3,
    "test_*.mp4": 1,
    # Portadas
    "portada_final_*.jpg": 3,
    "portada_base_*.jpg": 3,
    # Audio temporal (se regenera con cada video)
    "playlist_*.mp3": 1,
    "audio_dummy_*.mp3": 1,
    "polli_clip_*.mp3": 1,
    "polli_playlist_*.mp3": 1,
    # Archivos de debug/test
    "check_*.png": 1,
    "test_*.png": 1,
    "_counter_*.ass": 0,
    "_lista*.txt": 0,
    "*.ass": 0,
}


def _es_mas_antiguo(path: Path, dias: int) -> bool:
    if dias == 0:
        return True  # borrado inmediato
    limite = time.time() - (dias * 86400)
    return path.stat().st_mtime < limite


def _formatear_kb(bytes_: int) -> str:
    kb = bytes_ / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    return f"{kb/1024:.1f} MB"


def limpiar_canal(output_dir: Path, dry_run: bool = False) -> dict:
    if not output_dir.exists():
        log.warning("output_dir no existe: %s", output_dir)
        return {"borrados": 0, "espacio_kb": 0, "errores": []}

    log.info("Limpiando %s (dry_run=%s)", output_dir.name, dry_run)

    borrados = 0
    espacio = 0
    errores = []

    for patron, dias in RETENCION.items():
        for f in output_dir.glob(patron):
            if not f.is_file():
                continue
            if not _es_mas_antiguo(f, dias):
                continue

            tam = f.stat().st_size
            edad_dias = (time.time() - f.stat().st_mtime) / 86400

            if dry_run:
                log.info("  [DRY] %s (%.1f dias, %s)",
                         f.name, edad_dias, _formatear_kb(tam))
            else:
                try:
                    f.unlink()
                    log.info("  BORRADO %s (%.1f dias, %s)",
                             f.name, edad_dias, _formatear_kb(tam))
                except Exception as e:
                    log.error("  Error borrando %s: %s", f.name, e)
                    errores.append(str(f))
                    continue

            borrados += 1
            espacio += tam

    return {
        "borrados": borrados,
        "espacio_kb": espacio / 1024,
        "errores": errores,
    }


def limpiar_todos(dry_run: bool = False) -> dict:
    from core.channel_manager import listar_canales

    total_borrados = 0
    total_espacio = 0
    total_errores = []

    for canal in listar_canales(solo_habilitados=False):
        cid = canal["id"]
        project = Path(__file__).resolve().parent.parent
        output_dir = project / "output" / cid

        resultado = limpiar_canal(output_dir, dry_run=dry_run)
        total_borrados += resultado["borrados"]
        total_espacio += resultado["espacio_kb"]
        total_errores.extend(resultado["errores"])

    return {
        "borrados": total_borrados,
        "espacio_kb": total_espacio,
        "errores": total_errores,
    }


if __name__ == "__main__":
    import argparse
    from core.channel_manager import set_active_channel

    p = argparse.ArgumentParser(description="Limpieza de archivos antiguos")
    p.add_argument("--canal", type=str, default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    log.info("--- Limpieza de archivos antiguos ---")

    if args.canal:
        canal = set_active_channel(args.canal)
        r = limpiar_canal(canal["output_dir"], dry_run=args.dry_run)
    else:
        r = limpiar_todos(dry_run=args.dry_run)

    print()
    print("=" * 60)
    print(f"RESULTADO {'(DRY-RUN)' if args.dry_run else ''}")
    print("=" * 60)
    print(f"Archivos borrados: {r['borrados']}")
    print(f"Espacio liberado : {r['espacio_kb']:.1f} KB ({r['espacio_kb']/1024:.1f} MB)")
    if r["errores"]:
        print(f"Errores          : {len(r['errores'])}")
    print("=" * 60)
