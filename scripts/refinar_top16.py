"""refinar_top16.py - Usa la IA para elegir las 16 noticias mas manipulables del dia."""
import json, pathlib, sys, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

MEDIOS_OK = ["El País", "El Mundo", "ABC", "La Vanguardia", "elDiario.es", "El Confidencial", "El Español", "OkDiario", "The Objective", "HuffPost", "Bloomberg", "Europa Press", "20 Minutos", "Ara"]

def main():
    # 1. Leer la recolección limpia
    rec = json.loads((OUT / f"recoleccion_{FECHA}_limpia.json").read_text())
    
    # 2. Extraer titulares de la lista blanca
    titulares = []
    for sec in ("prensa", "agencias"):
        for medio, noticias in (rec.get(sec) or {}).items():
            if any(m in medio for m in MEDIOS_OK):
                for n in noticias:
                    if isinstance(n, dict) and n.get("titular"):
                        titulares.append(f"[{medio}] {n['titular']}")
    
    print(f"[refinar] {len(titulares)} titulares de medios generalistas encontrados.")
    
    # 3. Pedir a la IA que elija los 16 mejores (los más manipulables)
    prompt = (
        "Eres un editor jefe experto en detectar manipulación mediática. "
        "Aquí tienes una lista de titulares de hoy. "
        "Tu misión es elegir EXACTAMENTE los 16 titulares que tengan el mayor potencial de manipulación, framing o sesgo para ser desmontados en un vídeo. "
        "Devuelve SOLO un JSON con esta estructura: {\"elegidos\": [\"[Medio] Titular 1\", \"[Medio] Titular 2\", ...]}. "
        "Elige la flor y nata de la manipulación."
    )
    ctx = "\n".join(titulares)
    
    print("[refinar] Pidiendo a la IA que seleccione la flor y nata...")
    res = pedir_a_especialista("detector_tendencias_v2", prompt, contexto=ctx, proveedor="auto")
    
    # 4. Parsear el JSON
    import re
    try:
        m = re.search(r'\{.*\}', res, re.DOTALL)
        if m:
            d = json.loads(m.group(0))
            elegidos = d.get("elegidos", [])
        else:
            elegidos = []
    except:
        elegidos = []
        
    if not elegidos:
        print("❌ La IA falló al elegir. Usando fallback (primeros 16).")
        elegidos = titulares[:16]
        
    print(f"[refinar] La IA ha elegido {len(elegidos)} noticias.")
    
    # 5. Construir el nuevo top16 con sus URLs
    top16_nuevo = []
    for e in elegidos:
        # Buscar la URL original cruzando el titular
        for t in titulares:
            if e in t:
                # Extraer el medio
                medio = t.split("]")[0].replace("[", "")
                titular_limpio = t.split("] ")[1]
                # Buscar URL en la recolección
                for sec in ("prensa", "agencias"):
                    for m, noticias in (rec.get(sec) or {}).items():
                        if m == medio:
                            for n in noticias:
                                if n.get("titular") == titular_limpio:
                                    top16_nuevo.append({
                                        "titular": titular_limpio,
                                        "url": n.get("url", ""),
                                        "medio": medio
                                    })
                                    break
                break
    
    # 6. Guardar en analisis_fase1
    af = OUT / f"analisis_fase1_{FECHA}.json"
    if af.exists():
        data = json.loads(af.read_text())
        data["top16"] = top16_nuevo[:16]
        af.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"✅ Top16 actualizado en analisis_fase1_{FECHA}.json con {len(top16_nuevo)} noticias de oro.")
    else:
        print("❌ No existe analisis_fase1. Lanza primero analista_fase1.py.")

if __name__ == "__main__":
    main()
