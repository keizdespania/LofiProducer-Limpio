#!/usr/bin/env python3
"""gen_manual.py v3 - Manual unificado compacto. Auto-escanea ecosistema real.
Optimizado para tokens: 1 línea por elemento, agrupado por categoría."""
import sys, pathlib, json, subprocess, datetime, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts")); sys.path.insert(0, str(ROOT / "brain"))

def _docstring(path, max_len=100):
    """Primera línea del docstring del módulo."""
    try:
        txt = pathlib.Path(path).read_text(encoding="utf-8", errors="ignore")[:500]
        m = re.search(r'"""(.*?)"""', txt, re.DOTALL)
        if m:
            line = m.group(1).strip().split("\n")[0].strip()
            if line: return line[:max_len]
    except: pass
    return ""

def _scripts():
    """Dict {nombre: descripción} de scripts/*.py."""
    d = {}
    for f in sorted((ROOT/"scripts").glob("*.py")):
        if f.name.startswith("_"): continue
        d[f.stem] = _docstring(f)
    return d

def _brain():
    d = {}
    for f in sorted((ROOT/"brain").glob("*.py")):
        if f.name.startswith("_"): continue
        d[f.stem] = _docstring(f)
    return d

def _contratos():
    out = []
    for f in sorted((ROOT/"data"/"agent").glob("*contract*.json")):
        try:
            d = json.loads(f.read_text())
            v = d.get("version", "?")
            nom = d.get("nombre", f.stem)[:60]
            out.append(f"{f.name} v{v}: {nom}")
        except: pass
    return out

def _endpoints():
    """Endpoints Flask agrupados por prefijo."""
    out = {}
    try:
        txt = (ROOT/"encuadre_routes.py").read_text()
        for m in re.finditer(r'@encuadre_bp\.route\(["\']([^"\']+)', txt):
            ep = m.group(1)
            grupo = ep.split("/")[2] if ep.startswith("/api/") and len(ep.split("/")) > 2 else "otros"
            out.setdefault(grupo, []).append(ep)
    except: pass
    return out

def _crons():
    try:
        r = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        return [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("#")]
    except: return []

def _tools_por_categoria():
    import dios
    TODAS = {t["function"]["name"]: t["function"].get("description", "")[:90] for t in dios.TOOLS}
    CATS = {
        "FS": ["ejecutar_comando","read_file","write_file","validate_file","promote_file"],
        "Web": ["buscar_en_web","buscar_youtube","leer_rss","buscar_repositorio"],
        "Video": ["generar_video","generar_video_rapido","producir_video","producir_video_completo","ensamblar_video_largo","ensamblar_video_final","analizar_video_competencia","subir_youtube"],
        "Audio/Img": ["generar_cancion_kaggle","generar_narracion","generar_imagen"],
        "Blog/Redes": ["publicar_blog_completo","crear_blog_top","publicar_en_redes","procesar_cola_youtube","generar_informe_editorial"],
        "Sistema": ["estado_sistema","sanar_sistema","instalar_dependencia","notificar_movil","ejecutar_limpieza"],
        "Kaggle": ["lanzar_pipeline_kaggle","lanzar_notebook_kaggle"],
        "Canales": ["list_canales","crear_nicho","producir_nicho","evaluar_produccion"],
        "Memoria": ["recordar_hecho","consultar_hechos","documentar_aprendizaje","leer_documentacion","ver_mi_workspace","ver_ultimas_tareas","ver_fallos_similares","ver_costes_hoy"],
        "Auto/Manual": ["consultar_manual_ecosistema","buscar_en_manual","listar_mis_tools","auto_regenerar_manual","crear_nueva_tool","escanear_ecosistema"],
        "Delegación": ["delegar_tareas_paralelas","pedir_a_especialista","consultar_manual_python"],
    }
    asignadas = {}
    for cat, lst in CATS.items():
        for t in lst:
            if t in TODAS: asignadas[t] = cat
    for t in TODAS:
        if t not in asignadas: asignadas[t] = "Otros"
    grupos = {}
    for t, cat in asignadas.items():
        grupos.setdefault(cat, []).append(t)
    return grupos, TODAS

