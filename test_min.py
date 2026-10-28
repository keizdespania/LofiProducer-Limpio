import sherpa_onnx, os, pathlib, wave, sys

model_dir = "assets/models/tts/vits-piper-es_ES-davefx-medium"
onnx_path = os.path.join(model_dir, "es_ES-davefx-medium.onnx")
tokens_path = os.path.join(model_dir, "tokens.txt")
data_dir = os.path.join(model_dir, "espeak-ng-data")

print(f"data_dir existe: {os.path.exists(data_dir)}", flush=True)
print(f"data_dir contiene {len(os.listdir(data_dir)) if os.path.exists(data_dir) else 0} archivos", flush=True)

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
print("Modelo cargado. Generando 'Hola'...", flush=True)

audio = tts.generate("Hola")
print(f"Audio generado: {len(audio.samples)} samples", flush=True)

out = "output/audios/min_test.wav"
pathlib.Path("output/audios").mkdir(parents=True, exist_ok=True)
with wave.open(out, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(audio.sample_rate)
    wf.writeframes((audio.samples * 32767).astype("int16").tobytes())

print(f"✅ GUARDADO: {out} ({len(audio.samples)/audio.sample_rate:.2f}s)", flush=True)
