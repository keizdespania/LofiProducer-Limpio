"""
Cajon 07 - Generacion de imagenes con Cloudflare Workers AI (v5).

Modelo: @cf/black-forest-labs/flux-1-schnell
1 sola llamada -> 2 formatos (16:9 y 9:16).
Sanitizador NSFW incluido.
"""

from __future__ import annotations

import base64
import json
import re
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

from core.config import CLOUDFLARE_API_TOKEN, CLOUDFLARE_IMAGE_URL
from core.logger import get_logger


log = get_logger("fases.imagen")

TAMANOS_FINALES = {
    "horizontal": (1280, 720),
    "vertical":   (1080, 1920),
}

MAX_INTENTOS = 4

SANITIZADOR = {
    "bedroom": "cozy room",
    "bed": "sofa",
    "girl": "person",
    "boy": "person",
    "child": "person",
    "children": "people",
    "intimate": "warm",
    "sensual": "calm",
    "naked": "cozy",
    "lingerie": "clothing",
    "bathroom": "washroom",
    "shower": "rainy window",
    "bikini": "swimsuit",
    "underwear": "clothes",
    "breast": "soft",
    "sexy": "elegant",
    "erotic": "artistic",
    "seductive": "warm",
    "massage": "relax",
}


def _data_dir() -> Path:
    from core.config import DATA_DIR
    return DATA_DIR


def _output_dir() -> Path:
    from core.config import OUTPUT_DIR
    return OUTPUT_DIR


def sanitizar_prompt(prompt: str) -> str:
    resultado = prompt
    for palabra, reemplazo in SANITIZADOR.items():
        patron = r"\b" + re.escape(palabra.strip()) + r"\b"
        resultado = re.sub(patron, reemplazo.strip(), resultado, flags=re.IGNORECASE)
    if resultado != prompt:
        log.info("Prompt sanitizado (evita NSFW)")
    return resultado


def ultimo_seo_pack() -> Path:
    packs = sorted(_data_dir().glob("seo_pack_*.json"))
    if not packs:
        raise FileNotFoundError(
            f"No hay seo_pack_*.json en {_data_dir()}. "
            "Ejecuta: python -m fases.seo_ia"
        )
    return packs[-1]


def leer_prompt_visual() -> str:
    path = ultimo_seo_pack()
    log.info("Leyendo prompt visual desde %s", path.name)
    data = json.loads(path.read_text(encoding="utf-8"))
    prompt = data.get("prompt_visual_en", "").strip()
    if not prompt:
        raise RuntimeError(f"El pack {path.name} no contiene prompt_visual_en")
    log.info("Prompt visual (%d chars): %s...", len(prompt), prompt[:80])
    return prompt


def _generar_imagen_cf(prompt: str) -> Image.Image | None:
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"prompt": prompt}

    try:
        r = requests.post(CLOUDFLARE_IMAGE_URL, headers=headers,
                          json=payload, timeout=60)
    except requests.RequestException as e:
        log.warning("  -> error de red: %s", e)
        return None

    if r.status_code >= 400:
        log.warning("  -> HTTP %s: %s", r.status_code, r.text[:200])
        return None

    try:
        data = r.json()
    except json.JSONDecodeError:
        log.warning("  -> respuesta no-JSON")
        return None

    if not data.get("success"):
        err = data.get("errors", [{}])[0].get("message", "?")
        log.warning("  -> error CF: %s", err[:150])
        return None

    b64 = data.get("result", {}).get("image", "")
    if not b64:
        log.warning("  -> sin campo 'image'")
        return None

    try:
        img_bytes = base64.b64decode(b64)
    except Exception as e:
        log.warning("  -> error base64: %s", e)
        return None

    if len(img_bytes) < 10_000:
        log.warning("  -> imagen muy pequena: %d bytes", len(img_bytes))
        return None

    try:
        img = Image.open(BytesIO(img_bytes))
        img.verify()
        img = Image.open(BytesIO(img_bytes))
        log.info("  -> OK %dx%d, %.1f KB",
                 img.size[0], img.size[1], len(img_bytes) / 1024)
        return img.convert("RGB")
    except Exception as e:
        log.warning("  -> imagen invalida: %s", e)
        return None


def generar_imagen(prompt: str) -> Image.Image | None:
    prompt_limpio = sanitizar_prompt(prompt)
    for intento in range(1, MAX_INTENTOS + 1):
        log.info("Intento %d/%d", intento, MAX_INTENTOS)
        img = _generar_imagen_cf(prompt_limpio)
        if img is not None:
            return img
        if intento < MAX_INTENTOS:
            log.info("  esperando 5s antes de reintentar...")
            time.sleep(5)
    return None


def redimensionar_cover(img: Image.Image, ancho: int, alto: int) -> Image.Image:
    img = img.convert("RGB")
    w_src, h_src = img.size
    ratio_dst = ancho / alto
    ratio_src = w_src / h_src

    if ratio_src > ratio_dst:
        nuevo_h = alto
        nuevo_w = int(alto * ratio_src)
    else:
        nuevo_w = ancho
        nuevo_h = int(ancho / ratio_src)

    img = img.resize((nuevo_w, nuevo_h), Image.LANCZOS)
    x0 = (nuevo_w - ancho) // 2
    y0 = (nuevo_h - alto) // 2
    return img.crop((x0, y0, x0 + ancho, y0 + alto))


def generar_bases(prompt: str | None = None) -> dict[str, Path]:
    if prompt is None:
        prompt = leer_prompt_visual()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = _output_dir()
    resultados: dict[str, Path] = {}

    img_base = generar_imagen(prompt)
    if img_base is None:
        raise RuntimeError("Cloudflare no genero imagen tras reintentos.")

    base_path = out_dir / f"portada_base_cuadrada_{ts}.jpg"
    img_base.save(base_path, "JPEG", quality=92, optimize=True)
    log.info("Base cuadrada: %s", base_path.name)

    for nombre, (ancho_fin, alto_fin) in TAMANOS_FINALES.items():
        destino = out_dir / f"portada_base_{nombre}_{ts}.jpg"
        img_crop = redimensionar_cover(img_base, ancho_fin, alto_fin)
        img_crop.save(destino, "JPEG", quality=92, optimize=True)
        log.info("  %s -> %dx%d (%.1f KB)",
                 nombre, ancho_fin, alto_fin,
                 destino.stat().st_size / 1024)
        resultados[nombre] = destino

    return resultados


if __name__ == "__main__":
    from core.channel_manager import set_active_channel

    log.info("--- Cajon 07 v5: imagenes Cloudflare ---")
    set_active_channel(None)
    log.info("DATA_DIR  : %s", _data_dir())
    log.info("OUTPUT_DIR: %s", _output_dir())

    resultados = generar_bases()

    print()
    print("=" * 60)
    print("IMAGENES GENERADAS")
    print("=" * 60)
    for nombre, path in resultados.items():
        print(f"  {nombre:>10}: {path.name}")
    print("=" * 60)
    print(f"[OK] {len(resultados)} imagenes generadas")
