"""voz_edge.py - Voz con Edge-TTS y timestamps calculados (sin APIs externas)."""
import asyncio, json, pathlib, sys, subprocess, re
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TMP = ROOT / "output" / "tmp_voz"
TMP.mkdir(parents=True, exist_ok=True)
VOZ = "es-ES-AlvaroNeural"

def _dividir_frases(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return [f for f in frases if len(f) > 20]

async def _generar_frase(texto, salida_mp3):
    communicate = edge_tts.Communicate(texto, VOZ, rate="-5%")
    with open(salida_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
    # Obtener duración real del MP3 generado
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(salida_mp3)], capture_output=True, text=True)
    dur = float(r.stdout.strip()) if r.stdout.strip() else 2.0
    # Calcular timestamps proporcionalmente
    palabras = texto.split()
    if not palabras: return [], dur
    t_por_palabra = dur / len(palabras)
    timestamps = [{"palabra": w, "inicio": i * t_por_palabra, "duracion": t_por_palabra} for i, w in enumerate(palabras)]
    return timestamps, dur

def _concatenar(lista_mp3, salida):
    lista_txt = TMP / "concat.txt"
    with open(lista_txt, "w") as f:
        for m in lista_mp3: f.write(f"file '{m}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_txt), "-c", "copy", str(salida)], capture_output=True)

def _generar_ass(palabras, salida_ass):
    def seg_a_ass(seg):
        h = int(seg // 3600); m = int((seg % 3600) // 60); s = int(seg % 60); cs = int((seg - int(seg)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    lineas = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
              "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              "Style: Karaoke,Arial,60,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,150,1", "",
              "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for p in palabras:
        start = seg_a_ass(p["inicio"]); end = seg_a_ass(p["inicio"] + p["duracion"])
        dur_cs = int(p["duracion"] * 100)
        lineas.append(f"Dialogue: 0,{start},{end},Karaoke,,0,0,0,,{{\\kf{dur_cs}}}{p['palabra']} ")
    salida_ass.write_text("\n".join(lineas))

async def _procesar(texto, prefijo):
    frases = _dividir_frases(texto)
    mp3s, todas_palabras, offset = [], [], 0.0
    for i, frase in enumerate(frases):
        mp3_frase = TMP / f"{prefijo}_{i:03d}.mp3"
        palabras, dur = await _generar_frase(frase, mp3_frase)
        mp3s.append(mp3_frase)
        for p in palabras:
            p["inicio"] += offset
            todas_palabras.append(p)
        offset += dur
    return mp3s, todas_palabras

async def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    prod = OUT / f"produccion_{fecha}.json"
    datos = json.loads(prod.read_text())

    texto = datos.get("texto_voz_largo", "")
    if texto:
        print(f"🎙️ Generando voz del vídeo largo...")
        mp3s, palabras = await _procesar(texto, "largo")
        _concatenar(mp3s, OUT / f"voz_largo_{fecha}.mp3")
        _generar_ass(palabras, OUT / f"voz_largo_{fecha}.ass")
        print(f"✅ Voz largo y ASS listos ({len(palabras)} palabras).")

    for i, short in enumerate(datos.get("shorts_finales", [])[:4]):
        texto_s = short.get("guion") or short.get("hook", "")
        if not texto_s: continue
        print(f"🎙️ Generando voz del short {i+1}...")
        mp3s, palabras = await _procesar(texto_s, f"short_{i+1}")
        _concatenar(mp3s, OUT / f"short_{i+1}_voz_{fecha}.mp3")
        _generar_ass(palabras, OUT / f"short_{i+1}_{fecha}.ass")
        print(f"✅ Voz short {i+1} lista.")

if __name__ == "__main__":
    asyncio.run(main())
