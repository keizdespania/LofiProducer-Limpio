"""
Cajon 06 - Generacion SEO con IA.

Genera DOS titulos:
  - titulo_portada  : <=45 chars (para la imagen)
  - titulo_youtube  : <=70 chars (SEO, movil)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import DATA_DIR
from core.llm import ask
from core.logger import get_logger


log = get_logger("fases.seo_ia")

TOP_N = 10
MAX_TITULO_PORTADA = 45
MAX_TITULO_YOUTUBE = 70


def ultimo_json_tendencias() -> Path:
    archivos = sorted(DATA_DIR.glob("tendencias_*.json"))
    if not archivos:
        raise FileNotFoundError(
            f"No hay tendencias_*.json en {DATA_DIR}. "
            "Ejecuta primero: python -m fases.tendencias"
        )
    return archivos[-1]


def cargar_top_titulos(n: int = TOP_N) -> list[dict[str, Any]]:
    path = ultimo_json_tendencias()
    log.info("Leyendo tendencias desde %s", path.name)
    data = json.loads(path.read_text(encoding="utf-8"))
    videos = data.get("videos", [])[:n]
    log.info("Top %d titulos cargados (de %d totales)", len(videos),
             data.get("total", 0))
    return videos


SYSTEM_PROMPT = (
    "Eres un estratega de contenido especializado en canales de musica Lofi "
    "en YouTube, TikTok e Instagram. Respondes UNICAMENTE con JSON valido, "
    "sin texto adicional, sin markdown, sin ```json."
)


def construir_prompt(videos: list[dict[str, Any]]) -> str:
    lineas = []
    for i, v in enumerate(videos, 1):
        lineas.append(f"{i}. [{v['vistas']:,} vistas] {v['titulo']}")
    lista = "\n".join(lineas)

    return f"""Analiza estos titulos de videos Lofi virales actuales:

{lista}

Genera un pack SEO para un nuevo video de Lofi con esta estructura JSON EXACTA:

{{
  "titulo_portada": "texto corto para la miniatura",
  "titulo_youtube": "texto largo para el titulo del video",
  "prompt_visual_en": "detailed english prompt for lofi image, atmospheric, no text",
  "prompt_audio_en": "english prompt for lofi music generator, BPM, instruments, mood",
  "copys": {{
    "tiktok": "short catchy copy with hooks and 3-5 hashtags",
    "instagram": "engaging caption with 5-8 hashtags",
    "shorts": "punchy hook-first copy with 3-4 hashtags"
  }},
  "hashtags": ["#lofi", "#chillhop", "..."]
}}

REGLAS ESTRICTAS:
- titulo_portada: MAXIMO {MAX_TITULO_PORTADA} caracteres. Cuenta cada letra y espacio. Frase corta, sin emojis, sin pipes "|". Ejemplo OK: "MIDNIGHT LOFI BEATS" (20 chars). Ejemplo MAL: "2026 Ultimate Mind Relaxing Lofi Beats" (42 pero muy largo).
- titulo_youtube: MAXIMO {MAX_TITULO_YOUTUBE} caracteres. Aqui si puede llevar 1-2 emojis.
- prompt_visual_en: describe escena, iluminacion, estilo, colores. NUNCA menciones texto ni letras.
- prompt_audio_en: incluye BPM concreto, instrumentos, sensacion, genero (lofi/jazzhop/ambient).
- hashtags: exactamente 8, en ingles, sin duplicados.

Verifica el numero de caracteres de titulo_portada antes de responder. Si se pasa, acortalo."""


def parsear_json_llm(texto: str) -> dict[str, Any]:
    limpio = texto.strip()
    limpio = re.sub(r"^```(?:json)?\s*", "", limpio)
    limpio = re.sub(r"\s*```$", "", limpio)

    inicio = limpio.find("{")
    fin = limpio.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        limpio = limpio[inicio:fin + 1]

    try:
        return json.loads(limpio)
    except json.JSONDecodeError as exc:
        log.error("JSON invalido del LLM: %s", limpio[:400])
        raise RuntimeError(f"El LLM no devolvio JSON valido: {exc}") from exc


def _validar_pack(pack: dict[str, Any]) -> dict[str, Any]:
    """Fuerza los limites. Si el LLM se paso, trunca."""
    tp = (pack.get("titulo_portada") or "").strip()
    ty = (pack.get("titulo_youtube") or "").strip()

    if len(tp) > MAX_TITULO_PORTADA:
        log.warning("titulo_portada %d chars, truncando", len(tp))
        tp = tp[:MAX_TITULO_PORTADA].rstrip()

    if len(ty) > MAX_TITULO_YOUTUBE:
        log.warning("titulo_youtube %d chars, truncando", len(ty))
        ty = ty[:MAX_TITULO_YOUTUBE].rstrip()

    pack["titulo_portada"] = tp
    pack["titulo_youtube"] = ty

    log.info("titulo_portada (%d chars): %s", len(tp), tp)
    log.info("titulo_youtube (%d chars): %s", len(ty), ty)
    return pack


def generar_pack(videos: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    if videos is None:
        videos = cargar_top_titulos()

    if not videos:
        raise RuntimeError("No hay videos para analizar.")

    prompt = construir_prompt(videos)
    log.info("Enviando prompt a LLM (len=%d)", len(prompt))

    respuesta = ask(prompt, system=SYSTEM_PROMPT, temperature=0.8)
    log.info("Respuesta recibida (len=%d), parseando...", len(respuesta))

    pack = parsear_json_llm(respuesta)
    pack = _validar_pack(pack)

    pack["_meta"] = {
        "generado": datetime.now(timezone.utc).isoformat(),
        "fuente": ultimo_json_tendencias().name,
        "videos_analizados": len(videos),
    }
    return pack


def guardar_pack(pack: dict[str, Any]) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ruta = DATA_DIR / f"seo_pack_{ts}.json"
    ruta.write_text(
        json.dumps(pack, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("Pack SEO guardado en %s", ruta)
    return str(ruta)


if __name__ == "__main__":
    log.info("--- Cajon 06: SEO con IA (dos titulos) ---")

    pack = generar_pack()
    ruta = guardar_pack(pack)

    print()
    print("=" * 60)
    print("PACK SEO GENERADO")
    print("=" * 60)
    print(f"PORTADA ({len(pack['titulo_portada'])} chars):")
    print(f"  {pack['titulo_portada']}")
    print()
    print(f"YOUTUBE ({len(pack['titulo_youtube'])} chars):")
    print(f"  {pack['titulo_youtube']}")
    print()
    print("PROMPT VISUAL:")
    print(f"  {pack.get('prompt_visual_en', '')[:180]}...")
    print()
    print("HASHTAGS:")
    print(f"  {' '.join(pack.get('hashtags', []))}")
    print("=" * 60)
    print(f"[OK] Guardado: {ruta}")
