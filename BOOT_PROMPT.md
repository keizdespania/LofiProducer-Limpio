# 🚀 BOOT_PROMPT — LOFIPRODUCER · MODO DIOS v6.0
> Arranque del Imperio. Última actualización: 2026-10-23.
> Lee este documento completo antes de tocar código.

## 🧭 CONTEXTO PARA LA NUEVA IA (leer primero)

### 1. Archivos a leer en orden (30 min)
1. BOOT_PROMPT.md (este archivo) - arquitectura global
2. config/nichos.json - 4 canales + queries + subreddits
3. data/agent/*.json - 10 contratos de motores
4. brain/especialistas.py - 10 roles LLM
5. scripts/dios.py L200-450 - 40 tools registradas
6. scripts/motor_ensamblado.py (137L) - FFmpeg declarativo
7. brain/investigador_redes.py (139L) - detective multi-fuente
8. scripts/short_engine.py - 1 short end-to-end
9. scripts/crear_paquete_blog.py - 4 shorts + podcast
10. scripts/cola_publicacion.py - programación YouTube

### 2. Flujo de producción
INVESTIGADOR (5 fuentes) -> PAQUETE (4 shorts + podcast) -> COLA (Lun-Vie 13:00) -> YOUTUBE (publishAt)

### 3. Dónde buscar cuando algo falla
- data/logs/worker.log
- data/logs/omniroute.log
- data/agent/cola.db
- data/agent/cola_publicacion.db
- data/agent/investigacion_NICHO.json
- data/agent/blog_borradores/

### 4. Comandos de diagnóstico
curl -s http://127.0.0.1:8001/api/dashboard | python3 -m json.tool
ps aux | grep -E "task_worker|omniroute|keiz-web"
sv status keiz-web
bash ~/.shortcuts/despertar.sh

### 5. Webs y credenciales
- Web: http://127.0.0.1:8001
- OmniRoute: http://localhost:20128 (45-90s arranque)
- Blog: https://iaglobalnews.blogspot.com (ID 5810739452530624729)
- GitHub: keizdespania/LofiProducer-backup
- Kaggle: 2 cuentas (keizproductions, lofiproducer)

## 🏠 REPO Y HOST
- Repo: ~/LofiProducer · GitHub: keizdespania/LofiProducer-backup
- Host: Samsung A25 5G · Termux · Python 3.14
- Web: http://127.0.0.1:8001 (Flask, runsv keiz-web)
- Arranque: Widget -> ~/.shortcuts/despertar.sh -> start_all.py -> OmniRoute + Worker + Flask

## 🎯 QUÉ ES
Ecosistema local-first que produce, traduce y distribuye contenido multimedia monetizable.
Orquestado por el Dios (OmniRoute -> 7 proveedores). Músculo en Kaggle T4 (2 cuentas).
Objetivo: fábrica autónoma de 100 canales con detección de tendencias + multi-formato.

Filosofía:
- "El ecosistema crece por config, no por código."
- "Un output, 6 monetizaciones posibles."
- "Lo que se regenera, se borra. Lo único, se pregunta."

## 🏗️ ARQUITECTURA (6 capas)
- Cerebro dios.py (1500L): 40 tools, ReAct, doble cerebro, memoria SQLite, pruner -92%.
- Detective brain/investigador_redes.py: 5 fuentes (YouTube x2, Google Trends RSS, Reddit RSS, HackerNews).
- Web :8001: 60+ endpoints, 17 pestañas.
- Cola SQLite FIFO + cola_publicacion.db (programación YouTube Lun-Vie 13:00).
- Motores (10): ACE-Step v11 · Sherpa-ONNX · SDXL · Wan 2.2 · Stock (yt-dlp) · FFmpeg · YouTube · Blogger · Cloudflare · Cooldowns.
- Infra: OmniRoute (:20128, 45-90s) · Kaggle (2) · Cloudflare · GitHub · OAuth YouTube/Blogger.

## 📊 CONTENT FACTORY (1 tema = 7 activos)
INVESTIGADOR -> PREDICTOR -> PRODUCTOR -> DISTRIBUIDOR

Un tema produce:
- 1 artículo blog (1500-2000 palabras, quality gate >=8/10)
- 1 vídeo largo 16:9 (5-15 min)
- 4 shorts 9:16 (dato/contradicción/predicción/tutorial)
- 1 podcast MP3 (5 min)
- 1 hilo X/Twitter
- 1 post LinkedIn
- 1 post Instagram

## 🕵️ DETECTIVE MULTI-FUENTE
brain/investigador_redes.py - 5 fuentes en paralelo:

| Fuente | Método | Coste | Notas |
|--------|--------|-------|-------|
| YouTube search | API v3 search.list | 100u | Configurada |
| YouTube trending | API v3 chart=mostPopular | 1u | Viral región |
| Google Trends | RSS público (trending/rss) | 0 | NO pandas/trendspyg |
| Reddit | RSS público (hot.rss) | 0 | JSON bloqueado 2026 |
| HackerNews | Firebase API | 0 | Top 10 stories |

Config por nicho en config/nichos.json:
- queries_youtube: 3-5 queries
- subreddits: 3-4 subreddits
- keywords_trends: 3-4 keywords

Endpoints:
- GET /api/investigar/NICHO - en vivo (60-90s)
- GET /api/investigacion_guardada/NICHO - cache JSON
- Panel: http://127.0.0.1:8001/?view=tendencias

## 🎬 SHORT ENGINE (con blur)
scripts/short_engine.py - pipeline end-to-end en Termux:
guion (Groq) -> voz (Sherpa) -> 3 clips verticales (stock) -> blur FFmpeg -> ensamblado -> short 9:16

Recetas en config/montajes/:
- short_vertical.json - crop centrado simple
- short_vertical_blur.json - RECOMENDADA (fondo blur + clip centrado)
- video_largo.json - 16:9 1920x1080

Multiplicador scripts/crear_paquete_blog.py:
- Genera 4 shorts (ángulos: dato/contradicción/predicción/tutorial)
- Genera guion podcast (redactor_seo)
- Genera audio podcast (Sherpa)
- Manifest en output/videos/paquete_CANAL_TS.json

Clips stock scripts/stock_vertical_hack.py:
- Busca "pexels shorts QUERY" en YouTube
- yt-dlp (max 1080p, max 100MB)
- Si horizontal -> crop a 9:16 con FFmpeg

## 📅 COLA PROGRAMACIÓN YOUTUBE
scripts/cola_publicacion.py:
- 1 short/día Lun-Vie 13:00 (España)
- SQLite en data/agent/cola_publicacion.db
- privacyStatus=private + publishAt (ISO 8601 UTC)
- Comando: python3 scripts/cola_publicacion.py procesar

## 📝 BLOG + SEO + QUALITY GATE
scripts/publicar_blogger.py - reutiliza OAuth de YouTube:
- Blog: https://iaglobalnews.blogspot.com (ID 5810739452530624729)
- Quality Gate: artículo auditado con experto_blog. Si <8/10 -> reescribe
- Pipeline: RSS + Web + YouTube + Verificación + Redactor SEO + SEO + Blogger

Endpoints:
- POST /api/generar_borrador_blog
- GET /api/borradores_blog
- POST /api/publicar_borrador

Panel: http://127.0.0.1:8001/?view=blogs

## 🎙️ PODCAST
- Pipeline: guion (redactor_seo) -> audio (Sherpa) -> MP3
- Duración: 5 min (~700-900 palabras)
- Distribución (pendiente): Spotify for Podcasters + YouTube

## 🏛️ NICHOS (config/nichos.json)
- ia_news (video 60s): tono intriga, thriller tecnológico
- finanzas_barrio (video 60s): tono cercano, analogías
- boe (video 60s): tono claro, legal, pausado
- lofi (música 1h): tono relax, estudio

Cada nicho tiene:
- skills.presets (voz, música, imagen, vídeo, ffmpeg, youtube, blogger)
- skills.pipeline (pasos de producción)
- queries_youtube + subreddits + keywords_trends (detective)

## 📊 CONTRATOS (10 motores en data/agent/)
acestep · sherpa · image · video · blogger · ffmpeg · youtube · pixabay · cloudflare · cooldowns
Endpoints: GET /api/params/MOTOR · POST /api/user_presets/MOTOR

## 📁 NAMING (brain/naming.py)
Formato: CANAL-TIPO-NNN-titulo-slug.ext
Ejemplo: ia_news-musica-001-tension-cinematica.mp3

## ✅ FUNCIONA (2026-10-23)

Cerebro y herramientas:
- Dios: 40 tools, pruner, memoria, doble cerebro
- Especialistas: 10 roles (guionista, guionista_short, seo, redactor_seo, experto_blog, auditor, traductor, musico, programador, analista_visual)

Detective y análisis:
- Investigador: 5 fuentes
- Panel web: view=tendencias

Producción:
- Short engine: 55s · 1080x1920 · blur background
- Multiplicador: 4 shorts multi-ángulo + guion podcast
- Ensamblado: motor_ensamblado.py (recetas declarativas)

Distribución:
- Cola YouTube: Lun-Vie 13:00 con publishAt
- Blog: Blogger con OAuth YouTube. Quality gate >=8/10
- Widget Despertar: robusto (90s timeout + ~/.cache)

Motores:
- ACE-Step v11 batch validado
- Wan 2.2 6 presets
- SDXL 8 presets
- Sherpa 5 voces
- FFmpeg 12 presets

Publicado:
- Primer vídeo YouTube: https://youtu.be/IGGr8B5QM1Q (privado)
- Blogger: IAGLOBALNEWS

## 🔴 PENDIENTE

### P1 - Esta semana
1. Probar flujo end-to-end: tendencias -> paquete -> cola -> YouTube programado
2. Predictor de viralidad: score por tema
3. Panel Factory en web: dashboard unificado
4. Spotify upload API

### P2 - Próximas 2 semanas
5. Aprendizaje semanal: feedback loop
6. Rotación disco: limpiar shorts >7 días
7. IG/FB (Meta Sandbox)
8. TikTok (borradores)

### P3 - Mes 2-3
9. Notebook WanGP real (49 frames, 4 steps)
10. 10 canales activos
11. Productos digitales (curso, API, SaaS)

### P4 - Mes 6
12. 100 canales activos
13. Ingresos pasivos consolidados

## 🚨 REGLAS FRODO v2 (18 reglas)

### Operativas (heredadas)
1. clear al inicio de cada cajón
2. Máx 2 cajones por respuesta · 1 comando/cajón
3. Nano por defecto. Heredoc solo <50L
4. NUNCA borrar sin permiso
5. py_compile tras .py modificado
6. Nunca imprimir tokens/keys
7. No git push sin OK
8. No rehacer lo que funciona
9. >100MB o GPU -> Kaggle
10. Backup antes de tocar
11. Termux /tmp NO escribible -> $HOME/tmp/

### Nuevas (aprendidas 2026-10-23)
12. NUNCA heredoc con triple comilla o f-strings. Usar cat > $HOME/tmp/fichero.py << 'EOF' ... EOF && python3 $HOME/tmp/fichero.py
13. NUNCA sed con URLs, comillas o símbolos. Usar Python replace
14. NUNCA pip install de paquetes con pandas (rompe Termux). Usar urllib/RSS directo
15. OmniRoute tarda 45-90s en arrancar. Timeout start_all.py = 90s + mkdir -p ~/.cache
16. Si un proceso se queda pillado: ps aux | grep NOMBRE -> pkill -9 -f NOMBRE -> rm -f *.part
17. Antes de lanzar algo pesado: timeout N externo
18. Si un test falla 2 veces seguidas: parar, diagnosticar, no improvisar
19. **Verificar procesos con pgrep -f** en vez de ps aux | grep. En Termux,  puede dar falsos negativos.
20. **Cuando un fichero supere 3 fixes encadenados, reescribir entero** (con git checkout + reescritura limpia). Parchear sobre parches = deuda infinita. Aplicar en <150 líneas limpias.

## 🧠 MANUAL FRODO v6.0

Plan-Before-Code · Verificación · Test-First · Simplicidad · Seguridad · Contexto · Pushback · Lectura antes de Escritura · Fail Fast · Terminal seguro · Código Limpio · No Alucines · Verificación Final · Documentación

Si no puedes explicarlo en 1 frase, no lo hagas.

### Lecciones aprendidas (2026-10-23)
- Heredoc con comillas anidadas = 90% de fallos. Usar script externo
- Cloudflare WAF bloquea Pixabay desde Termux. Usar RSS/APIs propias o Kaggle proxy
- Reddit JSON bloqueado desde 2026. Usar .rss
- Google Trends trendspyg depende de pandas (rompe). Usar trending/rss directo
- OmniRoute tarda 45.9s en arrancar
- FFmpeg crop consume 400% CPU. Usar -preset ultrafast
- yt-dlp 4K puede bajar 2GB por clip. Usar --max-filesize 100M + --download-sections

## 🎯 5 PATRONES DE PROGRAMACIÓN PROBADOS

### 1. Parche quirúrgico
replace + py_compile. Para cambiar 1 función, NUNCA reescribir archivo entero

### 2. Script externo
cat > $HOME/tmp/patch.py << 'EOF' ... EOF && python3 $HOME/tmp/patch.py. Para scripts >5L

### 3. Fallback en cascada
API -> RSS -> scraping. Para fuentes que cambian

### 4. Pre-procesado antes del motor
Si el motor no soporta algo, se lo das ya hecho

### 5. Cola con publishAt
Para publicar sin spam. privacyStatus=private + publishAt ISO 8601 UTC

## ⚡ SISTEMA BATCH KAGGLE
1 kernel = N canciones/clips (timeout 55 min). Música 5/kernel · Vídeo 3/kernel
Rotator: cuenta 1 -> si cuota llena -> cuenta 2 (slug reescrito a lofiproducer/...)

## 🎙️ CONTRATO SHERPA-ONNX v2
5 voces (Davefx, Sharvard, Claude, Lessac, Ryan)
7 presets: noticias, narracion_relajada, urgente, audiobook, publicidad, tutorial, sintesis_rapida
Params: length_scale 0.5-2.0 (natural 1.1-1.25) · noise_scale 0.667 · silence_scale 0.2

## 🎨 CONTRATO CLOUDFLARE SDXL v1
8 presets (cinematic, anime, realistic, cartoon, product, portrait, landscape, abstract)
6 aspects (16:9 1344x768, 9:16 768x1344, 1:1 1024x1024, 4:3, 3:2, 21:9)
Params: num_steps 1-20 · guidance 7.5 · seed -1 aleatorio. NO texto en prompt

## 🎬 CONTRATO WAN 2.2 TI2V-5B v1
6 presets. Resoluciones múltiplo 32. num_frames 4n+1 (8-121)
NUNCA 1280x720. Prompt: Sujeto + Movimiento + Cámara + Iluminación
T4 15GB: 480p 49 frames seguro

## 📱 REDES MULTI-CUENTA

| Red | Límite |
|-----|--------|
| YouTube | 6 uploads/día por proyecto GCloud |
| Instagram | 25 posts/día |
| Facebook Page | Sin límite |
| TikTok | Solo borradores sin auditoría |

100 canales: ~9-17 proyectos GCloud + 2 apps Meta + Advanced Access TikTok
Spotify/Apple: RouteNote/DistroKid. Declarar IA. NUNCA Content ID

## 🗺️ HOJA DE RUTA (12 meses)
- **Mes 0 (piloto):** "El Encuadre" análisis medios + sesgos → 5 posts + 5 shorts + AdSense + afiliados + multi-idioma.

| Mes | Objetivo | KPI |
|-----|----------|-----|
| 1 | Fábrica autónoma: detective + predictor + productor + cola | 1 paquete/día · 5 posts blog |
| 2 | Spotify + IG/FB/TikTok + aprendizaje semanal | 20 shorts · 500 visitas |
| 3 | 10 canales + productos digitales iniciales | 2k visitas · 10k views YT |
| 4-5 | Escalado + doblaje + AdSense | 20-30k visitas · AdSense activo |
| 6 | 100 canales + ingresos pasivos | 50-100k visitas · 3-5k EUR/mes |

## 🚨 COMANDOS CLAVE

Arranque completo:
bash ~/.shortcuts/despertar.sh
python3 scripts/start_all.py

Detective:
python3 brain/investigador_redes.py ia_news

Producción:
python3 scripts/short_engine.py "OpenAI GPT-5" ia_news
python3 scripts/crear_paquete_blog.py "OpenAI GPT-5" ia_news
python3 scripts/musica_acestep.py "lofi" 60 --preset=lofi
python3 scripts/generar_imagen.py "cinematic neon"

Distribución:
python3 scripts/cola_publicacion.py procesar
python3 scripts/subir_youtube.py video.mp4 "Titulo" "desc" private
python3 scripts/publicar_blogger.py "Titulo" "<html>"

Sistema:
sv status keiz-web
sv restart keiz-web
python3 -c "from brain.sanador import sanar; print(sanar())"

## 🎯 PENDIENTES INMEDIATOS (orden de ataque)
1. Probar flujo end-to-end (tendencias -> paquete -> cola -> YouTube programado)
2. Panel Factory en web (dashboard unificado)
3. Predictor de viralidad (score por tema)
4. Spotify (registro + API)
5. Aprendizaje semanal (feedback loop)

## 🎯 PROYECTO "EL ENCUADRE" (NICHO ESTRELLA — 2026-10-26)

**Tesis:** Análisis técnico de cómo los medios usan sesgos cognitivos y framing. **EDUCATIVO, NO CRÍTICO, NO PARTIDISTA.**

- **ES:** El Encuadre (elencuadre.com ~15€/año)
- **EN:** The Framing Effect (framingeffect.com)
- **Futuro:** PT, FR, DE (mismo pipeline)

**Diferenciador TOP 1:** Índice de Manipulación Diario (0-100) + comparativa cruzada 3 medios + multi-idioma.

**Pipeline:** RSS 3 medios → analista_medios (matriz carga emocional) → graficos_sesgo (matplotlib) → abogado_medios (filtro legal) → artículo largo (web) + corto (Blogger) + short 30s + Telegram.

**Datos Kaggle:** MediaSpin, How Biased Is Your Thinking, news-deframe.

**Agentes M6 S1:** analista_medios + abogado_medios.

**Legal:** ✅ citar titulares + embed YouTube + enlazar + analizar lenguaje. ❌ descargar vídeos + copiar párrafos + imágenes sin licencia + acusar ("usa framing X").

**Monetización:** Fase 0 (0€): Blogger, GitHub Pages, AdSense, afiliados, Telegram. Fase 1: Printify, KDP. Fase 2: AdMob (25€) + dominio (15€/año).

**Roadmap M6:** S1 fundación + S2 distribución + S3 monetización + S4 verificación + expansión.

## 🎯 FILOSOFÍA
- "El ecosistema crece por config, no por código."
- "Un output, 6 monetizaciones posibles."
- "Lo que se regenera, se borra. Lo único, se pregunta."
- "15 pasos por delante."

Frodo Bolsón mode: 500 pasos por delante.

---

## ⚡ MODO FLASH

Cuando el usuario pide 'modo flash':

- Respuesta ultra-corta. Sin preámbulos. Sin explicaciones
- 1 cajón = 1 comando Python que hace TODO (crear, verificar, commit, push)
- Prohibido heredoc gigante (>50L) y prohibido nano
- Para ficheros grandes: script externo (cat > $HOME/tmp/patch.py << 'EOF')
- Verificación integrada al final: py_compile + grep -c + git commit + git push
- Si algo falla: 1 línea de diagnóstico + siguiente cajón
- Si funciona: 3 líneas de resumen + siguiente tarea

Formato de respuesta en modo flash:
- Encabezado: 1 línea
- Cajón: 1 comando bash
- Pregunta final: solo si es estrictamente necesario

Patrón reescribir (REGLA FRODO #20):
- Si un fichero tiene >3 fixes encadenados →  + reescribir <150 lineas.
- Parchear > reescribir = deuda tecnica. Reescribir siempre.
- Un fichero limpio = 90% menos bugs futuros.

Patrón mental:
- NUNCA expliques lo que vas a hacer. Hazlo y reporta
- NUNCA escribas 100 líneas para algo que Python resuelve en 1
- Los comandos de más de 20 líneas en bash = candidatos a Python
- El feedback del usuario manda. Si dice 'flash', flash



## 🆕 ARQUITECTURA REAL DE "SOMOS EL ENCUADRE" (Actualizado: 2026-10-27)

### FASE 1: Consejo de Inteligencia (15 Agentes)
- `recolector.py`: Extrae RSS + YouTube + descarga audios.
- `transcribir_groq.py`: Transcribe audios con Groq Whisper (User-Agent de Chrome para evitar 403).
- `analista_fase1.py`: Cadena de análisis (detective_tendencias_v2 → forense_medios → analista_emocional → detector_sesgos_cognitivos).
- `sintetizador.py`: Director de Inteligencia + Guionista de Retención + Bibliotecario.
- **Salida**: `dossier_{fecha}.json` (Dossier de Producción Total con 24 hooks).
- **Agentes clave**: `detective_tendencias_v2`, `forense_medios`, `abogado_del_diablo`, `analista_emocional`, `detector_sesgos_cognitivos`, `director_inteligencia_v2`, `guionista_retencion_v2`, `bibliotecario_v2`, `verificador_citas`.

### FASE 2: Fábrica de Contenido (10 Agentes)
- `fase2_produccion.py`: Orquestador.
  - `arquitecto_contenido`: Esqueleto del artículo (Unamuno/Einstein).
  - `redactor_blog`: Artículo 1500 palabras (Hunter S. Thompson).
  - `guionista_cinematografico`: Guion audiovisual (pausas, música, cortes).
  - `selector_hooks`: Elige los 4 mejores hooks (o los 24 si se piden).
  - `seo_maestro`: Títulos, descripciones, tags para todas las plataformas.
  - `disenador_visual`: Prompts para SDXL (20 imágenes).
  - `community_manager`: Textos con enlaces cruzados.
  - `analista_rendimiento`: Feedback loop.
  - `director_audiovisual`: Plan de montaje (FFmpeg) con ducking y loudnorm.
  - `abogado_legal`: Valida clips de terceros (derecho de cita, max 5s).
  - `dios_ffmpeg`: Genera el comando final de FFmpeg.

### NUEVOS SCRIPTS DE SOPORTE (2026-10-27)
- `descargar_musica_dinamica.py`: Descarga música de Tunetank MCP (search_music, search_sfx).
- `catalogo_tunetank.py`: Genera el catálogo de moods/géneros/playlists.
- `analista_audio.py`: Detecta el pico de energía de una canción (para no coger los primeros 30s).
- `planificador_montaje.py`: Genera el timeline de música (algorítmico + director).
- `preparar_assets.py`: Asegura que imágenes, voz y SRTs existen antes de renderizar.
- `generar_blueprint.py`: Genera el blueprint de escenas y el comando FFmpeg.
- `renderizador.py`: Ejecuta FFmpeg para montar el vídeo largo y los shorts.
- `hack_compartir_redes.py`: Comparte vídeos a TikTok/IG/Threads vía Android Intent (sin APIs).

### COMANDOS CLAVE ACTUALIZADOS
- Fase 1 completa:
  `python3 scripts/recolector.py && python3 scripts/transcribir_groq.py && python3 scripts/analista_fase1.py && python3 scripts/sintetizador.py`
- Fase 2 completa:
  `python3 scripts/fase2_produccion.py && python3 scripts/preparar_assets.py && python3 scripts/planificador_montaje.py && python3 scripts/generar_blueprint.py && python3 scripts/renderizador.py`
- Dashboard local:
  `sv restart keiz-web` → `http://127.0.0.1:8001/encuadre`

### REGLA FRODO #22 (NUEVA): NO DEJES HUÉRFANOS
> "Cada agente debe tener su script de soporte. Si un agente nuevo se inyecta, su script debe existir y estar enlazado en el pipeline. No dejes agentes sin casa."

### ESTADO ACTUAL (2026-10-27)
- **Fase 1**: ✅ Terminada y auditada (dossier con 24 hooks, 11 medios, citas académicas).
- **Fase 2**: ✅ Terminada y auditada (artículo, guion cinematográfico, SEO, shorts).
- **Renderizador**: ⏳ En pruebas (comando FFmpeg generado, pendiente de ejecutar).
- **Dashboard**: ⏳ Pendiente de actualizar con los nuevos datos.


## 🤖 SISTEMA AUTÓNOMO Y GLOBAL (Actualizado: 2026-10-28)

### ORQUESTACIÓN (Cron)
El sistema es 100% autónomo. No necesita intervención humana.
- **Pipeline Nacional (Diario)**: `0 6 * * *` -> `python3 scripts/pipeline_encuadre.py`
- **Pipeline Internacional (Lunes y Jueves)**: `0 7 * * 1,4` -> `python3 scripts/pipeline_internacional.py`

### RADAR GLOBAL
- **Nacional**: Ampliado a +10 canales de TV, +9 radios y +12 canales de YouTube.
- **Internacional**: Medios como The Guardian, Le Monde, BBC, Al Jazeera. Traducidos al castellano por el agente `traductor_humanizado` (Top 1 mundial).

### GENERACIÓN MASIVA DE CONTENIDO (El Enjambre)
Cada ejecución del pipeline genera:
- **12 Posts en la Web**: 1 Maestro + 3 Quirúrgicos + 5 Satélite + 3 Redes.
- **5 Posts en Blogger**: Artículo, Hub Vídeo, Cita Bomba, Tutorial, Radar.
- **Vídeos**: 1 Largo + 4 Shorts (con voz de Álvaro y karaoke).
- **Redes**: Textos SEO cruzados para TikTok, IG, X, Threads y YouTube Comunidad.

### AGENTES NUEVOS CLAVE
- `director_arte`: Decide las imágenes perfectas para cada post.
- `curador_imagenes`: Selecciona las mejores de las 20 generadas.
- `traductor_humanizado`: Traduce medios internacionales al castellano como un nativo.


## 💰 ROADMAP DE MONETIZACIÓN (Para la próxima IA)

**FASE 0 (Hoy mismo):**
1. Afiliados de Amazon: Añadir tag en los posts (Kahneman, Chomsky).
2. Botones de Donación (Buy Me a Coffee / Cripto) en el footer de la web.
3. Productos Digitales (Lemon Squeezy): Vender el Dossier en PDF.
4. APIs B2B: Vender el JSON del análisis.

**FASE 1 (1-3 meses):**
5. AdSense: Solicitar cuando haya 10+ posts.
6. Print-on-Demand (Printify): Subir imágenes de SDXL a camisetas.
7. Amazon KDP: Recopilar análisis en un libro PDF.
8. Telegram Premium: Canal VIP de pago.

**PRIORIDAD ESTRATÉGICA:**
- Comprar dominio `.com` (Namecheap/Porkbun) y VPS (NetGrid/BeoHosting) financiado con los ingresos de Fase 0.


## 🚀 ARQUITECTURA FINAL DE "SOMOS EL ENCUADRE" (Actualizado: 2026-10-28)

### 📡 LLM Y VOZ
- **Motor principal**: Groq Directo (`openai/gpt-oss-120b`). Es la única forma de evitar caídas de OmniRoute.
- **Voz**: Edge-TTS con `es-ES-AlvaroNeural`. El script `voz_edge.py` limpia acotaciones (`[Fade out]`, `Fin`, etc.) antes de generar.

### 🎬 PIPELINE DE 18 ESCENAS
- **Fase 1**: `recolector.py` → `transcribir_groq.py` → `analista_fase1.py` → `sintetizador.py`
- **Fase 2**: `fase2_produccion.py` genera el artículo y las 18 escenas (con fallback si el LLM falla).
- **Assets**: `director_arte.py` descarga 7 vídeos (Coverr) y genera 11 imágenes (SDXL) + 18 canciones.
- **Voz**: `voz_edge.py` genera 18 MP3s con 2s de silencio entre ellos y guarda `timeline_{fecha}.json`.
- **Render**: `renderizador.py` monta cada escena con su música y vídeo/imagen.

### ☁️ INFRAESTRUCTURA
- **GitHub**: `https://github.com/keizdespania/LofiProducer-Limpio`
- **Cloudflare Pages**: Proyecto `elencuadre`. El build debe ser `cd web && mkdocs build` (NO `-f web/mkdocs.yml`).
- **Cron**: Nacional 06:00 AM, Internacional Lunes y Jueves 07:00 AM.

### 🚨 REGLA FRODO #23 (NUEVA)
> "No dejes que un proceso local (OmniRoute) se convierta en un cuello de botella. Si falla, usa la API directa de Groq. La resiliencia es la clave del imperio."

### 🎯 SIGUIENTE PASO NATURAL (para la próxima IA)
1. Verificar que el pipeline completo de las 06:00 produce un vídeo de >10 minutos con 18 escenas.
2. Implementar la subida automática a YouTube con `publish_at`.
3. Configurar AdSense y Afiliados.
4. Lanzar el primer pipeline internacional (lunes/jueves).


## ⏳ TAREAS PENDIENTES (Actualizado: 2026-10-28)

### 🚀 RENDERIZADO EN KAGGLE (Pendiente)
**Objetivo**: Usar la GPU T4 de Kaggle para renderizar los vídeos de "Somos El Encuadre" en 2-3 minutos (vs 20-30 min en Termux).
**Scripts ya creados**:
- `scripts/kernel_render_encuadre.py`: El código que se sube a Kaggle (usa `h264_nvenc` para codificar en GPU).
- `scripts/renderizar_en_kaggle.py`: El orquestador local (sube assets, lanza kernel, descarga vídeo).
- `scripts/kaggle_bearer.py`: API de Kaggle (push_kernel, estado_kernel, output_kernel).

**Cómo retomarlo**:
1. Terminar el render actual en Termux para validar la calidad.
2. Crear un Dataset de Kaggle con los assets (`kaggle datasets create -p output/kaggle_assets`).
3. Ajustar el `KERNEL_SLUG` en `renderizar_en_kaggle.py` con el usuario real (ej. `keizproductions/render-encuadre`).
4. Probar el flujo completo: subir assets → lanzar kernel → descargar vídeo.

**Coste**: 0€. Kaggle es gratis y la GPU T4 es más que suficiente.

## 🚀 HOJA DE RUTA EVOLUTIVA (Top 1 Mundial)
Ver: agent/design/09_evolucion_top1.md
Estado: Diseñado. Próximos pasos: predictor_viralidad y verificador_factos (Semana 1).


## 🚀 EVOLUCIÓN TOP 1 MUNDIAL (Hoja de Ruta Completa)
Ver documento detallado: `agent/design/09_evolucion_top1.md`.

### 1. Meta-Agentes (El Sistema que se Auto-Mejora)
- `arquitecto_sistema`: Crea nuevos agentes y scripts.
- `auditor_codigo`: Caza bugs y refactoriza.
- `estratega_negocio`: Decide nichos y escalado a 100 canales.

### 2. Nuevos Agentes de Contenido (10)
- **Editorial**: `analista_sentimiento`, `verificador_factos` (✅), `detector_polarizacion`.
- **Optimización**: `predictor_viralidad` (✅), `generador_titulos_ab`, `analista_competencia`.
- **Escalado**: `traductor_multilingue`, `doblador_voz` (XTTS v2).
- **Comunidad**: `community_manager_auto`, `detector_tendencias_vivas`.

### 3. Nuevos Scripts de Proceso (8)
- **Feedback Loop**: `analytics_youtube`, `auto_ajuste_prompts`, `rotador_ab`.
- **Resiliencia**: `monitor_salud`, `rollback_auto`.
- **Planificación**: `calendario_editorial`, `detector_evergreen`.
- **Monetización**: `optimizador_adsense`.

### 4. Upgrades del Pipeline
- **Branching**: Seguridad -> Sentimiento -> Viralidad -> Publicación.
- **15 Assets por tema**: (Añadir EN largo, 4 shorts EN, PDF pago, miniaturas A/B).
- **Scheduler inteligente**: Publicación según engagement.

### 5. Dashboard (7 Pestañas)
Preview · Distribución · Monetización · Analytics · A/B Testing · Calendario · Agentes · Crisis.

### Priorización (Estado Actual)
- **Semana 1**: `predictor_viralidad` + `verificador_factos` + `monitor_salud`. (Los 2 primeros YA ESTÁN).
- **Semana 2-3**: Analytics y A/B testing.
- **Mes 2**: Traducción y doblaje.
- **Mes 3+**: Meta-agentes y auto-mejora.
