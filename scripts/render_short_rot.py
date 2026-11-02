"""render_short_rot.py v4 — Shorts con SRT propio + ffmpeg. Sin rot, sin torch.
Genera subtítulos exactos desde edge_tts (SentenceBoundary) y los quema con ffmpeg.
5 niveles de fallback para garantizar output.
"""
import sys, pathlib, subprocess, asyncio
from pathlib import Path

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _dur_audio(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
                           capture_output=True, text=True, timeout=10)
        return float(r.stdout.strip()) if r.stdout.strip() else 0
    except Exception:
        return 0

def _generar_srt(texto, srt_path):
    """Genera SRT desde edge_tts. Reutiliza el módulo srt_desde_voz."""
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from srt_desde_voz import generar_srt
        # El SRT necesita la voz. Si ya existe el MP3, solo regeneramos el SRT.
        # Pero edge_tts genera voz y SRT a la vez. Como la voz ya existe,
        # sintetizamos solo para el SRT (rápido, sin usar el audio).
        # Alternativa: extraer timestamps de un modo más ligero.
        # De momento: generar voz+S RT juntos en temp y usar el SRT.
        tmp_mp3 = srt_path.with_suffix(".tmp.mp3")
        n = asyncio.run(generar_srt(texto, str(tmp_mp3), str(srt_path)))
        try: tmp_mp3.unlink()
        except: pass
        return n > 0
    except Exception as e:
        print(f"    ⚠️ SRT falló: {e}", flush=True)
        return False

def _ffmpeg_render(img, voz_path, musica_path, salida, srt_path=None, con_musica=True):
    """Render con ffmpeg. Quema SRT si existe."""
    dur = _dur_audio(voz_path)
    if dur <= 0:
        raise ValueError("Audio sin duración")

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(img), "-i", str(voz_path)]

    if con_musica and musica_path and Path(musica_path).exists():
        cmd += ["-stream_loop", "-1", "-i", str(musica_path)]
        audio_filter = (
            f"[1:a]aresample=48000[voice];"
            f"[2:a]atrim=0:{dur+1},asetpts=PTS-STARTPTS,volume=0.15[music];"
            f"[voice][music]amix=inputs=2:duration=first:normalize=0[aout]"
        )
    else:
        audio_filter = "[1:a]aresample=48000[aout]"

    # Vídeo filter: escala + (opcional) subtítulos
    video_filter = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p"
    if srt_path and Path(srt_path).exists() and Path(srt_path).stat().st_size > 0:
        # Escapar path del SRT para ffmpeg (comillas simples, sin escapes)
        srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
        video_filter += f",subtitles='{srt_escaped}':force_style='FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=150'"
    video_filter += "[vout]"

    cmd += ["-filter_complex", f"{video_filter};{audio_filter}",
            "-map", "[vout]", "-map", "[aout]",
            "-t", str(dur + 0.3),
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-r", "30", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
            str(salida)]

    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if r.returncode != 0 or not Path(salida).exists():
        raise RuntimeError(f"ffmpeg fallo: {r.stderr[:300]}")
    return salida

