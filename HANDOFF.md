# HANDOFF — 2026-11-09 (cierre de sesión épica)
> Estado actual del ecosistema. LEER ANTES DE TOCAR.

## ESTADO EN 30 SEGUNDOS
Pipeline 06:00 OPERATIVO con redes cruzadas + 8 imágenes SDXL sociales automáticas.
Dios 76 tools + 40 reglas autónomas + bot Telegram. Factory OS 11 tabs funcional.
Cohete multi-red: 2 botones por red (🚀 intent URL / 🎥 share sheet).
Lotes LTX 5/6 corriendo en Kaggle. Web elencuadre.pages.dev estable.

## SERVICIOS SV (sv status)
- keiz-web       → Flask :8001 + dashboard + Factory OS
- bot_dios       → Bot Telegram interactivo (comandos + chat libre)
- dios_autonomo  → Daemon 40 reglas proactivas (cada 30min)
- crond          → Cron scheduler

## PIPELINE 06:00 (scripts/pipeline_encuadre.py)
limpieza → gen_manual → recolector → transcribir_groq → analista_fase1
→ sintetizador → fase2_produccion → voz_edge → director_arte (80 seg)
→ render_robusto → factory_shorts → generar_web_v3 + dossier
→ actualizar_web_index → mkdocs build → push
→ YouTube (5 vídeos con publish_at 18-21h ES)
→ MINIATURAS TOP-1 (auto upload)
→ REDES CRUZADAS LLM (extractos reales + hooks únicos)
→ 8 IMÁGENES SOCIALES SDXL (1 largo 16:9 + 4 shorts 9:16 + 3 posts 1:1)
→ podcast → redes finales

## DIOS (76 tools + memoria SQLite)
Memoria: dios_workspace, dios_episodios, dios_costes, dios_fallos, busqueda_fts
Pipeline: pipeline_step, pipeline_completo, pipeline_status, pipeline_kill,
  pipeline_custom, generar_short, generar_post_web, generar_podcast_dia,
  subir_youtube_dia, programar_youtube, publicar_blogger, generar_seo,
  generar_titulo_ab, cloudflare_stats, buscar_historico, reindexar_busqueda,
  rollback_snapshot, rollback_listar
Thumbnails: generar_thumbnails_lote (prompt top-1 brain/prompt_thumbnail.py)
Redes: publicar_comentario_youtube, analizar_short_viral, generar_thumbnail_video
Auto-reparación: read_file → write_file → validate_file → promote_file (CONFIRMACIÓN Telegram)

## DIOS AUTÓNOMO (40 reglas, daemon 30min, throttle 6h)
Contenido (SEO flojo, shorts incompletos, título corto, 2d sin pipeline...)
YouTube (sin subir, sin comentarios, falta thumbnail...)
Operacional (disco 95%, pipeline zombie, token YouTube, backup viejo...)
Estrategia (nicho parado, trending, evento calendario...)
Monetización (AdSense OFF silenciado hasta ser autónomo)
Telegram privado con botones ✅❌⏰. Aprobación → ejecución tool directa.

## FACTORY OS (http://127.0.0.1:8001/encuadre)
11 tabs: Preview / Publicar / Crear / Live / Analytics / A/B / Calendario /
         Agentes / CMS / Monetización / Tráfico

### Publicar (lo que más se usa)
Cada card expandible: VÍDEO LARGO + 4 SHORTS + 3 POSTS.
Por cada red: 3 botones → 📋 copiar / 🚀 intent URL / 🎥 share sheet.
- 🚀 X → app con texto (280 chars)
- 🚀 Threads → Brave via redir.html (sin + en espacios)
- 🚀 LinkedIn → app con texto
- 🚀 Telegram → app con texto
- 🚀 YouTube Comunidad → Brave /community (pegas texto)
- 🎥 TikTok → share sheet con vídeo MP4 (solo shorts)
- 🎥 IG → share sheet con vídeo o imagen
Redes con footer automático: YT + IG + TikTok + Telegram + Web según destino.

### Hooks y textos (scripts/generar_redes_cruzadas_llm.py)
- Largo: `VIDEO: {título}` + cita real + `Miralo: youtu.be/...` + `Web: ...`
- Shorts: hooks ÚNICOS por tipo (dato/contradicción/predicción/tutorial) via _generar_hook_red
- Posts: extracto real del .md + cliffhanger "👇" + link YT + web
- LinkedIn distinto por slug (largo/dossier/mediano)
- Pre-filtro local (evita petar Groq TPM)
- Detección rechazos LLM ("I'm sorry" → fallback)

## REDIRECTOR WEB (Threads / YT Comunidad via Brave)
Archivo: web/docs/redir.html → servido en /redir.html
Uso: https://elencuadre.pages.dev/redir.html?to=<url_encoded>
Por qué: la app de Threads no decodifica %20 (los convierte en +). La app de YT
no soporta /community. Brave sí decodifica bien → redirige a la web.

