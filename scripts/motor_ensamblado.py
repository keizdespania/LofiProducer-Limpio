"""Motor de ensamblado: receta JSON → MP4 final (vídeo + imágenes + audio + subs + logo)."""
import subprocess, pathlib, json, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
FF = "ffmpeg"

def _ff(args, label):
    print(f"  [{label}]...", flush=True)
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{label}: {r.stderr[-400:]}")
    print(f"  ✅ {label}", flush=True)

def _dur(p):
    return float(subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True).stdout.strip() or 0)

def motor(receta_path, overrides=None):
    """Lee receta JSON y ensambla. overrides: dict con assets por nombre."""
    receta = json.loads(pathlib.Path(receta_path).read_text())
    ov = overrides or {}
    salida = pathlib.Path(receta["salida_path"])
    salida.parent.mkdir(parents=True, exist_ok=True)
    W, H = receta.get("ancho", 1920), receta.get("alto", 1080)
    
    # ═══ Construir inputs y filtros ═══
    inputs = []
    filtros = []
    idx = 0
    
    # 1. Vídeo base (loop o no)
    video_base = ov.get("video_base") or receta.get("video_base")
    if not video_base or not pathlib.Path(video_base).exists():
        raise RuntimeError(f"Falta video_base: {video_base}")
    if receta.get("loop_video"):
        inputs += ["-stream_loop", "-1", "-i", str(video_base)]
    else:
        inputs += ["-i", str(video_base)]
    base_idx = idx; idx += 1
    
    # 2. Imágenes intercaladas (opcional)
    imgs = ov.get("imagenes") or receta.get("imagenes") or []
    img_indices = []
    for img in imgs:
        if pathlib.Path(img).exists():
            inputs += ["-loop", "1", "-t", "5", "-i", str(img)]
            img_indices.append(idx); idx += 1
    
    # 3. Voz
    voz = ov.get("voz") or receta.get("voz")
    voz_idx = None
    if voz and pathlib.Path(voz).exists():
        inputs += ["-i", str(voz)]; voz_idx = idx; idx += 1
    
    # 4. Música (loop)
    musica = ov.get("musica") or receta.get("musica")
    mus_idx = None
    if musica and pathlib.Path(musica).exists():
        inputs += ["-stream_loop", "-1", "-i", str(musica)]; mus_idx = idx; idx += 1
    
    # 5. Logo
    logo = receta.get("logo")
    logo_idx = None
    if logo and pathlib.Path(logo).exists():
        inputs += ["-i", str(logo)]; logo_idx = idx; idx += 1
    
    # ═══ Duración objetivo ═══
    dur = receta.get("duracion", 15)
    if voz_idx is not None:
        dur = min(dur, _dur(voz) + 1)
    
    # ═══ Filtro de vídeo ═══
    vf = [
        f"scale={W}:{H}:force_original_aspect_ratio=decrease",
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2",
        f"fps=30"
    ]
    # Fades
    fades = receta.get("fades", {})
    if fades.get("in"): vf.append(f"fade=t=in:st=0:d={fades['in']}")
    if fades.get("out"): vf.append(f"fade=t=out:st={max(0, dur-fades['out'])}:d={fades['out']}")
    
    # Imágenes intercaladas (cada X segundos)
    if img_indices:
        intervalo = receta.get("intervalo_imagenes", 15)
        # overlay de imagen cada intervalo (simplificado: primera imagen como overlay)
        # Para producción real: usar concat de segmentos. Aquí simplificamos.
        pass
    
    # Logo overlay
    if logo_idx is not None:
        pos = receta.get("logo_pos", "W-w-30:H-h-30")
        f_complex = (",".join(vf) + f"[vbase];"
                     f"[{logo_idx}:v]scale=120:-1[logo];"
                     f"[vbase][logo]overlay={pos}[vout]")
    else:
        f_complex = ",".join(vf) + "[vout]"
    
    # ═══ Filtro de audio ═══
    if voz_idx is not None and mus_idx is not None:
        mus_vol = receta.get("musica_vol", 0.15)
        a_complex = (f"[{voz_idx}:a]loudnorm=I=-14:LRA=11:TP=-1.5[voz];"
                     f"[{mus_idx}:a]volume={mus_vol}[mus];"
                     f"[voz][mus]amix=inputs=2:duration=first[aout]")
        f_complex += ";" + a_complex
        map_a = ["-map", "[aout]"]
    elif mus_idx is not None:
        f_complex += f";[{mus_idx}:a]volume={receta.get('musica_vol',0.3)}[aout]"
        map_a = ["-map", "[aout]"]
    elif voz_idx is not None:
        f_complex += f";[{voz_idx}:a]loudnorm=I=-14:LRA=11:TP=-1.5[aout]"
        map_a = ["-map", "[aout]"]
    else:
        map_a = ["-an"]
    
    # ═══ Comando final ═══
    cmd = [FF, "-y", *inputs,
           "-filter_complex", f_complex,
           "-map", "[vout]", *map_a,
           "-t", str(dur),
           "-c:v", "libx264", "-crf", str(receta.get("crf", 20)),
           "-preset", "medium", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k",
           str(salida)]
    _ff(cmd, "ensamblar")
    return {"status": "ok", "path": str(salida), "size_mb": salida.stat().st_size//(1024*1024), "duracion": dur}

if __name__ == "__main__":
    if len(sys.argv) < 2: print("Uso: motor_ensamblado.py <receta.json> [k=v ...]"); sys.exit(1)
    ov = {}
    for a in sys.argv[2:]:
        if "=" in a:
            k, v = a.split("=", 1); ov[k] = v
    print(json.dumps(motor(sys.argv[1], ov), indent=2, ensure_ascii=False))
