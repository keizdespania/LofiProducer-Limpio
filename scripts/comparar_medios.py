"""comparar_medios.py - Radar de Guerra Mediática (OmniRoute + Divide y Vencerás)."""
import sys, json, pathlib, datetime, re, urllib.request
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
OUT.mkdir(parents=True, exist_ok=True)

MEDIOS_RSS = {
    "El Pais": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada",
    "El Mundo": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml",
    "ABC": "https://www.abc.es/rss/2.0/portada/",
    "La Vanguardia": "https://www.lavanguardia.com/rss/home.xml",
    "elDiario.es": "https://www.eldiario.es/rss/",
    "El Confidencial": "https://rss.elconfidencial.com/espana/"
}

MEDIOS_TV = {
    "La Sexta": "https://www.youtube.com/@laSexta",
    "Antena 3": "https://www.youtube.com/@antena3",
    "Telemadrid": "https://www.youtube.com/@telemadrid",
    "Cadena SER": "https://www.youtube.com/@cadenaser",
    "Onda Cero": "https://www.youtube.com/@ondacero",
    "The Wild Project": "https://www.youtube.com/@TheWildProject"
}


def _parse_json_seguro(texto):
    if not texto: return {}
    # Quitar bloques de markdown
    texto = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE)
    texto = texto.replace('```', '').strip()
    try:
        return json.loads(texto)
    except: pass
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except: pass
    return {}

def _descargar_html(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    try:
        return urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='replace')
    except Exception:
        return ""

def _extraer_titulares(url_rss, max_n=5):
    html = _descargar_html(url_rss)
    if not html: return []
    items = re.findall(r'<item.*?</item>', html, re.DOTALL)
    titulares = []
    ayer = datetime.now(timezone.utc) - timedelta(days=1)
    for it in items:
        pubdate_m = re.search(r'<pubDate>(.*?)</pubDate>', it, re.DOTALL)
        if pubdate_m:
            try:
                from email.utils import parsedate_to_datetime
                if parsedate_to_datetime(pubdate_m.group(1).strip()) < ayer: continue
            except Exception: pass
        m = re.search(r'<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', it, re.DOTALL)
        if m: titulares.append(m.group(1).strip())
        if len(titulares) >= max_n: break
    return titulares

def _extraer_youtube(url_canal):
    import subprocess
    try:
        cmd = ["yt-dlp", "--flat-playlist", "--print", "%(upload_date)s|%(title)s", "-I", "1:5", url_canal]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if r.returncode == 0 and r.stdout:
            ayer_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
            hoy_str = datetime.now().strftime("%Y%m%d")
            titulares = []
            for line in r.stdout.splitlines():
                if "|" in line:
                    fecha_str, titulo = line.split("|", 1)
                    if fecha_str in (ayer_str, hoy_str): titulares.append(titulo.strip())
            if not titulares:
                # Fallback: si no hay de hoy/ayer, cogemos los últimos 2 del canal
                titulares = [line.split("|", 1)[1].strip() for line in r.stdout.splitlines() if "|" in line][:2]
            return titulares
    except Exception: pass
    return []

def _buscar_tema_comun(titulares_por_medio):
    from collections import Counter
    palabras = []
    for titulares in titulares_por_medio.values():
        for t in titulares:
            palabras.extend([p.lower() for p in re.findall(r'\b\w{5,}\b', t)])
    contador = Counter(palabras)
    comunes = [p for p, c in contador.most_common(10) if c >= 3]
    return " ".join(comunes[:3])