def generar_short(img, texto, voz_path, musica_path, salida):
    """Render blindado: SRT + ffmpeg. Fallback sin SRT. Fallback sin música. Fallback estático."""
    # Generar SRT
    srt_path = Path(str(salida).replace(".mp4", ".srt"))
    _generar_srt(texto, srt_path)

    # N1: ffmpeg + SRT + música
    try:
        _ffmpeg_render(img, voz_path, musica_path, salida, srt_path, con_musica=True)
        print(f"    ✅ [N1] ffmpeg+SRT+música OK", flush=True)
        return salida
    except Exception as e:
        print(f"    ⚠️ [N1] {str(e)[:80]}", flush=True)

    # N2: ffmpeg + SRT sin música
    try:
        _ffmpeg_render(img, voz_path, musica_path, salida, srt_path, con_musica=False)
        print(f"    ✅ [N2] ffmpeg+SRT sin música OK", flush=True)
        return salida
    except Exception as e:
        print(f"    ⚠️ [N2] {str(e)[:80]}", flush=True)

    # N3: ffmpeg sin SRT con música
    try:
        _ffmpeg_render(img, voz_path, musica_path, salida, None, con_musica=True)
        print(f"    ✅ [N3] ffmpeg sin SRT con música OK", flush=True)
        return salida
    except Exception as e:
        print(f"    ⚠️ [N3] {str(e)[:80]}", flush=True)

    # N4: ffmpeg sin SRT sin música
    try:
        _ffmpeg_render(img, voz_path, musica_path, salida, None, con_musica=False)
        print(f"    ✅ [N4] ffmpeg sin SRT sin música OK", flush=True)
        return salida
    except Exception as e:
        print(f"    ⚠️ [N4] {str(e)[:80]}", flush=True)

    # N5: estático 5s
    try:
        cmd = ["ffmpeg", "-y", "-loglevel", "error",
               "-loop", "1", "-i", str(img), "-i", str(voz_path),
               "-t", "5", "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
               "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "96k", "-shortest", str(salida)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if Path(salida).exists():
            print(f"    ✅ [N5] estático OK", flush=True)
            return salida
    except Exception as e:
        print(f"    ⚠️ [N5] {str(e)[:80]}", flush=True)
    raise RuntimeError("Todos los niveles fallaron")

def generar_short_multi(imagenes, texto, voz_path, musica_path, salida, logo_path=None):
    """Multi-imagen: concat simple + SRT + música. Fallback a single."""
    imagenes = [p for p in imagenes if p and Path(p).exists()]
    if not imagenes:
        raise ValueError("Sin imágenes")
    if len(imagenes) == 1:
        return generar_short(imagenes[0], texto, voz_path, musica_path, salida)

    try:
        dur = _dur_audio(voz_path)
        dur_por = dur / len(imagenes)

        # Generar SRT
        srt_path = Path(str(salida).replace(".mp4", ".srt"))
        _generar_srt(texto, srt_path)

        # Construir concat de imágenes
        cmd = ["ffmpeg", "-y", "-loglevel", "error"]
        for img in imagenes:
            cmd += ["-loop", "1", "-t", str(dur_por), "-i", str(img)]
        cmd += ["-i", str(voz_path)]
        if musica_path and Path(musica_path).exists():
            cmd += ["-stream_loop", "-1", "-i", str(musica_path)]

        # Filtros
        n = len(imagenes)
        vfilt = ""
        for i in range(n):
            vfilt += f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30[v{i}];"
        vfilt += "".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0"
        if srt_path and Path(srt_path).exists() and Path(srt_path).stat().st_size > 0:
            srt_escaped = str(srt_path).replace("\\", "/").replace(":", "\\:")
            vfilt += f",subtitles='{srt_escaped}':force_style='FontName=DejaVu Sans,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=150'"
        vfilt += ",format=yuv420p[vout]"

        voice_idx = n
        if musica_path and Path(musica_path).exists():
            music_idx = n + 1
            afilt = f"[{voice_idx}:a]aresample=48000[voice];[{music_idx}:a]atrim=0:{dur+1},asetpts=PTS-STARTPTS,volume=0.15[music];[voice][music]amix=inputs=2:duration=first:normalize=0[aout]"
        else:
            afilt = f"[{voice_idx}:a]aresample=48000[aout]"

        cmd += ["-filter_complex", f"{vfilt};{afilt}",
                "-map", "[vout]", "-map", "[aout]", "-t", str(dur + 0.3),
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-r", "30", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(salida)]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and Path(salida).exists():
            print(f"    ✅ [MULTI] concat+SRT+música OK", flush=True)
            return salida
    except Exception as e:
        print(f"    ⚠️ [MULTI] falló: {str(e)[:80]}", flush=True)
    return generar_short(imagenes[0], texto, voz_path, musica_path, salida)
