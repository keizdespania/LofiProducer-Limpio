"""renderizador.py - Renderizador Top 1: Estructura de un solo comando con concat filter."""
import sys, json, pathlib, subprocess, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
TMP = ROOT / "output" / "render_tmp"
TMP.mkdir(parents=True, exist_ok=True)

def _generar_intro_outro():
    """Genera intro (3s) y outro (4s) con audio silencioso para concatenar perfectamente."""
    logo = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
    intro = TMP / "intro.mp4"
    outro = TMP / "outro.mp4"
    
    if not logo.exists():
        print("❌ Falta el logo para intro/outro")
        return None, None

    # Intro: 3s, logo centrado, audio silencioso
    vf_intro = "scale=800:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-vf", vf_intro, "-t", "3", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-shortest", str(intro)], capture_output=True)

    # Outro: 4s, logo + texto, audio silencioso
    vf_outro = "scale=600:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2+50:black,drawtext=text='SOMOS EL ENCUADRE':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h-150,fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5"
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-vf", vf_outro, "-t", "4", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-shortest", str(outro)], capture_output=True)

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
        print("❌ No hay timeline"); return
    timeline = json.loads(tf.read_text())
    if not timeline:
        print("❌ Timeline vacío"); return
    voz = OUT / f"voz_largo_{fecha}.mp3"
    ass_original = OUT / f"voz_largo_{fecha}.ass"

    if not voz.exists():
        print("❌ Falta la voz"); return

    # 1. Generar intro y outro
    print("🎬 Generando intro y outro...")
    intro, outro = _generar_intro_outro()
    if not intro or not outro:
        return

    # 2. Desplazar el ASS por la duración de la intro (3s)
    offset = 3.0
    if ass_original.exists():
        ass_path = _desplazar_ass(ass_original, TMP / f"sub_{fecha}.ass", offset)
    else:
        ass_path = None

    # 3. Construir los inputs y el filter_complex
    inputs = []
    filtros = []
    video_labels = []
    audio_labels = []
    
    # Input 0: Intro
    inputs += ["-i", str(intro)]
    filtros.append("[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,setpts=PTS-STARTPTS[v0]")
    filtros.append("[0:a]anull[a0]")
    video_labels.append("[v0]")
    audio_labels.append("[a0]")

    # Input 1: Outro (Se prepara pero NO se añade todavía a la lista)
    inputs += ["-i", str(outro)]
    filtros.append("[1:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,setpts=PTS-STARTPTS[v_out]")
    
    # Calcular el tiempo total del vídeo antes del outro
    duracion_voz = timeline[-1]["fin"] if timeline else 0
    delay_outro = int((offset + duracion_voz) * 1000)
    filtros.append(f"[1:a]adelay={delay_outro}|{delay_outro}[a_out]")

    # Input 2: Voz
    inputs += ["-i", str(voz)]
    voz_idx = 2

    # Escenas
    for i, item in enumerate(timeline):
        num = item["id"]
        dur = item["fin"] - item["inicio"]
        tipo = item.get("tipo_visual", "imagen")
        vid = MEDIA / f"escena_{num:02d}.mp4"
        img = MEDIA / f"escena_{num:02d}.png"
        mus = MUSICA / f"escena_{num:02d}.mp3"

        # Visual
        v_idx = len(inputs) // 2
        if tipo == "video" and vid.exists():
            inputs += ["-stream_loop", "-1", "-i", str(vid)]
            filtros.append(f"[{v_idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
        elif img.exists():
            inputs += ["-loop", "1", "-i", str(img)]
            filtros.append(f"[{v_idx}:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS[v{i+1}]")
        else:
            print(f"❌ Falta visual escena {num}")
            return
        video_labels.append(f"[v{i+1}]")

        # Música
        a_idx = len(inputs) // 2
        if mus.exists():
            inputs += ["-stream_loop", "-1", "-i", str(mus)]
            delay_ms = int((offset + item["inicio"]) * 1000)
            fade_out_start = max(0, dur - min(2, dur/2))
            fade_out_dur = min(2, dur/2)
            filtros.append(f"[{a_idx}:a]atrim=0:{dur},afade=t=in:st=0:d=1,afade=t=out:st={fade_out_start}:d={fade_out_dur},volume=0.15,adelay={delay_ms}|{delay_ms}[a{i+1}]")
            audio_labels.append(f"[a{i+1}]")
        else:
            # Sin música: silencio para rellenar
            filtros.append(f"anullsrc=r=44100:cl=stereo,atrim=duration={dur}[a{i+1}]")
            audio_labels.append(f"[a{i+1}]")

    # Añadir el Outro al final de las listas
    video_labels.append("[v_out]")
    audio_labels.append("[a_out]")

    # 4. Concatenar vídeo
    todos_v = "".join(video_labels)
    filtros.append(f"{todos_v}concat=n={len(video_labels)}:v=1:a=0[v_concat]")

    # 5. Subtítulos (si existen)
    if ass_path:
        filtros.append(f"[v_concat]ass='{ass_path}'[v]")
    else:
        filtros.append("[v_concat]null[v]")

    # 6. Audio de la voz (con delay de intro)
    filtros.append(f"[{voz_idx}:a]adelay={int(offset*1000)}|{int(offset*1000)}[voice]")

    # 7. Mezclar toda la voz con los audios de las escenas
    todos_a = "[voice]" + "".join(audio_labels)
    filtros.append(f"{todos_a}amix=inputs={len(audio_labels)+1}:duration=longest:normalize=0,apad=whole_dur={dur_total}[a]")

    # Calcular duración exacta total (intro + voz + outro)
    dur_total = offset + (timeline[-1]["fin"] if timeline else 0) + 4 # 4s de outro
    print(f"  ⏱️ Duración total calculada: {dur_total:.1f}s")
    
    # 8. Comando final (Un solo FFmpeg)
    final = OUT / f"video_largo_{fecha}.mp4"
    cmd = ["ffmpeg", "-y"] + inputs + [
        "-filter_complex", ";".join(filtros),
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-c:a", "aac", "-b:a", "192k", "-t", str(dur_total), str(final)
    ]

    print(f"🎬 Renderizando vídeo largo (un solo comando, {len(timeline)} escenas)...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if r.returncode == 0 and final.exists():
        dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(final)], capture_output=True, text=True).stdout.strip()
        print(f"✅ VÍDEO FINAL: {final.name} ({float(dur)/60:.1f} min, {final.stat().st_size//1024//1024}MB)")
    else:
        print(f"❌ Error FFmpeg: {r.stderr[-500:]}")

if __name__ == "__main__":
    renderizar(sys.argv[1] if len(sys.argv) > 1 else None)
