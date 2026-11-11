# MANUAL ECOSISTEMA LOFIPRODUCER
> Auto-generado: 2026-11-11 06:00. NO editar a mano.
> Regenerar: `python3 scripts/gen_manual.py` o pedir a Dios: `# auto_regenerar_manual`

## 1. ARQUITECTURA (6 capas)
- **Cerebro**: scripts/dios.py (76 tools, ReAct, SQLite memoria)
- **Detective**: brain/investigador_redes.py (YouTube x2 + Trends + Reddit + HN)
- **Web**: web_dashboard.py :8001 + encuadre_routes.py (Factory OS)
- **Cola**: data/agent/cola_publicacion.db (SQLite FIFO + publish_at)
- **Motores**: ACE-Step / Sherpa / SDXL / Wan / LTX / FFmpeg / YouTube / Blogger
- **Infra**: Kaggle T4 x2 + Cloudflare Pages + GitHub + OAuth
- **Inventario**: 233 scripts · 30 brain · 42 contratos · 37 endpoints · 10 crons

## 2. PIPELINE DIARIO (cron 06:00)
`limpieza_pipeline` → `recolector` → `transcribir_groq` → `analista_fase1` → `sintetizador` → `fase2_produccion` → `voz_edge` → `director_arte` (80 seg) → `render_robusto` → `factory_shorts` → `generar_web_v3` + `dossier` → `actualizar_web_index` → `mkdocs build` → `git push` → YouTube 20:00

## 3. CONTRATOS (42)
- `acestep_1.5_contract.json v2.1: ACEStep 1.5 XL Turbo - Manual de Produccion`
- `acestep_contract.json v1.5: acestep_contract`
- `biblioteca_contract.json v1.0: Contrato Biblioteca de Producción - Somos El Encuadre`
- `blogger_contract.json v3.0: blogger_contract`
- `cloudflare_contract.json v?: cloudflare_contract`
- `cola_contract.json v1.0: cola_contract`
- `coverr_contract.json v2.0: Contrato de Coverr - Somos El Encuadre`
- `cron_contract.json v1.0: cron_contract`
- `dios_autonomo_contract.json v1.0: dios_autonomo_contract`
- `dios_contract.json v2.0: dios_contract`
- `director_fotografia_contract.json v1.0: director_fotografia_contract`
- `encuadre_pipeline_contract.json v5.1: Somos El Encuadre - Pipeline Top 1 Mundial`
- `evolucion_top1_contract.json v1.0: evolucion_top1_contract`
- `ffmpeg_contract.json v9.0.2: ffmpeg_contract`
- `groq_contract.json v1.0: groq_contract`
- `image_contract.json v?: image_contract`
- `jarvis_contract.json v1.0: jarvis_contract`
- `llm_contract.json v1.0: llm_contract`
- `ltx_continuidad_contract.json v3.3: Contrato LTX Continuidad y Biblioteca - El Encuadre`
- `ltx_contract.json v3.0: Contrato LTX-Video 2.3 - El Encuadre`
- `monetizacion_contract.json v1.0: monetizacion_contract`
- `monologo_contract.json v1.0: Monólogo El Encuadre (modo paralelo)`
- `musica_contract.json v1.0: Contrato de Descarga Musical - Somos El Encuadre`
- `notificador_telegram_contract.json v1.0: notificador_telegram_contract`
- `oauth_contract.json v1.0: oauth_contract`
- `oficina_virtual_contract.json v1.0: Contrato Dashboard Oficina Virtual (Sims) - El Encuadre`
- `pipeline_contract.json v1.0: pipeline_contract`
- `pipeline_internacional_contract.json v1.0: pipeline_internacional_contract`
- `pixabay_contract.json vv3: pixabay_contract`
- `posts_web_contract.json v1.0: posts_web_contract`
- `radar_global_contract.json v?: radar_global_contract`
- `sherpa_contract.json v1.13.8: sherpa_contract`
- `shorts_contract.json v4.0: Contrato de Shorts Verticales v3.0 - Somos El Encuadre`
- `stock_contract.json v1.0: stock_contract`
- `telegram_contract.json v1.0: telegram_contract`
- `thumbnails_contract.json v1.0: thumbnails_contract`
- `video_contract.json v3.1: Vídeo largo 16:9 (~11 min) con lofi CC de fondo`
- `videos_express_contract.json v0.1: Contrato Vídeos Express - El Encuadre`
- `voice_contract.json v2.1: Contrato de Voz - Somos El Encuadre`
- `wan_contract.json v1.0: Contrato Wan 2.2 - El Encuadre`
- `web_dashboard_contract.json v1.0: web_dashboard_contract`
- `youtube_contract.json v2.1: Contrato YouTube API v3 (upload + programación + refresh)`

