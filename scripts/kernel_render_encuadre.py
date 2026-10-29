"""kernel_render_encuadre.py v2 - Render en 4 pasadas (evita colgar FFmpeg)."""
import subprocess, pathlib, json, sys, os, urllib.request, tarfile, shutil, time, base64, re

FECHA = "__FECHA__"
GITHUB_TOKEN = "__GITHUB_TOKEN__"
GITHUB_REPO = "keizdespania/LofiProducer-backup"
WORK = pathlib.Path("/kaggle/working")


def _test_encoder(binario, codec):
    try:
        r = subprocess.run(
            [binario, "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.1",
             "-c:v", codec, "-t", "0.1", "-f", "null", "-"],
            capture_output=True, text=True, timeout=15)
        return r.returncode == 0
    except Exception:
        return False


def _elegir_encoder():
    for b, c in [("ffmpeg", "h264_nvenc"), ("ffmpeg", "libx264")]:
        if _test_encoder(b, c):
            print(f"[enc] {b} + {c}", flush=True)
            return b, c
    print("[enc] SIN encoder"); sys.exit(1)

FFMPEG, ENC = _elegir_encoder()


def _mount():
    for _ in range(30):
        for d in pathlib.Path("/kaggle/input").glob("*/"):
            if (d / "timeline.json").exists(): return d
            for sub in d.glob("*/"):
                if (sub / "timeline.json").exists(): return sub
        time.sleep(10)
    return pathlib.Path("/kaggle/input/encuadre-assets-v3")


ASSETS = _mount()
print(f"[assets] {ASSETS}", flush=True)
tl = json.loads((ASSETS / "timeline.json").read_text())
print(f"[tl] {len(tl)} escenas", flush=True)

# ─── PASO A: cada escena → clip 1080p@25fps N seg ───
CLIPS = WORK / "clips"; CLIPS.mkdir(exist_ok=True)
enc_args = ["-c:v", ENC]
if ENC == "h264_nvenc": enc_args += ["-preset", "p4", "-rc", "vbr", "-cq", "23", "-b:v", "4M"]
else: enc_args += ["-crf", "23", "-preset", "veryfast"]

for i, it in enumerate(tl):
    n = it["id"]; dur = round(it["fin"] - it["inicio"], 2)
    tipo = it.get("tipo_visual", "imagen")
    vid = ASSETS / f"escena_{n:02d}.mp4"; img = ASSETS / f"escena_{n:02d}.png"
    out = CLIPS / f"clip_{n:02d}.mp4"
    src = vid if (tipo == "video" and vid.exists()) else img
    if not src.exists():
        print(f"[A] FALTA escena {n}"); sys.exit(1)
    loop = ["-stream_loop", "-1"] if src.suffix == ".mp4" else ["-loop", "1"]
    cmd = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + loop + ["-i", str(src)] + [
        "-t", str(dur),
        "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
        "-an", "-pix_fmt", "yuv420p"] + enc_args + [str(out)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        print(f"[A] FAIL {n}: {r.stderr[-300:]}"); sys.exit(1)
    print(f"[A] {n:02d}/{len(tl)} ({dur}s, {time.time()-t0:.1f}s) {out.stat().st_size//1024}KB", flush=True)

# ─── PASO B: intro + clips + outro → vídeo base (concat demuxer) ───
intro = ASSETS / "intro.mp4"; outro = ASSETS / "outro.mp4"
def _gen_solid(p, dur):
    if not p.exists():
        subprocess.run([FFMPEG, "-y", "-f", "lavfi", "-i", f"color=c=0x0a0a0f:s=1920x1080:d={dur}:r=25",
                        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(p)],
                       capture_output=True, check=True)
_gen_solid(intro, 2); _gen_solid(outro, 2)

# Reencodear intro/outro si no son 1920x1080@25
def _norm(src, dst):
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(src),
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
                    "-an", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(dst)],
                   capture_output=True, check=True)
_norm(intro, CLIPS / "00_intro.mp4"); _norm(outro, CLIPS / "99_outro.mp4")

lista = CLIPS / "concat.txt"
with open(lista, "w") as f:
    f.write(f"file '{CLIPS/'00_intro.mp4'}'\n")
    for it in tl:
        _n = it["id"]
        f.write(f"file '{CLIPS}/clip_{_n:02d}.mp4'\n")
    f.write(f"file '{CLIPS/'99_outro.mp4'}'\n")

video_base = WORK / "video_base.mp4"
cmd_b = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(lista),
         "-c", "copy", str(video_base)]
