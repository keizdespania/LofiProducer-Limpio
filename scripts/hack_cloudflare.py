#!/usr/bin/env python3
"""hack_cloudflare.py — Extrae params de generar_imagen.py + config Cloudflare."""
import ast, json, os, re
from pathlib import Path

ROOT = Path.home() / "LofiProducer"
SCRIPT = ROOT / "scripts/generar_imagen.py"
ENV = ROOT / ".env"
OUT = ROOT / "data/agent/cloudflare_contract.json"

def extract_dict_assignments(tree):
    """Busca asignaciones de dicts literales (payloads) en el AST."""
    dicts = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    keys = []
                    for k in node.value.keys:
                        if isinstance(k, ast.Constant):
                            keys.append(k.value)
                    if keys:
                        dicts[target.id] = keys
    return dicts

def extract_function_params(tree):
    """Extrae funciones y sus parámetros por defecto."""
    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = []
            defaults = node.args.defaults
            arg_names = [a.arg for a in node.args.args]
            offset = len(arg_names) - len(defaults)
            for i, a in enumerate(arg_names):
                d = ast.unparse(defaults[i - offset]) if i >= offset else "REQUIRED"
                args.append({"name": a, "default": d})
            funcs[node.name] = args
    return funcs

def extract_strings(tree):
    """Strings largos: URLs, model IDs, prompts de sistema."""
    strings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) > 15 and ("http" in s or "@cf/" in s or "stable-diffusion" in s.lower() or "sdxl" in s.lower()):
                strings.append(s)
    return list(set(strings))

def env_keys():
    if not ENV.exists(): return []
    return [l.split("=",1)[0].strip() for l in ENV.read_text(errors="ignore").splitlines()
            if l.strip() and not l.startswith("#") and "=" in l]

def main():
    if not SCRIPT.exists():
        print(f"ERROR: {SCRIPT} no existe"); return
    tree = ast.parse(SCRIPT.read_text())
    out = {
        "script": str(SCRIPT),
        "payloads_detectados": extract_dict_assignments(tree),
        "funciones": extract_function_params(tree),
        "urls_y_modelos": extract_strings(tree),
        "env_keys_cloudflare": [k for k in env_keys() if "CLOUD" in k.upper() or "CF_" in k.upper()],
        "api_oficial_sdxl": {
            "endpoint": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0",
            "modelo": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
            "params_aceptados": {
                "prompt": {"type":"string","obligatorio":True,"max_chars":2048},
                "negative_prompt": {"type":"string","default":"","nota":"lo que NO quieres ver"},
                "num_steps": {"type":"int","default":20,"rango":[1,50],"nota":"mas pasos = mas calidad pero mas lento"},
                "guidance": {"type":"float","default":7.5,"rango":[1,20],"nota":"que tanto sigue el prompt"},
                "width": {"type":"int","default":1024,"rango":[256,2048],"nota":"debe ser multiplo de 8"},
                "height": {"type":"int","default":1024,"rango":[256,2048],"nota":"debe ser multiplo de 8"},
                "seed": {"type":"int","default":-1,"nota":"-1 aleatorio; fijo para reproducibilidad"},
            },
            "respuesta": "image/png binario (no JSON). Guardar con .png",
        },
        "reglas_anti_alucinacion": [
            "width y height DEBEN ser multiplos de 8; si no, la API falla",
            "prompt max 2048 chars; para lofi: 'cozy room, warm light, lofi aesthetic, 4k'",
            "negative_prompt SIEMPRE incluir: 'blurry, low quality, distorted, text, watermark'",
            "num_steps 20 es el default; 30+ mejora poco y tarda mas",
            "guidance 7.5 default; >12 suele quemar la imagen (over-saturated)",
            "La API devuelve PNG binario, NO JSON. Usar response.content, no .json()",
            "Para miniaturas YouTube: 1280x720. Para Shorts: 720x1280",
            "Para portadas lofi: 1024x1024 o 1280x720",
            "seed fijo = reproducible; seed -1 = aleatorio (cada llamada cuesta lo mismo)",
            "NO inventar nombres de modelo: solo '@cf/stabilityai/stable-diffusion-xl-base-1.0'",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  payloads detectados: {list(out['payloads_detectados'].keys())}")
    print(f"  funciones: {list(out['funciones'].keys())}")
    print(f"  urls/modelos: {len(out['urls_y_modelos'])}")
    print(f"  env_keys Cloudflare: {out['env_keys_cloudflare']}")

if __name__ == "__main__":
    main()
