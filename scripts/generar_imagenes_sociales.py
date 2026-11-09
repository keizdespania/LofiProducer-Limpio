#!/usr/bin/env python3
"""Genera 8 imagenes SDXL para redes: 1 largo 16:9 + 4 shorts 9:16 + 3 posts 1:1."""
import json, pathlib, sys, re
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre" / "social"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "brain"))
sys.path.insert(0, str(ROOT / "scripts"))
from prompt_thumbnail import generar_prompt

ASPECTS = {
    "largo": ("16:9", "16:9 widescreen, horizontal composition"),
    "short": ("9:16", "9:16 vertical, portrait composition for mobile"),
    "post":  ("1:1",  "1:1 square, centered composition"),
}

def _cargar(fecha):
    prod = {}
    p = ROOT / "output" / "encuadre" / f"produccion_{fecha}.json"
    if p.exists():
        try: prod = json.loads(p.read_text())
        except: pass
    return prod

def _gen(prompt, aspect, destino):
    import subprocess as _sp, shutil
    try:
        r = _sp.run(["python3", "scripts/generar_imagen.py", prompt, "--aspect", aspect, "--preset", "cinematic"],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        m = re.search(r'OK:\s*(\S+)', r.stdout or "")
        if not m:
            return None, (r.stdout or r.stderr or "")[-200:]
        src = pathlib.Path(m.group(1))
        if not src.exists(): return None, "no existe"
        shutil.copy2(src, destino)
        return destino, None
    except Exception as e:
        return None, str(e)

def main(fecha=None):
    import datetime
    fecha = fecha or datetime.date.today().isoformat()
    prod = _cargar(fecha)
    dossier = prod.get("dossier", {})
    titular = dossier.get("titular_brutal", "Analisis del dia")

    print(f"[1/8] Largo 16:9...")
    prompt = re.sub(r'\b16:9\b.*$', ASPECTS["largo"][1] + ", no text", generar_prompt(titular, tipo="largo"))
    dest = OUT / f"{fecha}_largo.png"
    if dest.exists() and dest.stat().st_size > 30000:
        print(f"     ya existe {dest.name}")
    else:
        r, err = _gen(prompt, "16:9", dest)
        print(f"     {'OK ' + dest.name if r else 'FAIL ' + (err or '')[:100]}")

    shorts = prod.get("shorts_finales", [])
    for i, s in enumerate(shorts[:4]):
        print(f"[{i+2}/8] Short {i+1} 9:16 ({s.get('tipo','')})...")
        tema = s.get("hook") or titular
        prompt = re.sub(r'\b16:9\b.*$', ASPECTS["short"][1] + ", no text", generar_prompt(tema, tipo="short"))
        dest = OUT / f"{fecha}_short_{i+1}.png"
        if dest.exists() and dest.stat().st_size > 30000:
            print(f"     ya existe {dest.name}")
        else:
            r, err = _gen(prompt, "9:16", dest)
            print(f"     {'OK ' + dest.name if r else 'FAIL ' + (err or '')[:100]}")

    for i, (slug, tipo, tema) in enumerate([
        ("largo", "Largo", titular),
        ("dossier", "Dossier", dossier.get("resumen_ejecutivo", titular)[:120]),
        ("mediano", "Mediano", f"Analisis sobre {titular[:100]}"),
    ]):
        print(f"[{i+6}/8] Post {tipo} 1:1...")
        prompt = re.sub(r'\b16:9\b.*$', ASPECTS["post"][1] + ", no text", generar_prompt(tema, tipo="post"))
        dest = OUT / f"{fecha}_post_{slug}.png"
        if dest.exists() and dest.stat().st_size > 30000:
            print(f"     ya existe {dest.name}")
        else:
            r, err = _gen(prompt, "1:1", dest)
            print(f"     {'OK ' + dest.name if r else 'FAIL ' + (err or '')[:100]}")

    idx = {}
    for f in sorted(OUT.glob(f"{fecha}_*.png")):
        slug = f.stem.replace(f"{fecha}_", "")
        idx[slug] = f"/output/encuadre/social/{f.name}"
    (OUT / f"{fecha}_index.json").write_text(json.dumps(idx, indent=2, ensure_ascii=False))
    print(f"\nOK indice: {len(idx)} imagenes -> {fecha}_index.json")
    for k, v in idx.items(): print(f"   {k}: {v}")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
