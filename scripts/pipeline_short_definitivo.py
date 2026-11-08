import sys, json, subprocess, pathlib, urllib.request, re, random, math
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "shorts"
OUT.mkdir(parents=True, exist_ok=True)

ANGULOS = {
    "dato": "Empieza con un dato impactante. Explica por qué importa. Cierra con impacto.",
    "contradiccion": "Empieza con 'Nadie habla de esto pero...'. Presenta el giro. Termina con pregunta.",
    "prediccion": "Empieza con 'En 6 meses...'. Predicción audaz. Termina con urgencia.",
    "tutorial": "Empieza con 'Así puedes...'. 2-3 pasos prácticos. CTA de acción.",
}

def run(cmd, label):
    print(f"  [{label}]...", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"❌ Fallo en {label}:\n{r.stderr[-300:]}")
        raise RuntimeError(label)

def get_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)

def descargar_clip_seguro():
    cats = ["bunker_operativo", "callejon_lluvia", "detalle_glove", "hacker_movil"]
    cat = random.choice(cats)
    idx = random.randint(1, 6)
    url = f"https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/output/videos/biblioteca/{cat}/{cat}_0{idx}_9x16.mp4"
    path = OUT / f"tmp_{cat}_{idx}_{random.randint(100,999)}.mp4"
    try:
        urllib.request.urlretrieve(url, path)
        if path.stat().st_size > 100000: return path
    except Exception: pass
    return None

