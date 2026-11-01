"""generar_imagenes_shorts.py - 4 fondos/día (uno por short, según ángulo)."""
import sys, pathlib, datetime, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "web" / "media" / "imagenes"
IMG.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# 4 fondos, uno por ángulo del short. Prompts fijos.
FONDOS = {
    1: ("controversia", "shattered boardroom, overturned chairs, broken glass, red emergency lighting, dramatic, cinematic, no text"),
    2: ("urgencia", "wall of broken TV screens, static, breaking news red alert, sparks, cinematic, no text"),
    3: ("justicia", "giant broken scales of justice, falling paper currency, red spotlight, dark background, cinematic, no text"),
    4: ("curiosidad", "infinite library, floating books, warm light filtering through dust, cinematic, no text"),
}

def generar_todos(fecha=None):
    fecha = fecha or FECHA
    from generar_imagen import generar
    
    print(f"Generando 4 fondos de shorts para {fecha}...")
    print("=" * 60)
    
    rutas = {}
    for num, (angulo, prompt) in FONDOS.items():
        nombre = f"short_fondo_{num}_{fecha}_{angulo}.png"
        destino = IMG / nombre
        
        if destino.exists() and destino.stat().st_size > 50000:
            print(f"  ♻️  Short {num} ({angulo}): ya existe")
            rutas[num] = str(destino)
            continue
        
        print(f"  🎨 Short {num} ({angulo}): generando...", end=" ", flush=True)
        try:
            ok = generar(prompt, str(destino))
            if ok and destino.exists() and destino.stat().st_size > 50000:
                print(f"✅ {destino.stat().st_size//1024}KB")
                rutas[num] = str(destino)
            else:
                # Fallback: usar short_bg_futurista.png
                fallback = IMG / "short_bg_futurista.png"
                if fallback.exists():
                    rutas[num] = str(fallback)
                    print("⚠️ fallback a short_bg_futurista.png")
        except Exception as e:
            print(f"❌ {e}")
            fallback = IMG / "short_bg_futurista.png"
            if fallback.exists():
                rutas[num] = str(fallback)
    
    out = IMG / f"short_urls_{fecha}.json"
    out.write_text(json.dumps(rutas, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(rutas)}/4 fondos listos")
    return rutas

if __name__ == "__main__":
    ok = generar_todos(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)