## 4. SCRIPTS (233 en scripts/)
- `pipeline_encuadre.py`: pipeline_encuadre.py - Orquestador Maestro Definitivo (Blindado).
- `dios.py`: (sin docstring)
- `generar_web_v3.py`: generar_web_v3.py - Anti-medio: 1 post largo + 1 mediano/día con técnicas reales
- `generar_web_dossier.py`: generar_web_dossier.py - Post mediano tipo DOSSIER con texto real (sin tocar el 
- `generar_imagenes_web.py`: generar_imagenes_web.py - Genera 3 imagenes por cada post basandose en su tema r
- `render_robusto.py`: render_robusto.py v4 - Ken Burns + duración exacta del audio + auto-recovery.
- `director_arte.py`: director_arte.py - Genera 72 imágenes (1 cada 8.5s) + timeline del vídeo largo.
- `director_fotografia.py`: director_fotografia.py - Traduce cualquier texto a un prompt visual de cine (Top
- `fase2_produccion.py`: fase2_produccion.py - Generación de contenido con Escaleta Editorial Top-1.
- `sintetizador.py`: sintetizador.py - Genera el Dossier Brutal (Python) + Hooks y Citas (LLM).
- `analista_fase1.py`: analista_fase1.py - Análisis con Editor Jefe y Bucle de Investigación Infinito.
- `recolector.py`: recolector.py - Radar Global Definitivo (50+ medios, 15 TV, 15 Radio, Agencias).
- `voz_edge.py`: voz_edge.py - Genera audio por escena y timeline con pausas de intriga.
- `subir_youtube.py`: Lee atribuciones del día y devuelve bloque de texto para la descripción.
- `publicar_blogger_encuadre.py`: publicar_blogger_encuadre.py - Publica el artículo del día en Blogger con SEO.
- `factory_shorts.py`: factory_shorts.py - Fábrica 4 shorts (dato/contradiccion/prediccion/tutorial).
- `limpieza_pipeline.py`: limpieza_pipeline.py v2 - Reset diario TOTAL. Mantiene solo HOY + AYER.
- `gen_manual.py`: gen_manual.py v3 - Manual unificado compacto. Auto-escanea ecosistema real.
- `rollback.py`: Snapshot pre-pipeline + rollback a cualquier tag.
- `smoke_test.py`: Smoke test pre-push: compila .py clave + valida .json + ping endpoints. Aborta s
- `watchdog_pipeline.py`: Watchdog v2 - Solo alerta errores REALES. Sin falsos positivos.
- `cola_youtube_auto.py`: Sube shorts programados cuyo publish_at ya pasó. Cron cada 30 min.
- `indexar_busqueda.py`: Indexa output/ y web/docs/ en SQLite FTS5 para búsqueda full-text.
- `cloudflare_stats.py`: cloudflare_stats.py - Lee Web Analytics (RUM) vía GraphQL.
- `agente_ltx_biblioteca.py`: Agente LTX Biblioteca - Genera clips de 6s Top-1 con crossfade, en lotes de 20.
- *Y 208 scripts más* (usar `escanear_ecosistema('scripts')`)

## 5. BRAIN (30 módulos)
- `especialistas.py`: Sub-agentes especializados con combos de OmniRoute por rol.
- `dios_memoria.py`: (sin doc)
- `dios_tools_dinamicas.py`: dios_tools_dinamicas.py - Carga tools desde data/agent/dios_tools_dinamicas.py.
- `investigador_redes.py`: investigador_redes.py - Detective multi-fuente de tendencias.
- `ejecutor_seguro.py`: Cajon 112.A - Ejecutor seguro de comandos con HITL (Human-in-the-loop).
- `llm_gemini.py`: Gemini como fallback LLM. Retry exponencial + cascada multi-modelo.
- `web_search.py`: Cajon 110.A - Busqueda web via webless (Termux-friendly, sin Rust).
- `memoria_db.py`: Cajon 111.A - Memoria persistente del Dios en SQLite.
- `pruner.py`: Compresor de prompts sin dependencias externas (reemplaza tokenpruner).

## 6. TOOLS (76)
**FS** (5): `ejecutar_comando`, `read_file`, `write_file`, `validate_file`, `promote_file`
**Web** (4): `buscar_en_web`, `buscar_youtube`, `leer_rss`, `buscar_repositorio`
**Video** (8): `generar_video`, `generar_video_rapido`, `producir_video`, `producir_video_completo`, `ensamblar_video_largo`, `ensamblar_video_final`, `analizar_video_competencia`, `subir_youtube`
**Audio/Img** (3): `generar_cancion_kaggle`, `generar_narracion`, `generar_imagen`
**Blog/Redes** (5): `publicar_blog_completo`, `crear_blog_top`, `publicar_en_redes`, `procesar_cola_youtube`, `generar_informe_editorial`
**Sistema** (5): `estado_sistema`, `sanar_sistema`, `instalar_dependencia`, `notificar_movil`, `ejecutar_limpieza`
**Kaggle** (2): `lanzar_pipeline_kaggle`, `lanzar_notebook_kaggle`
**Canales** (4): `list_canales`, `crear_nicho`, `producir_nicho`, `evaluar_produccion`
**Memoria** (8): `recordar_hecho`, `consultar_hechos`, `documentar_aprendizaje`, `leer_documentacion`, `ver_mi_workspace`, `ver_ultimas_tareas`, `ver_fallos_similares`, `ver_costes_hoy`
**Auto/Manual** (6): `consultar_manual_ecosistema`, `buscar_en_manual`, `listar_mis_tools`, `auto_regenerar_manual`, `crear_nueva_tool`, `escanear_ecosistema`
**Delegación** (3): `delegar_tareas_paralelas`, `pedir_a_especialista`, `consultar_manual_python`
**Otros** (23): `ver_contrato`, `pipeline_step`, `pipeline_completo`, `pipeline_status`, `pipeline_kill`, `pipeline_custom`, `generar_short`, `generar_post_web`, `generar_podcast_dia`, `subir_youtube_dia`, `programar_youtube`, `publicar_blogger`, `generar_seo`, `generar_titulo_ab`, `cloudflare_stats`, `buscar_historico`, `reindexar_busqueda`, `rollback_snapshot`, `rollback_listar`, `publicar_comentario_youtube`, `analizar_short_viral`, `generar_thumbnail_video`, `generar_thumbnails_lote`

## 7. ENDPOINTS Factory (37)
- `encuadre`: /api/encuadre/redes_cruzadas/<fecha>, /api/encuadre/copiar_portapapeles, /api/encuadre/youtube/<fecha>, /api/encuadre/podcast/<fecha>, /api/encuadre/buscar, /api/encuadre/buscar/reindex, /api/encuadre/rollback/list, /api/encuadre/rollback/create...
- `otros`: /ui-podcast/<path:filename>, /encuadre/factory.js, /encuadre
- `cms`: /api/cms/files, /api/cms/read, /api/cms/save, /api/cms/delete, /api/cms/build

## 8. CRONS ACTIVOS (10)
- `0 6 * * * cd ~/LofiProducer && python3 scripts/pipeline_encuadre.py >> data/logs/pipeline.log 2>&1`
- `0 7 * * 1,4 cd ~/LofiProducer && python3 scripts/pipeline_internacional.py >> data/logs/pipeline_intl.log 2>&1`
- `0 * * * * cd ~/LofiProducer && python3 scripts/liberar_cola.py >> data/logs/cola.log 2>&1`
- `*/5 * * * * pgrep crond > /dev/null || (termux-wake-lock && crond)`
- `0 3 * * 0 cd ~/LofiProducer && python3 scripts/cazar_links_musica.py --mantener >> data/logs/cazar.log 2>&1`
- `0 4 * * 0 cd ~/LofiProducer && python3 scripts/cazar_links_musica.py --tipo largo --mantener >> data/logs/cazar.log 2>&1`
- `*/15 * * * * cd ~/LofiProducer && python3 scripts/watchdog_pipeline.py >> data/logs/watchdog.log 2>&1`
- `0 5 * * 0 cd ~/LofiProducer && python3 scripts/limpieza_inteligente.py >> data/logs/limpieza.log 2>&1`
- `0 13 * * * cd ~/LofiProducer && python3 scripts/digest_diario.py >> data/logs/digest.log 2>&1`
- `*/30 * * * * cd ~/LofiProducer && python3 scripts/kaggle_cleanup.py >> data/logs/kaggle_cleanup.log 2>&1`

## 9. MEMORIA DIOS (data/agent/)
- `dios_workspace.json` → `ver_mi_workspace`
- `dios_episodios.db` → `ver_ultimas_tareas`
- `dios_costes.db` → `ver_costes_hoy`
- `dios_fallos.db` → `ver_fallos_similares`
Se inyecta auto ~200 tokens en prompt. No consultar salvo petición.

## 10. AUTO-REPARACIÓN
1. `read_file` → inspeccionar
2. `write_file` → sandbox/
3. `validate_file` → ast.parse
4. `promote_file` → **Telegram confirm + timeout 5min**
5. `documentar_aprendizaje` + `recordar_hecho`
NUNCA escribir directo al repo. NUNCA promote sin validate.

## 11. ERRORES CONOCIDOS
- OmniRoute 401 → cascada Groq directa
- Groq 429 → 4 keys + retry 5s
- YT invalid_grant → reautorizar_youtube.py
- mkdocs 404 → hook copy_media
- SDXL refusals → filtro 'lo siento'
- fatiga visual → 8 estilos + seed
- OOM 73f LTX → bajar a 49f
- libcudart.so.12 → LD_LIBRARY_PATH + dataset
- wildcards no expanden → _expand_globs en ejecutor
- render_work 399MB/día → fix en render_robusto

## 12. REGLAS FRODO (críticas)
#3 heredoc<50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #13 no sed URLs · #18 2 fallos→parar · #20 3+parches→reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u

## 13. CONTEXTOS DÍA (output/encuadre/)
`produccion_{f}` (18 escenas+guion+shorts) · `seo_{f}` (título+desc+tags) · `redes_{f}` (textos por red) · `dossier_enriquecido_{f}` (top3+citas+medios) · `timeline_{f}` · `video_largo_{f}.mp4` · `short_{1..4}_{f}.mp4` · `podcast_{f}.mp3` · `custom_request_{f}.json`

## 14. APIS
- **Groq**: `GROQ_API_KEY(_2,_3,_4)` → gpt-oss-120b (primario)
- **Gemini**: `GEMINI_API_KEY` → gemini-3.8-flash (cascada 8 modelos)
- **Cloudflare**: `CLOUDFLARE_API_TOKEN` + `ACCOUNT_ID` → SDXL, Pages, Analytics
- **Kaggle**: `KAGGLE_USERNAME` / `KAGGLE_KEY` (2 cuentas)
- **YouTube/Blogger**: `data/youtube_encuadre_token.json` (refresh obligatorio)

## 15. COMANDOS CRÍTICOS
- `sv restart keiz-web`
- `python3 scripts/dios.py "tu peticion"`
- `python3 scripts/pipeline_encuadre.py`
- `python3 scripts/limpieza_pipeline.py --dry-run`
- `python3 scripts/gen_manual.py`
- `python3 scripts/rollback.py snapshot|listar|rollback <tag>`
- `python3 scripts/smoke_test.py`
- `curl http://127.0.0.1:8001/api/dashboard`

## 16. LIMPIEZA (piloto automático)
Ejecutada al inicio del pipeline + cron domingos 05:00:
- **Borra**: <ayer + `render_work/`, `clips/`, `audios/`, `musica_temp/`, `web/site/`, `web/web/`, `.tmp.mp4`
- **Protege**: `data/agent/`, `config/`, `scripts/`, `brain/`, `web/dashboard/`, `output/videos/biblioteca/` (LTX), `output/nichos/`
- **Rolling 2 días**: mantiene HOY + AYER

## 17. INVENTARIO (auto)
- 233 scripts · 30 brain · 42 contratos
- 37 endpoints · 10 crons · 76 tools
- Generado: 2026-11-11T06:00:08

## 17b. RECIPES (tareas comunes, pasos exactos)
- **Añadir nicho**: editar config/nichos.json + crear output/nichos/<id>/canal.json + verificar con list_canales
- **Crear video completo**: producir_video_completo(nicho, tema) hace todo: guion+seo+voz+musica+video+YT
- **Solo un short**: generar_video(nicho, vertical=True) → ensamblar_video_final → subir_youtube(short)
- **Solo audio/musica**: generar_cancion_kaggle(prompt, preset) o generar_narracion(texto)
- **Solo imagen**: generar_imagen(prompt, preset, aspect)
- **Publicar blog**: publicar_blog_completo(tema) o crear_blog_top(tema) para quality gate >=8
- **Regenerar SEO dia**: ejecutar_comando('python3 scripts/generar_titulo_seo.py FECHA')
- **Subir pendientes YT**: procesar_cola_youtube() o ejecutar_comando('python3 scripts/cola_youtube_auto.py')
- **Buscar en historico**: buscar_en_web(query) NO. Usa ejecutar_comando('python3 scripts/indexar_busqueda.py') + consultar_manual_ecosistema
- **Rollback codigo**: ejecutar_comando('python3 scripts/rollback.py listar') → rollback <tag>
- **Ver logs pipeline**: ejecutar_comando('tail -50 data/logs/pipeline.log')
- **Ver estado sistema**: estado_sistema() o sanar_sistema() si hay fallos
- **Limpiar disco**: ejecutar_limpieza(dry_run=True) primero, luego sin dry_run
- **Cambiar home/blog**: CMS del dashboard o write_file a web/docs/index.md + promote_file
- **Regenerar manual**: auto_regenerar_manual()

## 18. REGLAS CON USUARIO
Pushback si dudas · leer antes de modificar · backup zona sagrada · NUNCA borrar sin OK · 3+ parches → reescribir · env vars para tokens · `python3 -u` en Termux
