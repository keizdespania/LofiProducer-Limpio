"""segmentar_imagenes.py - Segmenta voz en ~72 trozos de 10s + 1 concepto visual cada uno."""
import json, pathlib, sys, re, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"
CHUNK_SEG = 10.0


def _extraer_frases(ass_path):
    """Agrupa palabras del ASS en frases de ~10s."""
    if not ass_path.exists(): return []
    frases = []
    buffer = []
    t_ini = None
    t_fin = None
    for line in ass_path.read_text().splitlines():
        m = re.match(r'Dialogue: 0,(\d+):(\d+):([\d.]+),(\d+):(\d+):([\d.]+),.*?\}(.*)$', line)
        if not m: continue
        start = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        end = int(m.group(4))*3600 + int(m.group(5))*60 + float(m.group(6))
        palabra = m.group(7).strip()
        if not palabra: continue
        if t_ini is None:
            t_ini = start
            buffer = []
        buffer.append(palabra)
        t_fin = end
        dur_actual = t_fin - t_ini
        termina_frase = palabra.endswith(('.', '?', '!'))
        if dur_actual >= CHUNK_SEG or termina_frase:
            frases.append({"inicio": round(t_ini, 2), "fin": round(t_fin, 2), "texto": " ".join(buffer)})
            t_ini = None
            buffer = []
    if buffer and t_ini is not None:
        frases.append({"inicio": round(t_ini, 2), "fin": round(t_fin, 2), "texto": " ".join(buffer)})
    return frases


def _conceptos_visuales(frases):
    """1 llamada LLM por frase -> concepto visual en ingles."""
    print(f"[seg] {len(frases)} frases, generando conceptos...", flush=True)
    for i, f in enumerate(frases):
        prompt = (
            'Devuelve SOLO una descripcion visual en INGLES de 8-15 palabras, formato Subject + Action + Environment + Lighting + Style. '
            'Sin comillas, sin explicaciones.'
        )
        try:
            r = pedir_a_especialista("disenador_visual", prompt, contexto=f["texto"], proveedor="omni")
            r = r.strip().strip('"').strip("'")
            if len(r) > 15 and not re.search(r'[ñáéíóú]', r.lower()):
                f["concepto_visual"] = r[:150]
            else:
                f["concepto_visual"] = f"newspaper headline about media, {i} composition, cinematic"
        except Exception:
            f["concepto_visual"] = f"newspaper headline about media, {i} composition, cinematic"
        if i % 10 == 0: print(f"  [{i+1}/{len(frases)}] {f['concepto_visual'][:60]}", flush=True)
    return frases


def _generar_imagenes(frases):
    """1 imagen SDXL por frase."""
    from generar_imagen import generar
    img_dir = ROOT / "web" / "media" / "imagenes"
    img_dir.mkdir(parents=True, exist_ok=True)
    for i, f in enumerate(frases):
        n = i + 1
        destino = img_dir / f"seg_{n:03d}.png"
        if destino.exists(): continue
        print(f"  [{n}/{len(frases)}] {f['concepto_visual'][:60]}", flush=True)
        try:
            r = generar(f["concepto_visual"] + ", cinematic, no text, high detail",
                        preset="cinematic", aspect="16:9", canal="encuadre")
            if "OK: " in r:
                ruta = r.split("OK: ")[1].split(" ")[0]
                src = pathlib.Path(ruta)
                if src.exists():
                    import shutil
                    shutil.copy2(src, destino)
                    f["imagen"] = str(destino)
        except Exception as e:
            print(f"    fallo {n}: {e}", flush=True)
    return frases


def main():
    ass = OUT / f"voz_largo_{FECHA}.ass"
    if not ass.exists(): print(f"FALTA {ass}"); sys.exit(1)
    frases = _extraer_frases(ass)
    print(f"[seg] {len(frases)} frases detectadas", flush=True)
    frases = _conceptos_visuales(frases)
    frases = _generar_imagenes(frases)
    (OUT / f"timeline_{FECHA}.json").write_text(json.dumps(
        [{"id": i+1, "inicio": f["inicio"], "fin": f["fin"],
          "tipo_visual": "imagen", "concepto_visual": f["concepto_visual"],
          "imagen": f.get("imagen", ""), "texto": f["texto"]}
         for i, f in enumerate(frases)], indent=2, ensure_ascii=False))
    print(f"OK {len(frases)} segmentos", flush=True)


if __name__ == "__main__":
    main()
