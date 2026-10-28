import sys
import requests
import json

url = "https://6a5cc40331dbc69dd6.gradio.live"
print(f"Pidiendo configuración a {url}/config...")

try:
    r = requests.get(f"{url}/config", timeout=30)
    r.raise_for_status()
    config = r.json()
    
    # Guardamos el JSON por si acaso
    with open("gradio_config.json", "w") as f:
        json.dump(config, f)
    print("✅ Configuración guardada en gradio_config.json\n")
    
    # Traducir ID -> Nombre
    componentes = {}
    for comp in config.get("components", []):
        comp_id = comp.get("id")
        props = comp.get("props", {})
        nombre = props.get("label") or props.get("value") or comp.get("type")
        componentes[comp_id] = nombre

    # Buscar la función de generación
    print("🎯 FUNCIÓN: /generation_wrapper")
    print("Campos que necesita (en orden):\n")
    for dep in config.get("dependencies", []):
        if dep.get("api_name") == "generation_wrapper":
            for i, comp_id in enumerate(dep.get("inputs", [])):
                nombre = componentes.get(comp_id, f"Desconocido (ID {comp_id})")
                print(f"{i+1}. {nombre}")
            break
            
except Exception as e:
    print(f"❌ Error: {e}")
