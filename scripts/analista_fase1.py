"""analista_fase1.py - Cadena de análisis con el Consejo de Inteligencia."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def _parse_json_seguro(texto):
    if not texto: return {}
    # 1. Intentar JSON directo
    texto_limpio = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(texto_limpio)
    except: pass
    # 2. Buscar el JSON más grande dentro del texto
    matches = re.findall(r'\{.*?\}', texto, re.DOTALL)
    for m in sorted(matches, key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    # 3. Intentar extraer de bloques de código
    code_blocks = re.findall(r'```(?:json)?(.*?)```', texto, re.DOTALL)
    for block in code_blocks:
        try: return json.loads(block.strip())
        except: pass
    return {}

def analizar_fase1(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    recolector_json = OUT / f"recoleccion_{fecha}.json"
    if not recolector_json.exists():
        print(f"[fase1] No existe {recolector_json}")
        return None
    
    datos = json.loads(recolector_json.read_text())
    
    # 1. Detectar Top 3 noticias
    print("[fase1] Detectando Top 3 noticias...", flush=True)
    ctx_titulares = "TITULARES DE PRENSA:\n"
    for medio, noticias in datos.get("prensa", {}).items():
        ctx_titulares += f"\n[{medio}]\n"
        for n in noticias:
            ctx_titulares += f"- {n['titular']}\n"
    
    # Añadir también TV/Radio (primeros 200 chars de cada transcripción)
    for medio, videos in datos.get("tv_radio", {}).items():
        ctx_titulares += f"\n[{medio}]\n"
        for v in videos:
            ctx_titulares += f"- {v['titulo']}\n"
    
    r_tema = pedir_a_especialista("detective_tendencias_v2", "Detecta el Top 3 de noticias del día.", contexto=ctx_titulares[:4000])
    top3 = _parse_json_seguro(r_tema)
    if not top3:
        print("[fase1] ⚠️ Detective falló. Reintentando con prompt simplificado...", flush=True)
        r_tema2 = pedir_a_especialista("detective_tendencias_v2", 
            "Devuelve SOLO JSON: {\"noticia_1\": \"string\", \"noticia_2\": \"string\", \"noticia_3\": \"string\"}", 
            contexto=ctx_titulares[:2000])
        top3 = _parse_json_seguro(r_tema2)
        if not top3:
            print("[fase1] ❌ Reintento fallido. Usando fallback manual.", flush=True)
            # Fallback: usar los titulares más repetidos
            top3 = {"noticia_1": "Noticias del día", "noticia_2": "Actualidad política", "noticia_3": "Sucesos y sociedad"}
    print(f"[fase1] ✅ Top 3 detectado: {list(top3.values())}", flush=True)
    
    # 2. Analizar cada medio sobre cada noticia
    print("[fase1] Analizando cada medio (esto puede tardar)...", flush=True)
    todos_analisis = {}
    medios = list(datos.get("prensa", {}).keys()) + list(datos.get("tv_radio", {}).keys())
    
    for medio in medios:
        todos_analisis[medio] = []
        # Recopilar textos del medio
        textos = []
        if medio in datos.get("prensa", {}):
            for n in datos["prensa"][medio]:
                textos.append(n["titular"])
        if medio in datos.get("tv_radio", {}):
            for v in datos["tv_radio"][medio]:
                textos.append(v["titulo"])
        # Si hay transcripción, añadir un fragmento
        for a in datos.get("audios", []):
            if a.get("medio") == medio and a.get("transcripcion"):
                textos.append(a["transcripcion"][:2000])
        
        if not textos:
            continue
        
        # Contexto simplificado: solo los titulares (máx 500 chars) para evitar ahogar al LLM
        ctx_medio = f"MEDIO: {medio}\nTITULARES:\n" + "\n".join(textos[:3])
        noticia = list(top3.values())[0] if isinstance(top3, dict) else "noticias del día"
        
        print(f"  🔍 {medio}...", flush=True)
        prompt_forense = f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON con: nombre, titular_real, titular_traducido, imd_local (0-100), framing, palabra_cuchillo, tecnica_principal, omision."
        r = pedir_a_especialista("forense_medios", prompt_forense, contexto=ctx_medio[:800])
        analisis = _parse_json_seguro(r)
        if analisis:
            todos_analisis[medio].append(analisis)
            # Añadir análisis emocional y sesgos
            r_emo = pedir_a_especialista("analista_emocional", f"Analiza las emociones de {medio}", contexto=ctx_medio[:2000])
            emo = _parse_json_seguro(r_emo)
            if emo: analisis["emociones"] = emo
            
            r_sesgos = pedir_a_especialista("detector_sesgos_cognitivos", f"Detecta sesgos cognitivos en {medio}", contexto=ctx_medio[:2000])
            sesgos = _parse_json_seguro(r_sesgos)
            if sesgos: analisis["sesgos_cognitivos"] = sesgos
        time.sleep(1)  # Respiro para OmniRoute
    
    # 3. Guardar
    res = {
        "fecha": fecha,
        "top3": top3,
        "analisis": todos_analisis,
        "recoleccion": datos,
    }
    out_json = OUT / f"analisis_fase1_{fecha}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out_json}", flush=True)
    return res

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    analizar_fase1(fecha)
