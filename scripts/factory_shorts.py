"""factory_shorts.py - Fábrica 4 shorts (dato/contradiccion/prediccion/tutorial)."""
import sys, json, subprocess, pathlib, urllib.request, re, random, math, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))
from especialistas import pedir_a_especialista
OUT = ROOT / "output" / "encuadre"; OUT.mkdir(parents=True, exist_ok=True)
MUSICA_TEMP = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
DRY_RUN = "--dry-run" in sys.argv
if not FECHA: print("ERROR: python3 factory_shorts.py YYYY-MM-DD [--dry-run]"); sys.exit(1)
ANGLES = {
    "dato": "Empieza con un dato demoledor. Explica por qué importa. Cierra con impacto.",
    "contradiccion": "Empieza con 'Nadie habla de esto pero...'. Presenta el giro. Termina con pregunta incómoda.",
    "prediccion": "Empieza con 'En 6 meses...'. Predicción audaz. Termina con urgencia.",
    "tutorial": "Empieza con 'Así puedes...'. 2-3 pasos prácticos. CTA de acción.",
}
OUTROS = [
    {"texto": " Nosotros somos el encuadre. Si quieres saber más, suscríbete y entra en nuestra web. Elencuadre punto pages punto dev.", "prompt": "cyberpunk hacker sitting at futuristic desk from behind, LARGE glowing monitor center, 6 news screens background, blue neon lighting, cinematic"},
    {"texto": " Esto es solo el principio. En El Encuadre analizamos lo que otros callan. Suscríbete y visita elencuadre punto pages punto dev.", "prompt": "hooded figure at glass desk, holographic displays, dark room, orange accent lighting, camera from above, cinematic"},
    {"texto": " Si te ha removido, imagina lo que viene mañana. Somos El Encuadre. Suscríbete y entra en elencuadre punto pages punto dev.", "prompt": "hacker from behind typing, server racks and screens, green code rain background, dark cinematic office"},
    {"texto": " El análisis completo te espera. Suscríbete al canal y entra en elencuadre punto pages punto dev. Somos El Encuadre.", "prompt": "silhouette at desk with multiple TV news monitors, red glow, mysterious atmosphere, cinematic framing"},
]
def run(cmd, label):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0: print(f"❌ {label}:\n{r.stderr[-300:]}", flush=True); raise RuntimeError(label)
def get_duration(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)], capture_output=True, text=True)
    return float(r.stdout.strip() or 0)
def descargar_clip(usados):
    cats = ["bunker_operativo","callejon_lluvia","detalle_glove","hacker_movil"]
    for _ in range(30):
        cat = random.choice(cats); idx = random.randint(1,6); name = f"{cat}_0{idx}_9x16.mp4"
        if name in usados: continue
        url = f"https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/output/videos/biblioteca/{cat}/{name}"
        path = OUT / f"tmp_{cat}_{idx}_{random.randint(100,999)}.mp4"
        try:
            urllib.request.urlretrieve(url, path)
            if path.stat().st_size > 100000: usados.add(name); return path
        except Exception: pass
    pass
    for _ in range(10):
        cat = random.choice(cats); idx = random.randint(1,6)
        url = f"https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/output/videos/biblioteca/{cat}/{cat}_0{idx}_9x16.mp4"
        path = OUT / f"tmp_{cat}_{idx}_{random.randint(1000,9999)}.mp4"
        try:
            urllib.request.urlretrieve(url, path)
            if path.stat().st_size > 100000: return path
        except Exception: pass
    return None
