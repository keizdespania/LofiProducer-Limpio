"""generar_imagenes_web.py - Genera 3 imagenes por cada post basandose en su tema real."""
import sys, pathlib, datetime, json, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "web" / "media" / "imagenes"
IMG.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def _leer_temas(fecha):
    """Extrae los temas reales de los posts generados hoy."""
    temas = {}
    # Leer dossier
    dossier_path = ROOT / "output" / "encuadre" / f"dossier_{fecha}.json"
    if dossier_path.exists():
        try:
            d = json.loads(dossier_path.read_text())
            temas["dossier"] = d.get("dossier", {}).get("titular_brutal", "Análisis mediático del día")
        except: pass
    # Leer produccion
    prod_path = ROOT / "output" / "encuadre" / f"produccion_{fecha}.json"
    if prod_path.exists():
        try:
            p = json.loads(prod_path.read_text())
            temas["largo"] = p.get("titulo", temas.get("dossier", "El encuadre del día"))
            temas["mediano"] = temas["largo"] # Mismo tema base para variaciones
        except: pass

    # Fallback
    if not temas:
        temas = {"dossier": "Análisis mediático", "largo": "El encuadre del día"}
    return temas

def generar_todas(fecha=None):
    fecha = fecha or FECHA
    from generar_imagen import generar
    from director_fotografia import generar_prompt_visual

    temas = _leer_temas(fecha)
    print(f"Generando 3 imagenes por post para {fecha}...")
    print("=" * 60)

    urls_map = {}

    for tipo, tema in temas.items():
        urls_map[tipo] = []
        # 3 escenas por post (inicio, nudo, fin) para dar variedad
        escenas = [
            f"Plano general: {tema}",
            f"Detalle de periódicos y pantallas: {tema}",
            f"Consecuencias y calles vacías: {tema}"
        ]

        for i, escena in enumerate(escenas, 1):
            prompt = generar_prompt_visual(escena, vertical=False)
            nombre = f"post_{fecha}_{tipo}_{i}.png"
            destino = IMG / nombre

            if destino.exists() and destino.stat().st_size > 50000:
                print(f"  ♻️  {tipo}_{i}: ya existe ({destino.stat().st_size//1024}KB)")
                urls_map[tipo].append(nombre)
                continue

            print(f"  🎨 {tipo}_{i}: generando...", end=" ", flush=True)
            try:
                import shutil
                r = generar(prompt, preset="cinematic", aspect="16:9", canal="encuadre")
                if "OK: " in r:
                    ruta = r.split("OK: ")[1].split(" ")[0]
                    src = pathlib.Path(ruta)
                    if src.exists() and src.stat().st_size > 50000:
                        shutil.copy(src, destino)
                        print(f"✅ {destino.stat().st_size//1024}KB")
                        urls_map[tipo].append(nombre)
                    else:
                        print("⚠️ vacio")
                else:
                    print(f"⚠️ {r[:100]}")
            except Exception as e:
                print(f"❌ {e}")

    # Guardar mapa
    out = IMG / f"web_urls_{fecha}.json"
    out.write_text(json.dumps(urls_map, indent=2, ensure_ascii=False))
    print(f"\n✅ {sum(len(v) for v in urls_map.values())} imagenes web generadas")
    print(f"   Mapa: {out}")
    return urls_map

if __name__ == "__main__":
    ok = generar_todas(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)
