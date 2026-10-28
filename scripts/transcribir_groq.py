"""transcribir_groq.py - Transcribe audios usando Groq Whisper (gratis, rápido, sin instalar nada)."""
import sys, json, pathlib, urllib.request, urllib.parse, mimetypes, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_TRANS = ROOT / "output" / "encuadre" / "transcripciones"
OUT_TRANS.mkdir(parents=True, exist_ok=True)

def _leer_env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None

def transcribir_groq(audio_path):
    """Transcribe un audio usando Groq Whisper large-v3."""
    audio_path = Path(audio_path)
    if not audio_path.exists():
        return None
    out_txt = OUT_TRANS / (audio_path.stem + ".txt")
    if out_txt.exists() and out_txt.stat().st_size > 100:
        return out_txt.read_text()
    
    key = _leer_env("GROQ_API_KEY")
    if not key:
        print("[groq-stt] ❌ Falta GROQ_API_KEY")
        return None
    
    # Leer el archivo de audio como multipart/form-data
    boundary = uuid.uuid4().hex
    mime = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"
    audio_data = audio_path.read_bytes()
    
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="model"\r\n\r\nwhisper-large-v3\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="language"\r\n\r\nes\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="response_format"\r\n\r\ntext\r\n'
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{audio_path.name}"\r\n'
        f'Content-Type: {mime}\r\n\r\n'
    ).encode() + audio_data + f'\r\n--{boundary}--\r\n'.encode()
    
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        },
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        texto = resp.read().decode("utf-8", errors="replace")
        # Limpiar posible JSON wrapper
        if texto.startswith("{"):
            try:
                d = json.loads(texto)
                texto = d.get("text", texto)
            except: pass
        out_txt.write_text(texto)
        return texto
    except urllib.error.HTTPError as e:
        print(f"[groq-stt] HTTP {e.code}: {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"[groq-stt] Error: {e}")
        return None

def transcribir_todo(fecha=None):
    import datetime
    fecha = fecha or datetime.date.today().isoformat()
    recolector_json = ROOT / "output" / "encuadre" / f"recoleccion_{fecha}.json"
    if not recolector_json.exists():
        print(f"[stt] No existe {recolector_json}")
        return None
    
    datos = json.loads(recolector_json.read_text())
    audios = datos.get("audios", [])
    if not audios:
        print("[stt] No hay audios")
        return datos
    
    print(f"[stt] Transcribiendo {len(audios)} audios con Groq Whisper...", flush=True)
    for a in audios:
        audio = a.get("audio")
        if not audio: continue
        medio = a.get("medio", "?")
        print(f"  🎙️ {medio}...", end="", flush=True)
        texto = transcribir_groq(audio)
        if texto:
            a["transcripcion"] = texto
            print(f" ✅ {len(texto)} chars")
        else:
            print(f" ❌ Error")
    
    recolector_json.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"\n[stt] ✅ Guardado en {recolector_json}")
    return datos

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    transcribir_todo(fecha)
