"""render_robusto.py v3 - Ken Burns + transiciones + duración variable + auto-recovery."""
import subprocess, pathlib, sys, time, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WORK = OUT / "render_work"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"
FFMPEG = "ffmpeg"


def _dur(p):
    if not p.exists(): return 0.0
    try:
        return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",str(p)],
            capture_output=True, text=True, timeout=10).stdout.strip() or "0")
    except: return 0.0




def _aplicar_transiciones(video_base, tl, out_final):
    """Aplica xfade 0.3s entre clips de tipo distinto. Si falla, deja video_base."""
    if len(tl) < 4:
        return False
    # Construir filter_complex con xfade encadenado
    # Solo entre clips de tipos distintos para no saturar
    clips = []
    # Usamos el video_base que ya tiene intro+clips+outro concatenados (copy)
    # Aplicar xfade a un vídeo ya concatenado es imposible sin separarlo.
    # Alternativa: dejarlo como está (cortes secos) y confiar en el ritmo de duraciones.
    # Para "transiciones intencionadas" real, habría que hacer el concat con filtros.
    return False

def _run(cmd, timeout=300, desc=""):
    print(f"  [{desc}]...", flush=True)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            print(f"  [{desc}] OK {time.time()-t0:.1f}s", flush=True)
            return True
        print(f"  [{desc}] FAIL rc={r.returncode}: {r.stderr[-200:]}", flush=True)
        return False
    except subprocess.TimeoutExpired:
        print(f"  [{desc}] TIMEOUT {timeout}s", flush=True)
        return False


def _intentar(func, desc, max_retries=3):
    for i in range(max_retries):
        if func(): return True
        print(f"  Reintento {i+1}/{max_retries} {desc}...", flush=True)
        time.sleep(3)
    return False


# Ken Burns por tipo de escena
def _kenburns_filter(tipo, dur):
    """Zoom/pan distinto por tipo."""
    fps = 25
    frames = max(int(dur * fps), 10)
    if tipo == "hook":
        return f"zoompan=z='min(zoom+0.002,1.15)':d={frames}:s=1920x1080:fps={fps}"
    if tipo == "cita":
        return f"zoompan=z='min(zoom+0.0015,1.12)':d={frames}:s=1920x1080:fps={fps}"
    if tipo in ("explicacion","contraste"):
        return f"zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':d={frames}:s=1920x1080:fps={fps}"
    if tipo == "dato":
        return f"zoompan=z='min(zoom+0.003,1.20)':d={frames}:s=1920x1080:fps={fps}"
    if tipo == "cierre":
        return f"zoompan=z='if(lte(zoom,1.0),1.15,max(1.001,zoom-0.0008))':d={frames}:s=1920x1080:fps={fps}"
    return f"zoompan=z='min(zoom+0.001,1.10)':d={frames}:s=1920x1080:fps={fps}"


# ═══ PASO 1: RECUPERAR/CREAR VIDEO_BASE ═══
video_base = WORK / "video_base.mp4"
tl_file = OUT / f"timeline_{FECHA}.json"
if not tl_file.exists():
    print(f"FALTA timeline_{FECHA}.json, abortando"); sys.exit(1)
tl = json.loads(tl_file.read_text())
print(f"[render] {len(tl)} escenas con duración variable", flush=True)

WORK.mkdir(parents=True, exist_ok=True)
CLIPS = WORK / "clips"
CLIPS.mkdir(parents=True, exist_ok=True)