def generar_fondo_outro(prompt):
    url = "https://api.cloudflare.com/client/v4/accounts/{}/ai/run/@cf/bytedance/stable-diffusion-xl-lightning"
    acc, tok = "", ""
    if (ROOT/".env").exists():
        for line in (ROOT/".env").read_text().splitlines():
            if line.startswith("CLOUDFLARE_ACCOUNT_ID="): acc = line.split("=",1)[1].strip()
            if line.startswith("CLOUDFLARE_API_TOKEN="): tok = line.split("=",1)[1].strip()
    if not acc or not tok: return None
    body = json.dumps({"prompt":prompt,"negative_prompt":"text, watermark, letters, face, logo","num_steps":8,"guidance":7.5,"width":768,"height":1344}).encode()
    req = urllib.request.Request(url.format(acc), data=body, headers={"Authorization":f"Bearer {tok}","Content-Type":"application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60)
        img = OUT / f"outro_bg_{random.randint(100,999)}.jpg"
        with open(img,"wb") as f: f.write(r.read())
        return img
    except Exception as e: print(f"   ⚠️ SDXL: {e}", flush=True); return None
def t2s(t):
    h,m,sms = t.split(':'); s,ms = sms.split(','); return int(h)*3600+int(m)*60+int(s)+int(ms)/1000.0
def s2a(seg):
    h=int(seg//3600); m=int((seg%3600)//60); s=int(seg%60); ms=int((seg-int(seg))*100); return f"{h}:{m:02d}:{s:02d}.{ms:02d}"
def generar_guion(tipo, dossier):
    prompt = f"""Analiza este dossier:
{dossier[:1800]}

Instrucción narrativa: {ANGLES[tipo]}

REGLA CRÍTICA: entre 75 y 100 palabras. Ni una más. Solo texto plano."""
    
    # Fallback extremo por si Groq se rebela en los 3 intentos
    fallback = "Los medios ocultan la verdad sobre el fraude. Millones de euros blindados antes de dimitir. La fiscalía investiga. El gobierno calla. Pero las imágenes muestran la realidad. Entra en nuestra web y descubre cómo manipulan la información cada día."
    
    for intento in range(3):
        try:
            raw = pedir_a_especialista("guionista_short_factory", prompt)
            g = raw.strip().replace('"','').replace("'","")
            pal = g.split()
            
            # Si es muy corto (< 60), rechazar y reintentar
            if len(pal) < 60:
                print(f"   ⚠️ Guion muy corto ({len(pal)} palabras). Reintentando...", flush=True)
                continue
                
            # Si es muy largo (> 90), cortar
            if len(pal) > 90: 
                g = " ".join(pal[:90])
            return g
        except Exception as e:
            print(f"   ⚠️ Error LLM: {e}", flush=True)
            
    print("   🚨 LLM rebelde. Usando guion de respaldo.", flush=True)
    return fallback
def limpiar_temporales():
    for pat in ["factory_*","tmp_*","outro_bg_*.jpg"]:
        for f in OUT.glob(pat):
            if f.name.startswith("factory_done_"): continue
            try: f.unlink()
            except Exception: pass
def generar_un_short(tipo, guion, num, outro_cfg, clips_usados):
    print(f"\n--- Short {num}/4: {tipo.upper()} ---", flush=True)
    voz = OUT / f"factory_voz_{tipo}_{FECHA}.mp3"; srt = OUT / f"factory_voz_{tipo}_{FECHA}.srt"
    run([sys.executable, str(ROOT/"scripts/srt_desde_voz.py"), guion+outro_cfg["texto"], str(voz)], "voz")
    dur_total = get_duration(voz)
    voz_outro = OUT / f"factory_voz_outro_{tipo}_{FECHA}.mp3"
    run([sys.executable, str(ROOT/"scripts/srt_desde_voz.py"), outro_cfg["texto"], str(voz_outro)], "voz_outro")
    dur_outro = get_duration(voz_outro); dur_guion = dur_total - dur_outro
    if dur_guion <= 0: print(f"   ⚠️ Negativa", flush=True); return False
    print(f"   Guion {dur_guion:.1f}s | Outro {dur_outro:.1f}s | Total {dur_total:.1f}s", flush=True)
    n_clips = math.ceil(dur_guion / 6.0)
    clips = []
    for i in range(n_clips):
        clip = descargar_clip(clips_usados)
        if not clip: continue
        proc = OUT / f"factory_clip_{tipo}_{i}.mp4"
        w,h = 0,0
        try:
            r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=s=x:p=0",str(clip)], capture_output=True, text=True)
            w,h = map(int, r.stdout.strip().split("x"))
        except: pass
        if h > w: filtro = "[0:v]scale=1080:1920,zoompan=z='min(zoom+0.001,1.1)':d=1:s=1080x1920[vout]"
        else: filtro = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=25[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,zoompan=z='min(zoom+0.001,1.1)':d=1:s=1080x1920[vout]"
        run(["ffmpeg","-y","-i",str(clip),"-an","-filter_complex",filtro,"-map","[vout]","-c:v","libx264","-crf","20","-preset","ultrafast",str(proc)], f"clip_{i}")
        clips.append(proc)
    if not clips: print("   ⚠️ Sin clips", flush=True); return False
    lista = OUT / f"factory_lista_{tipo}.txt"; lista.write_text("\n".join([f"file '{c.absolute()}'" for c in clips]))
    base = OUT / f"factory_base_{tipo}.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lista),"-c","copy",str(base)], "concat")
    principal = OUT / f"factory_principal_{tipo}.mp4"
    run(["ffmpeg","-y","-i",str(base),"-t",str(dur_guion),"-c","copy",str(principal)], "trim")
    bg = generar_fondo_outro(outro_cfg["prompt"]); logo = str(ROOT/"web/media/logo_elencuadre.jpg")
    v_outro = OUT / f"factory_outro_{tipo}.mp4"
    if bg and bg.exists():
        fl = "[0:v]scale=1080:1920,eq=brightness=-0.1,zoompan=z='min(zoom+0.0005,1.05)':d=1:s=1080x1920[bg];[1:v]scale=350:-1,eq=brightness=0.1:saturation=1.2[logo];[bg][logo]overlay=(W-w)/2:(H-h)/2-80[vout]"
        run(["ffmpeg","-y","-loop","1","-i",str(bg),"-i",logo,"-filter_complex",fl,"-map","[vout]","-c:v","libx264","-crf","20","-preset","ultrafast","-t",str(dur_outro),str(v_outro)], "outro")
    else:
        fl = "[1:v]scale=600:-1[logo];[0:v][logo]overlay=(W-w)/2:(H-h)/2[vout]"
        run(["ffmpeg","-y","-f","lavfi","-i",f"color=c=black:s=1080x1920:d={dur_outro}","-i",logo,"-filter_complex",fl,"-map","[vout]","-c:v","libx264","-crf","20","-preset","ultrafast",str(v_outro)], "outro")
    lf = OUT / f"factory_lista_final_{tipo}.txt"; lf.write_text(f"file '{principal.absolute()}'\nfile '{v_outro.absolute()}'\n")
    full = OUT / f"factory_full_{tipo}.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lf),"-c","copy",str(full)], "unir")
    ass = OUT / f"factory_subs_{tipo}.ass"
    hdr = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Impact,75,&H000000FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,10,10,350,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    body = ""
    for b in re.findall(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n', srt.read_text(), re.DOTALL):
        txt = b[2].replace("\n"," ").strip().replace(" punto ", ".").replace(" punto",".")
        body += f"Dialogue: 0,{s2a(t2s(b[0]))},{s2a(t2s(b[1]))},Default,,0,0,0,,{txt}\n"
    ass.write_text(hdr+body, encoding="utf-8")
    vs = OUT / f"factory_subs_video_{tipo}.mp4"
    run(["ffmpeg","-y","-i",str(full),"-vf",f"ass={ass}","-c:v","libx264","-crf","20","-preset","ultrafast","-an",str(vs)], "quemar")
    mus = list(MUSICA_TEMP.glob(f"short_dia_{FECHA}*.mp3")) or list(MUSICA_TEMP.glob("short_dia_*.mp3"))
    musica = mus[-1] if mus else None
    final = OUT / f"short_{num}_{FECHA}.mp4"
    if musica:
        ff = "[1:a]loudnorm=I=-14:TP=-1.5[voz];[2:a]volume=0.15[mus];[voz][mus]amix=inputs=2:duration=first[a]"
        run(["ffmpeg","-y","-i",str(vs),"-i",str(voz),"-i",str(musica),"-filter_complex",ff,"-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-t","58.0",str(final)], "mix")
    else:
        run(["ffmpeg","-y","-i",str(vs),"-i",str(voz),"-map","0:v:0","-map","1:a","-c:v","copy","-c:a","aac","-t","58.0",str(final)], "mix")
    print(f"   ✅ {final.name} ({final.stat().st_size//1024//1024}MB)", flush=True)
    return True
def main():
    print(f"=== FÁBRICA {FECHA} dry_run={DRY_RUN} ===", flush=True)
    dp = ROOT/"output/encuadre"/f"dossier_{FECHA}_enriquecido.json"
    if not dp.exists():
        ds = sorted(list((ROOT/"output/encuadre").glob("dossier_*enriquecido.json")), reverse=True)
        if not ds: print("❌ No dossier"); return 1
        dp = ds[0]; print(f"   ⚠️ Usando {dp.name}", flush=True)
    dossier = dp.read_text()[:2500]
    try:
        r = subprocess.run([sys.executable, str(ROOT/"scripts/musica_short_del_dia.py")], capture_output=True, text=True, timeout=180)
        print(f"   Música: {r.stdout.strip().splitlines()[-1] if r.stdout else 'no'}", flush=True)
    except Exception as e: print(f"   ⚠️ Música: {e}", flush=True)
    tipos = ["dato","contradiccion","prediccion","tutorial"]
    usados = set(); meta = []; exitos = 0
    for idx, tipo in enumerate(tipos):
        print(f"\n[{idx+1}/4] {tipo.upper()}", flush=True)
        try:
            g = generar_guion(tipo, dossier)
            print(f"   Guion: {len(g.split())} palabras", flush=True)
            num = exitos + 1
            if generar_un_short(tipo, g, num, OUTROS[idx % len(OUTROS)], usados):
                exitos += 1
                meta.append({"tipo": tipo, "guion": g, "hook": g[:100], "archivo": f"short_{num}_{FECHA}.mp4"})
        except Exception as e: print(f"   ❌ {tipo}: {e}", flush=True)
    prod = OUT / f"produccion_{FECHA}.json"
    try:
        d = json.loads(prod.read_text()) if prod.exists() else {"fecha": FECHA}
        d["shorts_finales"] = meta
        d["factory_shorts"] = {"generados": exitos, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "dry_run": DRY_RUN}
        prod.write_text(json.dumps(d, indent=2, ensure_ascii=False))
        print(f"\n✅ produccion.json ({len(meta)} shorts)", flush=True)
    except Exception as e: print(f"❌ produccion.json: {e}", flush=True)
    try:
        r = subprocess.run([sys.executable, str(ROOT/"scripts/validar_video.py"), FECHA], capture_output=True, text=True, timeout=120)
        print(f"   Validación: {'OK' if r.returncode==0 else 'warnings'}", flush=True)
    except Exception as e: print(f"   ⚠️ Val: {e}", flush=True)
    limpiar_temporales()
    (OUT / f"factory_done_{FECHA}.txt").write_text(f"generated={exitos}/4\nts={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\ndry={DRY_RUN}\n")
    print(f"\n=== FIN: {exitos}/4 ===", flush=True)
    return 0 if exitos >= 1 else 1
if __name__ == "__main__":
    sys.exit(main())
