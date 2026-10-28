"""Evaluador de producción: 5 herramientas para que Dios decida antes de gastar GPU."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRATOS = {
    "musica": "acestep_contract.json", "voz": "sherpa_contract.json",
    "imagen": "image_contract.json", "video": "video_contract.json",
    "ffmpeg": "ffmpeg_contract.json", "youtube": "youtube_contract.json",
    "blogger": "blogger_contract.json", "pixabay": "pixabay_contract.json",
}

def _cargar(nombre):
    p = ROOT / "data" / "agent" / nombre
    return json.loads(p.read_text()) if p.exists() else {}

def _nicho(nicho):
    d = json.loads((ROOT / "config" / "nichos.json").read_text())
    cfg = d.get(nicho, {})
    base = cfg.get("extends")
    if base and base in d.get("_bases", {}):
        merged = dict(d["_bases"][base]); merged.update(cfg); return merged
    return cfg

# ═══ HERRAMIENTA 1: Coherencia prompt vs preset ═══
def evaluar_coherencia(prompt, preset, motor):
    contrato = _cargar(CONTRATOS.get(motor, ""))
    p_info = (contrato.get("presets") or {}).get(preset) if preset else None
    if not p_info:
        return {"nivel": "🟡", "motivo": f"Preset '{preset}' no encontrado en {motor}", "sugerencia": "Revisa el contrato o elige otro preset"}
    prompt_lower = (prompt or "").lower()
    # Buscar coherencia semántica simple
    anti = ["hiphop", "trap", "metal"] if preset in ("piano", "ambient") else []
    if any(a in prompt_lower for a in anti):
        return {"nivel": "🔴", "motivo": f"Prompt con '{anti[0]}' no encaja con preset '{preset}'", "sugerencia": "Cambiar preset o prompt"}
    return {"nivel": "🟢", "motivo": f"Coherente con preset '{preset}'"}

# ═══ HERRAMIENTA 2: Presupuesto de cuota ═══
def evaluar_presupuesto(motor, duracion=0, cantidad=1):
    costes = {"musica": 1, "video": 1, "imagen": 0, "voz": 0}
    coste_base = costes.get(motor, 0)
    if coste_base == 0:
        return {"nivel": "🟢", "motivo": f"{motor} no usa GPU de Kaggle", "cuota_min": 0}
    cuota = coste_base * cantidad * 30  # ~30 min por kernel
    if cuota > 240:  # >4h
        return {"nivel": "🔴", "motivo": f"{cuota} min de GPU ({cantidad} kernels)", "sugerencia": f"Usar batch: agrupar en {(cantidad+4)//5} kernels"}
    if cuota > 120:
        return {"nivel": "🟡", "motivo": f"{cuota} min de GPU", "sugerencia": "Considerar batch"}
    return {"nivel": "🟢", "motivo": f"{cuota} min de GPU"}

# ═══ HERRAMIENTA 3: Calidad del prompt ═══
def evaluar_calidad_prompt(prompt, motor):
    if not prompt or len(prompt) < 10:
        return {"nivel": "🔴", "motivo": "Prompt demasiado corto", "sugerencia": "Añadir sujeto + acción + detalle"}
    p = prompt.lower()
    checks = {
        "musica": ["estilo", "instrumentos", "mood", "bpm"],
        "video": ["sujeto", "movimiento", "cámara", "iluminación"],
        "imagen": ["sujeto", "estilo", "iluminación"],
    }
    esperados = checks.get(motor, [])
    if not esperados:
        return {"nivel": "🟢", "motivo": "Sin validación específica"}
    encontrados = sum(1 for e in esperados if e in p or len(p) > 40)
    if encontrados < 2:
        return {"nivel": "🟡", "motivo": f"Prompt genérico (falta detalle)", "sugerencia": f"Añadir: {', '.join(esperados[:2])}"}
    return {"nivel": "🟢", "motivo": "Prompt detallado"}

# ═══ HERRAMIENTA 4: Encaje con nicho ═══
def evaluar_encaje_nicho(plan, nicho):
    if not nicho:
        return {"nivel": "🟢", "motivo": "Sin nicho especificado"}
    cfg = _nicho(nicho)
    skills = cfg.get("skills", {}).get("presets", {})
    incoherentes = []
    for motor, preset in (plan or {}).items():
        esperado = skills.get(motor)
        if esperado and preset and preset != esperado:
            incoherentes.append(f"{motor}: esperado '{esperado}', tienes '{preset}'")
    if incoherentes:
        return {"nivel": "🟡", "motivo": "Presets diferentes al ADN del nicho", "detalle": incoherentes}
    return {"nivel": "🟢", "motivo": f"Presets coherentes con '{nicho}'"}

# ═══ HERRAMIENTA 5: Alternativas ═══
def consultar_alternativas(motor, preset_actual):
    contrato = _cargar(CONTRATOS.get(motor, ""))
    presets = list((contrato.get("presets") or {}).keys())
    if not presets:
        return []
    return [p for p in presets if p != preset_actual][:3]

# ═══ ORQUESTADORA ═══
def evaluar_produccion(prompt, motor, preset=None, nicho=None, cantidad=1, duracion=0):
    plan_presets = {motor: preset} if preset else {}
    informe = {
        "coherencia": evaluar_coherencia(prompt, preset, motor),
        "presupuesto": evaluar_presupuesto(motor, duracion, cantidad),
        "calidad": evaluar_calidad_prompt(prompt, motor),
        "encaje_nicho": evaluar_encaje_nicho(plan_presets, nicho),
        "alternativas": consultar_alternativas(motor, preset) if preset else [],
    }
    # Veredicto global
    niveles = [informe[k]["nivel"] for k in ("coherencia", "presupuesto", "calidad", "encaje_nicho")]
    if "🔴" in niveles:
        informe["veredicto"] = "🔴 RECHAZADO"
        informe["accion"] = "Revisar los 🔴 antes de producir"
    elif "🟡" in niveles:
        informe["veredicto"] = "🟡 APROBADO CON AVISOS"
        informe["accion"] = "Puedes producir pero revisa los avisos"
    else:
        informe["veredicto"] = "🟢 APROBADO"
        informe["accion"] = "Listo para producir"
    return informe

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: evaluar_produccion.py <prompt> <motor> [preset] [nicho]")
        sys.exit(1)
    import json as _j
    r = evaluar_produccion(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else None, sys.argv[4] if len(sys.argv)>4 else None)
    print(_j.dumps(r, indent=2, ensure_ascii=False))
