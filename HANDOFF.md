# HANDOFF — 2026-11-09
> Estado del ecosistema. LEER ANTES DE TOCAR.

## ESTADO EN 30 SEGUNDOS
OPERATIVO. Pipeline 06:00 diario + Dios autónomo (76 tools, 40 reglas) + Bot Telegram + Factory OS (11 tabs) + Web elencuadre.pages.dev.

## SERVICIOS
- keiz-web: Flask :8001 + dashboard
- bot_dios: Bot Telegram interactivo
- dios_autonomo: Daemon 40 reglas proactivas
- crond: Cron scheduler

## DIOS (76 tools)
Memoria SQLite: dios_workspace, dios_episodios, dios_costes, dios_fallos, busqueda_fts
Pipeline tools: pipeline_step, pipeline_completo, pipeline_status, pipeline_kill, pipeline_custom, generar_short, generar_post_web, generar_podcast_dia, subir_youtube_dia, programar_youtube, publicar_blogger, generar_seo, generar_titulo_ab, cloudflare_stats, buscar_historico, reindexar_busqueda, rollback_snapshot, rollback_listar
Thumbnails: generar_thumbnails_lote
Auto-reparación: read_file → write_file → validate_file → promote_file

## DIOS AUTÓNOMO (40 reglas)
Daemon cada 30min, throttle 6h. Telegram con botones ✅❌⏰.
Contenido + YouTube + Operacional + Estrategia + Monetización.

## TELEGRAM
Chat privado: alertas + ideas + bot
Canal público @somoselencuadre: solo contenido
Módulo: brain/notificador_top1.py

## MINIATURAS
Prompt top-1 en brain/prompt_thumbnail.py
Pipeline automático tras subir a YouTube
Throttle 45s upload, background retry si 429

## FACTORY OS
http://127.0.0.1:8001/encuadre
Preview · Publicar · Crear · Live · Analytics · A/B · Calendario · Agentes · CMS · Monetización · Tráfico

## WEB elencuadre.pages.dev
MkDocs Material · 49 posts · 8 podcasts RSS · banner Telegram · llms.txt · Schema.org · AdSense OFF
Hooks: copy_media + pre-push (bloquea si web/docs <3)

## LIMPIEZA rolling 2 días
scripts/limpieza_pipeline.py inicio 06:00 + domingos 05:00
Borra render_work, clips, audios, *.mp4 <ayer, web/site
PROTEGE web/docs, web/media, data/agent, output/videos/biblioteca

## CRONS
0 6 * * * pipeline_encuadre
0 7 * * 1,4 pipeline_internacional
*/15 * * * * watchdog
*/30 * * * * cola_youtube_auto
0 5 * * 0 limpieza_inteligente

## PRÓXIMOS PASOS
1. Verificar cron 06:00
2. Spotify for Podcasters
3. Cloudflare R2 (MP3)
4. Consolidar contratos
5. Reescribir BOOT_PROMPT.md

## NO ROMPER
pipeline_encuadre.py · ltx_continuidad_contract v3.3 · agente_ltx_biblioteca · .git/hooks/pre-push · notificador_top1.py · web/docs/ · output/videos/biblioteca/