t0 = time.time(); r = subprocess.run(cmd_b, capture_output=True, text=True, timeout=300)
if r.returncode != 0: print(f"[B] FAIL: {r.stderr[-300:]}"); sys.exit(1)
print(f"[B] {video_base.name} ({video_base.stat().st_size//1024//1024}MB, {time.time()-t0:.1f}s)", flush=True)

# ─── PASO C: audio (voz + músicas) → audio.m4a ───
voz = ASSETS / "voz_largo.mp3"
if not voz.exists(): print("[C] FALTA voz_largo.mp3"); sys.exit(1)

# Duración real de cada clip (= timeline)
dur_total = 2.0 + tl[-1]["fin"] + 2.0
inputs_a, filtros_a, a_labels = [], [], []
idx = [0]
def add_a(path, loop_mus=False):
    if loop_mus: inputs_a.extend(["-stream_loop", "-1", "-i", str(path)])
    else: inputs_a.extend(["-i", str(path)])
    idx[0] += 1; return idx[0] - 1

i_voz = add_a(voz)
filtros_a.append(f"[{i_voz}:a]adelay={int(2*1000)}|{int(2*1000)}[voice]")
a_labels.append("[voice]")
for it in tl:
    n = it["id"]; dur = round(it["fin"] - it["inicio"], 2)
    mus = ASSETS / f"escena_{n:02d}.mp3"
    delay = int((2.0 + it["inicio"]) * 1000)
    if mus.exists():
        ia = add_a(mus, loop_mus=True)
        fo = max(0, dur - min(2, dur/2))
        filtros_a.append(f"[{ia}:a]atrim=0:{dur},afade=t=in:st=0:d=0.8,afade=t=out:st={fo}:d={min(2,dur/2)},volume=0.12,adelay={delay}|{delay}[a{n}]")
    else:
        filtros_a.append(f"anullsrc=r=44100:cl=stereo:d={dur},adelay={delay}|{delay}[a{n}]")
    a_labels.append(f"[a{n}]")

filtros_a.append(f"{''.join(a_labels)}amix=inputs={len(a_labels)}:duration=longest:normalize=0,apad=whole_dur={dur_total}[a]")
audio_out = WORK / "audio.m4a"
cmd_c = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error"] + inputs_a + [
    "-filter_complex", ";".join(filtros_a),
    "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-t", str(dur_total), str(audio_out)]
t0 = time.time(); r = subprocess.run(cmd_c, capture_output=True, text=True, timeout=300)
if r.returncode != 0: print(f"[C] FAIL: {r.stderr[-300:]}"); sys.exit(1)
print(f"[C] {audio_out.name} ({audio_out.stat().st_size//1024}KB, {time.time()-t0:.1f}s)", flush=True)

# ─── PASO D: mux video_base + audio + subs ───
ass = ASSETS / "voz_largo.ass"
out_final = WORK / "video_largo.mp4"
ass_esc = str(ass).replace(":", "\\:").replace("'", "\\'")
vf = f"ass='{ass_esc}'" if ass.exists() else "null"

if ENC == "h264_nvenc":
    d_enc = ["-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr", "-cq", "22", "-b:v", "4M"]
else:
    d_enc = ["-c:v", "libx264", "-crf", "22", "-preset", "veryfast"]

cmd_d = [FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(video_base), "-i", str(audio_out),
         "-vf", vf, "-map", "0:v", "-map", "1:a"] + d_enc + [
         "-c:a", "copy", "-t", str(dur_total), "-movflags", "+faststart", str(out_final)]
t0 = time.time(); r = subprocess.run(cmd_d, capture_output=True, text=True, timeout=600)
if r.returncode != 0: print(f"[D] FAIL: {r.stderr[-500:]}"); sys.exit(1)
print(f"[D] OK {out_final.name} ({out_final.stat().st_size//1024//1024}MB, {time.time()-t0:.1f}s)", flush=True)

# ─── Subida GitHub ───
if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("__"):
    try:
        import requests as _rq
        with open(str(out_final), "rb") as f:
            content = base64.b64encode(f.read()).decode()
        dest = f"output/videos/render_{FECHA}.mp4"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{dest}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        g = _rq.get(url, headers=headers, timeout=30)
        sha = g.json().get("sha") if g.status_code == 200 else None
        payload = {"message": f"render {FECHA}", "content": content, "branch": "main"}
        if sha: payload["sha"] = sha
        p = _rq.put(url, headers=headers, json=payload, timeout=900)
        print(f"[github] PUT {dest}: {p.status_code}", flush=True)
    except Exception as e:
        print(f"[github] error: {e}", flush=True)
