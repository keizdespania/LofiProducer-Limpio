"""director_arte.py - Genera 72 imágenes (1 cada 8.5s) + timeline del vídeo largo.
Fusiona director_arte antiguo + segmentar_imagenes. Traduce ES→EN con LLM.
Elimina segmentar_imagenes.py: este script hace todo el trabajo visual.
"""
import json, pathlib, sys, re, subprocess, shutil

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MEDIA.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"

# Duración por tipo (segundos de imagen en pantalla)
DUR_POR_TIPO = {
    "hook": 4.0, "cita": 6.0, "explicacion": 11.0, "contraste": 7.0,
    "dato": 5.0, "cierre": 14.0, "pattern": 3.0, "default": 8.0,
}


def _duracion_audio(path):
    """Duración real del MP3 con ffprobe (robusto, no depende de timeline)."""
    if not path.exists():
        return 0.0
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0.0


def _detectar_tipo(texto, idx, total):
    """Detecta el tipo narrativo de una frase para prompt/duracion (ampliado 2026-11-04)."""
    t = (texto or "").lower().strip()
    if idx == 0 or any(t.startswith(x) for x in ["mira", "hola", "buenas", "vamos", "¿", "bienvenidos"]):
        return "hook"
    if idx >= total - 1:
        return "cierre"
    if "[pattern" in t:
        return "pattern"
    if any(c.isdigit() for c in t) and any(x in t for x in ["%", "millones", "mil ", "dato", "cifra", "115", "4.000"]):
        return "dato"
    if '"' in t or '«' in t or any(x in t for x in ["publicó", "dice que", "afirma", "asegura", "tituló", "titular", "según", "reza:"]):
        return "cita"
    if any(x in t for x in ["en cambio", "por su parte", "sin embargo", "mientras", "contrasta", "aunque"]):
        return "contraste"
    if any(x in t for x in ["framing", "sesgo", "técnica", "manipulación", "significa", "implica", "esto es", "fíjate", "medios", "prensa", "periodista", "oculta", "omite", "vende", "narrativa"]):
        return "explicacion"
    return "default"


def _extraer_frases(ass_path):
    """Parsea ASS y agrupa en frases (por . ? ! o 12s máx)."""
    if not ass_path.exists():
        print(f"  ⚠️ ASS no existe: {ass_path}")
        return []
    frases, buffer, t_ini, t_fin = [], [], None, None
    for line in ass_path.read_text().splitlines():
        m = re.match(r'Dialogue: 0,(\d+):(\d+):([\d.]+),(\d+):(\d+):([\d.]+),.*?\}(.*)$', line)
        if not m:
            continue
        start = int(m.group(1))*3600 + int(m.group(2))*60 + float(m.group(3))
        end = int(m.group(4))*3600 + int(m.group(5))*60 + float(m.group(6))
        palabra = m.group(7).strip()
        if not palabra:
            continue
        if t_ini is None:
            t_ini, buffer = start, []
        buffer.append(palabra)
        t_fin = end
        if (t_fin - t_ini) >= 12 or palabra.endswith(('.', '?', '!')):
            frases.append({"inicio": round(t_ini, 2), "fin": round(t_fin, 2), "texto": " ".join(buffer)})
            t_ini = None
    if buffer and t_ini is not None:
        frases.append({"inicio": round(t_ini, 2), "fin": round(t_fin, 2), "texto": " ".join(buffer)})
    return frases


