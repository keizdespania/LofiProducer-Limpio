#!/usr/bin/env python3
"""kaggle_cleanup.py — Detiene kernels huérfanos del proyecto."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from renderizar_en_kaggle import limpiar_kernels_huerfanos
    limpiar_kernels_huerfanos()
except Exception as e:
    print(f"[cleanup] ERROR: {e}", flush=True)
    sys.exit(1)
