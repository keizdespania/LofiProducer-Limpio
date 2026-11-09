import sys, pathlib
sys.path.insert(0, "scripts"); sys.path.insert(0, "brain")
import dios

# Agrupar tools por categoría (heurística por nombre)
CATS = {
    "FS / Shell": ["ejecutar_comando", "read_file", "write_file", "validate_file", "promote_file"],
    "Búsqueda web": ["buscar_en_web", "buscar_youtube", "leer_rss", "buscar_repositorio"],
    "Vídeo": ["generar_video", "generar_video_rapido", "producir_video", "producir_video_completo",
             "ensamblar_video_largo", "ensamblar_video_final", "analizar_video_competencia", "subir_youtube"],
    "Audio/Imagen": ["generar_cancion_kaggle", "generar_narracion", "generar_imagen"],
    "Blog/Redes": ["publicar_blog_completo", "crear_blog_top", "publicar_en_redes", "procesar_cola_youtube",
                  "generar_informe_editorial"],
    "Sistema": ["estado_sistema", "sanar_sistema", "instalar_dependencia", "notificar_movil"],
    "Kaggle": ["lanzar_pipeline_kaggle", "lanzar_notebook_kaggle"],
    "Canales": ["list_canales", "crear_nicho", "producir_nicho", "evaluar_produccion"],
    "Memoria": ["recordar_hecho", "consultar_hechos", "documentar_aprendizaje", "leer_documentacion",
               "ver_mi_workspace", "ver_ultimas_tareas", "ver_fallos_similares", "ver_costes_hoy"],
    "Manual": ["consultar_manual_ecosistema", "buscar_en_manual", "listar_mis_tools"],
    "Delegación": ["delegar_tareas_paralelas", "pedir_a_especialista", "consultar_manual_python"],
}

TODAS = {t["function"]["name"]: t["function"].get("description", "") for t in dios.TOOLS}

# Asignar cada tool a su categoría
asignadas = {}
for cat, tools in CATS.items():
    for t in tools:
        if t in TODAS: asignadas[t] = cat
# Las que no encajen → Otros
for t in TODAS:
    if t not in asignadas: asignadas[t] = "Otros"

# Construir manual
md = []
md.append("# MANUAL ECOSISTEMA LOFIPRODUCER")
md.append("> Autogenerado desde `dios.TOOLS`. No editar a mano. Actualizado 2026-11-09.\n")

md.append("## 1. ARQUITECTURA")
md.append("- Cerebro: `scripts/dios.py` (%d tools, ReAct, memoria SQLite)" % len(TODAS))
md.append("- Memoria: `brain/dios_memoria.py` (workspace + episodios + costes + fallos)")
md.append("- Manual: `docs/MANUAL_ECOSISTEMA.md` (este fichero)")
md.append("- Motor LLM: Groq (gpt-oss-120b) → Gemini 3.8 (cascada 8 modelos)")
md.append("- Detectives: `brain/investigador_redes.py` (5 fuentes)")
md.append("- Web: `web_dashboard.py` :8001 + `encuadre_routes.py` Factory OS")
md.append("- Cola: `data/agent/cola_publicacion.db`\n")

md.append("## 2. PIPELINE DIARIO (cron 06:00)")
md.append("`recolector` → `transcribir_groq` → `analista_fase1` → `sintetizador` → `fase2_produccion` → `voz_edge` → `director_arte` (80 seg, 8 estilos) → `render_robusto` → `factory_shorts` → `generar_web_v3` + `dossier` → `mkdocs build` → `git push` → YouTube 20:00.\n")

md.append("## 3. TODAS TUS TOOLS (%d)" % len(TODAS))
md.append("> Usa `listar_mis_tools` en cualquier momento para ver la lista viva.\n")
for cat in CATS:
    tools_cat = [t for t, c in asignadas.items() if c == cat]
    if not tools_cat: continue
    md.append("### " + cat + " (" + str(len(tools_cat)) + ")")
    for t in sorted(tools_cat):
        desc = TODAS.get(t, "")[:140]
        md.append("- **" + t + "**: " + desc)
    md.append("")
otros = [t for t, c in asignadas.items() if c == "Otros"]
if otros:
    md.append("### Otros (" + str(len(otros)) + ")")
    for t in sorted(otros): md.append("- **" + t + "**: " + TODAS.get(t, "")[:140])
    md.append("")

md.append("## 4. MEMORIA (SQLite en data/agent/)")
md.append("| Fichero | Qué guarda | Tool para consultarlo |")
md.append("|---|---|---|")
md.append("| `dios_workspace.json` | última tarea, tools usadas | `ver_mi_workspace` |")
md.append("| `dios_episodios.db` | historial de tareas con resultado | `ver_ultimas_tareas` |")
md.append("| `dios_costes.db` | tokens in/out por tarea | `ver_costes_hoy` |")
md.append("| `dios_fallos.db` | tools que fallaron y por qué | `ver_fallos_similares(prompt)` |")
md.append("")
md.append("Estas DBs se inyectan **automáticamente** en el prompt (compacto, ~200 tokens). No hace falta consultarlas salvo que el usuario pregunte explícitamente.\n")

