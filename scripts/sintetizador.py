"""sintetizador.py - Genera el Dossier Brutal, Hooks y Bibliotecario."""
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

def main():
    fecha = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    af = OUT / f"analisis_fase1_{fecha}.json"
    if not af.exists():
        print(f"❌ No existe {af}"); return
    datos = json.loads(af.read_text())
    
    top3 = datos.get("top3", {})
    top16 = datos.get("top16", [])
    medios = list(datos.get("analisis", {}).keys())

    # Contexto para el LLM
    ctx = f"TOP 3: {json.dumps(top3, ensure_ascii=False)}\n\n"
    ctx += f"TOP 16 NOTICIAS: {json.dumps(top16, ensure_ascii=False)}\n\n"
    ctx += f"MEDIOS ANALIZADOS ({len(medios)}): {json.dumps(medios, ensure_ascii=False)}\n\n"
    
    # Añadir extractos de los medios para el dossier
    for m, ans in list(datos.get("analisis", {}).items())[:10]:
        for a in ans:
            if a.get("framing"):
                ctx += f"[{m}] Framing: {a.get('framing')} | Técnica: {a.get('tecnica_principal')}\n"

    print("[sintetizador] Generando Dossier Brutal...", flush=True)
    prompt_dir = """Devuelve SOLO un JSON válido para un DOSSIER PERIODÍSTICO:
{
  "titular_brutal": "Titular mordaz para el blog",
  "resumen_ejecutivo": "3 párrafos resumiendo la manipulación",
  "contexto_historico": "2 párrafos de contexto",
  "desglose_medios": "Análisis de cómo los medios tratan la noticia",
  "tecnicas_manipulacion": ["Técnica 1", "Técnica 2", "Técnica 3", "Técnica 4", "Técnica 5"],
  "citas_bomba": ["Cita 1", "Cita 2", "Cita 3"],
  "conclusion": "1 párrafo final"
}
NO uses markdown, SOLO JSON."""
    dossier = _parse_json(pedir_a_especialista("director_inteligencia_v2", prompt_dir, contexto=ctx[:12000], proveedor="auto"))
    print(f"[sintetizador] Dossier: {len(dossier)} claves", flush=True)

    print("[sintetizador] Generando Hooks...", flush=True)
    prompt_hooks = """Devuelve SOLO un JSON: 
{"hooks": [{"tipo": "Cita", "hook": "Texto", "guion": "Texto", "score": 85}, ...]}
Genera 10 hooks para shorts basados en el top16. SOLO JSON."""
    guiones = _parse_json(pedir_a_especialista("guionista_retencion_v2", prompt_hooks, contexto=ctx[:8000], proveedor="auto"))
    hooks = guiones.get("hooks", [])
    print(f"[sintetizador] Hooks: {len(hooks)}", flush=True)

    print("[sintetizador] Bibliotecario buscando respaldo...", flush=True)
    prompt_bib = """Devuelve SOLO un JSON:
{"citas": [{"autor": "Nombre", "frase": "Texto", "contexto": "Texto"}, ...]}
Busca 3 citas académicas o de expertos sobre manipulación mediática. SOLO JSON."""
    bib = _parse_json(pedir_a_especialista("bibliotecario_v2", prompt_bib, contexto="Técnicas: framing, anclaje, hombre de paja", proveedor="auto"))
    citas = bib.get("citas", [])
    print(f"[sintetizador] Citas: {len(citas)}", flush=True)

    res = {
        "fecha": fecha,
        "top3": top3,
        "dossier": dossier,
        "guiones": {"hooks_totales": hooks},
        "citas": citas,
        "medios": medios
    }
    out = OUT / f"dossier_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[sintetizador] ✅ Guardado en {out}", flush=True)

if __name__ == "__main__":
    main()
