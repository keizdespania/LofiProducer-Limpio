# HANDOFF 2026-11-08
## LEER PRIMERO
1. AGENT_ONBOARDING.md
2. data/agent/ltx_continuidad_contract.json (v3.0)
3. scripts/agente_ltx_biblioteca.py

## DIAGNOSTICO
python3 -c "import sys; sys.path.insert(0,'scripts'); import kaggle_bearer as kb; print(kb.estado_kernel('keizproductions/ltx-biblioteca-v1-lote4').get('status'))"

## TAREAS
1. Verificar 40 MP4s en output/videos/biblioteca/.
2. Integrar shorts 30s (5 clips de 6s).
3. Hooks 8s (4 segmentos).
4. XTTS multi-idioma.

## NO ROMPER
pipeline_encuadre.py | ltx_continuidad_contract.json | tokens (env vars)