## MINIATURAS (auto)
Prompt: brain/prompt_thumbnail.py (concepto + estilo El Encuadre + composición)
Tool: _tool_generar_thumbnails_lote (dios.py)
Pipeline: tras subir a YouTube 06:00
Throttle: 45s entre uploads (rate limit YouTube)
Background retry: scripts/subir_thumbs_background.py (429 cada 30min)

## IMÁGENES SOCIALES (nuevo 2026-11-09)
Script: scripts/generar_imagenes_sociales.py
Genera 8/día: 1 largo 16:9 + 4 shorts 9:16 + 3 posts 1:1
Índice: output/encuadre/social/{fecha}_index.json
Prompt: brain/prompt_thumbnail.py adaptado a aspect
Backend: /api/encuadre/abrir_app acepta imagen_path → share_image para IG/TikTok

## TIKTOK API — PENDIENTE
Tenemos: TIKTOK_CLIENT_KEY + TIKTOK_CLIENT_SECRET en .env
Falta: ACCESS_TOKEN + REFRESH_TOKEN + REDIRECT_URI
Para hacer draft persistente real (endpoint inbox):
  1. developers.tiktok.com → Login Kit → añadir Redirect URI
  2. Verificar video.upload aprobado (NO video.publish que necesita auditoría)
  3. Ejecutar scripts/tiktok_auth.py (OAuth 1 vez manual)
  4. scripts/tiktok_draft.py → POST /v2/post/publish/inbox/video/init/
  5. Vídeo aparece en Borradores TikTok → usuario abre app, edita, publica
AHORA MISMO: share sheet funciona (0 APIs). Draft persistente requiere OAuth.

## WEB elencuadre.pages.dev
MkDocs Material + Cloudflare Pages. 51+ posts históricos + 8 podcasts + RSS.
- Hook copy_media.py: web/media/ → web/docs/media/ en build
- Hook pre-push: bloquea si web/docs <3 posts o falta mkdocs.yml
- llms.txt + robots.txt (GPTBot/ClaudeBot permitidos)
- Schema.org NewsArticle por post
- Banner Telegram (cierre 30d localStorage)
- AdSense preparado OFF (monetizacion_activa: false en mkdocs.yml)
- redir.html para redirector multi-red

## LIMPIEZA rolling 2 días (scripts/limpieza_pipeline.py)
Inicio pipeline 06:00 + domingos 05:00.
Borra: render_work, clips, audios, *.mp4/mp3/json <ayer, musica_temp, web/site
PROTEGE: web/docs, web/media, data/agent, output/videos/biblioteca, config, scripts, brain
Backup pre-limpieza: output/web_backups/ (rotación 7d)

## CRONS
0 6 * * *       pipeline_encuadre.py
0 7 * * 1,4     pipeline_internacional.py
0 * * * *       liberar_cola.py
*/5 * * * *     pgrep crond (keepalive)
0 3,4 * * 0     cazar_links_musica.py
*/15 * * * *    watchdog_pipeline.py
0 5 * * 0       limpieza_inteligente.py

## LOTES LTX (Kaggle)
Lotes 5/6 lanzados para 38 imágenes sin clip (periodico_fisico + servidores +
zoom_codigo + oficina_corp_06). Suben clips cada ~10min a GitHub.
Total esperado: 79 + 38 = ~117 clips en output/videos/biblioteca/.
Contrato: ltx_continuidad_contract.json v3.3.
Orquestador: scripts/agente_ltx_biblioteca.py (lanzar <lote>).

## CONTRATOS (41 en data/agent/)
Actualizados 2026-11-09:
- video_contract v3.1 (+ miniaturas + publishAt 2 pasos)
- youtube_contract v2.1 (403 thumbnails = verificación canal)
- dios_contract v2.0 (76 tools + 40 reglas)
- blogger_contract v3.0 (fusionado v1+v2)
- shorts_contract v4.0 (fusionado v1+v3)
Nuevos: thumbnails_contract, dios_autonomo_contract, notificador_telegram_contract

## PRÓXIMOS PASOS (por prioridad)
1. Verificar lote 5/6 completos en Kaggle (`estado_kernel`)
2. Verificar miniaturas background uploader terminó las 21
3. OAuth TikTok (si tienes acceso developers) → draft persistente
4. Spotify for Podcasters (10 min manual) → RSS ya listo
5. Cloudflare R2 (10 GB) → MP3 definitivos fuera de git
6. Primer pipeline internacional lunes 07:00

## NO ROMPER
- pipeline_encuadre.py (cron 06:00)
- ltx_continuidad_contract.json v3.3
- .git/hooks/pre-push (bloquea si web rota)
- brain/notificador_top1.py (throttle)
- web/docs/ (histórico web)
- output/videos/biblioteca/ (~117 clips LTX)
- scripts/generar_redes_cruzadas_llm.py (pre-filtro + hooks únicos)
- scripts/generar_imagenes_sociales.py (8 imgs/día)

## CÓMO RETOMAR
cd ~/LofiProducer
git pull --rebase --autostash
sv status keiz-web bot_dios dios_autonomo
pgrep -af pipeline_encuadre
tail -30 data/logs/pipeline.log

Web: http://127.0.0.1:8001/encuadre
Bot: chat privado Telegram → /help
