"""Voice Studio Pro v2: Presets, Historial, MP3, Batch, Diccionario."""
import sys, os, pathlib, wave, subprocess, json, time, uuid
import numpy as np
import sherpa_onnx

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "assets" / "models" / "tts"
OUT_DIR = ROOT / "output" / "audios"
HISTORY_FILE = OUT_DIR / "history.json"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ═══ CONTRATO SHERPA + VALIDADOR ═══
SHERPA_CONTRACT = pathlib.Path(__file__).resolve().parent.parent / "data" / "agent" / "sherpa_contract.json"

def _cargar_contrato_sherpa():
    if not SHERPA_CONTRACT.exists(): return None
    try: return json.loads(SHERPA_CONTRACT.read_text())
    except Exception: return None

def _aplicar_preset_contrato(nombre, params_actuales):
    """Fusiona un preset del contrato con los params actuales."""
    c = _cargar_contrato_sherpa()
    if not c or not nombre: return params_actuales
    preset = c.get("presets", {}).get(nombre)
    if not preset: return params_actuales
    fusion = dict(params_actuales)
    fusion.update(preset.get("params", {}))
    return fusion

def _validar_params_sherpa(params):
    """Clampea los params de voz según el validador del contrato."""
    c = _cargar_contrato_sherpa()
    if not c: return params
    out = dict(params)
    for r in c.get("validador", {}).get("reglas", []):
        campo = r["campo"]
        val = out.get(campo)
        if val is None: continue
        if isinstance(val, (int, float)):
            if val < r["min"]: out[campo] = r["min"]
            elif val > r["max"]: out[campo] = r["max"]
    return out


def _cargar_catalogo():
    p = MODELS_DIR / "catalogo.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"voces": []}

def _buscar_onnx(voz_id):
    for d in [voz_id, "vits-piper-" + voz_id]:
        dir_p = MODELS_DIR / d
        if dir_p.exists():
            onnx = list(dir_p.glob("*.onnx"))
            if onnx: return dir_p, onnx[0]
    return None, None

def _buscar_shared():
    shared = MODELS_DIR / "_shared"
    if (shared / "tokens.txt").exists() and (shared / "espeak-ng-data").exists():
        return shared / "tokens.txt", shared / "espeak-ng-data"
    base = MODELS_DIR / "vits-piper-es_ES-davefx-medium"
    return base / "tokens.txt", base / "espeak-ng-data"

def _aplicar_presets(preset, pitch, velocidad, compresor, reverb, bass):
    """Aplica preset. Los 4 originales + los 7 del contrato Sherpa."""
    p = preset.lower()
    # Presets originales del sistema
    if p == "podcast": return (0, 1.0, True, 5, 2)
    if p == "documental": return (-2, 0.9, True, 15, 4)
    if p == "tiktok": return (2, 1.15, False, 0, 6)
    if p == "finanzas": return (-4, 0.95, True, 0, 8)
    # Presets del contrato Sherpa (traducidos a tupla)
    if p == "noticias": return (0, 1.0, True, 0, 0)          # claro, sin reverb
    if p == "narracion_relajada": return (0, 0.9, True, 10, 2)  # pausado, reverb suave
    if p == "urgente": return (2, 1.15, False, 0, 4)          # rápido, tenso
    if p == "audiobook": return (0, 0.95, True, 8, 0)         # natural
    if p == "publicidad": return (2, 1.05, True, 0, 6)        # energético
    if p == "tutorial": return (0, 0.95, True, 0, 2)          # claro, didáctico
    if p == "sintesis_rapida": return (0, 1.25, False, 0, 0)  # borradores
    return (pitch, velocidad, compresor, reverb, bass)

