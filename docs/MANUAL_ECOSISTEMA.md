# MANUAL ECOSISTEMA LOFIPRODUCER
> Autogenerado desde `dios.TOOLS`. No editar a mano. Actualizado 2026-11-09.

## 1. ARQUITECTURA
- Cerebro: `scripts/dios.py` (52 tools, ReAct, memoria SQLite)
- Memoria: `brain/dios_memoria.py` (workspace + episodios + costes + fallos)
- Manual: `docs/MANUAL_ECOSISTEMA.md` (este fichero)
- Motor LLM: Groq (gpt-oss-120b) → Gemini 3.8 (cascada 8 modelos)
- Detectives: `brain/investigador_redes.py` (5 fuentes)
- Web: `web_dashboard.py` :8001 + `encuadre_routes.py` Factory OS
- Cola: `data/agent/cola_publicacion.db`

## 2. PIPELINE DIARIO (cron 06:00)
`recolector` → `transcribir_groq` → `analista_fase1` → `sintetizador` → `fase2_produccion` → `voz_edge` → `director_arte` (80 seg, 8 estilos) → `render_robusto` → `factory_shorts` → `generar_web_v3` + `dossier` → `mkdocs build` → `git push` → YouTube 20:00.

## 3. TODAS TUS TOOLS (52)
> Usa `listar_mis_tools` en cualquier momento para ver la lista viva.

### FS / Shell (5)
- **ejecutar_comando**: Ejecuta comandos en la terminal (pip install, python, git, etc). Comandos peligrosos pedirán confirmación al usuario.
- **promote_file**: Mueve un archivo validado de sandbox al repo real.
- **read_file**: Lee un archivo del repo.
- **validate_file**: Valida sintaxis Python (ast.parse) de un archivo en sandbox.
- **write_file**: Escribe un archivo en SANDBOX. Hace backup del original si existe. Luego valida y promueve.

### Búsqueda web (4)
- **buscar_en_web**: Busca informacion actual en internet (clima, noticias, precios, productos).
- **buscar_repositorio**: Busca librerías o herramientas en GitHub, PyPI o F-Droid. Úsalo antes de instalar algo para ver si existe y cuál es su URL.
- **buscar_youtube**: Busca videos en YouTube o consulta las tendencias actuales de una región. Usa esto ANTES que buscar_en_web para temas de YouTube.
- **leer_rss**: Lee noticias frescas. Fuentes: boe, techcrunch, hackernews, verge.

### Vídeo (8)
- **analizar_video_competencia**: Descarga un video de YouTube, extrae fotogramas y los analiza visualmente con Nemotron 550B. Borra el video despues.
- **ensamblar_video_final**: Une un video (MP4) y una cancion (MP3) en un solo archivo final.
- **ensamblar_video_largo**: Ensambla vídeo largo (vídeo + voz + música + logo + fades) usando la receta del nicho en config/montajes/<nicho>.json. Tarda 5-15 min según 
- **generar_video**: Genera un clip con Wan 2.2 TI2V-5B en Kaggle T4. 6 presets: cinematic_480p, cinematic_720p, vertical_480p, vertical_720p, turbo_4steps, draf
- **generar_video_rapido**: Genera un video rapido (2 min) con voz, clips de Pixabay y FFmpeg. Sin GPU. Ideal para noticias y shorts.
- **producir_video**: Toma un video, una cancion, los ensambla con FFmpeg, aplica fade y valida el resultado final.
- **producir_video_completo**: Pipeline completo: guion + SEO + voz + musica + video + ensamblado + YouTube. Ej: hazme video ia_news sobre GPT-5.
- **subir_youtube**: Sube vídeo a YouTube. 6 presets: draft_privado, publicar_ahora, programar, shorts_vertical, lofi_music, podcast. Sin auditoría Google, los u

### Audio/Imagen (3)
- **generar_cancion_kaggle**: Genera una cancion con ACE-Step v11 en Kaggle (T4, ~30 min). Soporta 11 presets: lofi, ambient, piano, cinematic, hiphop, electronic, jingle
- **generar_imagen**: Genera imagen con Cloudflare SDXL. 8 presets: cinematic, anime, realistic, cartoon, product, portrait, landscape, abstract. 6 aspect ratios:
- **generar_narracion**: Genera audio de voz con Sherpa-ONNX (5 voces Piper). Soporta 7 presets: noticias, narracion_relajada, urgente, audiobook, publicidad, tutori

