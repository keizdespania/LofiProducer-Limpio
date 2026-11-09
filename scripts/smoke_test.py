#!/usr/bin/env python3
"""Smoke test pre-push: compila .py clave + valida .json + ping endpoints. Aborta si falla."""
import subprocess, sys, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent.parent

CRITICOS = [
    "scripts/dios.py", "scripts/pipeline_encuadre.py", "encuadre_routes.py",
    "web_dashboard.py", "brain/dios_memoria.py", "brain/dios_tools_dinamicas.py",
    "brain/ejecutor_seguro.py", "brain/especialistas.py", "brain/llm_gemini.py",
]
JSONS = [
    "data/agent/video_contract.json", "data/agent/shorts_contract.json",
    "data/agent/ltx_continuidad_contract.json", "config/nichos.json",
]
ENDPOINTS = [
    "http://127.0.0.1:8001/api/dashboard",
    "http://127.0.0.1:8001/api/encuadre/fechas",
    "http://127.0.0.1:8001/api/encuadre/logs/list",
    "http://127.0.0.1:8001/api/cloudflare/stats",
]

fallos = []
# 1. py_compile
for f in CRITICOS:
    p = ROOT / f
    if not p.exists(): fallos.append(f"FALTA {f}"); continue
    try:
        import py_compile
        py_compile.compile(str(p), doraise=True)
    except Exception as e:
        fallos.append(f"COMPILE {f}: {e}")

# 2. JSON parse
for f in JSONS:
    p = ROOT / f
    if not p.exists(): fallos.append(f"FALTA {f}"); continue
    try: json.loads(p.read_text())
    except Exception as e: fallos.append(f"JSON {f}: {e}")

# 3. Endpoints
for url in ENDPOINTS:
    try:
        urllib.request.urlopen(url, timeout=5).read()
    except Exception as e:
        fallos.append(f"HTTP {url}: {e}")

if fallos:
    print(f"❌ SMOKE TEST FALLO ({len(fallos)} errores):")
    for f in fallos: print("  -", f)
    sys.exit(1)
print(f"✅ SMOKE OK ({len(CRITICOS)} py + {len(JSONS)} json + {len(ENDPOINTS)} endpoints)")
