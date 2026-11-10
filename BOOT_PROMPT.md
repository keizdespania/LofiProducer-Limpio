# BOOT_PROMPT — LOFIPRODUCER · v8.0
> 2026-11-09. **Lee HANDOFF.md PRIMERO** (168 líneas con estado exacto).

## ORDEN DE LECTURA (10 min)
1. HANDOFF.md (raíz, 168L) → estado actual
2. AGENT_ONBOARDING.md → reglas + arquitectura
3. data/agent/dios_contract.json → 76 tools
4. data/agent/video_contract.json v3.1 → pipeline vídeo + miniaturas
5. data/agent/dios_autonomo_contract.json → 40 reglas
6. BOOT_PROMPT.md (este) → contexto global

## QUÉ ES
Ecosistema local-first que produce contenido multimedia monetizable en Termux.
Orquestado por Dios (76 tools + ReAct). Músculo en Kaggle T4 x2.

## FILOSOFÍA
- "El ecosistema crece por config, no por código".
- Diagnostica con logs. Lee contratos ANTES de tocar.
- "Lo que se regenera, se borra. Lo único, se pregunta".

## ARQUITECTURA (6 capas)
1. Cerebro: scripts/dios.py (76 tools + 5 DBs SQLite + ReAct)
2. Detective: brain/investigador_redes.py (5 fuentes: YouTube x2 + Trends + Reddit + HN)
3. Web: web_dashboard.py + encuadre_routes.py (11 tabs)
4. Cola: data/agent/cola_publicacion.db
5. Motores: ACE-Step / Sherpa-ONNX / SDXL Cloudflare / Wan 2.2 / LTX 2.3 /
   FFmpeg / YouTube / Blogger / Cloudflare
6. Infra: Termux (sv services) + Kaggle T4 x2 + Cloudflare Pages + GitHub

## SERVICIOS SV
- keiz-web: Flask :8001 (dashboard + Factory OS)
- bot_dios: Bot Telegram interactivo
- dios_autonomo: Daemon 40 reglas proactivas
- crond: Cron scheduler

## DIOS (76 tools)
Categorías:
- Memoria: ver_mi_workspace, ver_ultimas_tareas, ver_costes_hoy, ver_fallos_similares, buscar_historico, reindexar_busqueda
- FS/Shell: ejecutar_comando, read_file, write_file, validate_file, promote_file (CONFIRMACIÓN Telegram)
- Pipeline (18): pipeline_step, pipeline_completo, pipeline_status, pipeline_kill,
  pipeline_custom, generar_short, generar_post_web, generar_podcast_dia,
  subir_youtube_dia, programar_youtube, publicar_blogger, generar_seo,
  generar_titulo_ab, cloudflare_stats, rollback_snapshot, rollback_listar
- Thumbnails: generar_thumbnails_lote
- Redes: publicar_comentario_youtube, analizar_short_viral, generar_thumbnail_video
- Web: buscar_en_web, buscar_youtube, leer_rss, buscar_repositorio, buscar_en_manual, consultar_manual_ecosistema, listar_mis_tools
- Producción: generar_video, generar_imagen, generar_narracion, generar_cancion_kaggle, producir_video, producir_video_completo, producir_nicho, ensamblar_video_final, ensamblar_video_largo, analizar_video_competencia
- Distribución: subir_youtube, procesar_cola_youtube, publicar_en_redes, publicar_blog_completo, crear_blog_top, generar_informe_editorial
- Sistema: estado_sistema, sanar_sistema, instalar_dependencia, notificar_movil
- Kaggle: lanzar_pipeline_kaggle, lanzar_notebook_kaggle
- Delegación: delegar_tareas_paralelas, pedir_a_especialista, consultar_manual_python
- Auto-mejora: auto_regenerar_manual, crear_nueva_tool, escanear_ecosistema

## DIOS AUTÓNOMO (40 reglas)
Daemon `scripts/dios_autonomo.py` cada 30min. Throttle 6h por regla.
Telegram privado con botones ✅ Ejecutar / ❌ Ignorar / ⏰ Posponer.
Categorías: contenido, YouTube, operacional, estrategia, monetización.
Aprobación → ejecución directa tool (sin agente improvisando).

## TELEGRAM
2 canales separados:
- Chat privado (TELEGRAM_CHAT_ID): alertas técnicas + ideas autónomas + bot
- Canal público (TELEGRAM_CHANNEL_ID @somoselencuadre): solo contenido
Módulo central: brain/notificador_top1.py (throttle 2-20h, dedupe 24h)

## PIPELINE 06:00 (scripts/pipeline_encuadre.py)
1. limpieza_pipeline (rolling 2 días)
2. gen_manual (regenera MANUAL_ECOSISTEMA.md)
3. recolector → transcribir_groq → analista_fase1 (15 agentes)
4. sintetizador → fase2_produccion (18 escenas)
5. voz_edge (edge_tts es-ES-AlvaroNeural)
6. director_arte (80 segmentos SDXL, 8 estilos rotativos)
7. render_robusto (Ken Burns + voz + lofi → video_largo.mp4)
8. factory_shorts (4 shorts 9:16)
9. generar_web_v3 + generar_web_dossier + actualizar_web_index
10. mkdocs build + push (Cloudflare despliega)
11. YouTube (5 subidas con publish_at 18-21h ES)
12. MINIATURAS TOP-1 (auto upload)
13. REDES CRUZADAS LLM (extractos reales + hooks únicos por tipo)
14. 8 IMÁGENES SOCIALES SDXL (1 largo 16:9 + 4 shorts 9:16 + 3 posts 1:1)
15. podcast MP3
16. redes finales

