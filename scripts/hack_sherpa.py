#!/usr/bin/env python3
"""hack_sherpa.py — Extrae params de Sherpa-ONNX via introspección (sin ejecutar TTS)."""
import inspect, json, sys
from pathlib import Path

try:
    import sherpa_onnx
except ImportError:
    print("ERROR: sherpa_onnx no importable"); sys.exit(1)

OUT = Path.home() / "LofiProducer/data/agent/sherpa_params.json"

# Clases de configuración relevantes para TTS offline
CLASSES = [
    "OfflineTtsConfig",
    "OfflineTtsModelConfig",
    "OfflineTtsVitsModelConfig",
    "OfflineTtsMatchaModelConfig",
    "OfflineTtsKokoroModelConfig",
    "GenerationConfig",   # config de generación (speed, sid, etc.)
]

def extract_signature(cls):
    """Extrae params de una clase pybind11 usando __init__ o __doc__."""
    params = {}
    # Intento 1: inspect.signature
    try:
        sig = inspect.signature(cls)
        for name, p in sig.parameters.items():
            params[name] = {
                "default": str(p.default) if p.default is not inspect.Parameter.empty else "REQUIRED",
                "type": str(p.annotation) if p.annotation is not inspect.Parameter.empty else "?"
            }
        if params:
            return params
    except (ValueError, TypeError):
        pass
    # Intento 2: parsear __doc__ (pybind11 suele poner la firma ahí)
    doc = inspect.getdoc(cls) or ""
    for line in doc.splitlines():
        line = line.strip()
        if "(" in line and ")" in line:
            # heurística simple: extrae nombres de params de la firma en doc
            inner = line.split("(", 1)[1].split(")", 1)[0]
            for token in inner.split(","):
                token = token.strip()
                if "=" in token:
                    k, v = token.split("=", 1)
                    params[k.strip()] = {"default": v.strip(), "type": "?"}
    return params

def main():
    out = {"sherpa_onnx_version": getattr(sherpa_onnx, "__version__", "?"),
           "classes": {}}
    for name in CLASSES:
        cls = getattr(sherpa_onnx, name, None)
        if cls is None:
            out["classes"][name] = {"available": False}
            continue
        out["classes"][name] = {
            "available": True,
            "params": extract_signature(cls),
            "doc": (inspect.getdoc(cls) or "")[:500],
        }
    total = sum(len(v.get("params", {})) for v in out["classes"].values() if v.get("available"))
    out["_total_params"] = total
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    for k, v in out["classes"].items():
        n = len(v.get("params", {})) if v.get("available") else 0
        print(f"  {k:32} {'OK' if v.get('available') else 'NO DISPONIBLE':15} params={n}")
    print(f"  TOTAL: {total}")

if __name__ == "__main__":
    main()
