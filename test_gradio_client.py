from gradio_client import Client
import sys

url = "https://134e97d343a933b35d.gradio.live"
print(f"Conectando con {url}...")

try:
    client = Client(url)
    print("✅ Conectado.")
    print("\nEndpoints disponibles:")
    client.view_api()
except Exception as e:
    print(f"❌ Error: {e}")
