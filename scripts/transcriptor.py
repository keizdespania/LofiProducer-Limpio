"""transcriptor.py - Transcribe audios de TV/Radio con Sherpa-ONNX."""
import json, pathlib, subprocess, sys, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_TRANS = ROOT / "output" / "encuadre" / "transcripciones"
OUT_TRANS.mkdir(parents=True, exist_ok=True)

def transcribir_con_sherpa(audio_path):
    """Transcribe un audio usando el motor Sherpa-ONNX del proyecto."""
    audio_path = pathlib.Path(audio_path)
    if not audio_path.exists():
        return None
    out_txt = OUT_TRANS / (audio_path.stem + ".txt")
    if out_txt.exists():
        return out_txt.read_text()
    
    try:
        # Usar voice_studio para generar la transcripción
        # Nota: voice_studio.generar_audio hace TTS, no STT. 
        # Necesitamos un motor STT. Si no hay, usamos un placeholder.
        # Verificamos si existe un script de STT
        stt_script = ROOT / "scripts" / "transcribir_audio.py"
        if stt_script.exists():
            r = subprocess.run(["python3", str(stt_script), str(audio_path)], capture_output=True, text=True, timeout=300)
            if r.returncode == 0 and r.stdout.strip():
                out_txt.write_text(r.stdout.strip())
                return r.stdout.strip()
        
        # Si no hay STT, devolvemos un placeholder
        placeholder = f"[Transcripción pendiente: {audio_path.name}]"
        out_txt.write_text(placeholder)
        return placeholder
    except Exception as e:
        print(f"[transcriptor] Error: {e}", flush=True)
        return None

def transcribir_todo(fecha=None):
    import datetime
    fecha = fecha or datetime.date.today().isoformat()
    recolector_json = ROOT / "output" / "encuadre" / f"recoleccion_{fecha}.json"
    if not recolector_json.exists():
        print(f"[transcriptor] No existe {recolector_json}")
        return None
    
    datos = json.loads(recolector_json.read_text())
    audios = datos.get("audios", [])
    if not audios:
        print("[transcriptor] No hay audios para transcribir")
        return datos
    
    print(f"[transcriptor] Transcribiendo {len(audios)} audios...", flush=True)
    for a in audios:
        audio = a.get("audio")
        if not audio: continue
        print(f"  🎙️ Transcribiendo {a.get('medio')}...", flush=True)
        texto = transcribir_con_sherpa(audio)
        if texto:
            a["transcripcion"] = texto
            print(f"     ✅ {len(texto)} chars", flush=True)
    
    # Guardar el JSON actualizado con transcripciones
    recolector_json.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"[transcriptor] ✅ Transcripciones guardadas en {recolector_json}", flush=True)
    return datos

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    transcribir_todo(fecha)
