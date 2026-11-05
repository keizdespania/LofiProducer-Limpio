# HANDOFF — SOMOS EL ENCUADRE · 2026-11-05

## ESTADO EN 30 SEGUNDOS
**Pipeline rediseñado a nivel visual.** Las imágenes cuentan la historia. SDXL hackeado usando un Director de Fotografía (Groq 4) que traduce a inglés literal. Shorts divididos en 3 escenas. Telegram envía métricas.

## COMMITS RECIENTES
- 47fcbf6 Prompt Maestro actualizado a literales
- 443c0d0 Conectar Director de Fotografía a todas las fábricas
- 178f4f0 Fusionar director_arte + segmentar_imagenes

## EL NUEVO FLUJO VISUAL
1. voz_edge.py genera el .ass.
2. director_arte.py lee el ASS, crea 72 segmentos y llama a director_fotografia.py.
3. director_fotografia.py llama a Groq 4 pidiendo descripciones literales.
4. SDXL genera las 72 imágenes sin texto alienígena.
5. render_robusto.py monta el vídeo.

## PENDIENTE
- Blogger: Pausado por baneo (reactivar 11/11).
- YouTube: Verificar subida con los títulos correctos (SEO del top16).
- Web: Generar los 2-3 posts diarios y publicar en Cloudflare.

## PRIMEROS PASOS PRÓXIMA IA
Para ver el log: tail -100 data/logs/pipeline.log | grep -E 'Director|arte|OK|Error'
ls -lh output/encuadre/video_largo_2026-11-05.mp4
ls -lh web/media/imagenes/seg_*.png | head -5

## NO ROMPER
- producir_fase2() (el clásico).
- El cron de las 06:00.
- web/site/ (Cloudflare).