def generar_fondo_outro():
    url = "https://api.cloudflare.com/client/v4/accounts/{}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
    acc, tok = "", ""
    if (ROOT / ".env").exists():
        for line in (ROOT / ".env").read_text().splitlines():
            if line.startswith("CLOUDFLARE_ACCOUNT_ID="): acc = line.split("=")[1].strip()
            if line.startswith("CLOUDFLARE_API_TOKEN="): tok = line.split("=")[1].strip()
    if not acc or not tok: return None
    prompt = "cyberpunk hacker sitting at futuristic desk from behind, facing a LARGE blank glowing computer monitor in the center, 6 smaller news monitors in the background, dark office, neon blue lighting, cinematic"
    body = json.dumps({"prompt": prompt, "negative_prompt": "text, watermark, letters, face", "num_steps": 8, "guidance": 7.5, "width": 768, "height": 1344}).encode()
    req = urllib.request.Request(url.format(acc), data=body, headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        img_path = OUT / f"outro_bg_{random.randint(1,999)}.jpg"
        with open(img_path, "wb") as f: f.write(r.read())
        return img_path
    except: return None

def time_to_sec(t_str):
    h, m, s_ms = t_str.split(':')
    s, ms = s_ms.split(',')
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

def sec_to_ass(seg):
    h = int(seg // 3600); m = int((seg % 3600) // 60); s = int(seg % 60)
    ms = int((seg - int(seg)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{ms:02d}"

def generar_short(angulo):
    print(f"\n=== GENERANDO SHORT: {angulo.upper()} ===")
    dossiers = sorted(list((ROOT / "output/encuadre").glob("dossier_*enriquecido.json")), reverse=True)
    dossier = dossiers[0].read_text()[:2000]
    
    instruccion = ANGULOS.get(angulo, ANGULOS["dato"])
    prompt = f"Escribe un guion para un short de 30 segundos sobre este dossier: {dossier}. Instrucción: {instruccion}. Usa 70 palabras exactas. Tono mordaz. SOLO devuelve el texto, sin comillas."
    guion_texto = pedir_a_especialista("guionista_short_v3", prompt).strip().replace('"', '').replace("'", "")
    if len(guion_texto.split()) < 40:
        guion_texto = "Los medios ocultan la verdad sobre el fraude de Adif. Millones de euros blindados antes de dimitir. La fiscalía investiga. El gobierno calla. Pero las imágenes muestran la realidad. Entra en nuestra web y descubre cómo manipulan la información cada día."
    
    texto_outro = " Nosotros... somos el encuadre. Si quieres saber más, suscríbete y entra en nuestra web. Elencuadre punto pages punto dev."
    texto_completo = guion_texto + texto_outro
    
    voz_full = OUT / f"voz_{angulo}.mp3"
    srt_full = OUT / f"voz_{angulo}.srt"
    subprocess.run([sys.executable, str(ROOT/"scripts/srt_desde_voz.py"), texto_completo, str(voz_full)], capture_output=True)
    
    dur_total_audio = get_duration(voz_full)
    
    ass_file = OUT / f"subs_{angulo}.ass"
    ass_content = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Impact,75,&H000000FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,10,10,350,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    
    srt_content = srt_full.read_text(encoding="utf-8")
    bloques = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n', srt_content, re.DOTALL)
    frases = []
    for b in bloques:
        start_s = time_to_sec(b[0])
        end_s = time_to_sec(b[1])
        text = b[2].replace('\n', ' ').strip().replace(" punto ", ".").replace(" punto", ".")
        frases.append({"start": start_s, "end": end_s, "text": text})
        ass_content += f"Dialogue: 0,{sec_to_ass(start_s)},{sec_to_ass(end_s)},Default,,0,0,0,,{text}\n"
    ass_file.write_text(ass_content, encoding="utf-8")

    idx_outro = len(frases)
    for i, f in enumerate(frases):
        if "Nosotros" in f["text"] or "somos el encuadre" in f["text"].lower():
            idx_outro = i
            break
    dur_guion = frases[idx_outro]["start"] if idx_outro < len(frases) else frases[-1]["end"]
    dur_outro = dur_total_audio - dur_guion

    num_clips = math.ceil(dur_guion / 6.0)
    clips_proc = []
    for i in range(num_clips):
        clip = descargar_clip_seguro()
        if not clip: continue
        proc = OUT / f"proc_{angulo}_{i}.mp4"
        w, h = 0, 0
        try:
            r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(clip)], capture_output=True, text=True)
            w, h = map(int, r.stdout.strip().split("x"))
        except: pass
        if h > w: filtro = "[0:v]scale=1080:1920,zoompan=z='min(zoom+0.001,1.1)':d=1:s=1080x1920[vout]"
        else: filtro = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=25[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,zoompan=z='min(zoom+0.001,1.1)':d=1:s=1080x1920[vout]"
        cmd = ["ffmpeg", "-y", "-i", str(clip), "-an", "-filter_complex", filtro, "-map", "[vout]", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", str(proc)]
        run(cmd, f"clip_{i}")
        clips_proc.append(proc)

    lista_v = OUT / f"lista_{angulo}.txt"
    lista_v.write_text("\n".join([f"file '{c.absolute()}'" for c in clips_proc]))
    base_concat = OUT / f"base_{angulo}.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_v), "-c", "copy", str(base_concat)], "concat")
    
    video_principal = OUT / f"principal_{angulo}.mp4"
    run(["ffmpeg", "-y", "-i", str(base_concat), "-t", str(dur_guion), "-c", "copy", str(video_principal)], "recorte")

    bg_outro = generar_fondo_outro()
    logo = str(ROOT / "web/media/logo_elencuadre.jpg")
    video_outro = OUT / f"outro_{angulo}.mp4"
    
    if bg_outro and bg_outro.exists():
        filtro_logo = "[0:v]scale=1080:1920,eq=brightness=-0.1,zoompan=z='min(zoom+0.0005,1.05)':d=1:s=1080x1920[bg];[1:v]scale=350:-1,eq=brightness=0.1:saturation=1.2[logo];[bg][logo]overlay=(W-w)/2:(H-h)/2-80[vout]"
        cmd_outro = ["ffmpeg", "-y", "-loop", "1", "-i", str(bg_outro), "-i", logo, "-filter_complex", filtro_logo, "-map", "[vout]", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", "-t", str(dur_outro), str(video_outro)]
    else:
        filtro_logo = "[1:v]scale=600:-1[logo];[0:v][logo]overlay=(W-w)/2:(H-h)/2[vout]"
        cmd_outro = ["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={dur_outro}", "-i", logo, "-filter_complex", filtro_logo, "-map", "[vout]", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", str(video_outro)]
    run(cmd_outro, "outro")

    lista_v_final = OUT / f"lista_final_{angulo}.txt"
    lista_v_final.write_text(f"file '{video_principal.absolute()}'\nfile '{video_outro.absolute()}'\n")
    video_full = OUT / f"full_{angulo}.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_v_final), "-c", "copy", str(video_full)], "unir")

    video_subs = OUT / f"subs_video_{angulo}.mp4"
    run(["ffmpeg", "-y", "-i", str(video_full), "-vf", f"ass={ass_file}", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", "-an", str(video_subs)], "quemar")

    musica = list((ROOT / "output/musica_temp").glob("short_dia_*.mp3"))
    musica_path = musica[-1] if musica else None
    final = OUT / f"short_{angulo}_TOP1.mp4"
    
    if musica_path:
        filtro_final = "[1:a]loudnorm=I=-14:TP=-1.5[voz];[2:a]volume=0.15[mus];[voz][mus]amix=inputs=2:duration=first[a]"
        cmd_final = ["ffmpeg", "-y", "-i", str(video_subs), "-i", str(voz_full), "-i", str(musica_path), "-filter_complex", filtro_final, "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(dur_total_audio), str(final)]
    else:
        cmd_final = ["ffmpeg", "-y", "-i", str(video_subs), "-i", str(voz_full), "-map", "0:v:0", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-t", str(dur_total_audio), str(final)]
    run(cmd_final, "mix")
    
    print(f"✅ Completado: {final.name}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generar_short(sys.argv[1])
    else:
        print("Uso: python3 pipeline_short_definitivo.py <dato|contradiccion|prediccion|tutorial>")