### Blog/Redes (5)
- **crear_blog_top**: Genera articulo con Quality Gate (auditor >=8/10) y lo guarda como borrador. Ej: crear blog sobre GPT-5
- **generar_informe_editorial**: Investiga tendencias en 5 fuentes y redacta un informe HTML para decidir que publicar hoy.
- **procesar_cola_youtube**: Sube a YouTube los shorts programados cuya hora ya ha pasado.
- **publicar_blog_completo**: Publica articulo SEO en Blogger (IAGLOBALNEWS). RSS+web+YouTube + verificacion + redactor + SEO + imagen + Blogger.
- **publicar_en_redes**: Publica un video final en varias redes sociales (YouTube, TikTok, Instagram, etc).

### Sistema (4)
- **estado_sistema**: Estado del ecosistema: git, procesos vivos, omniroute.
- **instalar_dependencia**: Instala una librería de Python (pip). Antes verifica que hay RAM y disco suficiente. Úsalo para auto-mejorar tu sistema.
- **notificar_movil**: Envia notificacion push al movil del usuario.
- **sanar_sistema**: Revisa y reinicia Flask y OmniRoute si estan caidos.

### Kaggle (2)
- **lanzar_notebook_kaggle**: Crea un notebook con codigo Python y lo ejecuta en Kaggle GPU.
- **lanzar_pipeline_kaggle**: Lanza un pipeline completo en Kaggle (genera música, vídeo y lo sube a GitHub) de forma automática y apaga la GPU al terminar.

### Canales (4)
- **crear_nicho**: Crea un canal completo: nicho en config + carpeta output/nichos/<nombre>/ con subcarpetas + canal.json + SKILL.md regenerado + notificación 
- **evaluar_produccion**: Evalúa un plan de producción ANTES de gastar GPU. Devuelve informe con semáforos 🟢🟡🔴 (coherencia, presupuesto, calidad prompt, encaje nicho)
- **list_canales**: Lista los canales configurados (config/channels.json).
- **producir_nicho**: Produce contenido completo para un nicho (ia_news, lofi, boe, finanzas_barrio): RSS -> guion -> voz -> musica -> imagen. Tarda ~30 min por e

### Memoria (8)
- **consultar_hechos**: Lee los datos importantes guardados en la memoria a largo plazo.
- **documentar_aprendizaje**: Añade un nuevo descubrimiento o hito al final de un archivo de documentación para nutrir a futuras IAs.
- **leer_documentacion**: Lee un archivo maestro de documentación (ej. TRASPASO.md, BOOT_PROMPT.md, MANUAL_KAGGLE.md).
- **recordar_hecho**: Guarda un dato importante en la memoria a largo plazo para no olvidarlo en el futuro.
- **ver_costes_hoy**: Costes de hoy.
- **ver_fallos_similares**: Busca fallos similares.
- **ver_mi_workspace**: Devuelve workspace: ultima tarea y tools usadas.
- **ver_ultimas_tareas**: 3 ultimas tareas con resultado.

### Manual (3)
- **buscar_en_manual**: Busca una query en MANUAL_ECOSISTEMA.md y devuelve lineas con contexto.
- **consultar_manual_ecosistema**: Consulta una seccion del MANUAL_ECOSISTEMA.md (arquitectura, errores, pipelines, contratos, motores, apis, comandos, contextos, reglas). Usa
- **listar_mis_tools**: Devuelve TODAS las tools disponibles con su descripcion. Usala cuando el usuario pregunte que puedes hacer o que tools tienes.

### Delegación (3)
- **consultar_manual_python**: Busca patrones en el manual de Python.
- **delegar_tareas_paralelas**: Delega múltiples tareas de investigación o análisis a OmniRoute en paralelo para ahorrar tiempo. Úsala cuando necesites leer varios archivos
- **pedir_a_especialista**: Delegar tarea a un sub-agente especializado. Roles: guionista, seo, auditor, traductor, musico.

