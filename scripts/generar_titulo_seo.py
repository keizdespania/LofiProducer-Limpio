#!/usr/bin/env python3
"""generar_titulo_seo.py - Genera títulos SEO únicos con hook + keywords.
Uso: python3 scripts/generar_titulo_seo.py 2026-11-03 [video_largo|short_1|short_2...]
"""
import json, sys
from pathlib import Path

ROOT = Path("/data/data/com.termux/files/home/LofiProducer")
OUT = ROOT / "output" / "encuadre"

# Keywords más buscadas en YouTube (ES) para nicho análisis mediático
KEYWORDS_TOP = [
    "manipulación mediática",
    "sesgo informativo",
    "cómo manipulan los medios",
    "análisis de medios",
    "fake news",
    "desinformación",
    "prensa española",
    "titulares manipulados",
    "framing",
    "propaganda",
]

def _leer_dossier(fecha):
    for f in [f"dossier_{fecha}_enriquecido.json", f"dossier_{fecha}.json"]:
        p = OUT / f
        if p.exists():
            return json.loads(p.read_text())
    return {}

def _leer_produccion(fecha):
    p = OUT / f"produccion_{fecha}.json"
    if not p.exists(): return {}
    return json.loads(p.read_text())

def generar_titulo_video_largo(fecha):
    """Título SEO con hook + keyword para el vídeo largo."""
    d = _leer_dossier(fecha)
    prod = _leer_produccion(fecha)

    titular = d.get("titular_brutal") or d.get("tema_del_dia") or ""
    protagonista = d.get("protagonista") or ""
    villano = d.get("villano") or ""
    imd = d.get("indice_manipulacion_global") or 0

    # Plantillas de hook (rotan según hash del tema)
    hooks = [
        f"Lo que NO te cuentan los medios sobre {protagonista}",
        f"El truco de {villano} que los medios ocultan",
        f"{protagonista}: la manipulación que no ves",
        f"Cómo {villano} manipula la información",
        f"La técnica secreta que usan los medios hoy",
        f"Por qué los medios te mienten sobre {protagonista}",
        f"IMD {imd}/100: el nivel de manipulación de hoy",
        f"El sesgo oculto en los titulares de hoy",
    ]

    # Si tenemos titular, usarlo como base + hook
    if titular and len(titular) > 20:
        base = titular[:60].strip()
        # Hook según IMD
        if imd >= 70:
            return f"🔴 {base} | Manipulación ALTA ({imd}/100)"
        elif imd >= 50:
            return f"⚠️ {base} | Análisis de sesgos"
        else:
            return f"📊 {base} | Análisis mediático"

    # Fallback: hook rotativo
    import hashlib
    idx = int(hashlib.md5(fecha.encode()).hexdigest(), 16) % len(hooks)
    return hooks[idx]

def generar_titulo_short(fecha, tipo, hook_base=""):
    """Título SEO para short. Máx 60 chars (límite YouTube Shorts)."""
    hooks_short = {
        "dato": [
            f"📊 El dato que los medios ocultan",
            f"⚠️ Cuidado con este titular",
            f"El número que no te enseñan",
        ],
        "contradiccion": [
            f"🤔 Te dijeron esto, pero...",
            f"La contradicción que nadie ve",
            f"Mira lo que ocultan",
        ],
        "prediccion": [
            f"🔮 Lo que viene después de esto",
            f"El futuro que no esperas",
            f"Esto va a pasar (y lo saben)",
        ],
        "tutorial": [
            f"🎯 Cómo detectar manipulación en 30s",
            f"El truco para no ser engañado",
            f"Detecta el sesgo en 30 segundos",
        ],
        "cita": [
            f"💣 La frase que lo cambia todo",
            f"Esta cita te va a sorprender",
            f"Lo que dijeron y no debían",
        ],
        "default": [
            f"👀 Lo que no quieren que veas",
            f"El análisis que necesitas",
            f"Manipulación mediática: el caso de hoy",
        ],
    }
    import hashlib
    opciones = hooks_short.get(tipo, hooks_short["default"])
    idx = int(hashlib.md5(f"{fecha}{tipo}".encode()).hexdigest(), 16) % len(opciones)
    titulo = opciones[idx]
    # Añadir keyword si cabe
    if len(titulo) < 40:
        titulo += " #ElEncuadre"
    return titulo[:100]

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else "2026-11-03"
    tipo = sys.argv[2] if len(sys.argv) > 2 else "video_largo"

    if tipo == "video_largo":
        t = generar_titulo_video_largo(fecha)
        print(f"📺 Vídeo largo ({len(t)} chars):")
        print(f"   {t}")
    elif tipo.startswith("short_"):
        # Leer tipo del short de producción
        prod = _leer_produccion(fecha)
        idx = int(tipo.replace("short_", "")) - 1
        shorts = prod.get("shorts_finales", [])
        if idx < len(shorts):
            t_tipo = shorts[idx].get("tipo", "default")
            t = generar_titulo_short(fecha, t_tipo)
            print(f"📱 {tipo} (tipo={t_tipo}, {len(t)} chars):")
            print(f"   {t}")
        else:
            print(f"❌ {tipo} no existe en producción")
    else:
        print("Uso: python3 scripts/generar_titulo_seo.py 2026-11-03 [video_largo|short_1|short_2|short_3|short_4]")
