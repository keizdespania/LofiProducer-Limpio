"""provisionar_canal.py - Auto-provisiona un canal nuevo."""
import sys, json, pathlib, shutil
ROOT = pathlib.Path(__file__).resolve().parent.parent

def provisionar(nombre, nicho="ia_news", plataformas=None, oauth_token=None):
    """Crea toda la estructura para un canal nuevo."""
    if not nombre: return {"error": "falta nombre"}
    nombre = nombre.strip().lower().replace(" ", "_").replace("-", "_")
    plataformas = plataformas or ["youtube", "blogger"]
    
    resultado = {"canal": nombre, "nicho": nicho, "plataformas": plataformas, "acciones": []}
    
    # 1. config/montajes/<canal>.json
    montaje_path = ROOT / "config" / "montajes" / (nombre + ".json")
    if not montaje_path.exists():
        base = ROOT / "config" / "montajes" / (nicho + ".json")
        if base.exists():
            receta = json.loads(base.read_text())
        else:
            receta = {"nombre": nombre, "ancho": 1080, "alto": 1920, "crf": 20, "duracion": 60, "loop_video": True, "crop_blur": True, "fades": {"in": 0.3, "out": 0.3}, "musica_vol": 0.12, "logo": None, "logo_pos": "W-w-30:30", "subtitulos": True, "salida_path": "output/nichos/" + nombre + "/final.mp4"}
        receta["nombre"] = nombre
        receta["salida_path"] = "output/nichos/" + nombre + "/final.mp4"
        montaje_path.write_text(json.dumps(receta, indent=2, ensure_ascii=False))
        resultado["acciones"].append("creado config/montajes/" + nombre + ".json")
    
    # 2. Añadir a config/nichos.json
    nichos_path = ROOT / "config" / "nichos.json"
    nichos = json.loads(nichos_path.read_text())
    if nombre not in nichos:
        base_nicho = nichos.get(nicho, {})
        nuevo_nicho = {
            "nombre": nombre.replace("_", " ").title(),
            "formato": base_nicho.get("formato", "video_voz"),
            "duracion": base_nicho.get("duracion", 60),
            "tono": base_nicho.get("tono", "neutral"),
            "queries_youtube": base_nicho.get("queries_youtube", []),
            "subreddits": base_nicho.get("subreddits", []),
            "keywords_trends": base_nicho.get("keywords_trends", []),
            "skills": base_nicho.get("skills", {}),
            "plataformas": plataformas,
            "oauth_configured": bool(oauth_token),
        }
        nichos[nombre] = nuevo_nicho
        nichos_path.write_text(json.dumps(nichos, indent=2, ensure_ascii=False))
        resultado["acciones"].append("anadido a config/nichos.json")
    
    # 3. Carpeta output/nichos/<canal>/
    out_dir = ROOT / "output" / "nichos" / nombre
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "manifest.json").write_text(json.dumps({"canal": nombre, "nicho": nicho, "creado": str(ROOT)}, indent=2))
    resultado["acciones"].append("creado output/nichos/" + nombre + "/")
    
    # 4. Guardar OAuth si se pasa
    if oauth_token:
        tokens_dir = ROOT / "data" / "oauth"
        tokens_dir.mkdir(parents=True, exist_ok=True)
        (tokens_dir / (nombre + "_youtube.json")).write_text(json.dumps({"canal": nombre, "token": oauth_token}, indent=2))
        resultado["acciones"].append("guardado OAuth en data/oauth/" + nombre + "_youtube.json")
    
    return {"status": "ok", "canal": nombre, "acciones": resultado["acciones"]}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: provisionar_canal.py <nombre> [nicho]")
        sys.exit(1)
    nombre = sys.argv[1]
    nicho = sys.argv[2] if len(sys.argv) > 2 else "ia_news"
    print(json.dumps(provisionar(nombre, nicho), indent=2, ensure_ascii=False))