# ═══════════════════════════════════════════
md = []
md.append("# MANUAL ECOSISTEMA LOFIPRODUCER")
md.append(f"> Auto-generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}. NO editar a mano.")
md.append(f"> Regenerar: `python3 scripts/gen_manual.py` o pedir a Dios: `# auto_regenerar_manual`\n")

# 1. ARQUITECTURA
scripts = _scripts(); brain = _brain(); contratos = _contratos()
endpoints = _endpoints(); crons = _crons()
grupos_tools, TODAS_TOOLS = _tools_por_categoria()

md.append("## 1. ARQUITECTURA (6 capas)")
md.append(f"- **Cerebro**: scripts/dios.py ({len(TODAS_TOOLS)} tools, ReAct, SQLite memoria)")
md.append("- **Detective**: brain/investigador_redes.py (YouTube x2 + Trends + Reddit + HN)")
md.append("- **Web**: web_dashboard.py :8001 + encuadre_routes.py (Factory OS)")
md.append("- **Cola**: data/agent/cola_publicacion.db (SQLite FIFO + publish_at)")
md.append("- **Motores**: ACE-Step / Sherpa / SDXL / Wan / LTX / FFmpeg / YouTube / Blogger")
md.append(f"- **Infra**: Kaggle T4 x2 + Cloudflare Pages + GitHub + OAuth")
md.append(f"- **Inventario**: {len(scripts)} scripts · {len(brain)} brain · {len(contratos)} contratos · {sum(len(v) for v in endpoints.values())} endpoints · {len(crons)} crons\n")

# 2. PIPELINE DIARIO
md.append("## 2. PIPELINE DIARIO (cron 06:00)")
md.append("`limpieza_pipeline` → `recolector` → `transcribir_groq` → `analista_fase1` → `sintetizador` → `fase2_produccion` → `voz_edge` → `director_arte` (80 seg) → `render_robusto` → `factory_shorts` → `generar_web_v3` + `dossier` → `actualizar_web_index` → `mkdocs build` → `git push` → YouTube 20:00\n")

# 3. CONTRATOS
md.append(f"## 3. CONTRATOS ({len(contratos)})")
for c in contratos: md.append(f"- `{c}`")
md.append("")

# 4. SCRIPTS CLAVE (compacto: solo los >5KB o con nombre crítico)
md.append(f"## 4. SCRIPTS ({len(scripts)} en scripts/)")
CRITICOS = ["pipeline_encuadre","dios","encuadre_routes","generar_web_v3","generar_web_dossier","generar_imagenes_web","render_robusto","director_arte","director_fotografia","fase2_produccion","sintetizador","analista_fase1","recolector","voz_edge","subir_youtube","publicar_blogger_encuadre","factory_shorts","limpieza_pipeline","gen_manual","rollback","smoke_test","watchdog_pipeline","cola_youtube_auto","indexar_busqueda","cloudflare_stats","agente_ltx_biblioteca"]
for name in CRITICOS:
    if name in scripts:
        d = scripts[name][:80] or "(sin docstring)"
        md.append(f"- `{name}.py`: {d}")
OTROS = [n for n in scripts if n not in CRITICOS]
if OTROS: md.append(f"- *Y {len(OTROS)} scripts más* (usar `escanear_ecosistema('scripts')`)\n")

# 5. BRAIN
md.append(f"## 5. BRAIN ({len(brain)} módulos)")
for name in ["especialistas","dios_memoria","dios_tools_dinamicas","investigador_redes","ejecutor_seguro","llm_gemini","web_search","memoria_db","pruner"]:
    if name in brain:
        md.append(f"- `{name}.py`: {brain[name][:80] or '(sin doc)'}")
md.append("")

# 6. TOOLS (agrupadas)
md.append(f"## 6. TOOLS ({len(TODAS_TOOLS)})")
for cat in ["FS","Web","Video","Audio/Img","Blog/Redes","Sistema","Kaggle","Canales","Memoria","Auto/Manual","Delegación","Otros"]:
    if cat not in grupos_tools: continue
    tools_cat = grupos_tools[cat]
    md.append(f"**{cat}** ({len(tools_cat)}): " + ", ".join(f"`{t}`" for t in tools_cat))
