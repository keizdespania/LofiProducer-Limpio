# MANUAL ECOSISTEMA LOFIPRODUCER
> Consulta antes de improvisar. Actualizado 2026-11-09.

## 1. ARQUITECTURA
- Cerebro: scripts/dios.py (43 tools, ReAct)
- Detective: brain/investigador_redes.py (5 fuentes)
- Web: web_dashboard.py (:8001) + encuadre_routes.py (Factory OS)
- Cola: data/agent/cola_publicacion.db
- Motores: ACE-Step, Sherpa, SDXL, Wan, LTX, FFmpeg, YouTube, Blogger
- Infra: Kaggle T4 x2, Cloudflare Pages, GitHub, OAuth

## 2. PIPELINE DIARIO (cron 06:00)
recolector → transcribir → analista_fase1 → sintetizador → fase2_produccion → voz_edge → director_arte (80 seg) → render_robusto → factory_shorts → generar_web_v3 + dossier → actualizar_web_index → mkdocs build + git push → YouTube 20:00.

## 3. CONTRATOS (data/agent/)
- video_contract v3.0: Ken Burns, 8 estilos, seed determinista
- shorts_contract v2.0: 5 pasos, 5 fallbacks, NUNCA rot
- ltx_continuidad v3.3: 49f, sample_params anidado, base64 init_image
- youtube_contract v2.0: refresh token SIEMPRE antes de subir

## 4. ERRORES CONOCIDOS
| Error | Fix |
|---|---|
| OmniRoute 401 | cascada Groq directa |
| Groq 429 | 4 keys + retry 5s |
| YouTube invalid_grant | reautorizar_youtube.py |
| mkdocs 404 | hook copy_media |
| SDXL refusals | filtro "lo siento" |
| Fatiga visual | 8 estilos + seed |
| OOM 73f LTX | bajar a 49f |
| libcudart.so.12 | LD_LIBRARY_PATH + dataset |
| _charla_rapida 401 | cascada Groq directa |
| wildcards no expanden | _expand_globs en ejecutor |

## 5. REGLAS FRODO
#3 heredoc <50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #13 no sed URLs · #18 2 fallos → parar · #20 3+ parches → reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u.

## 6. ESTRUCTURA
scripts/ (pipeline, dios, generar_*), brain/ (48 agentes), web/docs/ (blog MkDocs), web/dashboard/ (Factory), output/encuadre/ (producción diaria), data/agent/ (contratos, DBs), config/ (nichos.json), docs/ (este manual).

## 7. CONTEXTOS DÍA
produccion_{f}, seo_{f}, redes_{f}, dossier_enriquecido_{f}, timeline_{f}, video_largo_{f}.mp4, short_{1..4}_{f}.mp4, podcast_{f}.mp3, custom_request_{f}.json.

## 8. APIs
- Groq: GROQ_API_KEY(_2,_3,_4) → gpt-oss-120b
- Gemini: GEMINI_API_KEY → gemini-3.8-flash (cascada 8 modelos)
- Cloudflare: CLOUDFLARE_API_TOKEN + ACCOUNT_ID → AI/SDXL, Pages, Analytics
- YouTube: data/youtube_encuadre_token.json (refresh obligatorio)

## 9. COMANDOS
sv restart keiz-web · python3 scripts/dios.py "..." · python3 scripts/pipeline_encuadre.py · curl http://127.0.0.1:8001/api/dashboard

## 10. REGLAS CON USUARIO
Pushback si dudas · py_compile tras .py · leer antes de modificar · backup antes de zona sagrada · NUNCA borrar sin OK · 3+ parches → reescribir · env vars para tokens · python3 -u en Termux.
