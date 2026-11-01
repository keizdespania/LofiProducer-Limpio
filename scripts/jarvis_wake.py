#!/usr/bin/env python3
"""Jarvis Wake — openWakeWord + Groq Whisper (STT es) + termux-media-player (TTS)."""
import warnings; warnings.filterwarnings('ignore')
import os, sys, time, json, subprocess, glob, importlib.util
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))

from openwakeword.model import Model
import requests

# Cargar Whisper Groq
spec = importlib.util.spec_from_file_location("tg", ROOT / "scripts" / "transcribir_groq.py")
tg = importlib.util.module_from_spec(spec); spec.loader.exec_module(tg)

WAKE_THRESHOLD = 0.2
COOLDOWN = 4
CHUNK_DUR = 3
STORAGE = "/storage/emulated/0"
HOME = os.environ.get("HOME", "/data/data/com.termux/files/home")
WAV_TMP = Path(HOME) / "tmp" / "jarvis_chunk.wav"
WAV_CMD = Path(HOME) / "tmp" / "jarvis_cmd.wav"
JARVIS_API = "http://127.0.0.1:8001/api/jarvis/execute"
DIOS_API = "http://127.0.0.1:8001/api/dios_hablar"
LOG = ROOT / "data" / "logs" / "jarvis_wake.log"
LOG.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = time.strftime("%H:%M:%S")
    linea = "[" + ts + "] " + str(msg)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linea + chr(10))
    except Exception:
        pass

def notif(t, m):
    subprocess.run(["termux-notification", "-t", t, "-c", m,
                    "--id", "jarvis_wake", "--priority", "high"], capture_output=True)

def m4a_to_wav(m4a, wav, dur=None):
    cmd = ["ffmpeg", "-y", "-loglevel", "quiet", "-i", str(m4a),
           "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le"]
    if dur: cmd += ["-t", str(dur)]
    cmd += [str(wav)]
    subprocess.run(cmd, capture_output=True, timeout=10)

def grabar_chunk(dur):
    antes = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a"))
    subprocess.run(["termux-microphone-record", "-d", str(int(dur))], capture_output=True)
    time.sleep(dur + 0.3)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(0.2)
    nuevos = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a")) - antes
    if not nuevos: return None
    fichero = max(nuevos, key=os.path.getmtime)
    try:
        m4a_to_wav(fichero, WAV_TMP, dur)
        import wave
        with wave.open(str(WAV_TMP), "rb") as w:
            data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        try: os.remove(fichero)
        except: pass
        # NORMALIZAR: si RMS < 1500, amplificar
        rms = float(np.sqrt((data.astype(float)**2).mean()))
        if rms > 0 and rms < 1500:
            factor = min(3000 / rms, 8.0)  # max 8x
            data = np.clip(data.astype(np.float32) * factor, -32768, 32767).astype(np.int16)
        return data
    except Exception as e:
        log(f"⚠️ conv: {e}"); return None

def grabar_comando(dur=5):
    """Graba dur segundos para el comando y devuelve WAV path."""
    antes = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a"))
    subprocess.run(["termux-microphone-record", "-d", str(dur)], capture_output=True)
    time.sleep(dur + 0.3)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(0.2)
    nuevos = set(glob.glob(f"{STORAGE}/TermuxAudioRecording_*.m4a")) - antes
    if not nuevos: return None
    fichero = max(nuevos, key=os.path.getmtime)
    try:
        m4a_to_wav(fichero, WAV_CMD)
        try: os.remove(fichero)
        except: pass
        return str(WAV_CMD)
    except Exception as e:
        log(f"⚠️ conv cmd: {e}"); return None

def transcribir_es(wav_path):
    """Transcribe con Groq Whisper en español."""
    try:
        # Monkey-patch: forzar idioma español
        original = tg.transcribir_groq
        txt = original(wav_path)
        if txt:
            return txt.strip()
    except Exception as e:
        log(f"⚠️ whisper: {e}")
    return ""

