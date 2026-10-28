#!/usr/bin/env python3
"""hack_pixabay_contract.py — Contrato Pixabay v3 con presets + validador."""
import json, pathlib

OUT = pathlib.Path.home() / "LofiProducer/data/agent/pixabay_contract.json"

PRESETS = {
    "ia_news": {"desc": "B-roll para noticias IA", "params": {"q": "technology artificial intelligence robot", "video_type": "film", "category": "science", "order": "popular", "per_page": 3}},
    "lofi": {"desc": "Fondo lofi chill", "params": {"q": "coffee rain cozy room", "video_type": "film", "category": "nature", "order": "popular", "per_page": 3}},
    "finanzas": {"desc": "B-roll finanzas", "params": {"q": "money stock market business", "video_type": "film", "category": "business", "order": "popular", "per_page": 3}},
    "boe": {"desc": "Fondo legal/BOE", "params": {"q": "documents law spain office", "video_type": "film", "category": "people", "order": "popular", "per_page": 3}},
    "b_roll_generico": {"desc": "B-roll abstracto", "params": {"q": "abstract background loop", "video_type": "film", "order": "latest", "per_page": 3}},
    "cinematic_drone": {"desc": "Tomas aéreas cinematográficas", "params": {"q": "drone aerial mountains", "video_type": "film", "category": "nature", "order": "popular", "per_page": 3}}
}

VALIDADOR = {"reglas": [
    {"campo": "q", "min_chars": 3, "max_chars": 100, "nota": "Obligatorio. Si vacío, devuelve todo"},
    {"campo": "lang", "valores": ["es","en","pt","fr","de","it","ja","ko","zh"], "default": "es"},
    {"campo": "video_type", "valores": ["all","film","animation"], "default": "film"},
    {"campo": "category", "valores": ["backgrounds","fashion","nature","science","education","feelings","health","people","religion","places","animals","industry","computer","food","sports","transportation","travel","buildings","business","music"], "default": "nature"},
    {"campo": "order", "valores": ["popular","latest"], "default": "popular"},
    {"campo": "per_page", "min": 3, "max": 200, "default": 3},
    {"campo": "page", "min": 1, "max": 100, "default": 1},
    {"campo": "safesearch", "valores": ["true","false"], "default": "true", "nota": "SIEMPRE true"}
]}

ERRORES = [
    {"code": 400, "fix": "Parámetros inválidos (q, category, video_type). Revisar validador"},
    {"code": 401, "fix": "API key inválida. Revisar PIXABAY_API_KEY en .env"},
    {"code": 403, "fix": "API key sin permisos o cuenta suspendida"},
    {"code": 429, "fix": "Rate limit excedido (100 req/min). Esperar 60s"},
    {"code": "empty_results", "fix": "0 hits. Reducir palabras en q o cambiar category"}
]

REGLAS = [
    "Límite free: 100 req/min, 5000 req/hora. Más que suficiente para 3-4 vídeos/día",
    "per_page máx 200 por request. El script usa 3 (bien, eficiente)",
    "Pixabay NO permite redistribuir vídeos 'as-is' (crear banco de clips y venderlos)",
    "SÍ permite usar como B-roll en vídeo transformado (nuestro caso: noticias, lofi)",
    "Atribución recomendada (aunque no obligatoria desde 2019)",
    "safesearch=true SIEMPRE (evitar contenido NSFW involuntario)",
    "video_type=film para clips reales; animation para dibujos animados",
    "order=popular para calidad; latest para frescura",
    "q debe ser 3-100 chars. Palabras en inglés dan mejores resultados",
    "El campo 'videos.medium.url' es el que devuelve MP4 listo para FFmpeg",
    "Para lofi: buscar 'cozy rain coffee' da mejor mood que 'lofi music'",
    "Cloudflare puede bloquear curl_cffi. Usar 'impersonate=chrome' (ya implementado)"
]

EJEMPLOS = [
    {"input": "B-roll para noticia IA", "preset": "ia_news", "params": {"q": "technology ai robot", "video_type": "film"}},
    {"input": "fondo lofi con lluvia", "preset": "lofi", "params": {"q": "rain coffee window", "video_type": "film"}},
    {"input": "tomas aéreas", "preset": "cinematic_drone", "params": {"q": "drone mountain sunset", "video_type": "film"}}
]

def main():
    c = {
        "motor": "Pixabay API v3",
        "version": "v3",
        "endpoint_videos": "GET https://pixabay.com/api/videos/",
        "endpoint_imagenes": "GET https://pixabay.com/api/",
        "auth": "key en query string (?key=XXX)",
        "cuota_por_min": 100,
        "cuota_por_hora": 5000,
        "per_page_max": 200,
        "licencia": "Pixabay License (uso comercial OK, redistribuir as-is NO)",
        "requiere_atribucion": False,
        "presets": PRESETS,
        "validador": VALIDADOR,
        "errores": ERRORES,
        "reglas_anti_alucinacion": REGLAS,
        "ejemplos": EJEMPLOS,
        "script_local": "scripts/generar_video_rapido.py",
        "stats": {"presets": len(PRESETS), "reglas": len(REGLAS), "errores": len(ERRORES)}
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(c, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Presets: {len(PRESETS)} | Validador: {len(VALIDADOR['reglas'])} | Errores: {len(ERRORES)} | Reglas: {len(REGLAS)}")

if __name__ == "__main__":
    main()
