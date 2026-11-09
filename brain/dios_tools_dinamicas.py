"""dios_tools_dinamicas.py - Carga tools desde data/agent/dios_tools_dinamicas.py.
Si el fichero no existe o falla, devuelve vacío. Dios nunca peta por esto."""
import importlib.util, pathlib, sys, traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent
DYN_PATH = ROOT / "data" / "agent" / "dios_tools_dinamicas.py"


def cargar_tools_dinamicas():
    """Devuelve (TOOLS_LIST, TOOL_FNS_DICT) desde el fichero dinámico. Fail-safe."""
    if not DYN_PATH.exists():
        return [], {}
    try:
        spec = importlib.util.spec_from_file_location("dios_tools_dinamicas_dyn", str(DYN_PATH))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tools = getattr(mod, "TOOLS_DINAMICAS", []) or []
        fns = getattr(mod, "TOOL_FNS_DINAMICAS", {}) or {}
        # Sanity: solo dicts con function.name y handlers callables
        tools = [t for t in tools if isinstance(t, dict) and "function" in t]
        fns = {k: v for k, v in fns.items() if callable(v)}
        return tools, fns
    except Exception:
        print(f"   [dyn] ERROR cargando {DYN_PATH.name}:")
        traceback.print_exc()
        return [], {}


def persistir_tool(nombre, descripcion, codigo_funcion, parametros_json):
    """Añade una tool nueva al fichero dinámico. Devuelve (ok, mensaje)."""
    import json as _j, ast as _ast
    # 1. Validar que el código parsea
    try:
        _ast.parse(codigo_funcion)
    except SyntaxError as e:
        return False, f"SyntaxError en codigo_funcion: {e}"
    # 2. Validar JSON
    try:
        params = _j.loads(parametros_json) if isinstance(parametros_json, str) else parametros_json
        if not isinstance(params, dict):
            return False, "parametros_json debe ser dict"
    except Exception as e:
        return False, f"parametros_json invalido: {e}"
    # 3. Nombre limpio
    nombre = nombre.strip().replace(" ", "_")
    if not nombre.replace("_", "").isalnum():
        return False, f"nombre '{nombre}' debe ser snake_case alfanumérico"
    handler = "_tool_" + nombre
    # 4. Cargar contenido actual o crear cabecera
    if DYN_PATH.exists():
        contenido = DYN_PATH.read_text(encoding="utf-8")
    else:
        contenido = '''"""TOOLS DINAMICAS - Autogeneradas por Dios. No editar a mano."""
TOOLS_DINAMICAS = []
TOOL_FNS_DINAMICAS = {}

'''
    # 5. Rechazar duplicado
    if f'"name": "{nombre}"' in contenido:
        return False, f"Ya existe tool '{nombre}'"
    # 6. Construir bloque de tool declarativa
    tool_decl = _j.dumps({
        "type": "function",
        "function": {
            "name": nombre,
            "description": descripcion,
            "parameters": {"type": "object", "properties": params, "required": list(params.keys())},
        },
    }, ensure_ascii=False, indent=4)
    # 7. Construir append
    bloque = (
        f"\n# === TOOL {nombre} (auto 2026-11-09) ===\n"
        f"{codigo_funcion.strip()}\n"
        f"TOOLS_DINAMICAS.append({tool_decl})\n"
        f"TOOL_FNS_DINAMICAS['{nombre}'] = {handler}\n"
    )
    contenido += bloque
    # 8. Validar que el todo parsea antes de escribir
    try:
        _ast.parse(contenido)
    except SyntaxError as e:
        return False, f"SyntaxError tras append: {e}. Revisa codigo_funcion."
    # 9. Escribir
    DYN_PATH.parent.mkdir(parents=True, exist_ok=True)
    DYN_PATH.write_text(contenido, encoding="utf-8")
    return True, f"Tool '{nombre}' persistida en {DYN_PATH.name}. Se cargara en el proximo arranque."
