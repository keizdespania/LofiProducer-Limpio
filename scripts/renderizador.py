"""renderizador.py - Monta el vídeo largo y los shorts con ASS Karaoke e imágenes."""
import sys, json, pathlib, subprocess, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"
MUSICA = ROOT / "output" / "musica_temp"

def _buscar(patron):
    r = list(patron.parent.glob(patron.name))
    return r[0] if r else None

def renderizar_video_largo(fecha):
    imagenes = list(MEDIA.glob("adolfo_*.png"))
    if not imagenes: imagenes = list(MEDIA.glob("*.jpg")) + list(MEDIA.glob("*.png"))
    if not imagenes: imagenes = [MEDIA / "fondo_encuadre.jpg"]
    voz = OUT / f"voz_largo_{fecha}.mp3"
    srt = OUT / f"voz_largo_{fecha}.ass"
    musica = _buscar(MUSICA / "*.mp3")
    if not all([voz.exists(), musica, srt.exists()]):
        print("[render] Faltan assets"); return None
    
    # Crear slideshow de imágenes
    lista_imgs = OUT / f"slideshow_{fecha}.txt"
    with open(lista_imgs, "w") as f:
        for img in imagenes:
            f.write(f"file '{img}'\nduration 5\n")
        f.write(f"file '{imagenes[-1]}'\n")
    
    salida = OUT / f"video_largo_{fecha}.mp4"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_imgs), "-i", str(voz), "-i", str(musica),
           "-filter_complex",
           "[0:v]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,ass=" + str(srt) + "[v];"
           "[2:a]volume=0.2[mus];[1:a]asplit=2[voz_sc][voz_main];[voz_main][mus]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[duck];[voz_sc][duck]amix=inputs=2:duration=first:normalize=0[a]",
           "-map", "[v]", "-map", "[a]", "-shortest", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
           "-c:a", "aac", "-b:a", "192k", str(salida)]
    print("[render] Vídeo largo...")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if r.returncode == 0:
        print(f"[render] ✅ {salida.name}")
        return str(salida)
    print(f"[render] ❌ {r.stderr[-300:]}")
    return None

def renderizar_shorts(fecha):
    datos = json.loads((OUT / f"produccion_{fecha}.json").read_text())
    shorts = datos.get("shorts_finales", [])[:1]
    imagenes = list(MEDIA.glob("adolfo_*.png"))
    if not imagenes: imagenes = list(MEDIA.glob("*.jpg")) + list(MEDIA.glob("*.png"))
    if not imagenes: imagenes = [MEDIA / "fondo_encuadre.jpg"]
    musica = _buscar(MUSICA / "*.mp3")
    srt_base = OUT / f"voz_largo_{fecha}.ass"
    
    resultados = []
    for i, short in enumerate(shorts):
        imagen = imagenes[i % len(imagenes)]
        voz = OUT / f"short_{i+1}_voz_{fecha}.mp3"
        srt = OUT / f"short_{i+1}_{fecha}.ass"
        if not srt.exists(): srt = srt_base
        if not all([imagen.exists(), voz.exists(), musica, srt.exists()]):
            print(f"[render] Short {i+1}: faltan assets"); continue
        
        salida = OUT / f"short_{i+1}_{fecha}.mp4"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(imagen), "-i", str(voz), "-i", str(musica),
               "-filter_complex",
               "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass=" + str(srt) + "[v];"
               "[2:a]volume=0.2[mus];[1:a]asplit=2[voz_sc][voz_main];[voz_main][mus]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=500[duck];[voz_sc][duck]amix=inputs=2:duration=first:normalize=0[a]",
               "-map", "[v]", "-map", "[a]", "-shortest", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
               "-c:a", "aac", str(salida)]
        print(f"[render] Short {i+1}...")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            print(f"[render] ✅ {salida.name}"); resultados.append(str(salida))
        else:
            print(f"[render] ❌ {r.stderr[-200:]}")
    return resultados

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    print("=== RENDER VÍDEO LARGO ===")
    vl = renderizar_video_largo(fecha)
    print("\n=== RENDER SHORTS ===")
    shorts = renderizar_shorts(fecha)
    print(f"\n✅ Render: {1 if vl else 0} vídeo + {len(shorts)} shorts")
