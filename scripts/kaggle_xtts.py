"""Script para clonar voz con XTTS-v2 en Kaggle."""
import sys, os

# Configuracion (la inyectaremos al subir)
TEXTO = "Hola, soy la voz clonada del imperio LofiProducer."
AUDIO_REFERENCIA = "/kaggle/input/audio-referencia.wav" # Debes subir un WAV a un dataset de Kaggle
OUTPUT = "/kaggle/working/voz_clonada.wav"

print("=== INICIANDO XTTS-v2 EN KAGGLE ===")

# 1. Instalar dependencias
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "TTS==0.22.0"], check=True)
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "torch", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu118"], check=True)

# 2. Descargar el modelo
print("Cargando modelo XTTS-v2...")
import torch
from TTS.api import TTS

# Usar GPU si esta disponible
device = "cuda" if torch.cuda.is_available() else "cpu"
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

# 3. Generar la voz clonada
print(f"Clonando voz desde {AUDIO_REFERENCIA}...")
tts.tts_to_file(
    text=TEXTO,
    speaker_wav=AUDIO_REFERENCIA,
    language="es",
    file_path=OUTPUT
)

print("=== PROCESO FINALIZADO ===")
print(f"✅ Voz clonada en {OUTPUT}")
