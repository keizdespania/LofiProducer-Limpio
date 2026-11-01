#!/usr/bin/env python3
"""Jarvis Listen — Push-to-talk: UNA escucha, UN comando, UNA respuesta.
Se ejecuta cuando el usuario pulsa el botón. Se cierra solo."""
import warnings; warnings.filterwarnings('ignore')
import os, sys, time, json, subprocess, glob, importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))

import requests

spec = importlib.util.spec_from_file_location("tg", ROOT / "scripts" / "transcribir_groq.py")
tg = importlib.util.module_from_spec(spec); spec.loader.exec_module(tg)

STORAGE = "/storage/emulated/0"
HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
WAV_CMD = Path(HOME) / "tmp" / "jarvis_cmd.wav"
JARVIS_API = "http://127.0.0.1:8001/api/jarvis/execute"
DIOS_API = "http://127.0.0.1:8001/api/dios_hablar"
LOG = ROOT / "data" / "logs" / "jarvis_listen.log"
LOG.parent.mkdir(parents=True, exist_ok=True)
DURACION = 6  # segundos de grabación

def log(msg):
    linea = f"[{time.strftime('%H:%M:%S')}] {msg}"
    try:
        with open(LOG, "a", encoding="utf-8") as f: f.write(linea + "\n")
    except: pass

def notif(t, m):
    subprocess.run(["termux-notification", "-t", t, "-c", m,
                    "--id", "jarvis_listen", "--priority", "high"], capture_output=True)

def toast(m):
    subprocess.run(["termux-toast", m], capture_output=True)

def m4a_to_wav(m4a, wav):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "quiet", "-i", str(m4a),
                    "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", str(wav)],
                   capture_output=True, timeout=10)

def grabar(dur):
    antes = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a"))
    subprocess.run(["termux-microphone-record", "-l", str(dur)], capture_output=True)
    time.sleep(dur + 0.8)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(0.2)
    nuevos = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a")) - antes
    if not nuevos:
        log("⚠️ No se generó m4a")
        return None
    fichero = max(nuevos, key=os.path.getmtime)
    try:
        m4a_to_wav(fichero, WAV_CMD)
        os.remove(fichero)
        return str(WAV_CMD)
    except Exception as e:
        log(f"⚠️ conv: {e}")
        return None

def transcribir(wav):
    try:
        return (tg.transcribir_groq(wav) or "").strip()
    except Exception as e:
        log(f"⚠️ whisper: {e}")
        return ""

def tocar(ruta):
    """Reproduce MP3 del cache_voz o fallback TTS."""
    if not ruta: return
    nombre = ruta.split("/")[-1]
    if nombre.endswith(".mp3"):
        # Buscar en data/cache_voz
        cand = ROOT / "data" / "cache_voz" / nombre
        if cand.exists():
            subprocess.run(["termux-media-player", "play", str(cand.resolve())],
                           capture_output=True, timeout=15)
            return
    # Fallback TTS
    subprocess.run(["termux-tts-speak", "-l", "spa", "-p", "0.85", "-r", "1.05",
                    str(ruta)[:400]], capture_output=True)

def ejecutar(texto):
    t = texto.lower()
    tools = [
        (["pipeline", "produce todo"], "run_pipeline", {}),
        (["diagnóstico", "diagnostico", "doctor", "revisa"], "doctor", {}),
        (["canales", "nichos"], "ver_canales", {}),
        (["cola", "tareas"], "ver_cola", {}),
        (["música", "musica", "canción", "cancion"], "generar_musica", {"prompt": texto, "duration": 60, "preset": "lofi"}),
        (["imagen", "foto", "dibuja"], "generar_imagen", {"prompt": texto, "aspect_ratio": "1:1", "style": "cinematic"}),
        (["vídeo", "video", "clip"], "generar_video", {"prompt": texto, "preset": "cinematic"}),
        (["monetización", "monetizacion", "dinero", "ingresos"], "agente_monetizacion", {}),
        (["estrategia", "estratega", "recomienda"], "estratega", {}),
    ]
    for claves, tool, params in tools:
        if any(c in t for c in claves):
            log(f"⚡ Tool: {tool}")
            try:
                r = requests.post(JARVIS_API, json={"tool": tool, "params": params}, timeout=180)
                return r.json().get("result", {})
            except Exception as e:
                return {"error": str(e)}
    log("🤖 Consultando Dios...")
    try:
        r = requests.post(DIOS_API, json={"texto": texto}, timeout=120)
        return r.json()
    except Exception as e:
        return {"error": str(e)}

def formatear(res):
    if res is None: return "Hecho."
    if isinstance(res, str): return res[:400]
    if isinstance(res, list): return f"{len(res)} elementos"
    if isinstance(res, dict):
        for k in ("respuesta", "texto", "msg", "mensaje", "reporte", "resultado"):
            v = res.get(k)
            if isinstance(v, str) and v.strip():
                return v[:400]
        if "url" in res: return res["url"]
        if "result" in res: return formatear(res["result"])
        return "Hecho."
    return str(res)[:400]

def main():
    log("🚀 Jarvis Listen (push-to-talk)")
    toast("🎙️ Escuchando 6s...")
    notif("🎙️ Te escucho", f"Habla ahora ({DURACION}s)")
    wav = grabar(DURACION)
    if not wav:
        notif("🤖 Jarvis", "No te oí")
        toast("❌ No te oí")
        return
    log("🎤 Transcribiendo...")
    texto = transcribir(wav)
    if not texto or len(texto) < 3:
        notif("🤖 Jarvis", "No te entendí")
        toast("❌ No te entendí")
        return
    log(f"🗣️ Comando: {texto}")
    notif("🗣️ Tú", texto)
    res = ejecutar(texto)
    resp = formatear(res)
    log(f"🤖 Respuesta: {resp[:100]}")
    notif("🤖 Jarvis", resp[:400])
    tocar(resp)

if __name__ == "__main__":
    main()