def comparar(tema_forzado=None):
    print("[radar] Extrayendo titulares (Prensa + TV/Radio)...", flush=True)
    datos = {}
    
    for nombre, url in MEDIOS_RSS.items():
        tits = _extraer_titulares(url)
        if tits: datos[nombre] = tits
        
    for nombre, url in MEDIOS_TV.items():
        tits = _extraer_youtube(url)
        if tits: datos[nombre] = tits

    if tema_forzado:
        tema = tema_forzado
    else:
        print("[radar] Identificando el tema real del día con el LLM...", flush=True)
        from especialistas import pedir_a_especialista
        # Contexto completo en texto plano (mucho más eficiente que JSON)
        ctx_tema = "Estos son los titulares de hoy:\n"
        for m, tits in datos.items():
            ctx_tema += f"\n[{m}]:\n" + "\n".join([f"- {x}" for x in tits]) + "\n"
            
        r_tema = pedir_a_especialista("analista_medios", "Dime en un máximo de 5 palabras el tema principal del día (solo el tema, sin explicaciones)", contexto=ctx_tema)
        print(f"[DEBUG TEMA] Crudo: {r_tema[:200]}")
        tema = r_tema.strip().replace('"', '').replace('.', '')
        if len(tema) > 50: tema = "noticias de hoy"
    print(f"[radar] 🔥 Tema del día: '{tema}'", flush=True)

    from especialistas import pedir_a_especialista
    
    # FASE 1: Análisis individual (Repartimos carga)
    print("[radar] Analizando medios uno a uno (OmniRoute)...", flush=True)
    analisis_individual = []
    for medio, tits in datos.items():
        prompt = f"Analiza el sesgo de '{medio}' sobre el tema '{tema}'. Aquí están sus titulares del día:\n" + "\n".join([f"- {x}" for x in tits])
        r = pedir_a_especialista("analista_medios", prompt, contexto="Devuelve SOLO JSON: {nombre, imd_local (0-100), framing, palabra_cuchillo}")
        d = _parse_json_seguro(r)
        if d and isinstance(d, dict) and d.get("imd_local") is not None:
            d["nombre"] = medio
            analisis_individual.append(d)
        else:
            print(f"  ⚠️ {medio} falló. Crudo: {r[:150]}...")
        print(f"  ✅ {medio} analizado", flush=True)

    # FASE 2: Síntesis Global (La Cita Bomba)
    print("[radar] Generando Síntesis Global y Sarcasmo...", flush=True)

    # === SÍNTESIS POR CHUNKS (Para que el LLM respire) ===
    from especialistas import pedir_a_especialista
    import time

    # 1. Preparar contexto compacto
    ctx_medios = ""
    for a in analisis_individual:
        ctx_medios += f"- {a.get('nombre')}: IMD {a.get('imd_local')}, framing {a.get('framing')}, palabra '{a.get('palabra_cuchillo')}'\n"

    # CHUNK A: El Dossier Base
    print("[radar] Chunk A: Dossier Base (Narrativa, IMD, Cita)...", flush=True)
    prompt_a = """Basado en estos medios, genera el dossier base. Devuelve SOLO JSON:
    {"tema_del_dia": "string", "indice_manipulacion_global": 0, "el_relato_oficial": "string", "la_contra_narrativa": "string", "analisis_psicologico": "string", "cita_bomba": "string", "sarcasmo_del_dia": "string", "protagonista": "string", "villano": "string"}"""
    r_a = pedir_a_especialista("analista_medios", prompt_a, contexto=ctx_medios)
    chunk_a = _parse_json_seguro(r_a)
    time.sleep(2) # RESPIRO

    # CHUNK B: El Arsenal de Producción
    print("[radar] Chunk B: Arsenal de Producción (Hooks + Guion)...", flush=True)
    prompt_b = """Basado en este tema y análisis, genera el arsenal de producción. Devuelve SOLO JSON:
    {"hooks_shorts": {"dato": "string", "contradiccion": "string", "prediccion": "string", "tutorial": "string"}, "guion_video_largo": "string (200 palabras narracion continua)"}"""
    r_b = pedir_a_especialista("analista_medios", prompt_b, contexto=ctx_medios[:2000])
    chunk_b = _parse_json_seguro(r_b)
    time.sleep(2) # RESPIRO

    # CHUNK C: El Análisis Forense
    print("[radar] Chunk C: Análisis Forense (Técnicas por medio)...", flush=True)
    prompt_c = """Para cada medio, detalla su técnica principal y traducción sarcástica. Devuelve SOLO JSON:
    {"medios": [{"nombre": "string", "titular_real": "string", "titular_traducido": "string", "imd_local": 0, "palabra_cuchillo": "string", "tecnica_principal": "string"}]}"""
    r_c = pedir_a_especialista("analista_medios", prompt_c, contexto=ctx_medios[:2000])
    chunk_c = _parse_json_seguro(r_c)

    # UNIR LOS 3 CHUNKS
    analisis_global = {}
    analisis_global.update(chunk_a)
    analisis_global.update(chunk_b)
    # Siempre usamos los análisis individuales (son más completos y ya están calculados)
    # Fusión inteligente: Base sólida (11 medios) + Sarcasmo del Chunk C
    analisis_global["medios"] = analisis_individual
    if chunk_c.get("medios"):
        # Diccionario de traducciones del Chunk C por nombre
        traducciones = {m.get("nombre", "").lower(): m for m in chunk_c["medios"]}
        for m in analisis_global["medios"]:
            nombre = m.get("nombre", "").lower()
            t_chunk = traducciones.get(nombre)
            if t_chunk:
                # Inyectar traducción sarcástica y técnica si vienen
                if t_chunk.get("titular_traducido"):
                    m["titular_traducido"] = t_chunk["titular_traducido"]
                if t_chunk.get("tecnica_principal") and not m.get("tecnica_principal"):
                    m["tecnica_principal"] = t_chunk["tecnica_principal"]
                print(f"[radar] Fusión OK: {nombre}", flush=True)
    # Si chunk_c trajo traducciones sarcásticas, las fusionamos
    if chunk_c.get("medios"):
        traducciones = {m.get("nombre"): m for m in chunk_c["medios"]}
        for m in analisis_global["medios"]:
            t = traducciones.get(m.get("nombre"))
            if t:
                m["titular_traducido"] = t.get("titular_traducido", "")
                m["tecnica_principal"] = t.get("tecnica_principal", "")

    print(f"[radar] ✅ Dossier ensamblado: {len(analisis_global)} claves", flush=True)

    # Guardar
    ts = datetime.now().strftime("%Y-%m-%d")
    res = {"fecha": ts, "tema": tema, "datos_brutos": datos, "analisis": analisis_global, "medios": analisis_individual}
    out_json = OUT / f"encuadre_{ts}.json"
    out_json.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[radar] ✅ Radar completado -> {out_json}", flush=True)

if __name__ == "__main__":
    tema = sys.argv[1] if len(sys.argv) > 1 else None
    comparar(tema)