md.append("## 5. TOOL FALLBACK (automático)")
md.append("Si una tool falla, Dios prueba alternativas antes de rendirse:")
for k, v in dios.TOOL_FALLBACKS.items():
    md.append("- `" + k + "` → " + ", ".join("`" + x + "`" for x in v))
md.append("")

md.append("## 6. REFLECTION LOOP")
md.append("Cada 3 pasos sin éxito, Dios recibe: *'Reflexion: N pasos sin éxito. USA OTRA tool o di por qué no puedes.'* → evita bucles infinitos.\n")

md.append("## 7. AUTO-REPARACIÓN (promote_file)")
md.append("Flujo obligatorio para arreglar el repo:")
md.append("1. `read_file` — inspeccionar")
md.append("2. `write_file` — escribir a `sandbox/`")
md.append("3. `validate_file` — comprobar que parsea")
md.append("4. `promote_file` — **pide confirmación por Telegram + timeout 5 min**")
md.append("5. `documentar_aprendizaje` + `recordar_hecho`")
md.append("**NUNCA** escribir directo al repo. **NUNCA** promote_file sin validate_file.\n")

md.append("## 8. ERRORES CONOCIDOS")
md.append("| Error | Fix |")
md.append("|---|---|")
md.append("| OmniRoute 401 | cascada Groq directa (`_charla_rapida` ya lo hace) |")
md.append("| Groq 429 | 4 keys + retry 5s |")
md.append("| YouTube invalid_grant | `scripts/reautorizar_youtube.py` |")
md.append("| mkdocs 404 imágenes | hook `web/hooks/copy_media.py` |")
md.append("| SDXL refusals | filtro 'lo siento' en `generar_imagen.py` |")
md.append("| Fatiga visual | 8 estilos + seed determinista |")
md.append("| OOM 73f LTX | bajar a 49f |")
md.append("| libcudart.so.12 | LD_LIBRARY_PATH + dataset |")
md.append("| wildcards no expanden | `_expand_globs` en `ejecutor_seguro` |")
md.append("")

md.append("## 9. REGLAS FRODO")
md.append("#3 heredoc <50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #13 no sed URLs · #18 2 fallos → parar · #20 3+ parches → reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u.\n")

md.append("## 10. ESTRUCTURA")
md.append("`scripts/` (pipeline, dios, generar_*) · `brain/` (48 agentes, memoria) · `web/docs/` (blog MkDocs) · `web/dashboard/` (Factory OS) · `output/encuadre/` (producción diaria) · `data/agent/` (DBs, contratos) · `config/` (nichos.json) · `docs/` (este manual).\n")

md.append("## 11. CONTEXTOS DEL DÍA")
md.append("`produccion_{f}` · `seo_{f}` · `redes_{f}` · `dossier_enriquecido_{f}` · `timeline_{f}` · `video_largo_{f}.mp4` · `short_{1..4}_{f}.mp4` · `podcast_{f}.mp3` · `custom_request_{f}.json`.\n")

md.append("## 12. APIS")
md.append("- Groq: `GROQ_API_KEY(_2,_3,_4)` → gpt-oss-120b")
md.append("- Gemini: `GEMINI_API_KEY` → gemini-3.8-flash (cascada 8 modelos)")
md.append("- Cloudflare: `CLOUDFLARE_API_TOKEN` + `ACCOUNT_ID` → AI/SDXL, Pages, Analytics")
md.append("- YouTube: `data/youtube_encuadre_token.json` (refresh obligatorio)\n")

md.append("## 13. REGLAS CON EL USUARIO")
md.append("Pushback si dudas · `py_compile` tras .py · leer antes de modificar · backup antes de zona sagrada · NUNCA borrar sin OK · 3+ parches → reescribir · env vars para tokens · `python3 -u` en Termux.\n")

md.append("## 14. CÓMO ACTUALIZAR ESTE MANUAL")
md.append("Autogenerado desde `dios.TOOLS`. Para regenerar:")
md.append("```bash")
md.append("python3 scripts/gen_manual.py")
md.append("```")
md.append("O pídeselo a Dios: `# auto_regenerar_manual`.\n")

md.append("## 15. CÓMO CREAR UNA TOOL NUEVA (auto)")
md.append("Usa `crear_nueva_tool` con:")
md.append("- `nombre`: snake_case (ej: `saludar`)")
md.append("- `descripcion`: qué hace")
md.append("- `codigo_funcion`: cuerpo Python, ej:")
md.append("```python")
md.append("def _tool_saludar(args):")
md.append("    return f'Hola {args.get(\"nombre\", \"mundo\")}'")
md.append("```")
md.append("- `parametros_json`: schema JSON, ej `{\"nombre\":{\"type\":\"string\"}}`\n")
md.append("Flujo: sandbox → validación → Telegram confirm → regenera manual → disponible próxima ejecución.\n")

pathlib.Path("docs/MANUAL_ECOSISTEMA.md").write_text("\n".join(md), encoding="utf-8")
print("OK manual:", len(md), "líneas |", len(TODAS), "tools |", len(CATS), "categorías")
