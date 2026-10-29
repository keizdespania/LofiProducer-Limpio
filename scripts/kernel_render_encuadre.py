"""kernel_render_encuadre.py - Kernel que corre en Kaggle T4 (GPU).
Lee un dataset con assets/{escena_*.mp4,png, voz.mp3, voz.ass, musica/*}
y produce video_largo.mp4 en /kaggle/working con h264_nvenc."""
import subprocess, pathlib, json, sys, os

# Detectar directorio de assets (dataset Kaggle o local)
KAGGLE_INPUT = pathlib.Path("/kaggle/input")
ASSETS = None
for d in KAGGLE_INPUT.glob("*/"):
    if (d / "timeline.json").exists():
        ASSETS = d
        break
if not ASSETS:
    # Fallback para test local
    ASSETS = pathlib.Path(os.environ.get("ASSETS_DIR", "/kaggle/input/encuadre-assets"))

WORK = pathlib.Path("/kaggle/working")
OUT = WORK / "video_largo.mp4"

print(f"ASSETS: {ASSETS}", flush=True)
print(f"OUT: {OUT}", flush=True)

tl_file = ASSETS / "timeline.json"
if not tl_file.exists():
    print(f"ERROR: falta {tl_file}", flush=True); sys.exit(1)
timeline = json.loads(tl_file.read_text())

voz = ASSETS / "voz_largo.mp3"
ass = ASSETS / "voz_largo.ass"
intro = ASSETS / "intro.mp4"
outro = ASSETS / "outro.mp4"

# Generar intro/outro si faltan
for pp, dur in [(intro, 2), (outro, 2)]:
    if not pp.exists():
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"color=c=0x0a0a0f:s=1920x1080:d={dur}:r=25",
                       "-f","lavfi","-i",f"anullsrc=r=44100:cl=stereo:d={dur}",
                       "-shortest","-c:v","libx264","-preset","ultrafast","-c:a","aac",str(pp)], capture_output=True, check=True)

inputs = []
counter = [0]
def add_in(path, loop=False):
    if loop: inputs.extend(["-stream_loop","-1","-i",str(path)])
    else: inputs.extend(["-i",str(path)])
    counter[0] += 1
    return counter[0]-1

i_intro = add_in(intro); i_outro = add_in(outro); i_voz = add_in(voz)
filtros, v_labels, a_labels = [], [], []

# Encoder por GPU
def add_enc_inputs(path, loop=False):
    if loop: inputs.extend(["-stream_loop","-1","-i",str(path)])
    else: inputs.extend(["-i",str(path)])
    counter[0] += 1
    return counter[0]-1

# INTRO
filtros.append(f"[{i_intro}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,setpts=PTS-STARTPTS[v_intro]")
v_labels.append("[v_intro]")
offset = 2.0

for i, item in enumerate(timeline):
    num = item["id"]; dur = item["fin"] - item["inicio"]
    tipo = item.get("tipo_visual","imagen")
    vid = ASSETS / f"escena_{num:02d}.mp4"
    img = ASSETS / f"escena_{num:02d}.png"
    mus = ASSETS / f"escena_{num:02d}.mp3"

    if tipo == "video" and vid.exists():
        iv = add_in(vid, loop=True)
        filtros.append(f"[{iv}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
    elif img.exists():
        iv = add_in(img, loop=True)
        filtros.append(f"[{iv}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
    else:
        print(f"Falta visual escena {num}", flush=True); sys.exit(1)
    v_labels.append(f"[v{i+1}]")

    d = int((offset + item["inicio"]) * 1000)
    if mus.exists():
        ia = add_in(mus, loop=True)
        fo_s = max(0, dur - min(2, dur/2)); fo_d = min(2, dur/2)
        filtros.append(f"[{ia}:a]atrim=0:{dur},afade=t=in:st=0:d=1,afade=t=out:st={fo_s}:d={fo_d},volume=0.15,adelay={d}|{d}[a{i+1}]")
    else:
        filtros.append(f"aevalsrc=0:d={dur}:s=44100,adelay={d}|{d}[a{i+1}]")
    a_labels.append(f"[a{i+1}]")

fin_voz = timeline[-1]["fin"]
dur_total = offset + fin_voz + 2.0
delay_outro = int((offset + fin_voz) * 1000)
filtros.append(f"[{i_outro}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration=2,setpts=PTS-STARTPTS[v_out]")
filtros.append(f"[{i_outro}:a]atrim=0:2,adelay={delay_outro}|{delay_outro}[a_out]")
v_labels.append("[v_out]"); a_labels.append("[a_out]")
filtros.append(f"[{i_voz}:a]adelay={int(offset*1000)}|{int(offset*1000)}[voice]")
filtros.append(f"{''.join(v_labels)}concat=n={len(v_labels)}:v=1:a=0[v_concat]")

if ass.exists():
    filtros.append(f"[v_concat]ass='{ass}'[v]")
else:
    filtros.append("[v_concat]null[v]")

todos_a = "[voice]" + "".join(a_labels)
filtros.append(f"{todos_a}amix=inputs={len(a_labels)+1}:duration=longest:normalize=0,apad=whole_dur={dur_total}[a]")

print(f"Renderizando {len(timeline)} escenas, {dur_total:.1f}s, GPU...", flush=True)
cmd = ["ffmpeg","-y","-hwaccel","cuda"] + inputs + [
    "-filter_complex",";".join(filtros),
    "-map","[v]","-map","[a]",
    "-c:v","h264_nvenc","-preset","p4","-rc","vbr","-cq","20","-b:v","6M",
    "-c:a","aac","-b:a","192k","-t",str(dur_total),str(OUT)
]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=3300)
if r.returncode != 0:
    print(f"FFmpeg error:\n{r.stderr[-1500:]}", flush=True); sys.exit(1)
print(f"OK {OUT.name} ({OUT.stat().st_size//1024//1024}MB)", flush=True)
