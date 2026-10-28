"""sintetizador.py - Genera el Dossier, Hooks y Citas desde el análisis de medios."""
import sys, json, pathlib, datetime, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    matches = re.findall(r'\{.*?\}', texto, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    return {}

def sintetizar(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    analisis_file = OUT / f"analisis_fase1_{fecha}.json"
    if not analisis_file.exists():
        print(f"❌ No existe {analisis_file}")
        return None
    
    datos = json.loads(analisis_file.read_text())
    top3 = datos.get("top3", {})
    medios = datos.get("analisis", {})
    
    # 1. Preparar contexto de forma segura (evitando errores de listas)
    ctx = f"TOP 3 NOTICIAS:\n{json.dumps(top3, ensure_ascii=False)}\n\nANÁLISIS POR MEDIO:\n"
    for m, arr in medios.items():
        if not arr: continue
        a = arr[0]
        if isinstance(a, list) and len(a) > 0: a = a[0]
        if isinstance(a, dict):
            ctx += f"\n[{m}] IMD: {a.get('imd_local', '?')}, Framing: {a.get('framing', '?')}, Cuchillo: {a.get('palabra_cuchillo', '?')}\n"
    
    # 2. Director de Inteligencia (Dossier)
    print("[sintetizador] Director de Inteligencia generando Dossier Base...", flush=True)
    prompt_dir = "Basado en estos análisis, genera el Dossier Base. Devuelve SOLO JSON: {\"tema_del_dia\": \"string\", \"indice_manipulacion_global\": 0, \"el_relato_oficial\": \"string\", \"la_contra_narrativa\": \"string\", \"analisis_psicologico\": \"string\", \"cita_bomba\": \"string\", \"sarcasmo_del_dia\": \"string\", \"protagonista\": \"string\", \"villano\": \"string\"}"
    r = pedir_a_especialista("director_inteligencia_v2", prompt_dir, contexto=ctx[:4000])
    dossier = _parse_json_seguro(r)
    print(f"[sintetizador] Dossier: {len(dossier)} claves", flush=True)
    
    # 3. Guionista de Retención (Hooks)
    print("[sintetizador] Guionista generando hooks...", flush=True)
    prompt_guion = "Basado en el Dossier, genera TODOS los hooks posibles (mín 3 por noticia). Devuelve SOLO JSON: {\"hooks_totales\": [{\"noticia\": \"string\", \"tipo\": \"string\", \"hook\": \"string\", \"guion\": \"string\"}]}"
    r_g = pedir_a_especialista("guionista_retencion_v2", prompt_guion, contexto=json.dumps(dossier, ensure_ascii=False)[:3000])
    guiones = _parse_json_seguro(r_g)
    print(f"[sintetizador] Hooks generados: {len(guiones.get('hooks_totales', []))}", flush=True)
    
    # 4. Bibliotecario (Citas)
    print("[sintetizador] Bibliotecario buscando respaldo académico...", flush=True)
    tecnicas = []
    for m, arr in medios.items():
        for a in arr:
            if isinstance(a, dict):
                tec = a.get("tecnica_principal") or a.get("tecnica")
                if tec: tecnicas.append(tec)
    prompt_bib = "Para cada técnica, cita la obra académica real. Devuelve SOLO JSON: {\"tecnicas\": [{\"tecnica\": \"string\", \"autor\": \"string\", \"obra\": \"string\", \"año\": \"string\", \"cita_breve\": \"string\"}]}"
    r_b = pedir_a_especialista("bibliotecario_v2", prompt_bib, contexto="Técnicas: " + " | ".join(tecnicas[:5]))
    citas = _parse_json_seguro(r_b)
    
    # 5. Guardar
    res = {
        "fecha": fecha,
        "top3": top3,
        "dossier": dossier,
        "guiones": guiones,
        "citas": citas,
        "medios": medios,
    }
    out_json = OUT / f"dossier_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[sintetizador] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    sintetizar(sys.argv[1] if len(sys.argv) > 1 else None)
