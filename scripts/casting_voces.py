import asyncio
import edge_tts
import pathlib
import shutil

TEXTO = "No te contamos las noticias. Te enseñamos la maquinaria que hay detrás de ellas. Análisis técnico, académico e irónico sobre cómo los medios construyen tu percepción. Bienvenido a Somos El Encuadre."
OUT = pathlib.Path("output/pruebas_voz")
OUT.mkdir(parents=True, exist_ok=True)

VOCES = [
    {"nombre": "Alvaro_Original", "id": "es-ES-AlvaroNeural", "pitch": "+0Hz"},
    {"nombre": "Alvaro_Grave_15", "id": "es-ES-AlvaroNeural", "pitch": "-15Hz"},
    {"nombre": "Alvaro_Grave_25", "id": "es-ES-AlvaroNeural", "pitch": "-25Hz"},
    {"nombre": "Arnau", "id": "es-ES-ArnauNeural", "pitch": "+0Hz"},
    {"nombre": "Dario", "id": "es-ES-DarioNeural", "pitch": "+0Hz"},
    {"nombre": "Elias", "id": "es-ES-EliasNeural", "pitch": "+0Hz"},
    {"nombre": "Nil", "id": "es-ES-NilNeural", "pitch": "+0Hz"},
    {"nombre": "Saul", "id": "es-ES-SaulNeural", "pitch": "+0Hz"},
    {"nombre": "Teo", "id": "es-ES-TeO_Neural", "pitch": "+0Hz"}, # Corregido abajo
]

# Arreglo del ID de Teo (a veces viene con minúscula en la 'o')
VOCES[-1]["id"] = "es-ES-TeoNeural"

async def generar_muestra(voz):
    archivo = OUT / f"{voz['nombre']}.mp3"
    print(f"🎙️ Generando: {voz['nombre']}...")
    communicate = edge_tts.Communicate(TEXTO, voz["id"], pitch=voz["pitch"], rate="-5%")
    await communicate.save(str(archivo))

async def main():
    for voz in VOCES:
        try:
            await generar_muestra(voz)
        except Exception as e:
            print(f"❌ Error con {voz['nombre']}: {e}")
    print("\n✅ Todas las muestras generadas en output/pruebas_voz/")

if __name__ == "__main__":
    asyncio.run(main())
