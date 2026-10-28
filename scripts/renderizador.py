"""renderizador.py - Renderiza cada escena (video/imagen) con su musica y las concatena."""
import sys, json, pathlib, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
TMP = ROOT / "output" / "render_tmp"
TMP.mkdir(parents=True, exist_ok=True)

def _render_escena(item, fecha):
    num, ini, fin = item["id"], item["inicio"], item["fin"]
    dur = fin - ini
    tipo = item.get("tipo_visual", "imagen")
    vid = MEDIA / f"escena_{num:02d}.mp4"
    img = MEDIA / f"escena_{num:02d}.png"
    mus = MUSICA / f"escena_{num:02d}.mp3"
    voz = OUT / f"voz_largo_{fecha}.mp3"

    if tipo == "video" and vid.exists():
        cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(vid)]
        fv = f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.4,fade=t=out:st={max(0,dur-0.6)}:d=0.6[v]"
    elif img.exists():
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img)]
        frames = int(dur * 25)
        fv = f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,zoompan=z='min(zoom+0.0015,1.15)':d={frames}:s=1920x1080:fps=25,fade=t=in:st=0:d=0.4,fade=t=out:st={max(0,dur-0.6)}:d=0.6[v]"
    else:
        return None

    cmd += ["-i", str(voz)]
    if mus.exists():
        cmd += ["-i", str(mus)]
        fa = f"[1:a]atrim={ini}:{fin},asetpts=PTS-STARTPTS[voz];[2:a]atrim=0:{dur},afade=t=in:st=0:d=1,afade=t=out:st={max(0,dur-2)}:d=2,volume=0.15[mus];[voz][mus]amix=inputs=2:duration=first:normalize=0[a]"
    else:
        fa = f"[1:a]atrim={ini}:{fin},asetpts=PTS-STARTPTS[a]"

    out = TMP / f"escena_{num:02d}.mp4"
    cmd += ["-filter_complex", f"{fv};{fa}", "-map", "[v]", "-map", "[a]",
            "-t", str(dur), "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", str(out)]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if r.returncode == 0 and out.exists(): return out
    print(f"  X escena {num} fallo: {r.stderr[-200:]}")
    return None

def renderizar(fecha):
    tf = OUT / f"timeline_{fecha}.json"
    if not tf.exists():
        print("No timeline"); return
    timeline = json.loads(tf.read_text())
    print(f"Renderizando {len(timeline)} escenas...")
    segs = []
    for it in timeline:
        print(f"  [{it['id']}] {it.get('tipo_visual','?')}")
        s = _render_escena(it, fecha)
        if s: segs.append(s)
    if not segs:
        print("X sin segmentos"); return
    lista = TMP / "concat.txt"
    with open(lista, "w") as f:
        for s in segs: f.write(f"file '{s}'\n")
    final = OUT / f"video_largo_{fecha}.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(final)], capture_output=True)
    
    if final.exists():
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(final)], capture_output=True, text=True)
        d = float(r.stdout.strip()) if r.stdout.strip() else 0
        print(f"OK {final.name} ({d/60:.1f} min, {final.stat().st_size//1024//1024}MB)")

if __name__ == "__main__":
    renderizar(sys.argv[1] if len(sys.argv) > 1 else None)
