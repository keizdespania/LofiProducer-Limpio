"""Montador Top 1: Renderiza un short desde el JSON de beats + voz + musica CC + subtitulos.
Fallback inteligente: si el clip es 9:16 nativo, se usa directo. Si es 16:9, se le aplica blur.
"""
import json, subprocess, pathlib, sys, urllib.request, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "shorts"
OUT.mkdir(parents=True, exist_ok=True)
REPO = "keizdespania/LofiProducer-Limpio"

def descargar_clip(cat, idx):
    # Busca el video 9x16 de esa categoria
    url = f"https://raw.githubusercontent.com/{REPO}/main/output/videos/biblioteca/{cat}/{cat}_0{idx}_9x16.mp4"
    path = OUT / f"tmp_{cat}_{idx}.mp4"
    try:
        urllib.request.urlretrieve(url, path)
        if path.stat().st_size < 100000: raise Exception("Archivo corrupto")
        return path
    except Exception as e:
        print(f"  ⚠️ No se encontro {url}")
        return None

def obtener_dimensiones(video):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(video)], capture_output=True, text=True)
        w, h = r.stdout.strip().split("x")
        return int(w), int(h)
    except:
        return 0, 0

def procesar_clip(video, duracion, salida):
    w, h = obtener_dimensiones(video)
    if w == 0: return False
    
    # Si el clip ya es vertical (h > w), se escala directo sin blur
    if h > w:
        print(f"  ✅ 9:16 nativo ({w}x{h}), escalando...")
        cmd = ["ffmpeg", "-y", "-i", str(video), "-vf", "scale=1080:1920", "-t", str(duracion), "-an", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", str(salida)]
    else:
        # Si es horizontal (w > h), aplicamos blur de fondo
        print(f"  ⚠️ 16:9 ({w}x{h}), aplicando blur de fondo...")
        filtro = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=25[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
        cmd = ["ffmpeg", "-y", "-i", str(video), "-filter_complex", filtro, "-map", "[v]", "-t", str(duracion), "-an", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", str(salida)]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print(f"  ❌ Error procesando clip: {e}")
        return False

def montar(storyboard_path, voz_path, musica_path):
    sb = json.loads(pathlib.Path(storyboard_path).read_text())
    print(f"1. Descargando y procesando {len(sb['beats'])} clips...")
    
    clips_procesados = []
    for i, beat in enumerate(sb["beats"]):
        cat = beat["categoria"]
        dur = beat["duracion"]
        print(f"  [{i+1}/{len(sb['beats'])}] {cat} ({dur}s)")
        
        clip_raw = descargar_clip(cat, (i % 6) + 1)
        if not clip_raw: continue
        
        clip_final = OUT / f"proc_{i}_{cat}.mp4"
        if procesar_clip(clip_raw, dur, clip_final):
            clips_procesados.append(clip_final)
    
    if not clips_procesados: return print("ERROR: Sin clips procesados")
    
    print("2. Concatenando clips...")
    lista = OUT / "lista.txt"
    with open(lista, "w") as f:
        for c in clips_procesados:
            f.write(f"file '{c}'\n")
    
    base_video = OUT / "base_concat.mp4"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(base_video)], check=True)
    
    print("3. Ensamblando final (voz + musica)...")
    final = OUT / "short_final_test.mp4"
    filtro = "[0:v]copy[v];[1:a]loudnorm=I=-14:TP=-1.5[voz];[2:a]volume=0.15[mus];[voz][mus]amix=inputs=2:duration=first[aout]"
    
    cmd = ["ffmpeg", "-y", "-i", str(base_video), "-i", str(voz_path)]
    if musica_path: cmd += ["-i", str(musica_path)]
    else: cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    
    cmd += ["-filter_complex", filtro, "-map", "[v]", "-map", "[aout]", "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast", str(final)]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Montaje OK: {final}")
        subprocess.run(["cp", str(final), "/storage/emulated/0/DCIM/LTX_Biblio/"])
        print("✅ Copiado a Galeria")
    except Exception as e:
        print(f"❌ Fallo montaje: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 4: print("Uso: render_short_video.py <storyboard.json> <voz.mp3> [musica.mp3]")
    else: montar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else None)
