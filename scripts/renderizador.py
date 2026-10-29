"""renderizador.py v2 - índices FFmpeg correctos, intro+outro en concat, test sintético."""
import json, pathlib, subprocess, sys, argparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"


def _generar_intro_outro():
    intro = OUT / "intro.mp4"
    outro = OUT / "outro.mp4"
    for pp, dur in [(intro, 2), (outro, 2)]:
        if not pp.exists():
            subprocess.run([
                "ffmpeg","-y",
                "-f","lavfi","-i",f"color=c=0x0a0a0f:s=1920x1080:d={dur}:r=25",
                "-f","lavfi","-i",f"anullsrc=r=44100:cl=stereo:d={dur}",
                "-shortest","-c:v","libx264","-preset","ultrafast","-c:a","aac",
                str(pp)], capture_output=True)
    return intro, outro


def _desplazar_ass(ass_original, ass_nuevo, offset_seg):
    """Desplaza los timestamps del ASS para que empiecen después de la intro."""
    lineas = ass_original.read_text().splitlines()
    nuevas = []
    
    def parse_time(t):
        h, m, s = t.split(":")
        return int(h)*3600 + int(m)*60 + float(s)
        
    def format_time(sec):
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    for linea in lineas:
        if linea.startswith("Dialogue:"):
            partes = linea.split(",")
            if len(partes) >= 3:
                start = parse_time(partes[1].strip())
                end = parse_time(partes[2].strip())
                partes[1] = " " + format_time(start + offset_seg)
                partes[2] = " " + format_time(end + offset_seg)
                nuevas.append(",".join(partes))
                continue
        nuevas.append(linea)
    
    ass_nuevo.write_text("\n".join(nuevas))
    return ass_nuevo


def renderizar(fecha):
    tf = OUT / f"timeline_{fecha}.json"
    if not tf.exists():
        print(f"No hay timeline {tf}"); return False
    timeline = json.loads(tf.read_text())
    if not timeline:
        print("Timeline vacio"); return False

    intro, outro = _generar_intro_outro()
    voz = OUT / f"voz_largo_{fecha}.mp3"
    if not voz.exists():
        print(f"No hay voz {voz}"); return False
    ass_orig = OUT / f"voz_largo_{fecha}.ass"

    inputs = []
    counter = [0]

    def add_in(path, loop=False):
        if loop:
            inputs.extend(["-stream_loop", "-1", "-i", str(path)])
        else:
            inputs.extend(["-i", str(path)])
        counter[0] += 1
        return counter[0] - 1

    i_intro = add_in(intro)
    i_outro = add_in(outro)
    i_voz = add_in(voz)

    filtros, v_labels, a_labels = [], [], []

    filtros.append(f"[{i_intro}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,setpts=PTS-STARTPTS[v_intro]")
    v_labels.append("[v_intro]")
    offset = 2.0

    for i, item in enumerate(timeline):
        num = item["id"]; dur = item["fin"] - item["inicio"]
        tipo = item.get("tipo_visual","imagen")
        vid = MEDIA / f"escena_{num:02d}.mp4"
        img = MEDIA / f"escena_{num:02d}.png"
        mus = MUSICA / f"escena_{num:02d}.mp3"

        if tipo == "video" and vid.exists():
            iv = add_in(vid, loop=True)
            filtros.append(f"[{iv}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
        elif img.exists():
            iv = add_in(img, loop=True)
            filtros.append(f"[{iv}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
        else:
            print(f"Falta visual escena {num}"); return False
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
    v_labels.append("[v_out]")
    a_labels.append("[a_out]")

    filtros.append(f"[{i_voz}:a]adelay={int(offset*1000)}|{int(offset*1000)}[voice]")

    filtros.append(f"{''.join(v_labels)}concat=n={len(v_labels)}:v=1:a=0[v_concat]")

    if ass_orig.exists() and "_desplazar_ass" in globals():
        try:
            ass_d = OUT / f"voz_largo_{fecha}_despl.ass"
            _desplazar_ass(ass_orig, ass_d, offset)
            filtros.append(f"[v_concat]ass='{ass_d}'[v]")
        except Exception as e:
            print(f"  subs fallback: {e}")
            filtros.append("[v_concat]null[v]")
    else:
        filtros.append("[v_concat]null[v]")

    todos_a = "[voice]" + "".join(a_labels)
    filtros.append(f"{todos_a}amix=inputs={len(a_labels)+1}:duration=longest:normalize=0,apad=whole_dur={dur_total}[a]")

    final = OUT / f"video_largo_{fecha}.mp4"
    cmd = ["ffmpeg","-y"] + inputs + [
        "-filter_complex",";".join(filtros),
        "-map","[v]","-map","[a]",
        "-c:v","libx264","-crf","20","-preset","ultrafast",
        "-c:a","aac","-b:a","192k","-t",str(dur_total),str(final)
    ]
    print(f"Renderizando ({len(timeline)} escenas, {dur_total:.1f}s)...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    if r.returncode != 0:
        print(f"FFmpeg error:\n{r.stderr[-800:]}"); return False
    if not final.exists():
        print("Video no generado"); return False
    d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(final)], capture_output=True, text=True).stdout.strip()
    print(f"OK {final.name} ({float(d)/60:.2f} min, {final.stat().st_size//1024//1024}MB)")
    return True


def _test_sintetico():
    print("=== TEST SINTETICO 3 ESCENAS ===")
    fecha = "sintetico"
    MEDIA.mkdir(parents=True, exist_ok=True); MUSICA.mkdir(parents=True, exist_ok=True)
    voz = OUT / f"voz_largo_{fecha}.mp3"
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=440:duration=6","-c:a","libmp3lame",str(voz)], capture_output=True, check=True)
    colores = ["0x1e2840","0x40281e","0x28401e"]
    for n in [1,2,3]:
        vid = MEDIA / f"escena_{n:02d}.mp4"
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"color=c={colores[n-1]}:s=1920x1080:d=3:r=25","-c:v","libx264","-preset","ultrafast","-an",str(vid)], capture_output=True, check=True)
        mus = MUSICA / f"escena_{n:02d}.mp3"
        subprocess.run(["ffmpeg","-y","-f","lavfi","-i",f"sine=frequency={200+n*50}:duration=3","-c:a","libmp3lame",str(mus)], capture_output=True, check=True)
    tl = [{"id":1,"inicio":0.0,"fin":2.0,"tipo_visual":"video"},
          {"id":2,"inicio":2.0,"fin":4.0,"tipo_visual":"video"},
          {"id":3,"inicio":4.0,"fin":6.0,"tipo_visual":"video"}]
    (OUT / f"timeline_{fecha}.json").write_text(json.dumps(tl))
    ok = renderizar(fecha)
    if ok:
        final = OUT / f"video_largo_{fecha}.mp4"
        real = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(final)], capture_output=True, text=True).stdout.strip())
        esperado = 10.0
        print(f"  dur real={real:.2f}s esperado={esperado}s")
        if abs(real - esperado) > 0.5:
            print(f"  DESYNC"); return False
        a_stream = subprocess.run(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=codec_name","-of","default=noprint_wrappers=1:nokey=1",str(final)], capture_output=True, text=True).stdout.strip()
        print(f"  audio stream: {a_stream or 'NO'}")
        if not a_stream: return False
        print("  TEST OK")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fecha", nargs="?")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        sys.exit(0 if _test_sintetico() else 1)
    if not a.fecha:
        print("Uso: renderizador.py YYYY-MM-DD | --test"); sys.exit(1)
    sys.exit(0 if renderizar(a.fecha) else 1)
