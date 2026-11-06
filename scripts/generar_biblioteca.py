import json, os, sys, time, pathlib, urllib.request, urllib.error, random
from PIL import Image, ImageFilter

ROOT = pathlib.Path.home() / "LofiProducer"
OUT = ROOT / "data/agent/ltx_assets/biblioteca_src"
OUT.mkdir(parents=True, exist_ok=True)
AVATARS = ROOT / "data/agent/ltx_assets/avatares"

# Configuración (10 categorías x 6 variantes x 2 aspectos)
CATS = {
    "bunker_operativo": {"av": "avatar_espalda.png", "sc": 0.65, "y": 0.95, "p": ["dark server room, glowing monitors, blue light, empty chair", "basement control room, screens world map, red light", "hacker den, wall monitors, green code, dark", "underground bunker, network gear, wet floor", "surveillance room, TV wall news, dim", "industrial center, cables, servers, teal glow"]},
    "investigacion_forense": {"av": "avatar_tablet.png", "sc": 0.25, "y": 0.55, "p": ["top down desk, newspaper clippings, magnifying glass", "wooden desk, open books, warm flexo light", "forensic table, photos, red strings", "messy desk, coffee mug, notes", "archive room, boxes, dim light", "intelligence desk, maps, pins"]},
    "monitor_amenaza": {"av": "avatar_mascara.png", "sc": 0.50, "y": 0.85, "p": ["close up screen, red alert data, glitch", "dark monitor, green terminal text", "cracked screen, error codes", "surveillance feed, multiple cams", "data breach graphic, skull icon", "warning screen, red triangle"]},
    "callejon_lluvia": {"av": "avatar_perfil.png", "sc": 0.60, "y": 0.95, "p": ["dark alley night, rain, neon reflections", "cyberpunk street, wet asphalt, signs", "urban corner, steam, street lamp", "narrow passage, graffiti, puddles", "backdoor alley, dumpster, mist", "subway entrance, rain, neon"]},
    "oficina_corp": {"av": "avatar_frontal.png", "sc": 0.60, "y": 0.95, "p": ["empty office night, glass walls, city lights", "corporate boardroom, dark, skyline", "cubicle farm, night, emergency lights", "executive office, dark mahogany", "open space office, blue monitors", "corporate lobby, night, marble"]},
    "servidores": {"av": "avatar_3cuartos.png", "sc": 0.60, "y": 0.95, "p": ["server room aisle, green lights, fog", "data center, racks, cables, blue LEDs", "mainframe room, vintage servers", "cold aisle, cooling pipes", "network switch room, blinking lights", "supercomputer, liquid cooling"]},
    "periodico_fisico": {"av": "avatar_frontal.png", "sc": 0.60, "y": 0.95, "p": ["stack newspapers, coffee, window light", "printing press, old paper, dust", "archive library, old books", "newsroom desk, typewriter", "microfilm reader, dark room", "vintage newspaper stand, night"]},
    "hacker_movil": {"av": "avatar_perfil.png", "sc": 0.60, "y": 0.95, "p": ["rooftop night, city skyline, antennas", "balcony, neon signs, rain", "parking roof, city lights", "fire escape, brick wall, night", "bridge at night, cars light trails", "urban rooftop, AC units, night"]},
    "zoom_codigo": {"av": "avatar_mascara.png", "sc": 0.80, "y": 0.90, "p": ["abstract code rain, glowing green, dark", "binary matrix, falling numbers", "neural network visualization, blue", "data stream, neon lines, cyber", "hex dump, green terminal", "encryption algorithm, glowing lines"]},
    "detalle_glove": {"av": "avatar_frontal.png", "sc": 0.90, "y": 1.05, "p": ["black background, minimal, smoke", "dark void, single spotlight", "dramatic shadow, red rim light", "pure black, blue neon edge", "cyberpunk haze, purple light", "pitch black, orange embers"]}
}

ASPECTS = {"16:9": (1344, 768), "9:16": (768, 1344)}
API_URL = "https://api.cloudflare.com/client/v4/accounts/{}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="): return line.split("=", 1)[1].strip()

