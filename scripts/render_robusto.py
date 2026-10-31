"""render_robusto.py v4 - Ken Burns + duración exacta del audio + auto-recovery."""
import subprocess, pathlib, sys, time, json

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
WORK = OUT / "render_work"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"
FECHA = sys.argv[1] if len(sys.argv) > 1 else "2026-10-31"
FFMPEG = "ffmpeg"

def _dur(p):
    if not p.exists(): return 0.0
    try:
        return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
            "-of","default=noprint_wrappers=1:nokey=1",str(p)], capture_output=True, text=True, timeout=10).stdout.strip() or "0")
    except: return 0.0

def _run(cmd, timeout=300, desc=""):
    print(f"  [{desc}]...", flush=True)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0:
            print(f"  [{desc}] OK {time.time()-t0:.1f}s", flush=True)
            return True
        print(f"  [{desc}] FAIL: {r.stderr[-200:]}", flush=True)
        return False
    except subprocess.TimeoutExpired:
        print(f"  [{desc}] TIMEOUT", flush=True)
        return False

def _kenburns(tipo, dur):
    fps, frames = 25, max(int(dur * 25), 10)
    if tipo == "hook": return f"zoompan=z='min(zoom+0.002,1.15)':d={frames}:s=1920x1080:fps=25"
    if tipo == "dato": return f"zoompan=z='min(zoom+0.003,1.20)':d={frames}:s=1920x1080:fps=25"
    if tipo in ("explicacion","contraste","cierre"): return f"zoompan=z='if(lte(zoom,1.0),1.12,max(1.001,zoom-0.0012))':d={frames}:s=1920x1080:fps=25"
    return f"zoompan=z='min(zoom+0.0015,1.12)':d={frames}:s=1920x1080:fps=25"

def main():
    WORK.mkdir(parents=True, exist_ok=True)
    CLIPS = WORK / "clips"
    CLIPS.mkdir(parents=True, exist_ok=True)

    tl_file = OUT / f"timeline_{FECHA}.json"
    voz_file = OUT / f"voz_largo_{FECHA}.mp3"
    if not tl_file.exists() or not voz_file.exists():
        print("❌ Faltan timeline o voz."); sys.exit(1)
    
    tl = json.loads(tl_file.read_text())
    dur_voz = _dur(voz_file)
    print(f"[render] {len(tl)} escenas | Duración voz: {dur_voz:.1f}s", flush=True)

    # 1. CLIPS
    video_base = WORK / "video_base.mp4"
    if not video_base.exists() or _dur(video_base) < 60:
        print("[1] Generando clips...", flush=True)
        for i, it in enumerate(tl):
            n = it["id"]; dur = round(it["fin"] - it["inicio"], 2)
            tipo = it.get("tipo_escena", "default")
            img = MEDIA / f"seg_{n:03d}.png"
            if not img.exists(): img = MEDIA / f"escena_{n:02d}.png"
            clip = CLIPS / f"clip_{n:03d}.mp4"
            if clip.exists() and _dur(clip) > 0.5: continue
            if not img.exists(): print(f"❌ Falta imagen {n}"); sys.exit(1)
            
            kb = _kenburns(tipo, dur)
            cmd = [FFMPEG,"-y","-hide_banner","-loglevel","error","-loop","1","-i",str(img),"-t",str(dur),
                "-vf",f"scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,{kb},scale=1920:1080,format=yuv420p",
                "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-tune","stillimage",str(clip)]
            if not _run(cmd, 240, f"clip {n:03d} {tipo}"):
                print(f"❌ Falló clip {n}"); sys.exit(1)

        # Intro/outro
        intro, outro = OUT / "intro.mp4", OUT / "outro.mp4"
        for p, d in [(intro, 3), (outro, 3)]:
            if not p.exists():
                _run([FFMPEG,"-y","-hide_banner","-loglevel","error",
                    "-f","lavfi","-i",f"color=c=0x0a0a0f:s=1920x1080:d={d}:r=25",
                    "-i", str(ROOT/"assets"/"branding"/"logo_encuadre.jpg"),
                    "-filter_complex","[1:v]scale=800:-1[logo];[0:v][logo]overlay=(W-w)/2:(H-h)/2",
                    "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",str(p)], 60, f"gen {p.name}")
        
        for p, dst in [(intro, CLIPS/"000_intro.mp4"), (outro, CLIPS/"999_outro.mp4")]:
            if not dst.exists():
                _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-i",str(p),
                    "-vf","scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,fps=25",
                    "-an","-c:v","libx264","-preset","ultrafast","-crf","24","-pix_fmt","yuv420p",str(dst)], 120, f"norm {p.name}")

        lista = WORK / "concat.txt"
        with open(lista, "w") as f:
            f.write(f"file '{CLIPS/'000_intro.mp4'}'\n")
            for it in tl:
                _n = it["id"]
                f.write(f"file '{CLIPS}/clip_{_n:03d}.mp4'\n")
            f.write(f"file '{CLIPS/'999_outro.mp4'}'\n")
        
        if not _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(lista),"-c","copy",str(video_base)], 180, "concat"):
            sys.exit(1)

    # 2. AUDIO
    audio = WORK / "audio.m4a"
    dur_total = max(_dur(video_base), dur_voz + 2.0)
    print(f"[2] Audio | dur_total: {dur_total:.1f}s", flush=True)
    
    if not audio.exists() or _dur(audio) < dur_total - 10:
        lofi = MUSICA / "lofi_base.mp3"
        if not lofi.exists():
            lofi = MUSICA / "_silencio.mp3"
            _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t","900","-c:a","libmp3lame",str(lofi)], 60, "silencio")
        
        # Mezclar voz y musica con ducking
        cmd = [FFMPEG,"-y","-hide_banner","-loglevel","error",
            "-itsoffset","2","-i",str(voz_file), "-i",str(lofi),
            "-filter_complex",f"[0:a]volume=1.0[voz];[1:a]atrim=0:{dur_total:.1f},afade=t=in:st=0:d=3,afade=t=out:st={dur_total-3:.1f}:d=3,volume=0.10[mus];[voz][mus]amix=inputs=2:duration=first:normalize=0[a]",
            "-map","[a]","-c:a","aac","-b:a","192k","-t",str(dur_total),str(audio)]
        if not _run(cmd, 300, "amix"):
            print("⚠️ Mezcla falló, usando solo voz...", flush=True)
            _run([FFMPEG,"-y","-hide_banner","-loglevel","error","-itsoffset","2","-i",str(voz_file),"-c:a","aac","-b:a","192k","-t",str(dur_total),str(audio)], 120, "voz_sola")

    # 3. MUX FINAL
    final = OUT / f"video_largo_{FECHA}.mp4"
    print(f"[3] Mux final → {final.name}", flush=True)
    cmd = [FFMPEG,"-y","-hide_banner","-loglevel","error",
        "-i",str(video_base),"-i",str(audio),
        "-map","0:v","-map","1:a","-c","copy",
        "-t",f"{dur_total:.1f}","-movflags","+faststart","-avoid_negative_ts","make_zero",str(final)]
    if not _run(cmd, 180, "mux"): sys.exit(1)

    dur_real = _dur(final)
    print(f"\n✅ VÍDEO OK: {final.name} ({dur_real/60:.1f}min, {final.stat().st_size//1024//1024}MB)", flush=True)

if __name__ == "__main__":
    main()
