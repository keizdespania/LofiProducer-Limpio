"""short_engine_encuadre.py - Genera 4 shorts cinematográficos 9:16"""
import json, re, subprocess, pathlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _voz(texto, salida):
    from voice_studio import generar_audio
    r = generar_audio(texto, voz="es_ES-davefx-medium", preset="noticias", formato="mp3", nombre="short_" + salida.stem)
    if r.get("status") == "ok":
        mp3 = ROOT / "media" / "audios" / (r["audio_id"] + ".mp3")
        if mp3.exists():
            import shutil
            shutil.copy2(mp3, salida)
            return salida
    return None

def _generar_srt(texto, salida):
    palabras = texto.split()
    lineas = []
    tiempo = 0
    idx = 1
    while palabras:
        bloque = palabras[:8]
        palabras = palabras[8:]
        start = f"00:00:{tiempo:02d},000"
        fin = f"00:00:{min(tiempo+3, 60):02d},000"
        lineas.append(f"{idx}\n{start} --> {fin}\n{' '.join(bloque)}\n")
        idx += 1
        tiempo += 3
    salida.write_text("\n".join(lineas))
    return salida

def generar_shorts(fecha=None):
    fecha = fecha or pathlib.Path.today().isoformat()
    ret_file = OUT / f"guiones_{fecha}.json"
    if not ret_file.exists():
        print("[short] No hay JSON de retención"); return []
    
    ret = json.loads(ret_file.read_text())
    shorts_guiones = ret.get("shorts", [])
    if not shorts_guiones:
        print("[short] No hay shorts en el JSON"); return []

    html_file = OUT / f"post_largo_{fecha}.html"
    if not html_file.exists():
        print("[short] No hay post largo"); return []
    
    html = html_file.read_text()
    imgs = re.findall(r'<img src="(/media/imagenes/[^"]+)"', html)
    if not imgs: return []
    
    # Rotamos las imágenes si hay varias
    img_paths = [ROOT / i.lstrip("/") for i in imgs]

    generados = []
    for i, short in enumerate(shorts_guiones):
        idx = i + 1
        texto = short.get("guion", "")
        tipo = short.get("tipo", "Short")
        
        print(f"[short {idx}/4] Generando {tipo}...", flush=True)
        voz_path = OUT / f"short_{idx}_voz_{fecha}.mp3"
        v = _voz(texto, voz_path)
        if not v: continue

        srt_path = OUT / f"short_{idx}_sub_{fecha}.srt"
        _generar_srt(texto, srt_path)

        img = img_paths[i % len(img_paths)]
        out = OUT / f"short_{idx}_{fecha}.mp4"

        filtro = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.003,1.5)':d=1:s=1080x1920,subtitles=" + str(srt_path) + ":force_style='Fontsize=40,PrimaryColour=&H00FFFFFF,BorderStyle=3,Outline=1,Shadow=1,MarginV=150'"
        cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-i", str(v), "-filter_complex", f"[0:v]{filtro}[v]", "-map", "[v]", "-map", "1:a", "-t", "60", "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-c:a", "aac", str(out)]

        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and out.exists():
            print(f"  ✅ Guardado: {out.name}")
            generados.append(str(out))
        else:
            print(f"  ❌ Error FFmpeg: {r.stderr[-200:]}")

    return generados

if __name__ == "__main__":
    import sys
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    res = generar_shorts(fecha)
    print(json.dumps(res, indent=2))
