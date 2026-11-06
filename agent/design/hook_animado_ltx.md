# HOOK ANIMADO LTX — Diseño pipeline 06:00

## Objetivo
1ª escena del vídeo largo: SDXL estático → clip LTX 5s animado.

## Flujo
1. fase2_produccion.py emite hook_ltx_prompt (Sujeto+Movimiento+Cámara+Iluminación)
2. director_arte.py genera imagen base 1344x768
3. Encolar hook_YYYY-MM-DD en ltx_cola_pendiente.json
4. render_robusto.py prepende hook_YYYY-MM-DD.mp4 (fallback SDXL si no existe)

## Contrato
video_frames: 121 (5s), width: 1344, height: 768, steps: 20
RIESGO: OOM T4 → reducir a 1024x576 si peta

## Fases
F1 test aislado (mañana): 1 hook, medir OOM/calidad
F2 integración condicional (fallback estático si falla)
F3 multi-hook escenas 2-3

## No romper
render_robusto.py intacto si hook falla. Cron 06:00 sigue aunque LTX caído.
