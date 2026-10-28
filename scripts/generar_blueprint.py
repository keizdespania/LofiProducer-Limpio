"""generar_blueprint.py - Genera el blueprint y el comando FFmpeg final (con fallback seguro)."""
import sys, json, pathlib, datetime, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MEDIA = ROOT / "web" / "media" / "imagenes"

def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    matches = re.findall(r'\{.*?\}', texto, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def generar_blueprint(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists(): return None
    
    datos = json.loads(prod_file.read_text())
    escenas = datos.get("guion_cinematografico", {}).get("guion", [])
    shorts = datos.get("shorts_finales", [])
    
    # Assets
    imagenes = [f.name for f in MEDIA.glob("*.jpg")] + [f.name for f in MEDIA.glob("*.png")]
    voz_largo = f"voz_largo_{fecha}.mp3"
    srt_largo = f"voz_largo_{fecha}.srt"
    pistas = [f.name for f in (ROOT / "output" / "musica_temp").glob("*.mp3") if not f.name.startswith("sfx_")]
    
    # Generar blueprint algorítmico (el fallback que ya funcionaba)
    bp = {
        "video_largo": {
            "duracion_total": sum(max(5, min(15, len(e.get("texto", "")) // 10)) for e in escenas),
            "escenas": [
                {
                    "tipo": "intro" if i == 0 else ("outro" if i == len(escenas)-1 else "contenido"),
                    "inicio": i * 10,
                    "fin": (i+1) * 10,
                    "imagen": imagenes[i % len(imagenes)] if imagenes else "placeholder.jpg",
                    "voz": voz_largo,
                    "musica": pistas[0] if pistas else "sin_musica.mp3",
                    "transicion": "fade" if i % 2 == 0 else "none",
                    "logo": i == 0 or i == len(escenas)-1
                } for i, e in enumerate(escenas)
            ]
        },
        "shorts": [
            {"id": f"short_{i+1}", "duracion": 30, "imagen": imagenes[i % len(imagenes)] if imagenes else "placeholder.jpg",
             "voz": f"short_{i+1}_voz_{fecha}.mp3", "musica": pistas[0] if pistas else "sin_musica.mp3"}
            for i, s in enumerate(shorts[:4])
        ]
    }
    
    datos["blueprint"] = bp
    
    # Comando FFmpeg SEGURO (plantilla fija, sin LLM)
    cmd_base = "ffmpeg -y -loop 1 -i {img} -i {voz} -i {musica} -filter_complex \"[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,subtitles={srt}[v];[2:a]volume=0.3[mus];[1:a][mus]amix=inputs=2:duration=first[a]\" -map \"[v]\" -map \"[a]\" -t 60 -c:v libx264 -crf 20 -preset fast -c:a aac -b:a 192k {salida}"
    
    datos["comando_ffmpeg"] = {
        "comando": cmd_base,
        "descripcion": "Comando base para renderizar el vídeo largo (plantilla segura).",
        "advertencias": ["Usar comando con rutas absolutas en el renderizador."]
    }
    print(f"[blueprint] ✅ Blueprint guardado con comando seguro.")
    
    prod_file.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    return bp

if __name__ == "__main__":
    generar_blueprint(sys.argv[1] if len(sys.argv) > 1 else None)
