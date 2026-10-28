"""renderizador.py - Renderizador Top 1: sin zoompan, con transiciones, audio y subtítulos."""
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
    ass = OUT / f"voz_largo_{fecha}.ass"

    # 1. ELEGIR ASSET (Obligatorio)
    if tipo == "video" and vid.exists():
        input_visual = ["-stream_loop", "-1", "-i", str(vid)]
        fv = f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS"
    elif img.exists():
        input_visual = ["-loop", "1", "-i", str(img)]
        # EFECTO ESTÁTICO (sin zoompan, sin temblor)
        fv = f"[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25,trim=duration={dur},setpts=PTS-STARTPTS"
    else:
        print(f"  ❌ ERROR: No existe escena_{num:02d}.png ni .mp4")
        return None

    # 2. SUBTÍTULOS (si existen)
    if ass.exists():
        fv += f",ass={ass}"
    fv += "[v]"

    # 3. AUDIO (Voz + Música con ducking correcto)
    cmd = ["ffmpeg", "-y"] + input_visual + ["-i", str(voz)]
    if mus.exists():
        cmd += ["-i", str(mus)]
        # Ducking: la música baja cuando habla la voz
        fa = f"[1:a]atrim={ini}:{fin},asetpts=PTS-STARTPTS[voz];[2:a]atrim=0:{dur},afade=t=in:st=0:d=1,afade=t=out:st={max(0,dur-2)}:d=2,volume=0.15[mus];[voz][mus]amix=inputs=2:duration=longest:normalize=0[a]"
    else:
        fa = f"[1:a]atrim={ini}:{fin},asetpts=PTS-STARTPTS[a]"

    out = TMP / f"escena_{num:02d}.mp4"
    cmd += ["-filter_complex", f"{fv};{fa}", "-map", "[v]", "-map", "[a]",
            "-t", str(dur), "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", str(out)]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode == 0 and out.exists(): return out
    print(f"  ❌ Escena {num} falló: {r.stderr[-300:]}")
    return None

def _generar_intro_outro(fecha):
    """Genera intro y outro SIN zoompan (estático con fade)."""
    logo = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
    intro = TMP / "intro.mp4"
    outro = TMP / "outro.mp4"
    
    if logo.exists():
        # Intro: Logo centrado, 3 segundos, fade in/out
        vf_intro = "scale=800:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5"
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf_intro, "-t", "3", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(intro)], capture_output=True)
        
        # Outro: Logo + Texto CTA, 4 segundos
        vf_outro = "scale=600:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2+50:black,drawtext=text='SOMOS EL ENCUADRE':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h-150,fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5"
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf_outro, "-t", "4", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(outro)], capture_output=True)
    
    return intro if intro.exists() else None, outro if outro.exists() else None

def renderizar(fecha):
    tf = OUT / f"timeline_{fecha}.json"
    if not tf.exists():
        print("❌ No hay timeline"); return
    timeline = json.loads(tf.read_text())
    print(f"Renderizando {len(timeline)} escenas (SIN zoompan, estable)...")
    
    segs = []
    for it in timeline:
        print(f"  [{it['id']}] {it.get('tipo_visual','?')}")
        s = _render_escena(it, fecha)
        if s: segs.append(s)
    
    if not segs:
        print("❌ Sin segmentos generados"); return
    
    # Intro y Outro
    print("  🎬 Generando intro y outro...")
    intro, outro = _generar_intro_outro(fecha)
    
    # Concatenar: intro + escenas + outro
    lista_final = TMP / "concat_final.txt"
    with open(lista_final, "w") as f:
        if intro: f.write(f"file '{intro}'\n")
        for s in segs: f.write(f"file '{s}'\n")
        if outro: f.write(f"file '{outro}'\n")
    
    final = OUT / f"video_largo_{fecha}.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_final), "-c", "copy", str(final)], capture_output=True)
    
    if final.exists():
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(final)], capture_output=True, text=True)
        d = float(r.stdout.strip()) if r.stdout.strip() else 0
        print(f"✅ VÍDEO FINAL: {final.name} ({d/60:.1f} min, {final.stat().st_size//1024//1024}MB)")

if __name__ == "__main__":
    renderizar(sys.argv[1] if len(sys.argv) > 1 else None)
