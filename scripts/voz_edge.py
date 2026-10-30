"""voz_edge.py v3 - Alvaro humanizado: prosodia + rate dinamico + post-FX."""
import asyncio, json, pathlib, sys, subprocess, re
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TMP = ROOT / "output" / "tmp_voz"
TMP.mkdir(parents=True, exist_ok=True)
VOZ = "es-ES-AlvaroNeural"

RATE_MAP = {"tension":"-8%","misterio":"-8%","epico":"-5%","inspirador":"-5%","electronico":"-5%","relax":"-3%"}

def _humanizar_texto(texto):
    if not texto: return ""
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = re.sub(r'\(.*?\)', '', texto)
    texto = re.sub(r'\{.*?\}', '', texto)
    texto = re.sub(r'[*_#`>]', '', texto)
    for p in [r'El video (abre|empieza|cierra|termina) con[^.]*\.?\s*', r'(La c[áa]mara|El plano|La escena|El montaje)[^.]*\.?\s*', r'Corte a[^.]*\.?\s*', r'Fundido a[^.]*\.?\s*', r'(Vemos|Se ve|Se muestra|Se observa)[^.]*\.?\s*']:
        texto = re.sub(p, '', texto, flags=re.I|re.M)
    texto = texto.replace(', ', ', ')
        texto = texto.replace('...', '...\n')
        texto = re.sub(r'([.?!])\s+', r'\1\n', texto)
        texto = re.sub(r'([,;])\s+', r'\1', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    texto = re.sub(r'\b(tituló|dijo|afirmó)\s+', r'\1... ', texto)
    texto = re.sub(r'\b(pero|sin embargo|en cambio)\b', r'— \1', texto, flags=re.I)
    return texto.strip()

def _rate_para(escena):
    return RATE_MAP.get(escena.get("mood_musical","relax"), "-5%")

async def _gen_audio(texto, salida, rate="-5%"):
    c = edge_tts.Communicate(texto, VOZ, rate=rate)
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _postprocesar(entrada, salida):
    af = ("highpass=f=80,equalizer=f=180:t=q:w=1:g=2,equalizer=f=3000:t=q:w=1:g=-1.5,"
          "deesser=i=0.6,acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"
          "loudnorm=I=-16:TP=-1.5:LRA=11")
    subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(entrada),
                    "-af",af,"-c:a","libmp3lame","-b:a","192k",str(salida)],
                   capture_output=True, check=True)

def _dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)], capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

def _silencio(d, out):
    subprocess.run(["ffmpeg","-y","-f","lavfi","-i","anullsrc=r=44100:cl=mono","-t",str(d),"-q:a","9",str(out)], capture_output=True)

def _generar_ass(palabras, salida_ass):
    def seg(s):
        h=int(s//3600); m=int((s%3600)//60); se=int(s%60); cs=int((s-int(s))*100)
        return f"{h}:{m:02d}:{se:02d}.{cs:02d}"
    lineas=["[Script Info]","ScriptType: v4.00+","PlayResX: 1080","PlayResY: 1920","",
            "[V4+ Styles]","Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Karaoke,Arial,60,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3,1,2,50,50,150,1","",
            "[Events]","Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    for p in palabras:
        lineas.append(f"Dialogue: 0,{seg(p['inicio'])},{seg(p['inicio']+p['duracion'])},Karaoke,,0,0,0,,{{\\kf{int(p['duracion']*100)}}}{p['palabra']} ")
    salida_ass.write_text("\n".join(lineas))

async def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    prod = OUT / f"produccion_{fecha}.json" if fecha else None
    if not prod or not prod.exists():
        cs = sorted(OUT.glob("produccion_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if not cs: print("No hay produccion"); return
        prod = cs[0]; fecha = prod.stem.replace("produccion_", "")
    datos = json.loads(prod.read_text())
    escenas = datos.get("escenas", [])
    if not escenas: print("No escenas"); return

    print(f"Voz humanizada para {len(escenas)} escenas...")
    sil2 = TMP/"sil2.mp3"; _silencio(2.0, sil2)
    audios, timeline, offset, palabras_all = [], [], 0.0, []

    for e in escenas:
        num = e["id"]
        txt = _humanizar_texto(e.get("texto",""))
        if not txt: continue
        rate = _rate_para(e)
        raw = TMP/f"e_{num:02d}_raw.mp3"; hum = TMP/f"e_{num:02d}.mp3"
        print(f"  [{num}/{len(escenas)}] rate={rate}")
        await _gen_audio(txt, raw, rate=rate)
        _postprocesar(raw, hum)
        d = _dur(hum)
        timeline.append({"id":num,"inicio":offset,"fin":offset+d,"tipo_visual":e.get("tipo_visual","imagen")})
        audios.append(hum)
        palabras = txt.replace("\n"," ").split()
        if palabras:
            t_pal = d/len(palabras)
            palabras_all.extend([{"palabra":w,"inicio":offset+i*t_pal,"duracion":t_pal} for i,w in enumerate(palabras)])
        offset += d
        if num < len(escenas):
            audios.append(sil2); offset += 2.0

    lista = TMP/"concat.txt"
    with open(lista,"w") as f:
        for a in audios: f.write(f"file '{a}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(lista),"-c","copy",str(OUT/f"voz_largo_{fecha}.mp3")], capture_output=True)
    (OUT/f"timeline_{fecha}.json").write_text(json.dumps(timeline, indent=2))
    if palabras_all: _generar_ass(palabras_all, OUT/f"voz_largo_{fecha}.ass")
    print(f"OK voz humanizada ({len(timeline)} escenas)")

if __name__ == "__main__":
    asyncio.run(main())
