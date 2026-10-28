"""
Cajon 08 - Portadas con paleta clara y oscura.

Paletas:
  oscuro -> degradado negro + texto blanco + contorno negro
  claro  -> degradado blanco + texto azul noche + contorno blanco
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.config import DATA_DIR, FONTS_DIR, OUTPUT_DIR
from core.logger import get_logger


log = get_logger("fases.portada")

FUENTES_PREFERIDAS = [
    "Michroma-Regular.ttf",
    "Orbitron.ttf",
    "BebasNeue-Regular.ttf",
    "Montserrat-ExtraBold.ttf",
    "Poppins-Bold.ttf",
]

TAMANOS = {
    "horizontal": (1280, 720),
    "vertical":   (1080, 1920),
}

LAYOUT = {
    "horizontal": (0.45, 0.60),
    "vertical":   (0.40, 0.12),
}

MARGEN_LATERAL = 60
FUENTE_MAX = 90
FUENTE_MIN = 32
FUENTE_PASO = 2

PALETAS = {
    "oscuro": {
        "texto": (255, 255, 255),
        "contorno": (0, 0, 0),
        "degradado_rgb": (0, 0, 0),
        "degradado_alpha_max": 220,
    },
    "claro": {
        "texto": (10, 37, 64),
        "contorno": (255, 255, 255),
        "degradado_rgb": (255, 255, 255),
        "degradado_alpha_max": 230,
    },
}

RE_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+",
    flags=re.UNICODE,
)


def _ultimo(glob_pat: str) -> Path:
    archivos = sorted(OUTPUT_DIR.glob(glob_pat))
    if not archivos:
        raise FileNotFoundError(f"No hay {glob_pat} en {OUTPUT_DIR}.")
    return archivos[-1]


def _ultimo_pack() -> Path:
    packs = sorted(DATA_DIR.glob("seo_pack_*.json"))
    if not packs:
        raise FileNotFoundError(f"No hay seo_pack_*.json en {DATA_DIR}.")
    return packs[-1]


def titulo_para_mostrar() -> str:
    data = json.loads(_ultimo_pack().read_text(encoding="utf-8"))
    t = data.get("titulo_portada") or (data.get("titulos") or [""])[0]
    if not t:
        raise RuntimeError("El seo_pack no tiene titulo_portada.")
    t_limpio = RE_EMOJI.sub("", t).strip().upper()
    log.info("Titulo para portada (%d chars): %s", len(t_limpio), t_limpio)
    return t_limpio


def ruta_fuente() -> str:
    for nombre in FUENTES_PREFERIDAS:
        ruta = FONTS_DIR / nombre
        if ruta.exists():
            log.info("Fuente: %s", nombre)
            return str(ruta)
    raise FileNotFoundError(f"Ninguna fuente disponible en {FONTS_DIR}.")


def medir_texto(draw: ImageDraw.ImageDraw, texto: str,
                fuente: ImageFont.FreeTypeFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), texto, font=fuente, stroke_width=3)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def envolver_en_lineas(draw: ImageDraw.ImageDraw, texto: str,
                       fuente: ImageFont.FreeTypeFont,
                       ancho_max: int) -> list[str]:
    palabras = texto.split()
    lineas: list[str] = []
    actual = ""
    for palabra in palabras:
        candidata = f"{actual} {palabra}".strip()
        w, _ = medir_texto(draw, candidata, fuente)
        if w <= ancho_max or not actual:
            actual = candidata
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def ajustar_texto(texto: str, ancho_disp: int, alto_disp: int,
                  ruta_ttf: str) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    dummy = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    for tam in range(FUENTE_MAX, FUENTE_MIN - 1, -FUENTE_PASO):
        fuente = ImageFont.truetype(ruta_ttf, tam)
        lineas = envolver_en_lineas(dummy, texto, fuente, ancho_disp)
        interlineado = int(tam * 1.15)
        alto_total = interlineado * len(lineas)
        ancho_max = max(medir_texto(dummy, l, fuente)[0] for l in lineas)

        if ancho_max <= ancho_disp and alto_total <= alto_disp:
            return fuente, lineas

    fuente = ImageFont.truetype(ruta_ttf, FUENTE_MIN)
    return fuente, envolver_en_lineas(dummy, texto, fuente, ancho_disp)


def aplicar_degradado(img: Image.Image, zona: str, alto_pct: float,
                      color_rgb: tuple[int, int, int],
                      alpha_max: int) -> Image.Image:
    """
    Aplica un degradado RGBA correctamente mezclado con la imagen.
    Usa alpha_composite, no composite.
    """
    w, h = img.size
    alto_grad = int(h * alto_pct)

    # 1. Construir capa RGBA con alpha variable
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pixeles = capa.load()

    for y in range(alto_grad):
        if zona == "inferior":
            alpha = int(alpha_max * (y / alto_grad))
            fila_y = h - alto_grad + y
        else:
            alpha = int(alpha_max * (1 - y / alto_grad))
            fila_y = y
        r, g, b = color_rgb
        for x in range(w):
            pixeles[x, fila_y] = (r, g, b, alpha)

    # 2. Convertir base a RGBA y componer
    base_rgba = img.convert("RGBA")
    resultado = Image.alpha_composite(base_rgba, capa)
    return resultado.convert("RGB")


def dibujar_titulo(img: Image.Image, texto: str, formato: str,
                   paleta: dict) -> Image.Image:
    ancho, alto = img.size
    layout = LAYOUT[formato]
    zona_deg = "inferior" if formato == "horizontal" else "superior"

    img = aplicar_degradado(
        img, zona_deg, layout[0],
        paleta["degradado_rgb"], paleta["degradado_alpha_max"]
    )

    ancho_disp = ancho - 2 * MARGEN_LATERAL
    alto_disp = int(alto * 0.35)

    ruta_ttf = ruta_fuente()
    fuente, lineas = ajustar_texto(texto, ancho_disp, alto_disp, ruta_ttf)

    log.info("  Fuente tam=%d, %d lineas", fuente.size, len(lineas))

    draw = ImageDraw.Draw(img)
    interlineado = int(fuente.size * 1.15)
    alto_total = interlineado * len(lineas)

    if formato == "horizontal":
        y_inicio = alto - alto_total - MARGEN_LATERAL
    else:
        y_inicio = MARGEN_LATERAL + 80

    for i, linea in enumerate(lineas):
        w_linea, _ = medir_texto(draw, linea, fuente)
        x = (ancho - w_linea) // 2
        y = y_inicio + i * interlineado
        draw.text(
            (x, y), linea,
            font=fuente,
            fill=paleta["texto"],
            stroke_width=4,
            stroke_fill=paleta["contorno"],
        )

    return img


def generar_portadas(titulo: str | None = None) -> dict[str, Path]:
    if titulo is None:
        titulo = titulo_para_mostrar()

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    resultados: dict[str, Path] = {}

    for formato in ("horizontal", "vertical"):
        base = _ultimo(f"portada_base_{formato}_*.jpg")
        log.info("[%s] Base: %s", formato, base.name)

        for paleta_nombre, paleta in PALETAS.items():
            img = Image.open(base).convert("RGB")
            img = dibujar_titulo(img, titulo, formato, paleta)

            destino = OUTPUT_DIR / (
                f"portada_final_{formato}_{paleta_nombre}_{ts}.jpg"
            )
            img.save(destino, "JPEG", quality=92, optimize=True)
            log.info("  -> %s (%.1f KB)",
                     destino.name, destino.stat().st_size / 1024)
            resultados[f"{formato}_{paleta_nombre}"] = destino

    return resultados


if __name__ == "__main__":
    log.info("--- Cajon 08: portadas claro/oscuro (v2) ---")
    resultados = generar_portadas()

    print()
    print("=" * 60)
    print("PORTADAS GENERADAS")
    print("=" * 60)
    for clave, path in resultados.items():
        print(f"  {clave:>22}: {path.name}")
    print("=" * 60)
    print(f"[OK] {len(resultados)} portadas generadas")
