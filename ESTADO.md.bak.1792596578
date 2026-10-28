# ESTADO.md — LofiProducer (Imperio KeiZ)

> Fuente de verdad única. Actualizado: 2026-10-21.
> Para nueva IA: lee este fichero entero. Luego consulta docs/INDICE.md.

## 1. QUÉ ES
Ecosistema local-first (Termux Samsung A25) que produce, traduce y distribuye contenido multimedia monetizable. Orquestado por el Dios (agente LLM) + cola SQLite. Músculo en Kaggle (2 cuentas T4). Objetivo: 100 canales automatizados.

## 2. ARQUITECTURA
- Cerebro: scripts/dios.py (ReAct, tools, memoria SQLite)
- Interfaz: web_dashboard.py (Flask :8001, 16 pestañas, SSE, Media Center)
- Cola: scripts/task_worker.py + data/agent/cola.db
- Motores: scripts/*.py (video, música, voz, imagen, ensamblado, publicar)
- Infra: OmniRoute (:20128) → Groq; Kaggle (2 cuentas); Cloudflare SDXL; GitHub; YouTube OAuth
- Auto-cuidado: brain/sanador.py (Doctor), scripts/conserje.py (Conserje)

## 3. NICHOS (config/nichos.json)
- ia_news — video_narrado 90s — RSS→guion→TTS→img→video
- finanzas_barrio — video_narrado 90s — RSS BOE→guion→TTS→img
- boe — video_texto_voz — RSS BOE→resumen→TTS
- lofi — música_loop 1h — ACE-Step x10→loop FFmpeg

## 4. FUNCIONA (2026-10-21)
- Dios (Groq/OmniRoute): chat SSE, tools, memoria
- Web Flask :8001 (16 pestañas)
- TTS Sherpa-ONNX (5 voces, davefx)
- Música ACE-Step v11 Kaggle (auto-upload GitHub)
- Vídeo Wan 2.2 TI2V-5B Kaggle T4
- Cloudflare SDXL
- Ensamblado FFmpeg
- Publicar WordPress + YouTube
- Cola SQLite + worker + SSE reconexión
- Kaggle Bearer (2 cuentas)
- Conserje (Job 1005 diario)
- Doctor (sanador.py + widget)

## 5. FALTA
- Orquestador universal de nichos
- kaggle_rotator.py (60h/sem)
- Scraper BOE
- Multiformato (9:16, shorts, subtítulos)
- TikTok/Reels
- python_master_manual.md

## 6. REGLAS FRODO
1. clear al inicio
2. Máx 2 cajones, 1 cmd por cajón
3. Nano por defecto. Heredoc solo >100L o JSON. NUNCA heredoc gigante con markdown
4. NUNCA borrar sin permiso (mover a ~/.trash/)
5. py_compile tras cada .py
6. Nunca imprimir tokens/keys/.env
7. No git push sin OK
8. No rehacer lo que funciona
9. >100MB o GPU → Kaggle/Modal

## 7. COMANDOS
./scripts/start_all.py
python -c "from brain.sanador import sanar; print(sanar())"
python scripts/musica_acestep.py "upbeat lofi, 30s" 30
python scripts/kaggle_wan22_final.py "gato en bici"
python scripts/generar_imagen.py "cinematic neon"
python scripts/ensamblar_video.py video.mp4 musica.mp3 out.mp4
python scripts/conserje.py --dry

## 8. CREDENCIALES (valores en .env)
OMNIROUTE_*, GROQ_*, KAGGLE_API_TOKEN, KAGGLE_API_TOKEN_2, GITHUB_TOKEN, CLOUDFLARE_*, YOUTUBE_*, GOOGLE_*, DEEPSEEK_*, OPENROUTER_*, NVIDIA_*, ACEMUSIC_*, FREEMUSICLAB_*

## 9. AUTO
- Job 1004: notificar_accesos.sh cada 15min
- Job 1005: run_conserje.sh cada 24h
- Doctor: widget manual
- Despertar: widget manual → start_all.py
- auto_docs: desactivado del cron

## 10. FUTURO
- Mes 1: 1 canal, tools dinámicas, contexto reducido
- Mes 2-3: kaggle_rotator, orquestador nichos, multiformato
- Mes 4: 10 canales, auto-construcción config JSON
- Mes 5-6: 100 canales, ingresos pasivos
