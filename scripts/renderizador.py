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
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if r.returncode == 0 and out.exists(): return out
    print(f"  X escena {num} fallo: {r.stderr[-200:]}")
    return None


def _generar_intro_outro(tipo="intro"):
    logo = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
    salida = TMP / f"{tipo}.mp4"
    
    if not logo.exists():
        # Si no hay logo, usar fondo negro
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1920x1080:d=3", "-c:v", "libx264", "-t", "3", str(salida)], capture_output=True)
        return salida

    if tipo == "intro":
        # Intro de 3 segundos: Logo con zoom y fondo negro
        vf = "scale=800:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='min(zoom+0.002,1.1)':d=75:s=1920x1080:fps=25,fade=t=in:st=0:d=0.5,fade=t=out:st=2.5:d=0.5"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf, "-t", "3", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(salida)]
    else:
        # Outro de 4 segundos: Logo + Texto CTA
        texto = "SOMOS EL ENCUADRE"
        vf = f"scale=600:-1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2+50:black,drawtext=text='{texto}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=h-150,fade=t=in:st=0:d=0.5,fade=t=out:st=3.5:d=0.5"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf, "-t", "4", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(salida)]
    
    subprocess.run(cmd, capture_output=True)
    return salida

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
    print("  🎬 Generando intro y outro...")
    intro = _generar_intro_outro("intro")
    outro = _generar_intro_outro("outro")
    
    # Ensamblar: intro + escenas + outro
    lista_final = TMP / "concat_final.txt"
    with open(lista_final, "w") as f:
        if intro and intro.exists(): f.write(f"file '{intro}'\n")
        for s in segs: f.write(f"file '{s}'\n")
        if outro and outro.exists(): f.write(f"file '{outro}'\n")
    
    final = OUT / f"video_largo_{fecha}.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_final), "-c", "copy", str(final)], capture_output=True)
    
    if final.exists():
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(final)], capture_output=True, text=True)
        d = float(r.stdout.strip()) if r.stdout.strip() else 0
        print(f"OK {final.name} ({d/60:.1f} min, {final.stat().st_size//1024//1024}MB)")


def _generar_intro_outro_short(tipo="intro"):
    logo = ROOT / "assets" / "branding" / "logo_encuadre.jpg"
    salida = TMP / f"short_{tipo}.mp4"
    
    if not logo.exists():
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=2", "-c:v", "libx264", "-t", "2", str(salida)], capture_output=True)
        return salida

    if tipo == "intro":
        # Intro de 1.5s: Logo centrado con zoom rápido
        vf = "scale=600:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,zoompan=z='min(zoom+0.005,1.2)':d=38:s=1080x1920:fps=25,fade=t=in:st=0:d=0.3,fade=t=out:st=1.2:d=0.3"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf, "-t", "1.5", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(salida)]
    else:
        # Outro de 2s: Logo + Texto CTA
        texto = "SOMOS EL ENCUADRE"
        vf = f"scale=500:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2-100:black,drawtext=text='{texto}':fontcolor=white:fontsize=50:x=(w-text_w)/2:y=h-300,fade=t=in:st=0:d=0.3,fade=t=out:st=1.7:d=0.3"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(logo), "-vf", vf, "-t", "2", "-c:v", "libx264", "-crf", "20", "-preset", "fast", str(salida)]
    
    subprocess.run(cmd, capture_output=True)
    return salida

def renderizar_shorts(fecha):
    print("\n🎬 Renderizando Shorts...")
    prod = OUT / f"produccion_{fecha}.json"
    if not prod.exists(): return
    datos = json.loads(prod.read_text())
    shorts = datos.get("shorts_finales", [])
    if not shorts:
        print("  ⚠️ No hay shorts para renderizar")
        return

    # Generar intro/outro de shorts
    intro = _generar_intro_outro_short("intro")
    outro = _generar_intro_outro_short("outro")

    for i, short in enumerate(shorts[:4]):
        num = i + 1
        voz = OUT / f"short_{num}_voz_{fecha}.mp3"
        img = MEDIA / f"escena_01.png"  # Usar la primera imagen como fondo
        if not img.exists():
            imgs = list(MEDIA.glob("*.png"))
            if imgs: img = imgs[0]
        
        if not voz.exists() or not img.exists():
            print(f"  ⚠️ Short {num}: faltan assets")
            continue

        print(f"  [{num}/{len(shorts)}] Renderizando short...")
        body = TMP / f"short_{num}_body.mp4"
        
        # Renderizar cuerpo del short (fondo con zoom + voz)
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.002,1.2)':d=250:s=1080x1920:fps=25"
        cmd_body = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(voz),
                    "-filter_complex", f"[0:v]{vf}[v];[1:a]anull[a]",
                    "-map", "[v]", "-map", "[a]", "-shortest",
                    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", str(body)]
        subprocess.run(cmd_body, capture_output=True, timeout=180)

        # Concatenar: intro + body + outro
        lista = TMP / f"short_{num}_concat.txt"
        with open(lista, "w") as f:
            if intro.exists(): f.write(f"file '{intro}'\n")
            if body.exists(): f.write(f"file '{body}'\n")
            if outro.exists(): f.write(f"file '{outro}'\n")
        
        final = OUT / f"short_{num}_{fecha}.mp4"
        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(final)], capture_output=True)

        if final.exists():
            print(f"     ✅ {final.name}")
        else:
            print(f"     ❌ Error al montar short {num}")

if __name__ == "__main__":
    renderizar(sys.argv[1] if len(sys.argv) > 1 else None)
