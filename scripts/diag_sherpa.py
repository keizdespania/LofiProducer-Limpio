#!/usr/bin/env python3
"""diag_sherpa.py — Muestra __doc__ y atributos reales de las clases pybind11."""
import inspect, sherpa_onnx

CLASSES = ["OfflineTtsConfig","OfflineTtsModelConfig","OfflineTtsVitsModelConfig",
           "OfflineTtsMatchaModelConfig","OfflineTtsKokoroModelConfig","GenerationConfig"]

for name in CLASSES:
    cls = getattr(sherpa_onnx, name, None)
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    if cls is None:
        print("  NO EXISTE en esta version"); continue
    doc = inspect.getdoc(cls) or "(sin doc)"
    print(f"--- __doc__ (primeras 30 lineas) ---")
    for line in doc.splitlines()[:30]:
        print(f"  {line}")
    attrs = [a for a in dir(cls) if not a.startswith("__")]
    print(f"--- atributos publicos ({len(attrs)}) ---")
    print(f"  {attrs}")
    try:
        print(f"--- __init__ signature ---")
        print(f"  {inspect.signature(cls.__init__)}")
    except Exception as e:
        print(f"  ERROR: {e}")