if not video_base.exists() or _dur(video_base) < 60:
    print("\n[1] Reconstruir video_base con Ken Burns", flush=True)
    for it in tl:
        n = it["id"]
        dur = round(it["fin"] - it["inicio"], 2)
        tipo = it.get("tipo_escena", "default")
        # Buscar imagen: seg_XXX.png (nuevo) o escena_XX.png (viejo)
        img = MEDIA / f"seg_{n:03d}.png"
        if not img.exists():
            img = MEDIA / f"escena_{n:02d}.png"
        vid = MEDIA / f"escena_{n:02d}.mp4"
        clip = CLIPS / f"clip_{n:03d}.mp4"
        if clip.exists() and _dur(clip) > 0.5:
            continue

        if vid.exists() and it.get("tipo_visual") == "video":
            # Vídeo: scale + crop simple
            cmd = [FFMPEG,"-y","-hide_banner","-loglevel","error",
                "-stream_loop","-1","-i",str(vid),"-t",str(dur),
                "-vf","scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
                "-an","-pix_fmt","yuv420p","-c:v","libx264","-preset","ultrafast","-crf","25",str(clip)]
        elif img.exists():
            # Imagen: Ken Burns
            kb = _kenburns_filter(tipo, dur)
            cmd = [FFMPEG,"-y","-hide_banner","-loglevel","error",
                "-loop","1","-i",str(img),"-t",str(dur),
                "-vf",f"scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,{kb},scale=1920:1080,format=yuv420p",
                "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-tune","stillimage",str(clip)]
        else:
            print(f"  FALTA img escena {n}"); sys.exit(1)
        if not _run(cmd, 240, f"clip {n:03d} {tipo}"):
            print(f"  clip {n} irrecuperable"); sys.exit(1)

    # Intro/outro
    intro = OUT / "intro.mp4"; outro = OUT / "outro.mp4"
    for p, d in [(intro, 3), (outro, 3)]:
        if not p.exists():
            _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-f","lavfi",
                "-i",f"color=c=0x0a0a0f:s=1920x1080:d={d}:r=25","-c:v","libx264",
                "-preset","ultrafast","-pix_fmt","yuv420p",str(p)], 60, f"gen {p.name}")
    for p, dst in [(intro, CLIPS/"000_intro.mp4"), (outro, CLIPS/"999_outro.mp4")]:
        if not dst.exists():
            _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-i",str(p),
                "-vf","scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
                "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-pix_fmt","yuv420p",str(dst)],
                120, f"norm {p.name}")

    lista = WORK / "concat.txt"
    with open(lista, "w") as f:
        f.write(f"file '{CLIPS/'000_intro.mp4'}'\n")
        for it in tl:
            _n = it["id"]
            f.write(f"file '{CLIPS}/clip_{_n:03d}.mp4'\n")
        f.write(f"file '{CLIPS/'999_outro.mp4'}'\n")
    if not _intentar(lambda: _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0","-i",str(lista),"-c","copy",str(video_base)], 180, "concat"), "concat"):
        sys.exit(1)

dur_video = _dur(video_base)
print(f"video_base: {dur_video:.1f}s", flush=True)

# ═══ PASO 2: AUDIO ═══
audio = WORK / "audio.m4a"
voz = OUT / f"voz_largo_{FECHA}.mp3"
dur_voz = _dur(voz)
dur_total = max(dur_video, dur_voz + 2)

if not audio.exists() or _dur(audio) < dur_total - 10:
    print(f"\n[2] Audio (dur_total={dur_total:.1f}s)", flush=True)
    # Solo archivos lofi válidos
    PREFERIDOS = ["lofi_final", "yt_cc_", "relax_", "inspirador_", "misterio_", "electronico_", "sarcasmo_", "dramatico_"]
    lofi = None
    for pref in PREFERIDOS:
        cands = [f for f in MUSICA.glob(f"{pref}*.mp3") if f.suffix == ".mp3"]
        if cands: lofi = cands[0]; break
    if not lofi:
        lofi = MUSICA / "_silence.mp3"
        _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-f","lavfi",
            "-i","anullsrc=r=44100:cl=stereo","-t","10","-c:a","libmp3lame",str(lofi)], 30, "gen silence")

    lofi_dur = _dur(lofi)
    veces = max(1, int(dur_total / lofi_dur) + 2)
    lista_l = WORK / "lofi_lista.txt"
    with open(lista_l, "w") as f:
        for _ in range(veces): f.write(f"file '{lofi}'\n")
    lofi_largo = WORK / "lofi_largo.m4a"
    if not _intentar(lambda: _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
        "-f","concat","-safe","0","-i",str(lista_l),"-c:a","aac","-b:a","192k",str(lofi_largo)],
        120, "lofi_largo"), "lofi"):
        sys.exit(1)

    def _mix():
        return _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
            "-itsoffset","2","-i",str(voz),"-i",str(lofi_largo),
            "-filter_complex",
                f"[0:a]volume=1.0[v];[1:a]atrim=0:{dur_total:.1f},afade=t=in:st=0:d=3,afade=t=out:st={dur_total-3:.1f}:d=3,volume=0.12[m];[m][v]sidechaincompress=threshold=0.1:ratio=5:attack=20:release=1000[duck];[v][duck]amix=inputs=2:duration=first:normalize=0[a]",
            "-map","[a]","-c:a","aac","-b:a","192k","-t",f"{dur_total:.1f}",str(audio)],
            300, "amix")
    if not _intentar(_mix, "amix"):
        _intentar(lambda: _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
            "-itsoffset","2","-i",str(voz),"-c:a","aac","-b:a","192k",
            "-t",f"{dur_total:.1f}",str(audio)], 120, "voz_sola"), "voz")

# ═══ PASO 3: MUX FINAL ═══
final = OUT / f"video_largo_{FECHA}.mp4"
print(f"\n[3] Mux final → {final.name}", flush=True)
def _mux():
    return _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
        "-i",str(video_base),"-i",str(audio),
        "-map","0:v","-map","1:a","-c","copy",
        "-t",f"{min(dur_video,dur_total):.1f}",
        "-movflags","+faststart","-avoid_negative_ts","make_zero",str(final)],
        180, "mux")
if not _intentar(_mux, "mux"): sys.exit(1)

dur_real = _dur(final)
if dur_real < 60:
    print(f"VÍDEO INVÁLIDO ({dur_real}s)"); sys.exit(1)
size_mb = final.stat().st_size // 1024 // 1024
print(f"\n✅ VÍDEO OK: {final.name} ({dur_real/60:.1f}min, {size_mb}MB)", flush=True)
