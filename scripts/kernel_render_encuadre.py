"""kernel_render_encuadre.py - Kernel Kaggle T4 con FFmpeg NVENC + fallback CPU."""
import subprocess, pathlib, json, sys, os, urllib.request, tarfile, shutil, time, base64

FECHA = "__FECHA__"
GITHUB_TOKEN = "__GITHUB_TOKEN__"
GITHUB_REPO = "keizdespania/LofiProducer-backup"

# ─── 1. FFmpeg con NVENC (descarga estática) ───
WORK = pathlib.Path("/kaggle/working")
FFMPEG71 = WORK / "ffmpeg_static" / "ffmpeg"
NVENC_URLS = {
    # BtbN 7.1 (headers NVENC 13.0 → driver 570+)
    "7.1": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz",
    # BtbN master (headers 13.1 → driver 610, probablemente fallará en Kaggle)
    "master": "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
}
FFMPEG71 = WORK / "ffmpeg71" / "ffmpeg"


def _descargar_ffmpeg(version="7.1"):
    """Descarga FFmpeg estático de BtbN (7.1 compatible con driver Kaggle)."""
    if FFMPEG71.exists(): return str(FFMPEG71)
    url = NVENC_URLS.get(version, NVENC_URLS["7.1"])
    try:
        print(f"[ffmpeg] descargando {version}...", flush=True)
        tar = WORK / f"ffmpeg_{version}.tar.xz"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r, open(tar, "wb") as f:
            shutil.copyfileobj(r, f)
        print(f"[ffmpeg] {tar.stat().st_size//1024//1024}MB descargados", flush=True)
        extract = WORK / f"ffmpeg_{version}_extract"
        with tarfile.open(tar, "r:xz") as t:
            t.extractall(extract)
        FFMPEG71.parent.mkdir(parents=True, exist_ok=True)
        for d in extract.glob("ffmpeg-*/bin/ffmpeg"):
            shutil.copy2(d, FFMPEG71)
            FFMPEG71.chmod(0o755)
            print(f"[ffmpeg] OK en {FFMPEG71}", flush=True)
            return str(FFMPEG71)
    except Exception as e:
        print(f"[ffmpeg] fallo descarga {version}: {e}", flush=True)
    return None


def _test_encoder(ffmpeg_bin, codec):
    """Test REAL: encode 1 frame a null. No escribe fichero, solo verifica encoder."""
    if not ffmpeg_bin: return False
    if not (shutil.which(ffmpeg_bin) or Path(ffmpeg_bin).exists()): return False
    try:
        r = subprocess.run(
            [ffmpeg_bin, "-hide_banner", "-loglevel", "error",
             "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.1",
             "-c:v", codec, "-t", "0.1", "-f", "null", "-"],
            capture_output=True, text=True, timeout=20)
        if r.returncode == 0:
            print(f"[test] OK {ffmpeg_bin} + {codec}", flush=True)
            return True
        else:
            err = (r.stderr or "")[:200].replace("\n", " ")
            print(f"[test] FAIL {ffmpeg_bin} + {codec}: {err}", flush=True)
            return False
    except Exception as e:
        print(f"[test] EXC {ffmpeg_bin} + {codec}: {e}", flush=True)
        return False


# ─── Cascada de selección (sistema primero, luego BtbN 7.1, luego CPU) ───
# No descargamos BtbN hasta que sea necesario
FFMPEG, ENC = None, None

# 1. Sistema con NVENC (drivers Kaggle alineados, 0 descargas)
if _test_encoder("ffmpeg", "h264_nvenc"):
    FFMPEG, ENC = "ffmpeg", "h264_nvenc"

# 2. BtbN 7.1 con NVENC
if not FFMPEG:
    bin71 = _descargar_ffmpeg("7.1")
    if _test_encoder(bin71, "h264_nvenc"):
        FFMPEG, ENC = bin71, "h264_nvenc"

# 3. Sistema CPU (siempre funciona)
if not FFMPEG:
    if _test_encoder("ffmpeg", "libx264"):
        FFMPEG, ENC = "ffmpeg", "libx264"

# 4. BtbN 7.1 CPU
if not FFMPEG:
    bin71 = _descargar_ffmpeg("7.1") or str(FFMPEG71)
    if _test_encoder(bin71, "libx264"):
        FFMPEG, ENC = bin71, "libx264"

if not FFMPEG:
    print("[enc] SIN encoder válido, abortando", flush=True)
    sys.exit(1)

