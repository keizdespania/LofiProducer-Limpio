"""filtro_seguridad.py - Filtra noticias de sucesos trágicos para evitar baneos."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

# Lista de palabras clave prohibidas (ampliable)
PALABRAS_PROHIBIDAS = [
    # Accidentes y tragedias
    "accidente", "choque", "colisión", "vuelco", "atropello", "fallecido", "muerto", "muerte", "fatal", "tragedia", "víctima", "herido grave", "incendio", "explosión", "derrumbe",
    # Violencia y crímenes
    "asesinato", "homicidio", "tiroteo", "apuñalamiento", "agresión", "violación", "abuso", "secuestro", "terrorismo", "atentado", "guerra", "conflicto armado", "masacre",
    # Sucesos y desastres
    "suicidio", "desastre natural", "terremoto", "inundación", "huracán", "tsunami", "erupción", "pandemia", "crisis sanitaria",
    # Términos sensacionalistas
    "impactante", "escalofriante", "sobrecogedor", "terrorífico", "horroroso", "sangriento", "brutal", "shock", "alarma",
]

def _cargar_json(fecha):
    f = OUT / f"recoleccion_{fecha}.json"
    if not f.exists(): return None
    return json.loads(f.read_text())

def _es_segura(texto):
    texto = texto.lower()
    for p in PALABRAS_PROHIBIDAS:
        if p in texto:
            return False, p
    return True, None

def filtrar(fecha):
    datos = _cargar_json(fecha)
    if not datos: 
        print("❌ No hay recolección para filtrar"); return False

    print(f"🛡️ Abogado de Sucesos: filtrando noticias del {fecha}...")
    
    eliminadas = 0
    # Filtrar prensa
    for medio, noticias in list(datos.get("prensa", {}).items()):
        noticias_seguras = []
        for n in noticias:
            texto_completo = n.get("titular", "") + " " + n.get("url", "")
            seguro, palabra = _es_segura(texto_completo)
            if seguro:
                noticias_seguras.append(n)
            else:
                print(f"  🚫 Descartada de {medio}: '{n['titular'][:50]}...' (contiene '{palabra}')")
                eliminadas += 1
        datos["prensa"][medio] = noticias_seguras

    # Filtrar agencias
    for medio, noticias in list(datos.get("agencias", {}).items()):
        noticias_seguras = []
        for n in noticias:
            texto_completo = n.get("titular", "") + " " + n.get("url", "")
            seguro, palabra = _es_segura(texto_completo)
            if seguro:
                noticias_seguras.append(n)
            else:
                print(f"  🚫 Descartada de {medio}: '{n['titular'][:50]}...' (contiene '{palabra}')")
                eliminadas += 1
        datos["agencias"][medio] = noticias_seguras

    # Guardar el JSON filtrado
    out_file = OUT / f"recoleccion_{fecha}.json"
    out_file.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"✅ Filtro completado: {eliminadas} noticias eliminadas.")
    return True

if __name__ == "__main__":
    filtrar(sys.argv[1] if len(sys.argv) > 1 else None)