## FACTORY OS (http://127.0.0.1:8001/encuadre)
11 tabs: Preview / Publicar / Crear / Live / Analytics / A/B / Calendario /
         Agentes / CMS / Monetización / Tráfico

### Tab Publicar
Cada pieza expandible. 3 botones por red: 📋 copiar / 🚀 intent URL / 🎥 share.
- 🚀 X → app con texto
- 🚀 Threads → Brave (redir.html, sin +)
- 🚀 LinkedIn → app
- 🚀 Telegram → app
- 🚀 YouTube Comunidad → Brave /community
- 🎥 TikTok → share sheet MP4
- 🎥 IG → share sheet vídeo/imagen
Footer automático con links a TODAS las redes del canal.

### Hooks y textos (scripts/generar_redes_cruzadas_llm.py)
- Largo: `VIDEO: {título}` + cita + `Miralo: youtu.be/...` + `Web: ...`
- Shorts: hooks ÚNICOS por tipo (dato/contradicción/predicción/tutorial)
- Posts: extracto real del .md + cliffhanger + links
- Pre-filtro local (evita TPM 8000 Groq)
- Detección rechazos LLM → fallback

## REDES SOCIALES
- X: intent URL directo (280 chars)
- Threads: redir.html via Brave (evita bug + de app)
- LinkedIn: intent URL
- Telegram: intent URL
- YT Comunidad: redir.html → /community (pegar texto del clipboard)
- TikTok: share sheet con MP4 (draft persistente pendiente OAuth)
- IG: share sheet con imagen/vídeo (caption manual)

## MINIATURAS + IMÁGENES SOCIALES
Prompt: brain/prompt_thumbnail.py (60+ keywords + estilo El Encuadre + composición)
Miniaturas YT: pipeline auto + background retry (429 → cada 30min)
Imágenes redes: 8/día con aspect (16:9 / 9:16 / 1:1)
Índice: output/encuadre/social/{fecha}_index.json

## WEB elencuadre.pages.dev
MkDocs Material + Cloudflare Pages. 51+ posts + 8 podcasts + RSS.
- Hook copy_media (web/media → docs/media)
- Hook pre-push (bloquea si web/docs <3 posts)
- llms.txt + robots.txt (LLM-friendly)
- Schema.org NewsArticle
- Banner Telegram (cierre 30d)
- AdSense OFF (activar en mkdocs.yml cuando seas autónomo)
- redir.html (redirector multi-red via Brave)

## LOTES LTX
Contrato: ltx_continuidad_contract.json v3.3
Orquestador: scripts/agente_ltx_biblioteca.py (lanzar <lote>)
Runtime: keizproductions/ltx-free-runtime (dataset Kaggle)
Estado 2026-11-09: lotes 5/6 corriendo (38 imgs sin clip)
Total esperado: ~117 clips en output/videos/biblioteca/

## CONTRATOS (41 en data/agent/)
Críticos actualizados 2026-11-09:
- video_contract v3.1
- youtube_contract v2.1
- dios_contract v2.0
- dios_autonomo_contract v1.0
- thumbnails_contract v1.0
- notificador_telegram_contract v1.0

## REGLAS FRODO (críticas)
#3 heredoc <50L · #5 py_compile tras .py · #7 no push sin OK · #8 no rehacer lo que funciona
#11 $HOME/tmp (no /tmp) · #12 script externo >50L · #13 NUNCA sed con URLs/comillas
#18 si falla 2 veces → parar, diagnosticar · #20 3+ parches encadenados → reescribir entero
#35 Groq directo > OmniRoute · #39 User-Agent Chrome en Groq · #77 python3 -u en Termux

## NO ROMPER
- pipeline_encuadre.py (cron 06:00)
- ltx_continuidad_contract.json v3.3
- scripts/agente_ltx_biblioteca.py
- .git/hooks/pre-push
- brain/notificador_top1.py
- scripts/generar_redes_cruzadas_llm.py (pre-filtro + hooks únicos)
- scripts/generar_imagenes_sociales.py
- web/docs/ (histórico web)
- output/videos/biblioteca/ (~117 clips)

## CÓMO RETOMAR
cd ~/LofiProducer
git pull --rebase --autostash
sv status keiz-web bot_dios dios_autonomo
pgrep -af pipeline_encuadre
tail -30 data/logs/pipeline.log
curl -s http://127.0.0.1:8001/api/dashboard | python3 -m json.tool | head -20

Web: http://127.0.0.1:8001/encuadre
Bot Telegram: /help
Web pública: https://elencuadre.pages.dev
