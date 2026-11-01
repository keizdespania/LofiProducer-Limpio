"""generar_imagenes_web.py - Genera 6 imagenes/dia para web/blogger (van a catbox)."""
import sys, pathlib, datetime, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
IMG = ROOT / "web" / "media" / "imagenes"
IMG.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Prompts fijos (sin LLM, sin safety filters)
PROMPTS = {
    "arquetipo": "anonymous man silhouette, red grid background, black and white, dramatic lighting, wanted poster aesthetic, no face, no text",
    "collage": "newspaper clippings collage, red stamps, black background, chaotic, dramatic lighting, no readable text",
    "politica": "anonymous politician at podium silhouette, dramatic side lighting, red tie, dark background, cinematic, no text",
    "economia": "stock market screens red falling, trader silhouette, dark blue tones, cinematic, no text",
    "medios": "vintage TV wall with static, newspapers scattered, red accent, moody, cinematic, no text",
    "geopolitica": "world map hologram, red dots, dark room, cinematic, no text",
}

def generar_todas(fecha=None):
    fecha = fecha or FECHA
    from generar_imagen import generar
    
    print(f"Generando 6 imagenes web para {fecha}...")
    print("=" * 60)
    
    urls = {}
    for tipo, prompt in PROMPTS.items():
        nombre = f"web_{fecha}_{tipo}.png"
        destino = IMG / nombre
        
        if destino.exists() and destino.stat().st_size > 50000:
            print(f"  ♻️  {tipo}: ya existe ({destino.stat().st_size//1024}KB)")
            urls[tipo] = nombre
            continue
        
        print(f"  🎨 {tipo}: generando...", end=" ", flush=True)
        try:
            ok = generar(prompt, str(destino))
            if ok and destino.exists() and destino.stat().st_size > 50000:
                print(f"✅ {destino.stat().st_size//1024}KB")
                urls[tipo] = nombre
            else:
                print("⚠️ vacio")
        except Exception as e:
            print(f"❌ {e}")
    
    # Guardar mapa
    out = IMG / f"web_urls_{fecha}.json"
    out.write_text(json.dumps(urls, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(urls)}/6 imagenes web generadas")
    print(f"   Mapa: {out}")
    return urls

if __name__ == "__main__":
    ok = generar_todas(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)