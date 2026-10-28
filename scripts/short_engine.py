"""short_engine.py — Motor de Shorts end-to-end (sin Kaggle).
Flujo: guion -> voz (Sherpa) -> clips verticales (stock local) -> música (ACE-Step pool) -> ensamblar.
"""
import os, sys, json, pathlib, subprocess, time, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))

OUT_VIDEOS = ROOT / "output" / "videos"
OUT_AUDIOS = ROOT / "output" / "audios"
STOCK = ROOT / "output" / "stock"
POOL_MUSICA = ROOT / "output" / "musica"


def _ff(args, label=""):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{label}: {r.stderr[-400:]}")
    return r.stdout


def _concat_clips(clips, salida):
    """Concatena clips con concat demuxer (stream copy, rápido)."""
    lista = salida.parent / f"_concat_{int(time.time())}.txt"
    lista.write_text("\n".join(f"file '{c}'" for c in clips))
    _ff(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
         "-c", "copy", "-an", str(salida)], "concat")
    lista.unlink(missing_ok=True)
    return salida



def _aplicar_crop_blur(video_base, salida, W=1080, H=1920, blur_sigma=25, brightness=-0.15):
    filtro = (
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
        f"gblur=sigma={blur_sigma},eq=brightness={brightness}[bg];"
        f"[0:v]scale={W}:-2[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )
    args = [
        "ffmpeg", "-y", "-i", str(video_base),
        "-filter_complex", filtro,
        "-map", "[v]",
        "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-an", str(salida)
    ]
    print(f"[short] Aplicando crop+blur ({blur_sigma}px)...", flush=True)
    _ff(args, "crop_blur")
    return salida

def _generar_voz(texto, canal, ts):
    """Llama a voice_studio.py por CLI."""
    nombre = f"{canal}_short_{ts}"
    cmd = [sys.executable, str(ROOT / "scripts" / "voice_studio.py"),
           "--texto", texto,
           "--voz", "es_ES-davefx-medium",
           "--preset", "noticias",
           "--formato", "mp3"]
    print(f"[short] Voz: {len(texto.split())} palabras...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    try:
        last = r.stdout.strip().split("\n")[-1]
        d = json.loads(last)
        if d.get("status") == "ok":
            # La voz está en media/audios/ según el url devuelto
            url = d.get("url", "")
            if url.startswith("/media/"):
                ruta = ROOT / url.lstrip("/").replace("media/", "media/", 1)
                # ROOT/media/audios/xxx.mp3
                ruta = ROOT / url.lstrip("/")
            else:
                ruta = ROOT / "media" / "audios" / (str(d["audio_id"]) + ".mp3")
            if not ruta.exists():
                # fallback: buscar en output/audios
                alt = ROOT / "output" / "audios" / (str(d["audio_id"]) + ".mp3")
                if alt.exists():
                    ruta = alt
            print(f"[short] Voz OK: {ruta} ({d.get('duracion',0):.1f}s)", flush=True)
            return ruta
    except Exception as e:
        print(f"[short] Voz fallo: {e} | stdout: {r.stdout[-200:]} | stderr: {r.stderr[-200:]}", flush=True)
    return None


def _elegir_musica():
    """Coge una música del pool (ya generada por ACE-Step)."""
    if not POOL_MUSICA.exists():
        return None
    mp3s = sorted(POOL_MUSICA.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    return mp3s[0] if mp3s else None


def _elegir_clips(max_clips=3):
    """Coge hasta N clips verticales de output/stock/."""
    clips = sorted(STOCK.glob("vert_*.mp4"), key=lambda p: p.stat().st_size, reverse=True)
    return clips[:max_clips]


def crear_short(tema, canal="ia_news", max_clips=3, angulo="dato"):
    """Pipeline completo. Devuelve dict con rutas."""
    ts = int(time.time())
    OUT_VIDEOS.mkdir(parents=True, exist_ok=True)

    # 1. Guion
    print(f"[short] Generando guion sobre: {tema}", flush=True)
    from especialistas import pedir_a_especialista
    ANGULOS = {
        "dato": "Empieza con un dato impactante. Explica por que importa. Cierra con impacto.",
        "contradiccion": "Empieza con 'Nadie habla de esto pero...'. Presenta el giro. Termina con pregunta.",
        "prediccion": "Empieza con 'En 6 meses...'. Prediccion audaz. Termina con urgencia.",
        "tutorial": "Empieza con 'Asi puedes...'. 2-3 pasos practicos. CTA de accion.",
    }
    instruccion = ANGULOS.get(angulo, ANGULOS["dato"])
    guion = pedir_a_especialista("guionista_short",
        f"Guion de 60 segundos sobre: {tema}. Tono intriga. {instruccion}")
    if not guion or len(guion.split()) < 30:
        return {"error": "guion invalido", "guion": guion[:200]}
    print(f"[short] Guion: {len(guion.split())} palabras", flush=True)
    (ROOT / "output" / "videos").mkdir(exist_ok=True)
    (OUT_VIDEOS / f"short_{ts}_guion.txt").write_text(guion, encoding="utf-8")

    # 2. Voz
    voz = _generar_voz(guion, canal, ts)
    if not voz:
        return {"error": "voz fallo"}

    # 3. Clips
    clips = _elegir_clips(max_clips)
    if len(clips) < 1:
        return {"error": "no hay clips verticales en output/stock/"}
    print(f"[short] {len(clips)} clips verticales", flush=True)

    # 4. Concatenar clips
    base_video = OUT_VIDEOS / f"short_{ts}_base.mp4"
    _concat_clips([str(c) for c in clips], base_video)
    print(f"[short] Base concatenada: {base_video.name}", flush=True)

    # 5. Música (opcional)
    musica = _elegir_musica()
    print(f"[short] Música: {musica.name if musica else 'sin musica'}", flush=True)

    # 6. Ensamblar con receta (blur preferida)
    from motor_ensamblado import motor
    receta = str(ROOT / "config" / "montajes" / "short_vertical_blur.json")
    if not pathlib.Path(receta).exists():
        receta = str(ROOT / "config" / "montajes" / "short_vertical.json")

    # Sobreescribimos salida_path para no pisar la receta
    receta_data = json.loads(pathlib.Path(receta).read_text())
    salida_final = OUT_VIDEOS / f"short_{canal}_{ts}.mp4"
    receta_data["salida_path"] = str(salida_final)
    receta_temp = OUT_VIDEOS / f"_receta_{ts}.json"
    receta_temp.write_text(json.dumps(receta_data, indent=2))

    # Pre-procesar blur si la receta lo pide
    import json as _json
    _rec = _json.loads(pathlib.Path(receta).read_text())
    if _rec.get("crop_blur"):
        blurred = OUT_VIDEOS / f"_blur_{ts}.mp4"
        _aplicar_crop_blur(base_video, blurred)
        base_video = blurred

    overrides = {"video_base": str(base_video), "voz": str(voz)}
    if musica:
        overrides["musica"] = str(musica)

    print(f"[short] Ensamblando (motor_ensamblado)...", flush=True)
    r = motor(str(receta_temp), overrides)
    receta_temp.unlink(missing_ok=True)

    if r.get("status") == "ok":
        print(f"[short] ✅ {salida_final} ({r['size_mb']}MB, {r['duracion']:.1f}s)", flush=True)
        # SEO para YouTube
        seo_youtube = {}
        try:
            import json as _json
            import re as _re
            from especialistas import pedir_a_especialista
            seo_raw = pedir_a_especialista("seo_youtube", "SEO para: " + tema + ". Angulo: " + angulo, contexto=guion[:500])
            _m = _re.search(r'\{.*\}', seo_raw, _re.DOTALL)
            seo_youtube = _json.loads(_m.group(0)) if _m else {}
            _seo_file = OUT_VIDEOS / (salida_final.stem + ".seo.json")
            _seo_file.write_text(_json.dumps(seo_youtube, indent=2, ensure_ascii=False))
            print(f"[short] SEO guardado: {_seo_file.name}", flush=True)
        except Exception as _e:
            print(f"[short] SEO fallo (no critico): {_e}", flush=True)
        return {
            "status": "ok",
            "path": str(salida_final),
            "duracion": r["duracion"],
            "size_mb": r["size_mb"],
            "guion": guion,
            "clip_count": len(clips),
            "seo": seo_youtube,
            "angulo": angulo,
        }
    return {"error": "ensamblado fallo", "result": r}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: short_engine.py <tema> [canal]")
        sys.exit(1)
    tema = sys.argv[1]
    canal = sys.argv[2] if len(sys.argv) > 2 else "ia_news"
    print(json.dumps(crear_short(tema, canal), indent=2, ensure_ascii=False))