CF_ACC = _env("CLOUDFLARE_ACCOUNT_ID")
CF_TOK = _env("CLOUDFLARE_API_TOKEN")
if not CF_ACC or not CF_TOK: sys.exit("ERROR: faltan CLOUDFLARE_ACCOUNT_ID o CLOUDFLARE_API_TOKEN en .env")

def gen_fondo(prompt, w, h, seed):
    body = json.dumps({
        "prompt": f"{prompt}, cinematic, photorealistic, no people, no humans, no hackers",
        "negative_prompt": "person, human, hacker, people, face, silhouette, text, letters, watermark",
        "num_steps": 8, "guidance": 8.0, "width": w, "height": h, "seed": seed
    }).encode()
    req = urllib.request.Request(API_URL.format(CF_ACC), data=body, headers={
        "Authorization": f"Bearer {CF_TOK}", "Content-Type": "application/json"
    }, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def componer(fondo_bytes, avatar_path, escala, pos_y, out_path):
    fondo = Image.open(__import__("io").BytesIO(fondo_bytes)).convert("RGBA")
    av = Image.open(avatar_path).convert("RGBA")
    
    # 1. Recortar el avatar a su caja mínima (quitando bordes vacíos)
    bbox = av.getbbox()
    if bbox:
        av = av.crop(bbox)
    
    # 2. Escalar
    target_h = int(fondo.height * escala)
    ratio = target_h / av.height
    target_w = int(av.width * ratio)
    av = av.resize((target_w, target_h), Image.LANCZOS)
    
    # 3. Color grading (tinte sutil)
    bg_blur = fondo.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    tint = Image.new("RGBA", av.size, bg_blur)
    av = Image.blend(av, tint, alpha=0.15)
    
    # 4. Sombra radial suave (solo si el avatar toca el suelo)
    x = (fondo.width - av.width) // 2
    y = int(fondo.height * pos_y) - av.height
    
    if pos_y > 0.8:
        # Crear una capa de sombra del tamaño de los pies
        shadow_w = int(av.width * 0.8)
        shadow_h = int(av.height * 0.05)
        shadow = Image.new("RGBA", (shadow_w, shadow_h), (0,0,0,0))
        
        # Degradado radial manual
        for i in range(shadow_h):
            for j in range(shadow_w):
                dist = ((j - shadow_w/2)**2 / (shadow_w/2)**2 + (i - shadow_h/2)**2 / (shadow_h/2)**2) ** 0.5
                if dist < 1:
                    alpha = int(120 * (1 - dist))
                    shadow.putpixel((j, i), (0, 0, 0, alpha))
        
        # Pegar sombra
        fondo.alpha_composite(shadow, (x + int(av.width*0.1), y + av.height - shadow_h))
    
    # 5. Pegar avatar
    fondo.alpha_composite(av, (x, y))
    
    # 6. Guardar con calidad 95
    fondo.convert("RGB").save(out_path, quality=95)

def run():
    total = len(CATS) * 6 * 2
    i = 0
    for cat, cfg in CATS.items():
        for v_idx, prompt in enumerate(cfg["p"]):
            for asp, (w, h) in ASPECTS.items():
                i += 1
                name = f"{cat}_{v_idx+1:02d}_{asp.replace(':','x')}.jpg"
                out = OUT / name
                if out.exists(): continue
                print(f"[{i}/{total}] {name} ...", flush=True)
                try:
                    # Ajustar aspect ratio: si es 9:16 y la imagen es vertical, ok. Si no, rotamos dimensiones
                    seed = abs(hash(cat + str(v_idx) + asp)) % 1000000
                    fb = gen_fondo(prompt, w, h, seed)
                    componer(fb, AVATARS / cfg["av"], cfg["sc"], cfg["y"], out)
                except Exception as e:
                    print(f"  ERROR: {e}", flush=True)
                    time.sleep(2)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test rápido con solo 2 imágenes
        test = list(CATS.keys())[:2]
        for cat in test:
            cfg = CATS[cat]
            for asp, (w, h) in ASPECTS.items():
                name = f"TEST_{cat}_{asp.replace(':','x')}.jpg"
                print(f"Test: {name}")
                fb = gen_fondo(cfg["p"][0], w, h, 42)
                componer(fb, AVATARS / cfg["av"], cfg["sc"], cfg["y"], OUT / name)
        print("TEST OK. Revisa:", OUT)
    else:
        run()
