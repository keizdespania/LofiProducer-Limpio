"""WanGP-Kaggle: la solucion probada para T4."""
import sys, subprocess

print("=== WANGP-KAGGLE (Solucion T4) ===")
# 1. Clonar el repo
subprocess.run(["git", "clone", "https://github.com/kayas881/WanGP-Kaggle.git", "/kaggle/working/WanGP-Kaggle"], check=True)

# 2. Instalar dependencias (celdas 1-5 del README)
subprocess.run(["pip", "install", "-q", "torch", "torchvision", "torchaudio", "--index-url", "https://download.pytorch.org/whl/cu121"], check=True)
subprocess.run(["pip", "install", "-q", "gradio", "transformers", "accelerate", "safetensors", "sentencepiece", "protobuf"], check=True)

# 3. Reiniciar kernel (WanGP lo requiere)
print("IMPORTANTE: Reinicia el kernel manualmente antes de continuar.")
print("El script se ha preparado. Ve a la pestana 'Run' -> 'Restart and Clear Cell Outputs'.")
print("Luego ejecuta el notebook de WanGP-Kaggle.")
