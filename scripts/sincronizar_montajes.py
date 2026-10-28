"""Sincroniza config/nichos.json → config/montajes/<canal>.json."""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NICHOS = ROOT / "config" / "nichos.json"
MONTAJES = ROOT / "config" / "montajes"

DEFAULTS_BY_FORMATO = {
    "video_voz_imagen": {"duracion": 900, "loop_video": True, "fades": {"in": 2.0, "out": 2.0}, "musica_vol": 0.15, "logo_pos": "W-w-30:H-h-30"},
    "video_texto_voz":  {"duracion": 600, "loop_video": True, "fades": {"in": 1.5, "out": 1.5}, "musica_vol": 0.10, "logo_pos": "30:30"},
    "musica_loop":      {"duracion": 3600, "loop_video": True, "fades": {"in": 3.0, "out": 3.0}, "musica_vol": 1.0, "logo_pos": "W-w-30:H-h-30"},
}

BASE = {"ancho": 1920, "alto": 1080, "crf": 20, "intervalo_imagenes": 15, "logo": None}

def _validar_con_ffmpeg(montaje):
    """Clampea crf/duracion según el contrato FFmpeg si existe."""
    contrato_path = ROOT / "data" / "agent" / "ffmpeg_contract.json"
    if not contrato_path.exists(): return montaje
    try: contrato = json.loads(contrato_path.read_text())
    except Exception: return montaje
    rangos = {r["campo"]: r for r in contrato.get("validador", {}).get("reglas", [])}
    out = dict(montaje)
    if "crf" in rangos:
        r = rangos["crf"]
        if out.get("crf", 20) < r["min"]: out["crf"] = r["min"]
        if out.get("crf", 20) > r["max"]: out["crf"] = r["max"]
    return out

def generar_montaje_por_defecto(nicho_cfg):
    """Genera un montaje con defaults inteligentes según formato."""
    formato = nicho_cfg.get("formato", "video_voz_imagen")
    defaults = DEFAULTS_BY_FORMATO.get(formato, DEFAULTS_BY_FORMATO["video_voz_imagen"])
    montaje = dict(BASE)
    montaje.update(defaults)
    return _validar_con_ffmpeg(montaje)

def sincronizar(nombre=None):
    """Genera config/montajes/<canal>.json para cada nicho (o solo uno)."""
    cfg = json.loads(NICHOS.read_text())
    MONTAJES.mkdir(parents=True, exist_ok=True)
    generados = []
    for nicho, cfg_nicho in cfg.items():
        if nicho.startswith("_"): continue
        if nombre and nicho != nombre: continue
        skills = cfg_nicho.get("skills", {})
        montaje = skills.get("montaje") or generar_montaje_por_defecto(cfg_nicho)
        montaje = _validar_con_ffmpeg(montaje)
        # Completar con salida_path
        out = dict(montaje)
        out["salida_path"] = f"output/videos/{nicho}-final.mp4"
        path = MONTAJES / (nicho + ".json")
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
        generados.append(nicho)
    print(f"✅ Sincronizados {len(generados)} montajes: {', '.join(generados)}")
    return generados

if __name__ == "__main__":
    nombre = sys.argv[1] if len(sys.argv) > 1 else None
    sincronizar(nombre)
