"""gestor_musica.py - Orquesta la música: YouTube CC > Tunetank fallback + atribución."""
import json, pathlib, random, sys, subprocess, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MUSICA = ROOT / "output" / "musica_temp"
MUSICA.mkdir(parents=True, exist_ok=True)
INDEX = MUSICA / "rotacion_musica.json"
sys.path.insert(0, str(ROOT / "scripts"))


def _cargar_rotacion():
    if INDEX.exists():
        try: return json.loads(INDEX.read_text())
        except: return {"usos": {}, "atribuciones": []}
    return {"usos": {}, "atribuciones": []}


def _guardar_rotacion(rot):
    INDEX.write_text(json.dumps(rot, indent=2, ensure_ascii=False))


def _locales_cc():
    """Tracks CC ya descargados localmente."""
    return sorted(MUSICA.glob("yt_cc_*.mp3"))


def _elegir_rotando(tracks, rot):
    """Elige el menos usado recientemente."""
    if not tracks: return None
    # Ordenar por (num_usos, ultimo_uso)
    def _score(t):
        u = rot["usos"].get(t.name, {"n": 0, "t": 0})
        return (u.get("n", 0), u.get("t", 0))
    tracks_sorted = sorted(tracks, key=_score)
    # Entre los 3 menos usados, elegir aleatorio
    candidatos = tracks_sorted[:3]
    return random.choice(candidatos)


def _descargar_cc_para_mood(mood):
    """Busca y descarga YouTube CC para un mood."""
    QUERY_MAP = {
        "relax": "lofi hip hop instrumental 1 hour",
        "tension": "dark ambient instrumental 1 hour",
        "epico": "epic cinematic instrumental 1 hour",
        "inspirador": "inspiring instrumental orchestral 1 hour",
        "misterio": "mystery ambient instrumental 1 hour",
        "electronico": "electronic ambient instrumental 1 hour",
    }
    q = QUERY_MAP.get(mood, f"{mood} instrumental track")
    try:
        from descargar_youtube_cc import buscar_y_descargar
        res = buscar_y_descargar(q, 2)
        return res
    except Exception as e:
        print(f"  CC fallo: {e}", flush=True)
        return []


def _fallback_tunetank(mood, duracion):
    """Tunetank con filtros variados (no solo mood)."""
    try:
        from descargar_musica_dinamica import descargar_por_mood
        r = descargar_por_mood(mood, 1)
        if r and len(r) > 0:
            nombre = r[0]["archivo"]
            ruta = MUSICA / nombre
            if ruta.exists():
                return {"archivo": ruta, "titulo": nombre, "autor": "Tunetank",
                        "url": "https://tunetank.com", "licencia": "Tunetank (verificar comercial)",
                        "atribucion": f"Music: {nombre} (Tunetank - check commercial license)"}
    except Exception as e:
        print(f"  Tunetank fallo: {e}", flush=True)
    return None


def obtener_musica(mood="relax", duracion_objetivo=600):
    """Devuelve dict con archivo + atribucion. Orden: local CC > descarga CC > Tunetank."""
    rot = _cargar_rotacion()

    # 1. Local CC
    locales = _locales_cc()
    if locales:
        elegido = _elegir_rotando(locales, rot)
        if elegido:
            # Leer metadata de index si existe
            idx = MUSICA / "index_youtube_cc.json"
            meta = {}
            if idx.exists():
                try:
                    data = json.loads(idx.read_text())
                    for t in data:
                        if t.get("archivo") == elegido.name:
                            meta = t; break
                except: pass
            rot["usos"][elegido.name] = {"n": rot["usos"].get(elegido.name, {}).get("n", 0) + 1, "t": __import__("time").time()}
            _guardar_rotacion(rot)
            print(f"  Local CC: {elegido.name}", flush=True)
            return {"archivo": elegido, "titulo": meta.get("titulo", elegido.stem),
                    "autor": meta.get("autor", "Desconocido"),
                    "url": meta.get("url", ""), "licencia": "CC BY",
                    "atribucion": meta.get("atribucion") or f"Music: {elegido.stem} (CC BY)"}

    # 2. Descargar CC
    print(f"  Sin locales CC, descargando para mood={mood}...", flush=True)
    descargas = _descargar_cc_para_mood(mood)
    if descargas:
        d = descargas[0]
        ruta = MUSICA / d["archivo"]
        if ruta.exists():
            rot["usos"][d["archivo"]] = {"n": 1, "t": __import__("time").time()}
            _guardar_rotacion(rot)
            return {"archivo": ruta, "titulo": d.get("titulo", d["archivo"]),
                    "autor": d.get("autor", "Desconocido"),
                    "url": d.get("url", ""), "licencia": d.get("licencia", "CC BY"),
                    "atribucion": d.get("atribucion", f"Music: {d['archivo']} (CC BY)")}

    # 3. Tunetank fallback
    print(f"  Fallback Tunetank mood={mood}...", flush=True)
    fb = _fallback_tunetank(mood, duracion_objetivo)
    if fb:
        return fb

    raise RuntimeError(f"Sin música disponible para mood={mood}")


def asegurar_duracion(track_path, duracion_objetivo, salida):
    """Si track_path < duracion_objetivo, lo concatena consigo mismo hasta cubrir."""
    import math
    dur_real = _dur(track_path)
    if dur_real >= duracion_objetivo:
        return track_path
    veces = math.ceil(duracion_objetivo / dur_real) + 1
    print("  Concatenando " + str(veces) + "x " + track_path.name, flush=True)
    lista = salida.parent / ("concat_" + track_path.stem + ".txt")
    contenido = ""
    for _ in range(veces):
        contenido += "file '" + str(track_path) + "'\n"
    lista.write_text(contenido)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lista),
        "-c:a", "aac", "-b:a", "192k", str(salida)],
        capture_output=True, check=True)
    lista.unlink(missing_ok=True)
    return salida


def atribuciones_dia(fecha=None):
    """Devuelve lista de atribuciones para meter en descripción YouTube."""
    rot = _cargar_rotacion()
    return [info.get("atribucion", "") for fname, info in rot.get("usos", {}).items()
            if info.get("atribucion")]


if __name__ == "__main__":
    mood = sys.argv[1] if len(sys.argv) > 1 else "relax"
    r = obtener_musica(mood)
    print(json.dumps({"archivo": str(r["archivo"]), "atribucion": r["atribucion"]}, indent=2, ensure_ascii=False))
