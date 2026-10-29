"""segmentar_imagenes.py v2 - 72 imágenes con distribución inteligente por tipo."""
import json, pathlib, sys, re, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"

DUR_POR_TIPO = {
    "hook": 4.0, "cita": 6.0, "explicacion": 11.0, "contraste": 7.0,
    "dato": 5.0, "cierre": 14.0, "default": 8.0,
}


def _detectar_tipo(texto, idx, total):
    t = (texto or "").lower().strip()
    if idx == 0 or any(t.startswith(x) for x in ["hola", "buenas", "saludos", "¿", "bienvenidos"]):
        return "hook"
    if idx >= total - 1:
        return "cierre"
    if any(x in t for x in ["tituló", "titular de", "publicó", "reza:", "\""]):
        return "cita"
    if any(x in t for x in ["framing", "sesgo", "técnica", "manipulación", "significa", "implica", "esto es"]):
        return "explicacion"
    if any(x in t for x in ["en cambio", "por su parte", "sin embargo", "mientras", "contrasta"]):
        return "contraste"
    if any(c.isdigit() for c in t) and any(x in t for x in ["%", "millones", "mil ", "dato", "cifra"]):
        return "dato"
    return "default"


def _extraer_frases(ass_path):
    """Parsea ASS y agrupa en frases (por . ? ! o 12s máx)."""
    if not ass_path.exists(): return []
    frases, buffer, t_ini, t_fin = [], [], None, None
    for line in ass_path.read_text().splitlines():
        m = re.match(r'Dialogue: 0,(\d+):(\d+):([\d.]+),(\d+):(\d+):([\d.]+),.*?\}(.*)$', line)
        if not m: continue
        start = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        end = int(m.group(4))*3600 + int(m.group(5))*60 + float(m.group(6))
        palabra = m.group(7).strip()
        if not palabra: continue
        if t_ini is None: t_ini, buffer = start, []
        buffer.append(palabra)
        t_fin = end
        if (t_fin - t_ini) >= 12 or palabra.endswith(('.', '?', '!')):
            frases.append({"inicio": round(t_ini,2), "fin": round(t_fin,2), "texto": " ".join(buffer)})
            t_ini = None
    if buffer and t_ini is not None:
        frases.append({"inicio": round(t_ini,2), "fin": round(t_fin,2), "texto": " ".join(buffer)})
    return frases


def _fusionar_a_72(frases):
    """Fusiona frases cortas hasta llegar a ~72 segmentos."""
    total_dur = frases[-1]["fin"] if frases else 0
    if total_dur < 60:
        return frases
    target = 72
    # Si hay más de 72, fusionar las más cortas con vecinas
    while len(frases) > target:
        # Fusión mínima
        frases[0:2] = [{"inicio": frases[0]["inicio"], "fin": frases[1]["fin"], "texto": frases[0]["texto"] + " " + frases[1]["texto"]}]
    return frases


def _conceptos_visuales(segmentos):
    print(f"[seg] {len(segmentos)} segmentos, generando conceptos visuales...", flush=True)
    for i, s in enumerate(segmentos):
        tipo = s["tipo"]
        prompt = f"Segmento tipo={tipo}. Texto: {s['texto'][:200]}. Devuelve SOLO un prompt visual en INGLÉS de 8-15 palabras para SDXL, formato Subject + Action + Environment + Lighting + Style. Sin comillas, sin texto legible."
        try:
            r = pedir_a_especialista("disenador_visual", prompt, contexto=s["texto"], proveedor="omni")
            r = r.strip().strip('"').strip("'").split('\n')[0][:150]
            if len(r) > 15 and not re.search(r'[ñáéíóú]', r.lower()):
                s["concepto_visual"] = r
            else:
                s["concepto_visual"] = f"cinematic newspaper scene about {tipo}, dramatic light, no text"
        except Exception:
            s["concepto_visual"] = f"cinematic newspaper scene about {tipo}, dramatic light, no text"
        if i % 10 == 0:
            print(f"  [{i+1}/{len(segmentos)}] {s['concepto_visual'][:60]}", flush=True)
    return segmentos


def _generar_imagenes(segmentos):
    from generar_imagen import generar
    img_dir = ROOT / "web" / "media" / "imagenes"
    img_dir.mkdir(parents=True, exist_ok=True)
    for i, s in enumerate(segmentos):
        n = i + 1
        destino = img_dir / f"seg_{n:03d}.png"
        if destino.exists():
            s["imagen"] = str(destino)
            continue
        try:
            r = generar(s["concepto_visual"] + ", cinematic, no text, high detail",
                        preset="cinematic", aspect="16:9", canal="encuadre")
            if "OK: " in r:
                ruta = r.split("OK: ")[1].split(" ")[0]
                src = pathlib.Path(ruta)
                if src.exists():
                    import shutil
                    shutil.copy2(src, destino)
                    s["imagen"] = str(destino)
        except Exception as e:
            print(f"  fallo {n}: {e}", flush=True)
        if n % 10 == 0:
            print(f"  [{n}/{len(segmentos)}] img OK", flush=True)
    return segmentos


def main():
    ass = OUT / f"voz_largo_{FECHA}.ass"
    if not ass.exists():
        print(f"FALTA {ass}")
        sys.exit(1)
    frases = _extraer_frases(ass)
    print(f"[seg] {len(frases)} frases detectadas", flush=True)
    frases = _fusionar_a_72(frases)
    print(f"[seg] {len(frases)} segmentos tras fusión", flush=True)
    for i, f in enumerate(frases):
        f["tipo"] = _detectar_tipo(f["texto"], i, len(frases))
        f["duracion"] = DUR_POR_TIPO.get(f["tipo"], 8.0)
    frases = _conceptos_visuales(frases)
    frases = _generar_imagenes(frases)
    # Timeline con duración variable
    timeline = []
    for i, f in enumerate(frases):
        # Forzar duración real (respetar ASS si es menor)
        dur_ass = round(f["fin"] - f["inicio"], 2)
        dur_final = min(dur_ass, f["duracion"]) if dur_ass > 0 else f["duracion"]
        timeline.append({
            "id": i + 1,
            "inicio": f["inicio"],
            "fin": round(f["inicio"] + dur_final, 2),
            "tipo_visual": "imagen",
            "tipo_escena": f["tipo"],
            "concepto_visual": f["concepto_visual"],
            "imagen": f.get("imagen", ""),
            "texto": f["texto"],
        })
    (OUT / f"timeline_{FECHA}.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))
    print(f"OK {len(timeline)} segmentos con tipos + imágenes", flush=True)


if __name__ == "__main__":
    main()
