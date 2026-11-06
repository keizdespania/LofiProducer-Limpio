# HANDOFF PRÓXIMA IA (2026-11-06)

## LEE PRIMERO
1. BOOT_PROMPT.md → bloque "SESIÓN 2026-11-06"
2. data/agent/ltx_contract.json v2.1
3. scripts/agente_ltx_kaggle_v6.py
4. scripts/preparar_dataset_ltx.py

## ESTADO
via_c LTX OPERATIVA. Runtime cacheado 1.89GB. ~7min/vídeo. Cuenta 2 preparada sin productor. Pipeline 06:00 intacto.

## TAREAS
1. Tuning steps 20→12
2. Cola automática tras éxito
3. Hook animado pipeline nacional
4. Doblaje XTTS (alta prioridad usuario)
5. LoRA El Encuadre

## NO FUNCIONÓ (no reintentar)
- kaggle kernels output con KGAT → usar /kaggle/input mount
- kernels/output/{slug} path → query params
- cfg_scale top-level LTX → dentro sample_params
- init_image path → data URI base64