def _fusionar_a_segmentos(frases, duracion_audio, cada_seg=8.5):
    """Corta el audio en trozos exactos de 8.5s, ignorando los saltos del ASS."""
    if not frases or duracion_audio <= 0:
        return []
    num_imagenes = max(10, int(duracion_audio / cada_seg))
    dur_por_trozo = duracion_audio / num_imagenes
    texto_completo = " ".join([f["texto"] for f in frases])
    palabras = texto_completo.split()
    pal_por_trozo = max(10, len(palabras) // num_imagenes)

    segmentos = []
    for i in range(num_imagenes):
        inicio = i * dur_por_trozo
        fin = (i + 1) * dur_por_trozo
        if fin > duracion_audio:
            fin = duracion_audio
        texto_trozo = " ".join(palabras[i*pal_por_trozo : (i+1)*pal_por_trozo])
        if not texto_trozo:
            texto_trozo = "Análisis de técnicas de manipulación."
        segmentos.append({
            "inicio": round(inicio, 2),
            "fin": round(fin, 2),
            "texto": texto_trozo,
        })
    return segmentos


def _generar_conceptos_visuales(segmentos, fecha="hoy"):
    """Genera prompts visuales usando el módulo central (Groq 4 sin filtros)."""
    from director_fotografia import generar_prompt_visual
    print(f"[arte] {len(segmentos)} segmentos → conceptos visuales (Director de Fotografía)...", flush=True)

    for i, s in enumerate(segmentos):
        # Usamos el texto completo del segmento para que el director de foto se inspire
        s["concepto_visual"] = generar_prompt_visual(s["texto"], vertical=False, idx=i, fecha=fecha)
        
        if i % 10 == 0:
            print(f"  [{i+1}/{len(segmentos)}] {s['concepto_visual'][:70]}", flush=True)

    return segmentos

def _insertar_pattern_interrupts(segmentos, cada_n=15):
    """Cada N segmentos, inserta 1 pattern interrupt de 3s (imagen abstracta)."""
    if len(segmentos) < cada_n * 2:
        return segmentos
    nuevos = []
    for i, s in enumerate(segmentos):
        nuevos.append(s)
        if (i + 1) % cada_n == 0 and (i + 1) < len(segmentos) - 2:
            nuevos.append({
                "inicio": s["fin"],
                "fin": round(s["fin"] + 3.0, 2),
                "texto": "[PATTERN INTERRUPT]",
                "tipo": "pattern",
                "duracion": 3.0,
                "concepto_visual": "abstract question mark silhouette, dramatic dark background, cinematic, no text",
            })
    return nuevos


def _limpiar_imagenes_antiguas(dias=7):
    """Borra seg_*.png / escena_*.png de más de N días. Conserva histórico reciente."""
    import time as _t
    corte = _t.time() - (dias * 86400)
    borradas = 0
    for pattern in ("seg_*.png", "escena_*.png"):
        for f in MEDIA.glob(pattern):
            try:
                if f.stat().st_mtime < corte:
                    f.unlink(); borradas += 1
            except Exception:
                pass
    if borradas:
        print(f"[arte] Borradas {borradas} imagenes >{dias}d", flush=True)


def _generar_imagenes(segmentos, fecha="hoy"):
    """Genera seg_NNN.png (16:9) con SDXL a partir del concepto_visual."""
    from generar_imagen import generar
    for i, s in enumerate(segmentos):
        n = i + 1
        destino = MEDIA / f"seg_{n:03d}_{fecha}.png"
        destino_legacy = MEDIA / f"seg_{n:03d}.png"
        if destino.exists() and destino.stat().st_size > 50000:
            s["imagen"] = str(destino); continue
        if destino_legacy.exists() and destino_legacy.stat().st_size > 50000:
            s["imagen"] = str(destino_legacy); continue
        try:
            seed = (hash(str(fecha)) ^ (n * 2654435761)) & 0xFFFFFFFF
            r = generar(
                s["concepto_visual"],
                preset="cinematic", aspect="16:9", canal="encuadre",
                seed=seed
            )
            if "OK: " in r:
                ruta = r.split("OK: ")[1].split(" ")[0]
                src = pathlib.Path(ruta)
                if src.exists():
                    shutil.copy2(src, destino)
                    s["imagen"] = str(destino)
        except Exception as e:
            print(f"  fallo {n}: {e}", flush=True)
        if n % 10 == 0:
            print(f"  [{n}/{len(segmentos)}] img OK", flush=True)
    return segmentos


def preparar(fecha=None):
    fecha = fecha or FECHA
    print("=" * 60)
    print(f"[arte] Director de Arte: preparando {fecha}")
    print("=" * 60)

    # 1. Limpiar imágenes viejas
    _limpiar_imagenes_antiguas()

    # 2. Verificar ASS (subtítulos con timestamps de palabra)
    ass = OUT / f"voz_largo_{fecha}.ass"
    if not ass.exists():
        print(f"❌ FALTA {ass} → ejecuta voz_edge.py primero")
        sys.exit(1)

    # 3. Duración del audio (ffprobe del MP3)
    voz_mp3 = OUT / f"voz_largo_{fecha}.mp3"
    dur_audio = _duracion_audio(voz_mp3)
    if dur_audio <= 0:
        print(f"❌ No puedo leer duración de {voz_mp3}")
        sys.exit(1)
    print(f"[arte] Duración voz: {dur_audio:.1f}s ({dur_audio/60:.1f} min)")

    # 4. Extraer frases del ASS
    frases = _extraer_frases(ass)
    print(f"[arte] {len(frases)} frases detectadas")

    # 5. Fusionar en segmentos de ~8.5s
    segmentos = _fusionar_a_segmentos(frases, dur_audio)
    print(f"[arte] {len(segmentos)} segmentos (1 imagen / 8.5s)")

    # 6. Detectar tipo por segmento
    for i, f in enumerate(segmentos):
        f["tipo"] = _detectar_tipo(f["texto"], i, len(segmentos))
        f["duracion"] = DUR_POR_TIPO.get(f["tipo"], 8.0)

    # 7. Pattern interrupts cada 15 segmentos
    segmentos = _insertar_pattern_interrupts(segmentos, cada_n=15)
    print(f"[arte] {len(segmentos)} segmentos finales (con pattern interrupts)")

    # 8. Conceptos visuales con LLM
    segmentos = _generar_conceptos_visuales(segmentos, fecha)

    # 9. Generar imágenes SDXL
    segmentos = _generar_imagenes(segmentos, fecha)

    # 10. Timeline final
    timeline = []
    for i, f in enumerate(segmentos):
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
    (OUT / f"timeline_{fecha}.json").write_text(json.dumps(timeline, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(timeline)} segmentos con timeline final")


if __name__ == "__main__":
    preparar(sys.argv[1] if len(sys.argv) > 1 else None)