def generar_audio(texto, voz="es_ES-davefx-medium", formato="mp3", preset="ninguno",
                  pitch=0, velocidad=1.0, distorsion=0, reverb=0, bass=0, treble=0,
                  compresor=False, normalizar=True, diccionario=None, nombre="",
                  length_scale=None, noise_scale=None, noise_scale_w=None,
                  silence_scale=None, max_num_sentences=None, num_threads=None):
    # Aplicar preset del contrato (si existe) sobre los defaults
    if preset and preset != "ninguno":
        params = _aplicar_preset_contrato(preset, {
            "length_scale": length_scale, "noise_scale": noise_scale,
            "noise_scale_w": noise_scale_w, "silence_scale": silence_scale,
            "max_num_sentences": max_num_sentences, "num_threads": num_threads,
        })
        length_scale = params.get("length_scale", length_scale)
        noise_scale = params.get("noise_scale", noise_scale)
        noise_scale_w = params.get("noise_scale_w", noise_scale_w)
        silence_scale = params.get("silence_scale", silence_scale)
        max_num_sentences = params.get("max_num_sentences", max_num_sentences)
        num_threads = params.get("num_threads", num_threads)
        if "speed" in params:
            velocidad = params["speed"]
    
    # Validador del contrato
    validado = _validar_params_sherpa({
        "length_scale": length_scale if length_scale is not None else 1.0,
        "noise_scale": noise_scale if noise_scale is not None else 0.667,
        "noise_scale_w": noise_scale_w if noise_scale_w is not None else 0.8,
        "silence_scale": silence_scale if silence_scale is not None else 0.2,
        "max_num_sentences": max_num_sentences if max_num_sentences is not None else 5,
        "num_threads": num_threads if num_threads is not None else 2,
        "speed": velocidad,
    })
    length_scale = validado["length_scale"]
    noise_scale = validado["noise_scale"]
    noise_scale_w = validado["noise_scale_w"]
    silence_scale = validado["silence_scale"]
    max_num_sentences = validado["max_num_sentences"]
    num_threads = validado["num_threads"]
    
    if diccionario:
        for k, v in diccionario.items():
            texto = texto.replace(k, v)

    p, v, c, r, b = _aplicar_presets(preset, pitch, velocidad, compresor, reverb, bass)

    model_dir, onnx_path = _buscar_onnx(voz)
    if onnx_path is None: return {"error": f"Voz no instalada: {voz}"}
    tok_path, espeak_path = _buscar_shared()
    if not tok_path.exists(): return {"error": "Faltan archivos shared (_shared/tokens.txt)"}

    try:
        vits_cfg = sherpa_onnx.OfflineTtsVitsModelConfig(
            model=str(onnx_path), tokens=str(tok_path), data_dir=str(espeak_path),
            noise_scale=float(noise_scale), noise_scale_w=float(noise_scale_w),
            length_scale=float(length_scale),
        )
        model_cfg = sherpa_onnx.OfflineTtsModelConfig(
            vits=vits_cfg, num_threads=int(num_threads), provider="cpu",
        )
        config = sherpa_onnx.OfflineTtsConfig(
            model=model_cfg, silence_scale=float(silence_scale),
            max_num_sentences=int(max_num_sentences),
        )
        tts = sherpa_onnx.OfflineTts(config)
        audio = tts.generate(texto)
        if not audio.samples: return {"error": "No se genero audio"}

        ts = int(time.time()); uid = uuid.uuid4().hex[:6]
        temp_wav = OUT_DIR / f"studio_{ts}_{uid}_temp.wav"
        samples = np.array(audio.samples, dtype=np.float32)
        s16 = (samples * 32767).clip(-32768, 32767).astype(np.int16)
        with wave.open(str(temp_wav), 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(audio.sample_rate)
            wf.writeframes(s16.tobytes())

        # Filtros
        f = []
        if p != 0:
            factor = 2 ** (p / 12.0)
            f.append(f"asetrate={audio.sample_rate}*{factor}"); f.append(f"atempo={1/factor}")
        if v != 1.0: f.append(f"atempo={v}")
        if distorsion > 0: f.append(f"acrusher=bits={max(4, int(16-(distorsion/100)*12))}:mode=log:aa=1")
        if r > 0: f.append(f"aecho=0.8:{min(0.9, 0.3+r/200)}:{500+int(r*10)}:{min(0.9, 0.3+r/200)*0.8}")
        if b != 0: f.append(f"bass=g={b}:f=100:w=0.5")
        if treble != 0: f.append(f"treble=g={treble}:f=3000:w=0.5")
        if c: f.append("acompressor=threshold=-20dB:ratio=4:attack=5:release=50")
        if normalizar: f.append("loudnorm=I=-16:LRA=11:TP=-1.5")

        ext = "mp3" if formato == "mp3" else "wav"
        final_out = OUT_DIR / f"studio_{ts}_{uid}.{ext}"
        cmd = ["ffmpeg", "-y", "-i", str(temp_wav)]
        if f: cmd += ["-af", ",".join(f)]
        if ext == "mp3": cmd += ["-b:a", "192k", "-codec:a", "libmp3lame"]
        cmd.append(str(final_out))
        
        subprocess.run(cmd, check=True, capture_output=True)
        temp_wav.unlink(missing_ok=True)

        # Historial
        record = {
            "id": f"studio_{ts}_{uid}", "nombre": nombre or f"Audio {ts}", "texto": texto[:100],
            "voz": voz, "duracion": round(len(audio.samples)/audio.sample_rate, 2),
            "url": f"/media/audios/{final_out.name}", "formato": ext, "ts": ts,
            "perfil": {"preset": preset, "pitch": p, "vel": v}
        }
        history = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else []
        history.insert(0, record)
        HISTORY_FILE.write_text(json.dumps(history[:50], indent=2)) # Guardar ultimos 50

        return {"status": "ok", "audio_id": record["id"], "url": record["url"], "duracion": record["duracion"]}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--texto", required=True)
    p.add_argument("--voz", default="es_ES-davefx-medium")
    p.add_argument("--preset", default="ninguno")
    p.add_argument("--formato", default="mp3")
    p.add_argument("--pitch", type=int, default=0)
    p.add_argument("--velocidad", type=float, default=1.0)
    p.add_argument("--distorsion", type=int, default=0)
    p.add_argument("--reverb", type=int, default=0)
    p.add_argument("--bass", type=int, default=0)
    p.add_argument("--treble", type=int, default=0)
    p.add_argument("--compresor", action="store_true")
    p.add_argument("--no-normalizar", action="store_true")
    p.add_argument("--perfil-dios", action="store_true")
    p.add_argument("--length-scale", type=float, default=None)
    p.add_argument("--noise-scale", type=float, default=None)
    p.add_argument("--noise-scale-w", type=float, default=None)
    p.add_argument("--silence-scale", type=float, default=None)
    p.add_argument("--max-num-sentences", type=int, default=None)
    p.add_argument("--num-threads", type=int, default=None)
    a = p.parse_args()
    if a.perfil_dios:
        pp = ROOT / "data" / "agent" / "voz_dios.json"
        if pp.exists():
            perfil = json.loads(pp.read_text())
            a.voz = perfil.get("voz", a.voz)
            a.preset = perfil.get("preset", a.preset)
            
    r = generar_audio(
        a.texto, voz=a.voz, formato=a.formato, preset=a.preset,
        pitch=a.pitch, velocidad=a.velocidad, distorsion=a.distorsion, 
        reverb=a.reverb, bass=a.bass, treble=a.treble, 
        compresor=a.compresor, normalizar=not a.no_normalizar
    )
    print(json.dumps(r))
