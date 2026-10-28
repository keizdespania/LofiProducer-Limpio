#!/usr/bin/env python3
"""hack_pixabay.py — Extrae params de Pixabay desde tus scripts + contrato oficial."""
import ast, json, re
from pathlib import Path

ROOT = Path.home() / "LofiProducer"
OUT  = ROOT / "data/agent/pixabay_contract.json"

# Scripts donde puede vivir la lógica de Pixabay
CANDIDATOS = [
    "scripts/generar_video_rapido.py",
    "scripts/descargar_video_auto.py",
    "scripts/descargar_video_exacto.py",
    "scripts/generar_video.py",
]

PARAMS_OFICIALES = {
    "key": {"type":"string","obligatorio":True,"nota":"API key gratis en pixabay.com/api/docs"},
    "q": {"type":"string","nota":"query; máx 100 chars"},
    "lang": {"type":"string","valores":["es","en","pt","it","fr","de","ja","ko","ru"],"default":"en"},
    "video_type": {"type":"enum","valores":["all","film","animation"],"default":"all"},
    "category": {"type":"enum","valores":["backgrounds","fashion","nature","science","education","feelings","health","people","religion","places","animals","industry","computer","food","sports","transportation","travel","buildings","business","music"],"nota":"solo videos"},
    "min_width": {"type":"int","default":0},
    "min_height": {"type":"int","default":0},
    "orientation": {"type":"enum","valores":["all","horizontal","vertical"],"default":"all"},
    "editors_choice": {"type":"bool","default":False},
    "safesearch": {"type":"bool","default":False},
    "order": {"type":"enum","valores":["popular","latest"],"default":"popular"},
    "page": {"type":"int","default":1},
    "per_page": {"type":"int","min":3,"max":200,"default":20},
}

REGLAS = [
    "Endpoint videos: https://pixabay.com/api/videos/ | imágenes: https://pixabay.com/api/",
    "NO usar endpoints no documentados: /api/videos/ y /api/ son los únicos.",
    "per_page máx 200; para 1h de lofi necesitas ~60 clips -> 3 páginas de 20.",
    "orientation=vertical OBLIGATORIO para Shorts/TikTok/Reels.",
    "min_duration NO existe en la API oficial: filtrar por duración después de descargar.",
    "Cachear la API key en .env como PIXABAY_KEY; NO hardcodearla.",
    "Límite free: 100 req/min. Añadir sleep 1s entre páginas.",
    "Cloudflare puede bloquear curl normal: usar curl_cffi con impersonate='chrome' (ya lo haces).",
    "Los clips vienen en múltiples resoluciones: elegir 'large' (1920x1080) o 'medium' (1280x720).",
    "NO pedir más de 500 resultados por búsqueda (page*per_page <= 500).",
]

def extraer(tree, script_rel):
    hallazgos = {"script": script_rel, "urls_pixabay": [], "funciones": [], "params_usados": set(), "headers": []}
    for node in ast.walk(tree):
        # URLs con pixabay
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if "pixabay.com" in s:
                hallazgos["urls_pixabay"].append(s)
        # funciones
        if isinstance(node, ast.FunctionDef):
            hallazgos["funciones"].append(node.name)
        # dicts con keys tipo params
        if isinstance(node, ast.Dict):
            for k in node.keys:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    if k.value in PARAMS_OFICIALES:
                        hallazgos["params_usados"].add(k.value)
        # headers con impersonate / User-Agent
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "impersonate" in node.value or "User-Agent" in node.value or "curl_cffi" in node.value:
                hallazgos["headers"].append(node.value[:80])
    hallazgos["params_usados"] = sorted(hallazgos["params_usados"])
    hallazgos["urls_pixabay"] = list(dict.fromkeys(hallazgos["urls_pixabay"]))
    hallazgos["headers"] = list(dict.fromkeys(hallazgos["headers"]))
    return hallazgos

def main():
    contrato = {
        "motor": "Pixabay API",
        "endpoints": {
            "videos": "https://pixabay.com/api/videos/",
            "imagenes": "https://pixabay.com/api/",
        },
        "auth": {"tipo":"api_key_query", "env_var":"PIXABAY_KEY", "donde":"pixabay.com/api/docs"},
        "params_oficiales": PARAMS_OFICIALES,
        "limites": {"req_min": 100, "req_hora": 5000, "per_page_max": 200, "resultados_max": 500},
        "anti_cloudflare": {
            "libreria": "curl_cffi",
            "impersonate": "chrome",
            "nota": "curl normal puede recibir 403; curl_cffi impersona TLS de Chrome",
        },
        "reglas_anti_alucinacion": REGLAS,
        "scripts_analizados": [],
    }

    for rel in CANDIDATOS:
        p = ROOT / rel
        if not p.exists(): continue
        try:
            tree = ast.parse(p.read_text(errors="ignore"))
            h = extraer(tree, rel)
            if h["urls_pixabay"] or h["params_usados"] or "pixabay" in p.read_text(errors="ignore").lower():
                contrato["scripts_analizados"].append(h)
        except Exception as e:
            contrato["scripts_analizados"].append({"script": rel, "error": str(e)})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Endpoints: videos + imagenes")
    print(f"  Scripts con Pixabay: {len(contrato['scripts_analizados'])}")
    for s in contrato["scripts_analizados"]:
        if "error" in s:
            print(f"    [{s['script']}] ERROR: {s['error']}")
        else:
            print(f"    [{s['script']}] urls={len(s['urls_pixabay'])} params={s['params_usados']}")
    print(f"  Límite free: 100 req/min | per_page máx 200")

if __name__ == "__main__":
    main()