print(f"[enc] SELECCIONADO: {FFMPEG} + {ENC}", flush=True)

# ─── 2. Assets ───
KAGGLE_INPUT = pathlib.Path("/kaggle/input")
ASSETS = None
print("[mount] esperando dataset...", flush=True)
for waited in range(0, 300, 10):
    for d in KAGGLE_INPUT.glob("*/"):
        if (d / "timeline.json").exists():
            ASSETS = d; print(f"[mount] OK en {waited}s: {d}", flush=True); break
        # Buscar también dentro (por si --dir-mode zip crea subcarpeta)
        for sub in d.glob("*/"):
            if (sub / "timeline.json").exists():
                ASSETS = sub; print(f"[mount] OK (sub) en {waited}s: {sub}", flush=True); break
        if ASSETS: break
    if ASSETS: break
    if waited % 30 == 0: print(f"[mount] {waited}s...", flush=True)
    time.sleep(10)
if not ASSETS:
    print(f"[mount] fallback {KAGGLE_INPUT}", flush=True)
    ASSETS = pathlib.Path(os.environ.get("ASSETS_DIR", "/kaggle/input/encuadre-assets"))

OUT = WORK / "video_largo.mp4"
print(f"[assets] {ASSETS}", flush=True)

tl_file = ASSETS / "timeline.json"
if not tl_file.exists():
    print(f"ERROR: falta {tl_file}", flush=True); sys.exit(1)
timeline = json.loads(tl_file.read_text())

voz = ASSETS / "voz_largo.mp3"
ass = ASSETS / "voz_largo.ass"
intro = ASSETS / "intro.mp4"
outro = ASSETS / "outro.mp4"

for pp, dur in [(intro, 2), (outro, 2)]:
    if not pp.exists():
        subprocess.run([FFMPEG,"-y","-f","lavfi","-i",f"color=c=0x0a0a0f:s=1920x1080:d={dur}:r=25",
                       "-f","lavfi","-i",f"anullsrc=r=44100:cl=stereo:d={dur}",
                       "-shortest","-c:v","libx264","-preset","ultrafast","-c:a","aac",str(pp)],
                       capture_output=True, check=True)

# ─── 3. Filtros ───
inputs, counter = [], [0]
def add_in(path, loop=False):
    if loop: inputs.extend(["-stream_loop","-1","-i",str(path)])
    else: inputs.extend(["-i",str(path)])
    counter[0] += 1
    return counter[0]-1

i_intro = add_in(intro); i_outro = add_in(outro); i_voz = add_in(voz)
filtros, v_labels, a_labels = [], [], []

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

# ─── 4. Render con encoder elegido ───
print(f"[render] {len(timeline)} escenas, {dur_total:.1f}s, {ENC}", flush=True)
if ENC == "h264_nvenc":
    enc_args = ["-c:v","h264_nvenc","-preset","p4","-rc","vbr","-cq","20","-b:v","6M"]
else:
    enc_args = ["-c:v","libx264","-crf","20","-preset","fast"]

cmd = [FFMPEG,"-y"] + inputs + [
    "-filter_complex",";".join(filtros),
    "-map","[v]","-map","[a]",
] + enc_args + ["-c:a","aac","-b:a","192k","-t",str(dur_total),str(OUT)]

r = subprocess.run(cmd, capture_output=True, text=True, timeout=3300)
if r.returncode != 0:
    print(f"FFmpeg error:\n{r.stderr[-1500:]}", flush=True); sys.exit(1)
print(f"OK {OUT.name} ({OUT.stat().st_size//1024//1024}MB)", flush=True)

# ─── 5. Subir a GitHub (patrón Wan) ───
if GITHUB_TOKEN and not GITHUB_TOKEN.startswith("__") and OUT.exists():
    try:
        import requests as _rq
        with open(str(OUT), "rb") as f:
            content = base64.b64encode(f.read()).decode()
        dest_path = f"output/videos/render_{FECHA}.mp4"
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{dest_path}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        r = _rq.get(url, headers=headers, timeout=30)
        sha = r.json().get("sha") if r.status_code == 200 else None
        payload = {"message": f"render {FECHA}", "content": content, "branch": "main"}
        if sha: payload["sha"] = sha
        r = _rq.put(url, headers=headers, json=payload, timeout=600)
        print(f"[github] PUT {dest_path}: {r.status_code}", flush=True)
    except Exception as e:
        print(f"[github] error: {e}", flush=True)
