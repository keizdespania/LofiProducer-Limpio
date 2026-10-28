import sherpa_onnx, os, pathlib, wave

model_dir = "assets/models/tts/vits-piper-es_ES-davefx-low"
out_file = "output/audios/sherpa_light.wav"
pathlib.Path("output/audios").mkdir(parents=True, exist_ok=True)

config = sherpa_onnx.OfflineTtsConfig(
    model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(
            model=os.path.join(model_dir, "es_ES-davefx-low.onnx"),
            tokens=os.path.join(model_dir, "tokens.txt"),
            data_dir=os.path.join(model_dir, "espeak-ng-data"),
        ),
        num_threads=1,
        provider="cpu",
    )
)
tts = sherpa_onnx.OfflineTts(config)

print("Generando audio (modelo low, 1 hilo)...")
audio = tts.generate("Hola Arquitecto. El modelo ligero funciona sin colapsar el movil.")
if len(audio.samples) == 0:
    print("❌ Error: No se generó audio.")
    exit(1)

with wave.open(str(out_file), 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(audio.sample_rate)
    wf.writeframes((audio.samples * 32767).astype("int16").tobytes())

print(f"✅ Audio generado: {out_file} ({len(audio.samples)/audio.sample_rate:.1f}s)")
