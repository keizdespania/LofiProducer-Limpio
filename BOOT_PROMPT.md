# BOOT_PROMPT — LOFIPRODUCER · v7.0
> 2026-11-09. Lee HANDOFF.md PRIMERO (estado actual en 61 líneas).

## ORDEN DE LECTURA (10 min)
1. HANDOFF.md (raíz) — estado actual
2. AGENT_ONBOARDING.md — reglas + arquitectura
3. data/agent/dios_contract.json — 76 tools
4. data/agent/video_contract.json v3.0 — pipeline vídeo
5. BOOT_PROMPT.md (este) — contexto global

## QUÉ ES
Ecosistema local-first que produce contenido multimedia monetizable. Orquestado por Dios (76 tools). Músculo en Kaggle T4.

## ARQUITECTURA (6 capas)
1. Cerebro: scripts/dios.py (76 tools + memoria SQLite + ReAct)
2. Detective: brain/investigador_redes.py (5 fuentes)
3. Web: web_dashboard.py + encuadre_routes.py (11 tabs)
4. Cola: data/agent/cola_publicacion.db
5. Motores: ACE-Step / Sherpa / SDXL / Wan / LTX / FFmpeg / YouTube / Blogger
6. Infra: Termux (sv) + Kaggle T4 x2 + Cloudflare Pages + GitHub

## SERVICIOS SV
- keiz-web: Flask :8001
- bot_dios: Bot Telegram interactivo
- dios_autonomo: Daemon 40 reglas proactivas
- crond: Cron

## DIOS
76 tools. 5 categorías:
- Memoria (workspace, episodios, costes, fallos, FTS5)
- Pipeline (18 tools: step, completo, custom, short, post, podcast, YT, SEO, CF, FTS, rollback)
- Thumbnails (lote con prompt top-1)
- Auto-reparación (write→validate→promote con confirmación)
- Delegación + búsqueda

## DIOS AUTÓNOMO
40 reglas detectando cada 30min. Throttle 6h. Telegram con botones ✅❌⏰.
Categorías: contenido, YouTube, operacional, estrategia, monetización.

## TELEGRAM
- Chat privado: alertas + ideas + bot
- Canal @somoselencuadre: solo contenido
- Módulo: brain/notificador_top1.py

## PIPELINE 06:00
limpieza → gen_manual → recolector → analizar → guion → voz → arte (80 seg) → render vídeo → shorts → web → YouTube → MINIATURAS AUTO → podcast → redes

## FACTORY OS
http://127.0.0.1:8001/encuadre (11 tabs)

## WEB
elencuadre.pages.dev (MkDocs + Cloudflare Pages)

## REGLAS FRODO
#3 heredoc<50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #12 script externo · #13 no sed URLs · #18 2 fallos→parar · #20 3+parches→reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u

## NO ROMPER
- pipeline_encuadre.py (cron 06:00)
- .git/hooks/pre-push (bloquea si web rota)
- brain/notificador_top1.py (throttle)
- output/videos/biblioteca/ (79 clips LTX)
- web/docs/ (histórico)
