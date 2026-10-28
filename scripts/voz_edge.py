"""voz_edge.py - Genera audio por escena y timeline con pausas de intriga."""
import asyncio, json, pathlib, sys, subprocess, re
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TMP = ROOT / "output" / "tmp_voz"
TMP.mkdir(parents=True, exist_ok=True)
VOZ = "es-ES-AlvaroNeural"

def _limpiar(texto):
    texto = re.sub(r'\[.*?\]', '', texto)
    texto = re.sub(r'\(.*?\)', '', texto)
    texto = re.sub(r'\{.*?\}', '', texto)
    for w in ["fade out", "fade in", "fin", "corte", "silencio"]:
        texto = re.sub(r'\b' + w + r'\b', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'[*_#\`>]', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

async def _gen_audio(texto, salida):
    c = edge_tts.Communicate(texto, VOZ, rate="-5%")
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(p)], capture_output=True, text=True)
    return float(r.stdout.strip()) if r.stdout.strip() else 0.0

def _silencio(d, out):
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", str(d), "-q:a", "9", str(out)], capture_output=True)

async def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    prod = OUT / f"produccion_{fecha}.json"
    datos = json.loads(prod.read_text())
    escenas = datos.get("escenas", [])
    if not escenas:
        print("No hay escenas"); return

    print(f"Voz para {len(escenas)} escenas...")
    sil2 = TMP / "sil2.mp3"
    _silencio(2.0, sil2)
    audios, timeline, offset = [], [], 0.0

    for e in escenas:
        num = e["id"]
        txt = _limpiar(e["texto"])
        if not txt: continue
        mp3 = TMP / f"e_{num:02d}.mp3"
        print(f"  [{num}/{len(escenas)}]")
        await _gen_audio(txt, mp3)
        d = _dur(mp3)
        timeline.append({"id": num, "inicio": offset, "fin": offset + d, "tipo_visual": e.get("tipo_visual", "imagen")})
        audios.append(mp3)
        offset += d
        if num < len(escenas):
            audios.append(sil2)
            offset += 2.0

    lista = TMP / "concat.txt"
    with open(lista, "w") as f:
        for a in audios: f.write(f"file '{a}'\n")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy", str(OUT / f"voz_largo_{fecha}.mp3")], capture_output=True)
    (OUT / f"timeline_{fecha}.json").write_text(json.dumps(timeline, indent=2))
    print(f"OK voz y timeline ({len(timeline)} escenas)")

if __name__ == "__main__":
    asyncio.run(main())
