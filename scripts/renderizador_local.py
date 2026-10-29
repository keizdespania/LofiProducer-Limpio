"""renderizador_local.py - 4 pasadas A/B/C/D en Termux."""
import subprocess, json, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
WORK = OUT / "render_work"
WORK.mkdir(parents=True, exist_ok=True)
CLIPS = WORK / "clips"
CLIPS.mkdir(parents=True, exist_ok=True)
FFMPEG = "ffmpeg"

FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-29"
tl = json.loads((OUT / ("timeline_" + FECHA + ".json")).read_text())
print("[render] " + FECHA + " | " + str(len(tl)) + " escenas", flush=True)

# PASO A
print("\n[A] Clips por escena", flush=True)
tA = time.time()
for i, it in enumerate(tl):
    n = it["id"]
    dur = round(it["fin"] - it["inicio"], 2)
    tipo = it.get("tipo_visual", "imagen")
    vid = MEDIA / ("escena_%02d.mp4" % n)
    img = MEDIA / ("escena_%02d.png" % n)
    out = CLIPS / ("clip_%02d.mp4" % n)
    src = vid if (tipo == "video" and vid.exists()) else img
    if not src.exists():
        print("[A] FALTA escena %d" % n)
        sys.exit(1)
    loop = ["-stream_loop", "-1"] if src.suffix == ".mp4" else ["-loop", "1"]
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + loop + ["-i", str(src)] + [
        "-t", str(dur),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
        "-an", "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0:
        print("[A] FAIL %d: %s" % (n, r.stderr[-300:]))
        sys.exit(1)
    print("  %02d/%d (%ss, %.1fs) %dKB" % (n, len(tl), dur, time.time()-t0, out.stat().st_size//1024), flush=True)
print("[A] OK %.1fs" % (time.time()-tA), flush=True)

# PASO B
print("\n[B] Concat", flush=True)
intro = OUT / "intro.mp4"
outro = OUT / "outro.mp4"

def gen_solid(p, dur):
    if not p.exists():
        subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", "color=c=0x0a0a0f:s=1920x1080:d=" + str(dur) + ":r=25",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(p)],
            capture_output=True, check=True)

gen_solid(intro, 2)
gen_solid(outro, 2)

def norm(src, dst):
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
        "-an", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p", str(dst)],
        capture_output=True, check=True)

norm(intro, CLIPS / "00_intro.mp4")
norm(outro, CLIPS / "99_outro.mp4")

lista = WORK / "concat.txt"
with open(lista, "w") as f:
    f.write("file '" + str(CLIPS / "00_intro.mp4") + "'\n")
    for it in tl:
        f.write("file '" + str(CLIPS / ("clip_%02d.mp4" % it["id"])) + "'\n")
    f.write("file '" + str(CLIPS / "99_outro.mp4") + "'\n")

video_base = WORK / "video_base.mp4"
tB = time.time()
r = subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
    "-f", "concat", "-safe", "0", "-i", str(lista),
    "-c", "copy", str(video_base)], capture_output=True, text=True, timeout=180)
if r.returncode != 0:
    print("[B] FAIL: " + r.stderr[-300:])
    sys.exit(1)
print("[B] OK %dMB %.1fs" % (video_base.stat().st_size//1024//1024, time.time()-tB), flush=True)

# PASO C - lofi continuo de fondo (RUTA A)
print("\n[C] Lofi continuo", flush=True)
voz = OUT / ("voz_largo_" + FECHA + ".mp3")
if not voz.exists(): print("[C] FALTA voz"); sys.exit(1)
dur_total = 2.0 + tl[-1]["fin"] + 2.0

# Elegir 1 lofi: el MP3 mas largo de musica_temp
candidatos = sorted(MUSICA.glob("*.mp3"), key=lambda x: x.stat().st_size, reverse=True)
if not candidatos: print("[C] FALTA musica_temp/*.mp3"); sys.exit(1)
lofi_src = candidatos[0]
print("[C] lofi: " + lofi_src.name, flush=True)

audio_out = WORK / "audio.m4a"
cmd_c = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
    "-i", str(voz),
    "-stream_loop", "-1", "-i", str(lofi_src),
    "-filter_complex",
        "[0:a]adelay=2000|2000,apad=whole_dur=" + str(dur_total) + "[voz];"
        "[1:a]atrim=0:" + str(dur_total) + ",afade=t=in:st=0:d=3,afade=t=out:st=" + str(max(0, dur_total-3)) + ":d=3,volume=0.10[mus];"
        "[voz][mus]amix=inputs=2:duration=longest:normalize=0[a]",
    "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-t", str(dur_total), str(audio_out)]
import time as _t; _t0 = _t.time()
r = subprocess.run(cmd_c, capture_output=True, text=True, timeout=180)
if r.returncode != 0: print("[C] FAIL: " + r.stderr[-300:]); sys.exit(1)
print("[C] OK %dKB %.1fs" % (audio_out.stat().st_size//1024, _t.time()-_t0), flush=True)

# PASO D
print("\n[D] Mux final", flush=True)
ass = OUT / ("voz_largo_" + FECHA + ".ass")
out_final = OUT / ("video_largo_" + FECHA + ".mp4")
ass_esc = str(ass).replace(":", "\\:").replace("'", "\\'")
vf = "null"  # RUTA A: sin ASS, YouTube auto-subs

cmd_d = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(video_base), "-i", str(audio_out),
         "-vf", vf, "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
         "-c:a", "copy", "-t", str(dur_total), "-movflags", "+faststart", str(out_final)]
tD = time.time()
r = subprocess.run(cmd_d, capture_output=True, text=True, timeout=600)
if r.returncode != 0:
    print("[D] FAIL: " + r.stderr[-500:])
    sys.exit(1)
print("[D] OK " + out_final.name + " %dMB %.1fs" % (out_final.stat().st_size//1024//1024, time.time()-tD), flush=True)

# Verificacion
dur_real = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
    "-of", "default=noprint_wrappers=1:nokey=1", str(out_final)],
    capture_output=True, text=True).stdout.strip()
print("\nOK COMPLETADO: " + out_final.name + " %.1f min" % (float(dur_real)/60), flush=True)