### Otros (3)
- **auto_regenerar_manual**: Regenera docs/MANUAL_ECOSISTEMA.md desde el estado actual de TOOLS. Usalo tras crear tools nuevas.
- **crear_nueva_tool**: Crea una tool nueva persistente. Recibe nombre (snake_case), descripcion, codigo_funcion (def _tool_NOMBRE(args): ...) y parametros_json (di
- **ejecutar_limpieza**: Ejecuta scripts/limpieza_pipeline.py (reset diario: borra <ayer + temporales). Con dry_run=True solo simula sin borrar.

## 4. MEMORIA (SQLite en data/agent/)
| Fichero | Qué guarda | Tool para consultarlo |
|---|---|---|
| `dios_workspace.json` | última tarea, tools usadas | `ver_mi_workspace` |
| `dios_episodios.db` | historial de tareas con resultado | `ver_ultimas_tareas` |
| `dios_costes.db` | tokens in/out por tarea | `ver_costes_hoy` |
| `dios_fallos.db` | tools que fallaron y por qué | `ver_fallos_similares(prompt)` |

Estas DBs se inyectan **automáticamente** en el prompt (compacto, ~200 tokens). No hace falta consultarlas salvo que el usuario pregunte explícitamente.

## 5. TOOL FALLBACK (automático)
Si una tool falla, Dios prueba alternativas antes de rendirse:
- `generar_video` → `generar_video_rapido`, `ensamblar_video_final`
- `producir_video_completo` → `producir_video`, `generar_video`
- `buscar_en_web` → `buscar_youtube`, `leer_rss`
- `buscar_youtube` → `buscar_en_web`, `leer_rss`
- `producir_nicho` → `producir_video_completo`
- `subir_youtube` → `procesar_cola_youtube`

## 6. REFLECTION LOOP
Cada 3 pasos sin éxito, Dios recibe: *'Reflexion: N pasos sin éxito. USA OTRA tool o di por qué no puedes.'* → evita bucles infinitos.

## 7. AUTO-REPARACIÓN (promote_file)
Flujo obligatorio para arreglar el repo:
1. `read_file` — inspeccionar
2. `write_file` — escribir a `sandbox/`
3. `validate_file` — comprobar que parsea
4. `promote_file` — **pide confirmación por Telegram + timeout 5 min**
5. `documentar_aprendizaje` + `recordar_hecho`
**NUNCA** escribir directo al repo. **NUNCA** promote_file sin validate_file.

## 8. ERRORES CONOCIDOS
| Error | Fix |
|---|---|
| OmniRoute 401 | cascada Groq directa (`_charla_rapida` ya lo hace) |
| Groq 429 | 4 keys + retry 5s |
| YouTube invalid_grant | `scripts/reautorizar_youtube.py` |
| mkdocs 404 imágenes | hook `web/hooks/copy_media.py` |
| SDXL refusals | filtro 'lo siento' en `generar_imagen.py` |
| Fatiga visual | 8 estilos + seed determinista |
| OOM 73f LTX | bajar a 49f |
| libcudart.so.12 | LD_LIBRARY_PATH + dataset |
| wildcards no expanden | `_expand_globs` en `ejecutor_seguro` |

## 9. REGLAS FRODO
#3 heredoc <50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #13 no sed URLs · #18 2 fallos → parar · #20 3+ parches → reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u.

## 10. ESTRUCTURA
`scripts/` (pipeline, dios, generar_*) · `brain/` (48 agentes, memoria) · `web/docs/` (blog MkDocs) · `web/dashboard/` (Factory OS) · `output/encuadre/` (producción diaria) · `data/agent/` (DBs, contratos) · `config/` (nichos.json) · `docs/` (este manual).

## 11. CONTEXTOS DEL DÍA
`produccion_{f}` · `seo_{f}` · `redes_{f}` · `dossier_enriquecido_{f}` · `timeline_{f}` · `video_largo_{f}.mp4` · `short_{1..4}_{f}.mp4` · `podcast_{f}.mp3` · `custom_request_{f}.json`.

## 12. APIS
- Groq: `GROQ_API_KEY(_2,_3,_4)` → gpt-oss-120b
- Gemini: `GEMINI_API_KEY` → gemini-3.8-flash (cascada 8 modelos)
- Cloudflare: `CLOUDFLARE_API_TOKEN` + `ACCOUNT_ID` → AI/SDXL, Pages, Analytics
- YouTube: `data/youtube_encuadre_token.json` (refresh obligatorio)

## 13. REGLAS CON EL USUARIO
Pushback si dudas · `py_compile` tras .py · leer antes de modificar · backup antes de zona sagrada · NUNCA borrar sin OK · 3+ parches → reescribir · env vars para tokens · `python3 -u` en Termux.

## 14. CÓMO ACTUALIZAR ESTE MANUAL
Autogenerado desde `dios.TOOLS`. Para regenerar:
```bash
python3 scripts/gen_manual.py
```
O pídeselo a Dios: `# auto_regenerar_manual`.

## 15. CÓMO CREAR UNA TOOL NUEVA (auto)
Usa `crear_nueva_tool` con:
- `nombre`: snake_case (ej: `saludar`)
- `descripcion`: qué hace
- `codigo_funcion`: cuerpo Python, ej:
```python
def _tool_saludar(args):
    return f'Hola {args.get("nombre", "mundo")}'
```
- `parametros_json`: schema JSON, ej `{"nombre":{"type":"string"}}`

Flujo: sandbox → validación → Telegram confirm → regenera manual → disponible próxima ejecución.