md.append("")

# 7. ENDPOINTS
md.append(f"## 7. ENDPOINTS Factory ({sum(len(v) for v in endpoints.values())})")
for grupo, eps in endpoints.items():
    md.append(f"- `{grupo}`: " + ", ".join(eps[:8]) + ("..." if len(eps) > 8 else ""))
md.append("")

# 8. CRONS
md.append(f"## 8. CRONS ACTIVOS ({len(crons)})")
for c in crons: md.append(f"- `{c}`")
md.append("")

# 9. MEMORIA
md.append("## 9. MEMORIA DIOS (data/agent/)")
md.append("- `dios_workspace.json` → `ver_mi_workspace`")
md.append("- `dios_episodios.db` → `ver_ultimas_tareas`")
md.append("- `dios_costes.db` → `ver_costes_hoy`")
md.append("- `dios_fallos.db` → `ver_fallos_similares`")
md.append("Se inyecta auto ~200 tokens en prompt. No consultar salvo petición.\n")

# 10. AUTO-REPARACIÓN
md.append("## 10. AUTO-REPARACIÓN")
md.append("1. `read_file` → inspeccionar")
md.append("2. `write_file` → sandbox/")
md.append("3. `validate_file` → ast.parse")
md.append("4. `promote_file` → **Telegram confirm + timeout 5min**")
md.append("5. `documentar_aprendizaje` + `recordar_hecho`")
md.append("NUNCA escribir directo al repo. NUNCA promote sin validate.\n")

# 11. ERRORES CONOCIDOS
md.append("## 11. ERRORES CONOCIDOS")
ERRORES = [
    ("OmniRoute 401","cascada Groq directa"),
    ("Groq 429","4 keys + retry 5s"),
    ("YT invalid_grant","reautorizar_youtube.py"),
    ("mkdocs 404","hook copy_media"),
    ("SDXL refusals","filtro 'lo siento'"),
    ("fatiga visual","8 estilos + seed"),
    ("OOM 73f LTX","bajar a 49f"),
    ("libcudart.so.12","LD_LIBRARY_PATH + dataset"),
    ("wildcards no expanden","_expand_globs en ejecutor"),
    ("render_work 399MB/día","fix en render_robusto"),
]
for e, f in ERRORES: md.append(f"- {e} → {f}")
md.append("")

# 12. REGLAS FRODO
md.append("## 12. REGLAS FRODO (críticas)")
md.append("#3 heredoc<50L · #5 py_compile · #7 no push sin OK · #8 no rehacer · #11 $HOME/tmp · #13 no sed URLs · #18 2 fallos→parar · #20 3+parches→reescribir · #35 Groq>OmniRoute · #39 User-Agent Chrome · #77 python3 -u\n")

# 13. CONTEXTOS DEL DÍA
md.append("## 13. CONTEXTOS DÍA (output/encuadre/)")
md.append("`produccion_{f}` (18 escenas+guion+shorts) · `seo_{f}` (título+desc+tags) · `redes_{f}` (textos por red) · `dossier_enriquecido_{f}` (top3+citas+medios) · `timeline_{f}` · `video_largo_{f}.mp4` · `short_{1..4}_{f}.mp4` · `podcast_{f}.mp3` · `custom_request_{f}.json`\n")

# 14. APIS EXTERNAS
md.append("## 14. APIS")
md.append("- **Groq**: `GROQ_API_KEY(_2,_3,_4)` → gpt-oss-120b (primario)")
md.append("- **Gemini**: `GEMINI_API_KEY` → gemini-3.8-flash (cascada 8 modelos)")
md.append("- **Cloudflare**: `CLOUDFLARE_API_TOKEN` + `ACCOUNT_ID` → SDXL, Pages, Analytics")
md.append("- **Kaggle**: `KAGGLE_USERNAME` / `KAGGLE_KEY` (2 cuentas)")
md.append("- **YouTube/Blogger**: `data/youtube_encuadre_token.json` (refresh obligatorio)\n")

