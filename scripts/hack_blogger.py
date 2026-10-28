#!/usr/bin/env python3
"""hack_blogger.py — Extrae params de publicar_blogger.py + contrato oficial."""
import ast, json
from pathlib import Path

ROOT = Path.home() / "LofiProducer"
SCRIPT = ROOT / "scripts/publicar_blogger.py"
OUT = ROOT / "data/agent/blogger_contract.json"

def extraer_funciones(tree):
    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            defaults = [ast.unparse(d) for d in node.args.defaults]
            funcs[node.name] = {"args": args, "defaults": defaults}
    return funcs

def extraer_strings(tree):
    urls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if "blogger.googleapis.com" in s or "blogger/v3" in s:
                urls.append(s)
    return list(dict.fromkeys(urls))

def main():
    contrato = {
        "motor": "Blogger API v3",
        "endpoint": "POST https://www.googleapis.com/blogger/v3/blogs/{blogId}/posts",
        "scope_oauth": "https://www.googleapis.com/auth/blogger",
        "parametros_url": {
            "blogId": {"type": "string", "obligatorio": True, "nota": "ID del blog"},
            "isDraft": {"type": "boolean", "opcional": True, "nota": "true=borrador, false=publicar"},
        },
        "cuerpo_posts_resource": {
            "title": {"type": "string", "obligatorio": True},
            "content": {"type": "string (HTML)", "obligatorio": True},
            "labels": {"type": "array[string]", "opcional": True, "nota": "etiquetas del post"},
            "published": {"type": "datetime ISO8601", "opcional": True, "nota": "si se omite, usa la fecha actual"},
        },
        "limites_criticos": {
            "cuota_api_nominal": "10,000 requests/día",
            "limite_real_posts": "100 posts/día por blog (independiente de la cuota)",
            "anti_spam_blog_nuevo": "Publicar en ráfaga puede bloquear posts.insert con 403 por 7-14 días",
            "recomendacion_blog_nuevo": "1-2 posts/día, espaciados, con actividad manual previa",
        },
        "reglas_anti_alucinacion": [
            "NO asumir que la cuota de 10,000 permite 10,000 posts: el límite real es 100/día/blog.",
            "En blogs nuevos: empezar con 1-2 posts/día; un bloqueo anti-spam dura 7-14 días.",
            "isDraft=true para pruebas; false solo cuando el contenido esté validado.",
            "labels es array de strings (nombres), NO IDs como en WordPress.",
            "El scope es https://www.googleapis.com/auth/blogger (no readonly).",
            "Si recibes 403 PERMISSION_DENIED, NO reintentar en bucle: puede ser bloqueo anti-spam.",
        ],
    }

    if SCRIPT.exists():
        tree = ast.parse(SCRIPT.read_text(errors="ignore"))
        contrato["script_local"] = {
            "path": str(SCRIPT),
            "funciones": extraer_funciones(tree),
            "urls_blogger_detectadas": extraer_strings(tree),
        }
    else:
        contrato["script_local"] = {"existe": False, "nota": "script no encontrado"}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contrato, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  Endpoint: {contrato['endpoint']}")
    print(f"  Scope: {contrato['scope_oauth']}")
    if SCRIPT.exists():
        print(f"  Funciones en tu script: {list(contrato['script_local']['funciones'].keys())}")
        print(f"  URLs Blogger: {contrato['script_local']['urls_blogger_detectadas']}")
    else:
        print(f"  Script local: NO encontrado")

if __name__ == "__main__":
    main()