def tocar_mp3(url_o_ruta):
    """Reproduce MP3. Acepta /media/... o /data/cache_voz/..."""
    if not url_o_ruta: return
    ruta = url_o_ruta
    # Convertir URL → ruta local (múltiples formatos)
    # Caso 1: /media/data/cache_voz/X.mp3 → data/cache_voz/X.mp3
    if ruta.startswith("/media/data/"):
        ruta = ruta[len("/media/"):]  # data/cache_voz/X.mp3
    # Caso 2: /media/otros → data/cache_voz/X.mp3 (fallback por nombre)
    elif ruta.startswith("/media/"):
        nombre = ruta.split("/")[-1]
        cand = ROOT / "data" / "cache_voz" / nombre
        if cand.exists():
            ruta = str(cand)
    # Caso 3: /data/cache_voz/X.mp3
    if ruta.startswith("/"):
        ruta = ruta[1:]
    # Caso 4: http URL
    if ruta.startswith("http"):
        try:
            tmp = Path(HOME) / "tmp" / "jarvis_tts.mp3"
            r = requests.get(ruta, timeout=10)
            tmp.write_bytes(r.content)
            ruta_local = tmp
            if ruta_local.exists():
                subprocess.run(["termux-media-player", "play", str(ruta_local.resolve())],
                               capture_output=True, timeout=10)
        except: pass
        return
    if ruta.startswith("data/"):
        ruta_local = ROOT / ruta
    elif ruta.startswith("http"):
        # Descargar
        try:
            tmp = Path(HOME) / "tmp" / "jarvis_tts.mp3"
            r = requests.get(ruta, timeout=10)
            tmp.write_bytes(r.content)
            ruta_local = tmp
        except: return
    else:
        ruta_local = Path(ruta)
    if not ruta_local.exists():
        # Fallback: buscar por nombre
        nombre = ruta.split("/")[-1]
        cands = list((ROOT / "data" / "cache_voz").glob(nombre))
        if cands: ruta_local = cands[0]
    if ruta_local.exists() and str(ruta_local).endswith(".mp3"):
        try:
            subprocess.run(["termux-media-player", "play", str(ruta_local.resolve())],
                           capture_output=True, timeout=10)
            return
        except: pass
    # Fallback: TTS del sistema (voz masculina española)
    subprocess.run(["termux-tts-speak", "-l", "spa", "-p", "0.85", "-r", "1.05",
                    str(url_o_ruta)[:400]], capture_output=True)

def ejecutar(texto):
    t = texto.lower()
    tools = [
        (["pipeline", "produce todo"], "run_pipeline", {}),
        (["diagnóstico", "doctor", "revisa", "diagnostico"], "doctor", {}),
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
        for k in ("respuesta", "texto", "msg", "mensaje", "reporte", "resultado", "content"):
            v = res.get(k)
            if isinstance(v, str) and v.strip() and not v.startswith("/"):
                return v[:400]
        if "url" in res:
            return res["url"]  # señal para tocar_mp3
        if "result" in res: return formatear(res["result"])
        return "Hecho."
    return str(res)[:400]

def main():
    log("🚀 Jarvis Wake (Groq Whisper)")
    notif("🤖 Jarvis activo", "Di 'Hey Jarvis'")
    log("Cargando modelo...")
    model = Model(wakeword_models=['hey_jarvis'], inference_framework='tflite')
    log("✅ Modelo cargado")
    ultima = 0; dets = 0; ok = 0; fail = 0
    try:
        while True:
            audio = grabar_chunk(CHUNK_DUR)
            if audio is None or len(audio) < 1280:
                fail += 1; continue
            ok += 1
            max_score = 0.0
            for i in range(0, len(audio) - 1280, 1280):
                pred = model.predict(audio[i:i+1280])
                s = float(pred.get("hey_jarvis", 0))
                if s > max_score: max_score = s
            # Reset si no hubo nada (evita estado estancado)
            if max_score < 0.05:
                try: model.reset()
                except: pass
            rms = float(np.sqrt((audio.astype(float)**2).mean()))
            log(f"   chunk score={max_score:.3f} rms={rms:.0f}")
            # Guardar WAV del chunk actual para inspección
            try:
                import wave
                with wave.open(str(Path(HOME) / "tmp" / "last_chunk.wav"), "wb") as wf:
                    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
                    wf.writeframes(audio.tobytes())
            except Exception: pass
            if max_score > WAKE_THRESHOLD:
                ahora = time.time()
                if ahora - ultima < COOLDOWN: continue
                ultima = ahora; dets += 1
                log(f"✅ Hey Jarvis #{dets} (score={max_score:.2f})")
                notif("👂 Te escucho...", "Habla AHORA (5s)")
                time.sleep(1.0)  # tiempo para que el usuario empiece a hablar
                # Grabar comando
                wav = grabar_comando(5)
                if not wav:
                    notif("🤖 Jarvis", "No te he oído"); continue
                # Transcribir con Whisper Groq (español)
                log("🎤 Transcribiendo con Whisper...")
                texto = transcribir_es(wav)
                if not texto:
                    notif("🤖 Jarvis", "No te entendí"); continue
                log(f"🗣️ Comando: {texto}")
                notif("🗣️ Tú", texto)
                # Ejecutar
                res = ejecutar(texto)
                respuesta = formatear(res)
                log(f"🤖 Respuesta: {respuesta[:100]}")
                # Si es URL de MP3 → reproducir
                if respuesta.startswith("/") or "cache_voz" in respuesta:
                    tocar_mp3(respuesta)
                    notif("🤖 Jarvis", "Reproduciendo respuesta...")
                else:
                    notif("🤖 Jarvis", respuesta[:400])
    except KeyboardInterrupt:
        log("🛑 Detenido")
    finally:
        log(f"👋 Cerrado. OK={ok} FAIL={fail}")

if __name__ == "__main__":
    main()
