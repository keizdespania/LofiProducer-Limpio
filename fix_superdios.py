"""Inyecta las 5 herramientas del Superdios en dios.py."""
import pathlib, ast

p = pathlib.Path("scripts/dios.py")
t = p.read_text()

# ── Schemas ──
schemas = (
    '    {"type": "function", "function": {"name": "sanar_sistema", "description": "Revisa y reinicia Flask y OmniRoute si estan caidos.", "parameters": {"type": "object", "properties": {}}}},\n'
    '    {"type": "function", "function": {"name": "notificar_movil", "description": "Envia notificacion push al movil del usuario.", "parameters": {"type": "object", "properties": {"titulo": {"type": "string"}, "mensaje": {"type": "string"}}, "required": ["titulo", "mensaje"]}}},\n'
    '    {"type": "function", "function": {"name": "leer_rss", "description": "Lee noticias frescas. Fuentes: boe, techcrunch, hackernews, verge.", "parameters": {"type": "object", "properties": {"fuente": {"type": "string"}, "limite": {"type": "integer"}}, "required": ["fuente"]}}},\n'
    '    {"type": "function", "function": {"name": "pedir_a_especialista", "description": "Delegar tarea a un sub-agente especializado. Roles: guionista, seo, auditor, traductor, musico.", "parameters": {"type": "object", "properties": {"rol": {"type": "string"}, "tarea": {"type": "string"}, "contexto": {"type": "string"}}, "required": ["rol", "tarea"]}}},\n'
    '    {"type": "function", "function": {"name": "lanzar_notebook_kaggle", "description": "Crea un notebook con codigo Python y lo ejecuta en Kaggle GPU.", "parameters": {"type": "object", "properties": {"nombre": {"type": "string"}, "codigo_python": {"type": "string"}}, "required": ["nombre", "codigo_python"]}}},\n'
)

if '"name": "sanar_sistema"' not in t:
    idx_fns = t.find("TOOL_FNS = {")
    idx_cierre = t.rfind("]", 0, idx_fns)
    t = t[:idx_cierre] + schemas + t[idx_cierre:]
    print("OK: 5 schemas inyectados")

# ── Funciones ──
funcs = (
    '\ndef _tool_sanar_sistema(args):\n'
    '    from brain.sanador import sanar\n'
    '    return sanar()\n'
    '\ndef _tool_notificar_movil(args):\n'
    '    from brain.notificador import notificar\n'
    '    return notificar(args["titulo"], args["mensaje"])\n'
    '\ndef _tool_leer_rss(args):\n'
    '    from brain.rss_reader import leer_feed\n'
    '    return leer_feed(args["fuente"], args.get("limite", 5))\n'
    '\ndef _tool_pedir_a_especialista(args):\n'
    '    from brain.especialistas import pedir_a_especialista\n'
    '    return pedir_a_especialista(args["rol"], args["tarea"], args.get("contexto", ""))\n'
    '\ndef _tool_lanzar_notebook_kaggle(args):\n'
    '    from brain.kaggle_launcher import lanzar_notebook\n'
    '    return lanzar_notebook(args["nombre"], args["codigo_python"])\n\n'
)

if "def _tool_sanar_sistema" not in t:
    idx_fns = t.find("TOOL_FNS = {")
    t = t[:idx_fns] + funcs + t[idx_fns:]
    print("OK: 5 funciones inyectadas")

# ── Registro en TOOL_FNS ──
ancla = '    "instalar_dependencia": _tool_instalar_dependencia,'
nuevos = (ancla + "\n"
    '    "sanar_sistema": _tool_sanar_sistema,\n'
    '    "notificar_movil": _tool_notificar_movil,\n'
    '    "leer_rss": _tool_leer_rss,\n'
    '    "pedir_a_especialista": _tool_pedir_a_especialista,\n'
    '    "lanzar_notebook_kaggle": _tool_lanzar_notebook_kaggle,')

if '"sanar_sistema": _tool_sanar_sistema' not in t and ancla in t:
    t = t.replace(ancla, nuevos)
    print("OK: 5 herramientas registradas en TOOL_FNS")
elif ancla not in t:
    print("AVISO: No encontre el ancla de instalar_dependencia. Buscando otro cierre...")
    # Fallback: insertar antes del cierre del diccionario
    idx_close = t.find("\n}", t.find("TOOL_FNS = {"))
    insert = ('    "sanar_sistema": _tool_sanar_sistema,\n'
              '    "notificar_movil": _tool_notificar_movil,\n'
              '    "leer_rss": _tool_leer_rss,\n'
              '    "pedir_a_especialista": _tool_pedir_a_especialista,\n'
              '    "lanzar_notebook_kaggle": _tool_lanzar_notebook_kaggle,\n')
    t = t[:idx_close] + insert + t[idx_close:]
    print("OK: 5 herramientas registradas en TOOL_FNS (fallback)")

# ── Regla ──
regla = (
    "\n23. ARSENAL SUPERDIOS (5 herramientas nuevas):\n"
    "    - sanar_sistema(): Si algo falla, usala para reiniciar Flask o OmniRoute.\n"
    "    - notificar_movil(titulo, mensaje): Avisa al usuario al movil cuando termines tareas largas.\n"
    "    - leer_rss(fuente, limite): Lee noticias frescas (boe, techcrunch, hackernews, verge).\n"
    "    - pedir_a_especialista(rol, tarea): Sub-agentes expertos (guionista, seo, auditor, traductor, musico).\n"
    "    - lanzar_notebook_kaggle(nombre, codigo_python): Ejecuta codigo Python en una GPU de Kaggle.\n"
)
if "23. ARSENAL SUPERDIOS" not in t:
    idx = t.rfind('"""')
    t = t[:idx] + regla + t[idx:]
    print("OK: Regla 23 inyectada")

p.write_text(t)
ast.parse(t)
print("OK: Sintaxis final OK")
