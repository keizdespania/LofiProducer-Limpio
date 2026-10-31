"""sintetizador.py - Genera el Dossier Brutal (Python) + Hooks y Citas (LLM)."""
import sys, json, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json(texto):
    import re
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.I).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    for m in sorted(re.findall(r'\{.*?\}', texto, re.DOTALL), key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def _construir_dossier_python(datos, fecha):
    """Construye un dossier masivo usando solo Python y los datos del analisis."""
    top3 = datos.get("top3", {})
    top16 = datos.get("top16", [])
    medios_data = datos.get("analisis", {})
    
    # 1. Titular brutal (basado en el top 3)
    tema = list(top3.values())[0] if top3 else "La manipulación del día"
    titular_brutal = f"El Encuadre: {tema[:80]}..."
    
    # 2. Resumen ejecutivo
    resumen = (
        f"Hoy hemos auditado {len(medios_data)} medios de comunicación. "
        f"El tema central es: {tema}. "
        f"Los medios han utilizado diferentes enfoques para desviar la atención, "
        f"demostrando que la manipulación no es un accidente, sino una estrategia."
    )
    
    # 3. Desglose de medios (la joya de la corona)
    desglose = []
    tecnicas_totales = []
    for m, ans in medios_data.items():
        for a in ans:
            if not isinstance(a, dict): continue
            framing = a.get("framing", "N/A")
            tecnica = a.get("tecnica_principal", "N/A")
            omision = a.get("omision", "N/A")
            tit = a.get("titular_real", "N/A")
            
            if tecnica != "N/A": tecnicas_totales.append(tecnica)
            
            desglose.append(
                f"**{m}**: '{tit}' -> **Framing:** {framing} | **Técnica:** {tecnica} | **Omite:** {omision}"
            )
    
    desglose_str = "\n".join(desglose) if desglose else "No hay datos de medios."
    
    # 4. Técnicas de manipulación (únicas)
    tecnicas_unicas = list(set([t for t in tecnicas_totales if t and t != "N/A"]))
    
    # 5. Citas bomba (titulares del top16)
    citas = [n.get("titular", "") for n in top16[:5]]
    
    # 6. Contexto y conclusión
    contexto = (
        f"El análisis de hoy se centra en {len(top16)} noticias críticas. "
        "Los medios analizados han mostrado un patrón claro de manipulación, "
        "utilizando titulares cargados de emoción para moldear la percepción pública."
    )
    conclusion = (
        "La manipulación mediática es un hecho. La única forma de combatirla es "
        "la lectura crítica y el contraste de fuentes. No te dejes engañar."
    )
    
    return {
        "titular_brutal": titular_brutal,
        "resumen_ejecutivo": resumen,
        "contexto_historico": contexto,
        "desglose_medios": desglose_str,
        "tecnicas_manipulacion": tecnicas_unicas[:8], # Top 8 técnicas
        "citas_bomba": citas,
        "conclusion": conclusion,
        "metricas": {
            "medios_analizados": len(medios_data),
            "noticias_top16": len(top16),
            "tecnicas_detectadas": len(tecnicas_unicas)
        }
    }

def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    af = OUT / f"analisis_fase1_{fecha}.json"
    if not af.exists():
        print(f"❌ No existe {af}"); return
    datos = json.loads(af.read_text())

    print("[sintetizador] Construyendo Dossier Brutal (100% Python)...", flush=True)
    dossier = _construir_dossier_python(datos, fecha)
    print(f"[sintetizador] Dossier generado con {len(dossier)} claves y {len(dossier['tecnicas_manipulacion'])} tecnicas.", flush=True)

    # Contexto para el LLM (solo para hooks y citas)
    top3 = datos.get("top3", {})
    top16 = datos.get("top16", [])
    ctx = f"TOP 3: {json.dumps(top3, ensure_ascii=False)}\n"
    ctx += f"TOP 16: {json.dumps(top16, ensure_ascii=False)}\n"
    ctx += f"TECNICAS: {json.dumps(dossier['tecnicas_manipulacion'], ensure_ascii=False)}"

    print("[sintetizador] Generando Hooks (LLM)...", flush=True)
    prompt_hooks = """Devuelve SOLO un JSON: 
{"hooks": [{"tipo": "Cita", "hook": "Texto", "guion": "Texto", "score": 85}, ...]}
Genera 10 hooks para shorts basados en el top16. SOLO JSON."""
    guiones = _parse_json(pedir_a_especialista("guionista_retencion_v2", prompt_hooks, contexto=ctx[:8000], proveedor="auto"))
    hooks = guiones.get("hooks", [])
    print(f"[sintetizador] Hooks: {len(hooks)}", flush=True)

    print("[sintetizador] Bibliotecario buscando respaldo (LLM)...", flush=True)
    prompt_bib = """Devuelve SOLO un JSON:
{"citas": [{"autor": "Nombre", "frase": "Texto", "contexto": "Texto"}, ...]}
Busca 3 citas académicas o de expertos sobre manipulación mediática. SOLO JSON."""
    bib = _parse_json(pedir_a_especialista("bibliotecario_v2", prompt_bib, contexto="Técnicas: framing, anclaje, hombre de paja", proveedor="auto"))
    citas_academicas = bib.get("citas", [])
    print(f"[sintetizador] Citas académicas: {len(citas_academicas)}", flush=True)

    res = {
        "fecha": fecha,
        "top3": top3,
        "dossier": dossier,
        "guiones": {"hooks_totales": hooks},
        "citas": citas_academicas,
        "medios": list(datos.get("analisis", {}).keys())
    }
    out = OUT / f"dossier_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[sintetizador] ✅ Guardado en {out}", flush=True)

if __name__ == "__main__":
    main()
