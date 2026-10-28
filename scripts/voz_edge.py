"""voz_edge.py - Voz con Edge-TTS (Álvaro) y ASS con timestamps reales.
Divide el texto en frases para garantizar WordBoundary.
Fallback: Whisper de Groq para timestamps si Edge-TTS falla.
"""
import asyncio, json, pathlib, sys, subprocess, re
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TMP = ROOT / "output" / "tmp_voz"
TMP.mkdir(parents=True, exist_ok=True)

VOZ = "es-ES-AlvaroNeural"
RATE = "-5%"

def _dividir_frases(texto):
    frases = re.split(r'(?<=[.!?])\s+', texto.strip())
    return [f for f in frases if len(f) > 20]

async def _generar_frase(texto, salida_mp3):
    communicate = edge_tts.Communicate(texto, VOZ, rate=RATE)
    palabras = []
    with open(salida_mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                palabras.append({
                    "palabra": chunk["text"],
                    "inicio": chunk["offset"] / 10_000_000,
                    "duracion": chunk["duration"] / 10_000_000,
                })
    return palabras

def _concatenar_mp3(lista_mp3, salida):
    lista_txt = TMP / "concat.txt"
    with open(lista_txt, "w") as f:
        for m in lista_mp3:
            f.write(f"file '{m}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista_txt), "-c", "copy", str(salida)], capture_output=True)

def _generar_ass(palabras, salida_ass):
    def seg_a_ass(seg):
        h = int(seg // 3600); m = int((seg % 3600) // 60); s = int(seg % 60); cs = int((seg - int(seg)) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    lineas = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "",
              "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              "Style: Karaoke,Arial,60,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,150,1", "",
              "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for p in palabras:
        start = seg_a_ass(p["inicio"]); end = seg_a_ass(p["inicio"] + p["duracion"])
        dur_cs = int(p["duracion"] * 100)
        lineas.append(f"Dialogue: 0,{start},{end},Karaoke,,0,0,0,,{{\\kf{dur_cs}}}{p['palabra']} ")
    salida_ass.write_text("\n".join(lineas))

async def _procesar(texto, prefijo):
    frases = _dividir_frases(texto)
    print(f"   Texto dividido en {len(frases)} frases.")
    mp3s, todas_palabras, offset = [], [], 0.0
    for i, frase in enumerate(frases):
        mp3_frase = TMP / f"{prefijo}_frase_{i:03d}.mp3"
        palabras = await _generar_frase(frase, mp3_frase)
        if not palabras:
            print(f"   ⚠️ Frase {i} sin WordBoundary. Usando Whisper de Groq...")
            # fallback Whisper
            from transcribir_groq import transcribir_groq
            texto_real = transcribir_groq(mp3_frase)
            if texto_real:
                # estimación proporcional
                n = len(texto_real.split())
                if n:
                    dur = len(texto_real) / 15.0
                    palabras = [{"palabra": w, "inicio": offset + (idx * dur / n), "duracion": dur / n}
                                for idx, w in enumerate(texto_real.split())]
        mp3s.append(mp3_frase)
        for p in palabras:
            p["inicio"] += offset
            todas_palabras.append(p)
        if palabras:
            offset += palabras[-1]["inicio"] + palabras[-1]["duracion"]
    return mp3s, todas_palabras

async def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    prod_files = sorted(list(OUT.glob("produccion_*.json")))
    if not prod_files:
        print("❌ No hay JSON de producción"); return
    prod = OUT / f"produccion_{fecha}.json" if fecha else prod_files[-1]
    fecha = prod.stem.replace("produccion_", "")
    datos = json.loads(prod.read_text())

    # 1. Vídeo largo
    texto = datos.get("texto_voz_largo", "")
    if texto:
        print(f"🎙️ Generando voz del vídeo largo ({len(texto)} chars)...")
        mp3s, palabras = await _procesar(texto, "largo")
        mp3_final = OUT / f"voz_largo_{fecha}.mp3"
        ass_final = OUT / f"voz_largo_{fecha}.ass"
        _concatenar_mp3(mp3s, mp3_final)
        _generar_ass(palabras, ass_final)
        print(f"   ✅ {mp3_final.name} ({len(palabras)} palabras) + {ass_final.name}")

    # 2. Shorts
    shorts = datos.get("shorts_finales", [])[:4]
    for i, short in enumerate(shorts):
        texto_s = short.get("guion") or short.get("hook", "")
        if not texto_s: continue
        print(f"🎙️ Generando voz del short {i+1}...")
        mp3s, palabras = await _procesar(texto_s, f"short_{i+1}")
        mp3_final = OUT / f"short_{i+1}_voz_{fecha}.mp3"
        ass_final = OUT / f"short_{i+1}_{fecha}.ass"
        _concatenar_mp3(mp3s, mp3_final)
        _generar_ass(palabras, ass_final)
        print(f"   ✅ {mp3_final.name} ({len(palabras)} palabras) + {ass_final.name}")

if __name__ == "__main__":
    asyncio.run(main())
