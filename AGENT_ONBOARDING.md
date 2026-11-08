# ONBOARDING IA — LOFIPRODUCER
## FILOSOFIA
"El ecosistema crece por config, no por codigo". Diagnostica con logs. Lee contratos ANTES de tocar.

## ARQUITECTURA
- Pipeline 06:00: medios -> agentes -> SDXL -> voz -> YouTube.
- LTX 2.3 Kaggle T4: /sdcpp/v1/vid_gen puerto 1234.
- Top-1 Cinematic: 3 segmentos 49f + xfade + eq = 6s de cine.

## VISION
Mes 3: 10 canales. Mes 6: 100 canales multi-idioma.

## REGLAS DE ORO
1. NUNCA hardcodear tokens GitHub (env vars).
2. LEER ltx_continuidad_contract.json v3.0 antes de tocar.
3. Definir IMGS y BIBLIO_RAW en templates.
4. python3 -u en Termux.
5. Si no esta en contrato, pregunta al usuario.