# 15. COMANDOS CRÍTICOS
md.append("## 15. COMANDOS CRÍTICOS")
cmds = [
    "sv restart keiz-web",
    "python3 scripts/dios.py \"tu peticion\"",
    "python3 scripts/pipeline_encuadre.py",
    "python3 scripts/limpieza_pipeline.py --dry-run",
    "python3 scripts/gen_manual.py",
    "python3 scripts/rollback.py snapshot|listar|rollback <tag>",
    "python3 scripts/smoke_test.py",
    "curl http://127.0.0.1:8001/api/dashboard",
]
for c in cmds: md.append(f"- `{c}`")
md.append("")

# 16. LIMPIEZA
md.append("## 16. LIMPIEZA (piloto automático)")
md.append("Ejecutada al inicio del pipeline + cron domingos 05:00:")
md.append("- **Borra**: <ayer + `render_work/`, `clips/`, `audios/`, `musica_temp/`, `web/site/`, `web/web/`, `.tmp.mp4`")
md.append("- **Protege**: `data/agent/`, `config/`, `scripts/`, `brain/`, `web/dashboard/`, `output/videos/biblioteca/` (LTX), `output/nichos/`")
md.append("- **Rolling 2 días**: mantiene HOY + AYER\n")

# 17. INVENTARIO
md.append("## 17. INVENTARIO (auto)")
md.append(f"- {len(scripts)} scripts · {len(brain)} brain · {len(contratos)} contratos")
md.append(f"- {sum(len(v) for v in endpoints.values())} endpoints · {len(crons)} crons · {len(TODAS_TOOLS)} tools")
md.append(f"- Generado: {datetime.datetime.now().isoformat()[:19]}\n")

# 17b. RECIPES (tareas típicas)
md.append("## 17b. RECIPES (tareas comunes, pasos exactos)")
RECIPES = [
    ("Añadir nicho", "editar config/nichos.json + crear output/nichos/<id>/canal.json + verificar con list_canales"),
    ("Crear video completo", "producir_video_completo(nicho, tema) hace todo: guion+seo+voz+musica+video+YT"),
    ("Solo un short", "generar_video(nicho, vertical=True) → ensamblar_video_final → subir_youtube(short)"),
    ("Solo audio/musica", "generar_cancion_kaggle(prompt, preset) o generar_narracion(texto)"),
    ("Solo imagen", "generar_imagen(prompt, preset, aspect)"),
    ("Publicar blog", "publicar_blog_completo(tema) o crear_blog_top(tema) para quality gate >=8"),
    ("Regenerar SEO dia", "ejecutar_comando('python3 scripts/generar_titulo_seo.py FECHA')"),
    ("Subir pendientes YT", "procesar_cola_youtube() o ejecutar_comando('python3 scripts/cola_youtube_auto.py')"),
    ("Buscar en historico", "buscar_en_web(query) NO. Usa ejecutar_comando('python3 scripts/indexar_busqueda.py') + consultar_manual_ecosistema"),
    ("Rollback codigo", "ejecutar_comando('python3 scripts/rollback.py listar') → rollback <tag>"),
    ("Ver logs pipeline", "ejecutar_comando('tail -50 data/logs/pipeline.log')"),
    ("Ver estado sistema", "estado_sistema() o sanar_sistema() si hay fallos"),
    ("Limpiar disco", "ejecutar_limpieza(dry_run=True) primero, luego sin dry_run"),
    ("Cambiar home/blog", "CMS del dashboard o write_file a web/docs/index.md + promote_file"),
    ("Regenerar manual", "auto_regenerar_manual()"),
]
for nombre, pasos in RECIPES:
    md.append(f"- **{nombre}**: {pasos}")
md.append("")

# 18. REGLAS CON USUARIO
md.append("## 18. REGLAS CON USUARIO")
md.append("Pushback si dudas · leer antes de modificar · backup zona sagrada · NUNCA borrar sin OK · 3+ parches → reescribir · env vars para tokens · `python3 -u` en Termux\n")

pathlib.Path(ROOT/"docs"/"MANUAL_ECOSISTEMA.md").write_text("\n".join(md), encoding="utf-8")
print(f"OK manual: {len(md)} líneas | {len(scripts)} scripts | {len(brain)} brain | {len(contratos)} contratos | {len(TODAS_TOOLS)} tools | ~{len(chr(10).join(md))//4} tokens")
