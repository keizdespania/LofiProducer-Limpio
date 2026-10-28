"""voz_edge.py - Genera voz con Edge-TTS (Álvaro) y ASS Karaoke con timestamps reales."""
import asyncio, json, pathlib, sys
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def generar_ass(palabras, salida_ass):
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

async def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    if not fecha:
        prod_files = sorted(list(OUT.glob("produccion_*.json")))
        if not prod_files:
            print("❌ No hay JSON de producción"); return
        prod = prod_files[-1]
        fecha = prod.stem.replace("produccion_", "") # Saca la fecha del nombre
    else:
        prod = OUT / f"produccion_{fecha}.json"
    if not prod.exists():
        print("❌ No hay JSON de producción"); return
    datos = json.loads(prod.read_text())
    texto = datos.get("texto_voz_largo", "")
    if not texto:
        print("❌ No hay texto_voz_largo"); return

    mp3 = OUT / f"voz_largo_{fecha}.mp3"
    ass = OUT / f"voz_largo_{fecha}.ass"
    print(f"🎙️ Generando voz de Álvaro para {fecha}...")
    
    communicate = edge_tts.Communicate(texto, "es-ES-AlvaroNeural", rate="-5%")
    palabras = []
    with open(mp3, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio": f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                palabras.append({"palabra": chunk["text"], "inicio": chunk["offset"]/10_000_000, "duracion": chunk["duration"]/10_000_000})
    
    print(f"✅ Audio: {mp3.name} ({len(palabras)} palabras)")
    generar_ass(palabras, ass)
    print(f"✅ ASS: {ass.name}")
    
    datos["timestamps_voz"] = palabras
    prod.write_text(json.dumps(datos, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
