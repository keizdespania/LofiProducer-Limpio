#!/usr/bin/env python3
"""hack_youtube.py — Contrato YouTube v3 (compacto)."""
import ast, json, pathlib

ROOT = pathlib.Path.home() / "LofiProducer"
SCRIPT = ROOT / "scripts/subir_youtube.py"
OUT = ROOT / "data" / "agent" / "youtube_contract.json"

PRESETS = {
    "draft_privado": {"desc": "Borrador privado", "params": {"privacyStatus": "private", "notifySubscribers": False, "categoryId": "22"}},
    "publicar_ahora": {"desc": "Publicar (requiere auditoría)", "params": {"privacyStatus": "public", "notifySubscribers": True, "categoryId": "22"}},
    "programar": {"desc": "Programar con publishAt", "params": {"privacyStatus": "private", "publishAt": "ISO8601", "categoryId": "22"}},
    "shorts_vertical": {"desc": "Shorts <60s 9:16", "params": {"privacyStatus": "public", "categoryId": "24", "duracion_max": 60}},
    "lofi_music": {"desc": "Música lofi", "params": {"privacyStatus": "public", "categoryId": "10"}},
    "podcast": {"desc": "Podcast", "params": {"privacyStatus": "public", "categoryId": "22", "defaultLanguage": "es"}}
}

VALIDADOR = {"reglas": [
    {"campo": "title", "min": 1, "max": 100},
    {"campo": "description", "min": 0, "max": 5000},
    {"campo": "tags_total_chars", "min": 0, "max": 500},
    {"campo": "categoryId", "valores": ["10","17","20","22","23","24","25","26","27","28"], "default": "22"},
    {"campo": "privacyStatus", "valores": ["private","unlisted","public"], "default": "private"},
    {"campo": "defaultLanguage", "valores": ["es","en","pt","fr","de","it"], "default": "es"}
]}

COSTOS = {"videos.insert": 1600, "thumbnails.set": 50, "playlistItems.insert": 50, "videos.update": 50, "videos.list": 1, "captions.insert": 400, "search.list": 100}

ERRORES = [
    {"code": 403, "reason": "quotaExceeded", "fix": "Esperar 24h o rotar proyecto Google Cloud"},
    {"code": 400, "reason": "uploadLimitExceeded", "fix": "Máx 6/día. Rotar proyecto"},
    {"code": 400, "reason": "invalidTitle", "fix": "1-100 chars, sin < >"},
    {"code": 400, "reason": "invalidTags", "fix": "Suma <= 500 chars"},
    {"code": 403, "reason": "forbidden", "fix": "Sin auditoría Google, todo privado"}
]

REGLAS = [
    "Costo 1600 units/upload. 10000/día = 6 uploads max",
    "privacyStatus='private' por defecto hasta auditar Google",
    "Sin auditoría Google: todos los uploads salen privados",
    "selfDeclaredMadeForKids=false SIEMPRE",
    "notifySubscribers=false en masivo, true en estrenos",
    "100 canales = 17 proyectos Google Cloud",
    "Thumbnail 50 units extra (pero obligatorio para CTR)",
    "Shorts: <60s, 9:16, NO como vídeo largo",
    "categoryId coherente (lofi=10, news=25, edu=27)",
    "defaultLanguage SIEMPRE (SEO internacional)"
]

EJEMPLOS = [
    {"input": "sube en privado", "preset": "draft_privado"},
    {"input": "sube short", "preset": "shorts_vertical"},
    {"input": "programa lofi mañana", "preset": "programar"}
]

def extraer(tree):
    funcs = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef):
            funcs[n.name] = {"args": [a.arg for a in n.args.args], "kwonly": [a.arg for a in n.args.kwonlyargs]}
    return funcs

def main():
    c = {"motor": "YouTube Data API v3", "version": "v3",
         "endpoint_upload": "POST https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
         "cuota_diaria": 10000, "cuota_reset": "Medianoche PT",
         "costos": COSTOS, "uploads_max_dia": 6,
         "proyectos_para_100_canales": 17,
         "scopes": ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly", "https://www.googleapis.com/auth/youtube.force-ssl"],
         "presets": PRESETS, "validador": VALIDADOR, "errores": ERRORES,
         "reglas_anti_alucinacion": REGLAS, "ejemplos": EJEMPLOS,
         "stats": {"presets": len(PRESETS), "reglas": len(REGLAS), "errores": len(ERRORES)}}
    if SCRIPT.exists():
        c["script_local"] = {"path": str(SCRIPT), "funciones": extraer(ast.parse(SCRIPT.read_text()))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(c, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Presets: {len(PRESETS)} | Validador: {len(VALIDADOR['reglas'])} | Errores: {len(ERRORES)} | Reglas: {len(REGLAS)}")

if __name__ == "__main__":
    main()
