import sherpa_onnx, os, pathlib, wave, threading, time

model_dir = "assets/models/tts/vits-piper-es_ES-davefx-medium"
out_file = "output/audios/sherpa_medium.wav"
pathlib.Path("output/audios").mkdir(parents=True, exist_ok=True)

# Comprobar que los archivos existen
onnx_path = os.path.join(model_dir, "es_ES-davefx-medium.onnx")
tokens_path = os.path.join(model_dir, "tokens.txt")
data_dir = os.path.join(model_dir, "espeak-ng-data")
print(f"onnx: {os.path.exists(onnx_path)}")
print(f"tokens: {os.path.exists(tokens_path)}")
print(f"data_dir: {os.path.exists(data_dir)}")

# Monitor de RAM en segundo plano
def monitor():
    for _ in range(60):
        with open("/proc/meminfo") as f:
            lines = f.read().splitlines()
            avail = next((l for l in lines if l.startswith("MemAvailable")), "")
        print(f"[RAM] {avail}")
        time.sleep(1)
threading.Thread(target=monitor, daemon=True).start()

print("Cargando modelo...")
config = sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=onnx_path,
            tokens=tokens_path,
            data_dir=data_dir,
        ),
        num_threads=1,
        provider="cpu",
    )
)
tts = sherpa_onnx.OfflineTts(config)
print("✅ Modelo cargado")

print("Generando audio (texto corto para minimizar RAM)...")
audio = tts.generate("Hola. Prueba.")
if len(audio.samples) == 0:
    print("❌ Sin audio")
    exit(1)

with wave.open(str(out_file), 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(audio.sample_rate)
    wf.writeframes((audio.samples * 32767).astype("int16").tobytes())

print(f"✅ Audio: {out_file} ({len(audio.samples)/audio.sample_rate:.1f}s)")
