# LofiProducer pipeline
"""
Cajon 14 - Orquestador principal del pipeline LofiProducer.
"""
from __future__ import annotations
import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from core.config import DATA_DIR, OUTPUT_DIR
from core.logger import get_logger

log = get_logger("main")
RUN_LOG = DATA_DIR / "run_log.jsonl"

INTRO_PATH = Path.home() / "LofiProducer/assets/intro/intro_kz.mp4"
OUTRO_PATH = Path.home() / "LofiProducer/assets/outro/outro_kz.mp4"

def registrar(nombre: str, estado: str, segundos: float, extra: dict | None = None) -> None:
    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "paso": nombre,
        "estado": estado,
        "segundos": round(segundos, 2),
    }
    if extra:
        entry.update(extra)
    with RUN_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def paso_1_tendencias(args) -> dict:
    from fases.tendencias import recoger_tendencias, guardar_json
    videos = recoger_tendencias()
    if not videos:
        raise RuntimeError("Sin videos encontrados en tendencias.")
    ruta = guardar_json(videos)
    return {"ruta": ruta, "total": len(videos)}

def paso_2_seo(args) -> dict:
    from fases.seo_ia import generar_pack, guardar_pack
    pack = generar_pack()
    ruta = guardar_pack(pack)
    return {"ruta": ruta, "titulo": (pack.get("titulos") or [""])[0]}

def paso_3_imagen(args) -> dict:
    from fases.imagen import generar_bases
    resultados = generar_bases()
    if not resultados:
        raise RuntimeError("No se genero ninguna imagen base.")
    return {"imagenes": {k: str(v) for k, v in resultados.items()}}

def paso_4_portada(args) -> dict:
    from fases.portada import generar_portadas
    resultados = generar_portadas()
    return {"portadas": {k: str(v) for k, v in resultados.items()}}

def paso_5_video(args) -> dict:
    from fases.video import construir_video_youtube
    from fases.audio import descargar_audio_ccmixter
    
    # 1. Intentar descargar audio real
    log.info("Solicitando audio real a CCMixter...")
    audio_path = descargar_audio_ccmixter("lofi,chill")
    if audio_path:
        log.info("Usando AUDIO REAL: %s", audio_path.name)
    else:
        log.warning("No se pudo obtener audio real. Se usara ruido rosa (fallback).")

    # 2. Construir el video pasandole el audio (o None si fallo)
    ruta = construir_video_youtube(audio_real=audio_path)
    return {"ruta": str(ruta), "mb": ruta.stat().st_size / 1024 / 1024}

def paso_6_intro(args) -> dict:
    if INTRO_PATH.exists() and not args.regenerar_intro_outro:
        return {"ruta": str(INTRO_PATH), "reutilizada": True}
    from fases.intro import generar_intro
    ruta = generar_intro()
    return {"ruta": str(ruta), "reutilizada": False}

def paso_7_outro(args) -> dict:
    if OUTRO_PATH.exists() and not args.regenerar_intro_outro:
        return {"ruta": str(OUTRO_PATH), "reutilizada": True}
    from fases.outro import generar_outro
    ruta = generar_outro()
    return {"ruta": str(ruta), "reutilizada": False}

def paso_8_ensamblado(args) -> dict:
    from fases.ensamblado import ensamblar
    ruta = ensamblar()
    return {"ruta": str(ruta), "mb": ruta.stat().st_size / 1024 / 1024}

def paso_9_subida(args) -> dict:
    if not args.subir:
        return {"omitido": True}
    from fases.subida import subir
    return subir(privacidad=args.privacidad)

PASOS = [
    ("Tendencias YouTube", paso_1_tendencias),
    ("SEO con IA",         paso_2_seo),
    ("Imagen base",        paso_3_imagen),
    ("Portada con titulo", paso_4_portada),
    ("Video horizontal",   paso_5_video),
    ("Intro KZ",           paso_6_intro),
    ("Outro KZ",           paso_7_outro),
    ("Ensamblado final",   paso_8_ensamblado),
    ("Subida a YouTube",   paso_9_subida),
]

def ejecutar_paso(n: int, total: int, nombre: str, fn, args) -> dict:
    log.info("PASO %d/%d: %s", n, total, nombre)
    t0 = time.monotonic()
    try:
        resultado = fn(args)
        elapsed = time.monotonic() - t0
        log.info("OK en %.1fs", elapsed)
        registrar(nombre, "ok", elapsed, resultado if isinstance(resultado, dict) else None)
        return resultado
    except Exception as e:
        elapsed = time.monotonic() - t0
        log.error("FALLO en %.1fs: %s", elapsed, e)
        registrar(nombre, f"error: {type(e).__name__}", elapsed)
        raise

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--subir", action="store_true")
    p.add_argument("--privacidad", default="private")
    p.add_argument("--desde", type=int, default=1)
    p.add_argument("--solo", type=int, default=None)
    p.add_argument("--regenerar-intro-outro", action="store_true")
    p.add_argument("--sin-intro-outro", action="store_true")
    return p.parse_args()

def main() -> int:
    args = parse_args()
    t_global = time.monotonic()
    
    for i, (nombre, fn) in enumerate(PASOS, 1):
        if args.solo is not None and i != args.solo: continue
        if args.solo is None and i < args.desde: continue
        if args.sin_intro_outro and i in (6, 7): continue

        try:
            ejecutar_paso(i, len(PASOS), nombre, fn, args)
        except Exception:
            log.error("PIPELINE ABORTADO EN EL PASO %d", i)
            return 1

    elapsed = time.monotonic() - t_global
    print(f"\nPIPELINE COMPLETADO en {elapsed/60:.1f} min")
    return 0

if __name__ == "__main__":
    sys.exit(main())
