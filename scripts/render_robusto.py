"""render_robusto.py - Mux + retry + auto-recovery. Si falla, prueba variantes."""
import subprocess, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WORK = OUT / "render_work"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"
FFMPEG = "ffmpeg"
SIL = "error"


def _dur(p):
    if not p.exists(): return 0.0
    try:
        return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, timeout=10).stdout.strip() or "0")
    except: return 0.0


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


# ═══════════════════════════════════════════════
# 1. RECUPERAR/CREAR VIDEO_BASE
# ═══════════════════════════════════════════════
video_base = WORK / "video_base.mp4"
tl_file = OUT / f"timeline_{FECHA}.json"
if not tl_file.exists():
    print(f"FALTA timeline_{FECHA}.json, abortando"); sys.exit(1)
import json
tl = json.loads(tl_file.read_text())

if not video_base.exists() or _dur(video_base) < 60:
    print("\n[1] Reconstruir video_base", flush=True)
    CLIPS = WORK / "clips"; CLIPS.mkdir(parents=True, exist_ok=True)
    # A: clips
    for it in tl:
        n = it["id"]; dur = round(it["fin"] - it["inicio"], 2)
        clip = CLIPS / f"clip_{n:02d}.mp4"
        if clip.exists() and _dur(clip) > 0.5:
            continue
        tipo = it.get("tipo_visual", "imagen")
        vid = MEDIA / f"escena_{n:02d}.mp4"; img = MEDIA / f"escena_{n:02d}.png"
        src = vid if (tipo == "video" and vid.exists()) else img
        if not src.exists():
            print(f"  FALTA escena {n}"); sys.exit(1)
        loop = ["-stream_loop", "-1"] if src.suffix == ".mp4" else ["-loop", "1"]
        cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + loop + ["-i", str(src), "-t", str(dur),
            "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
            "-an", "-pix_fmt", "yuv420p", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25", str(clip)]
        if not _run(cmd, 240, f"A clip {n}"):
            print(f"  ❌ clip {n} irrecuperable"); sys.exit(1)
    # B: concat
    intro = OUT / "intro.mp4"; outro = OUT / "outro.mp4"
    for p, d in [(intro, 3), (outro, 3)]:
        if not p.exists():
            _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                "-i", f"color=c=0x0a0a0f:s=1920x1080:d={d}:r=25", "-c:v", "libx264",
                "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(p)], 60, f"gen {p.name}")
    for p, dst in [(intro, CLIPS/"00_intro.mp4"), (outro, CLIPS/"99_outro.mp4")]:
        if not dst.exists():
            _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(p),
                "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
                "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25", "-pix_fmt", "yuv420p", str(dst)],
                120, f"norm {p.name}")
    lista = WORK / "concat.txt"
    with open(lista, "w") as f:
        f.write(f"file '{CLIPS/'00_intro.mp4'}'\n")
        for it in tl: f.write(f"file '{CLIPS}/clip_{it['id']:02d}.mp4'\n")
        f.write(f"file '{CLIPS/'99_outro.mp4'}'\n")
    if not _intentar(lambda: _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(video_base)], 180, "B concat"), "B"):
        sys.exit(1)

dur_video = _dur(video_base)
print(f"video_base: {dur_video:.1f}s", flush=True)

# ═══════════════════════════════════════════════
# 2. RECUPERAR/CREAR AUDIO (con 3 estrategias)
# ═══════════════════════════════════════════════
audio = WORK / "audio.m4a"
voz = OUT / f"voz_largo_{FECHA}.mp3"
dur_voz = _dur(voz)
dur_total = max(dur_video, dur_voz + 2)  # +2s intro

if not audio.exists() or _dur(audio) < dur_total - 10:
    print(f"\n[2] Reconstruir audio (dur_total={dur_total:.1f}s)", flush=True)
    # C1: lofi_largo
    lofi = None
    cc = sorted(MUSICA.glob("yt_cc_*.mp3"))
    tun = sorted(MUSICA.glob("*_*.mp3"))
    for lista in [cc, tun]:
        for f in lista:
            if "voz" not in f.name and "short" not in f.name:
                lofi = f; break
        if lofi: break
    if not lofi:
        print("  Sin música, usando silencio"); 
        lofi = MUSICA / "_silence.mp3"
        _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
            "-i", "anullsrc=r=44100:cl=stereo", "-t", "10", "-c:a", "libmp3lame", str(lofi)], 30, "gen silence")
    
    lofi_dur = _dur(lofi)
    veces = max(1, int(dur_total / lofi_dur) + 2)
    lista_l = WORK / "lofi_lista.txt"
    with open(lista_l, "w") as f:
        for _ in range(veces): f.write(f"file '{lofi}'\n")
    lofi_largo = WORK / "lofi_largo.m4a"
    if not _intentar(lambda: _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(lista_l), "-c:a", "aac", "-b:a", "192k",
        str(lofi_largo)], 120, "C1 lofi_largo"), "C1"): sys.exit(1)
    
    # C2: amix (itsoffset + duration=first)
    def _mix():
        return _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-itsoffset", "2", "-i", str(voz), "-i", str(lofi_largo),
            "-filter_complex",
                f"[0:a]volume=1.0[v];[1:a]atrim=0:{dur_total:.1f},afade=t=in:st=0:d=3,afade=t=out:st={dur_total-3:.1f}:d=3,volume=0.10[m];[v][m]amix=inputs=2:duration=first:normalize=0[a]",
            "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-t", f"{dur_total:.1f}", str(audio)],
            300, "C2 amix")
    if not _intentar(_mix, "C2"):
        print("  Fallback: voz sola (sin música)")
        _intentar(lambda: _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-itsoffset", "2", "-i", str(voz), "-c:a", "aac", "-b:a", "192k", "-t", f"{dur_total:.1f}",
            str(audio)], 120, "C2 fallback"), "C2 fallback")

# ═══════════════════════════════════════════════
# 3. MUX FINAL
# ═══════════════════════════════════════════════
final = OUT / f"video_largo_{FECHA}.mp4"
print(f"\n[3] Mux final → {final.name}", flush=True)
def _mux():
    return _run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_base), "-i", str(audio),
        "-map", "0:v", "-map", "1:a", "-c", "copy",
        "-t", f"{min(dur_video, dur_total):.1f}",
        "-movflags", "+faststart", "-avoid_negative_ts", "make_zero", str(final)],
        180, "D mux")
if not _intentar(_mux, "D"):
    sys.exit(1)

# ═══════════════════════════════════════════════
# 4. VERIFICAR
# ═══════════════════════════════════════════════
dur_real = _dur(final)
if dur_real < 60:
    print(f"❌ VÍDEO INVÁLIDO ({dur_real}s)"); sys.exit(1)
size_mb = final.stat().st_size // 1024 // 1024
print(f"\n✅ VÍDEO OK: {final.name} ({dur_real/60:.1f}min, {size_mb}MB)", flush=True)
