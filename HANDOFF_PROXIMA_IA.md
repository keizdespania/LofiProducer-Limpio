# HANDOFF — SOMOS EL ENCUADRE · 2026-11-05

## ESTADO EN 30 SEGUNDOS
Pipeline visual rediseñado. SDXL genera 72 fotos cinematográficas, shorts con 3 escenas, voz de Álvaro con pitch grave y pausas 0.75s. Wan 2.2 Turbo configurado como agente paralelo (I2V) en Kaggle. Falló primera prueba por repo Turbo inexistente. Corregido a yetter-ai/Wan2.2-TI2V-5B-Turbo-Diffusers.

## COMMITS RECIENTES
- 3c1c813 feat(wan): factory con Turbo (4 steps) + batch + prompt negativo
- 79120f4 docs(contracts): actualizar contratos, BOOT y HANDOFF
- 4d7f849 feat(voz): narrador Top 1 - pausa 0.75s y tono grave

## FUNCIONA
- Pipeline diario (SDXL + Groq 4 + voz + podcast + web).
- Shorts con 3 escenas narrativas (9:16).
- Token GitHub Fine-grained verificado.
- Contrato Wan 2.2 con presets y errores conocidos.

## PENDIENTE
- Wan Factory: relanzar con repo yetter-ai.
- Blogger: pausado hasta 11/11.
- Batch Wan: probar 20-30 imagenes/kernel.

## PRIMEROS PASOS
cd ~/LofiProducer
python3 scripts/agente_wan_encuadre.py lanzar
tail -100 data/logs/pipeline.log | grep -E 'Director|arte|OK|Error'

## REGLAS CRITICAS
- #56: SDXL no entiende metaforas. Describe objetos fisicos.
- #57: SDXL no sabe escribir. Prohibido titulares.
- #58: Groq 4 directo para prompts visuales.
- #59: 3 escenas por short.
- #60: Wan 2.2 Turbo: yetter-ai/Wan2.2-TI2V-5B-Turbo-Diffusers (bfloat16, 4 pasos).

## NO ROMPER
- producir_fase2() (clasico).
- Cron 06:00.
- web/site/ (Cloudflare).
