"""planificador_montaje.py - Genera el plan de montaje (algorítmico + director IA)."""
import sys, json, pathlib, re, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista
from descargar_musica_dinamica import descargar_por_mood, pedir_efecto

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
MUSICA_DIR = ROOT / "output" / "musica_temp"

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

def _detectar_pista_para_mood(mood, pistas_disponibles):
    """Busca una pista descargada que tenga el mood (o la que más se acerque)."""
    # 1. Coincidencia exacta
    for p in pistas_disponibles:
        if p.startswith(mood):
            return p
    # 2. Fallback: cualquier pista
    return pistas_disponibles[0] if pistas_disponibles else None

def planificar(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists(): return None
    
    datos = json.loads(prod_file.read_text())
    escenas = datos.get("guion_cinematografico", {}).get("guion", [])
    if not escenas: 
        print("[plan] No hay escenas")
        return None
    

    # Cargar el índice de música CC (con análisis de energía)
    cc_index_path = ROOT / "output" / "musica_temp" / "index_musica_cc.json"
    pistas_cc = []
    if cc_index_path.exists():
        pistas_cc = json.loads(cc_index_path.read_text())
        print(f"[plan] Pistas CC disponibles: {len(pistas_cc)}", flush=True)
    # 1. Detectar moods necesarios
    moods = set(e.get("musica", "relax") for e in escenas)
    print(f"[plan] Moods: {moods}", flush=True)
    
    # 2. Descargar música
    for m in moods:
        if m and m != "None":
            descargar_por_mood(m, 1)
    
    # 3. Listar pistas disponibles
    pistas = [f.name for f in MUSICA_DIR.glob("*.mp3") if not f.name.startswith("sfx_")]
    sfx_files = [f.name for f in MUSICA_DIR.glob("sfx_*.mp3")]
    print(f"[plan] Pistas disponibles: {len(pistas)}", flush=True)
    print(f"[plan] SFX disponibles: {len(sfx_files)}", flush=True)
    
    # 4. Construir timeline ALGORÍTMICO (basado en las escenas)

    # 3. Construir timeline con pistas CC (usando sus picos de energía)
    timeline = []
    tiempo_actual = 0.0
    for i, esc in enumerate(escenas):
        duracion = max(5, min(15, len(esc.get("texto", "")) // 10))
        # Elegir una pista CC rotativa
        pista_cc = pistas_cc[i % len(pistas_cc)] if pistas_cc else None
        if pista_cc:
            analisis = pista_cc.get("analisis_audio", {})
            inicio_musica = analisis.get("sugerencia_inicio", 0)
            timeline.append({
                "capa": "musica",
                "inicio": tiempo_actual,
                "fin": tiempo_actual + duracion,
                "archivo": pista_cc["archivo"],
                "track_inicio": inicio_musica,
                "volumen_base": 0.15,
                "ducking": True,
                "fade_in": 1.0,
                "fade_out": 1.0
            })
        tiempo_actual += duracion
    
    # 5. Añadir SFX al inicio
    if sfx_files:
        timeline.insert(0, {
            "capa": "efecto",
            "inicio": 0,
            "fin": 1,
            "archivo": sfx_files[0],
            "track_inicio": 0,
            "volumen_base": 0.8,
            "ducking": False
        })
    
    # 6. Config global
    plan = {
        "config_global": {"loudnorm_target": -16, "true_peak": -1.5, "lra": 11},
        "timeline": timeline,
        "ffmpeg_filter": "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=400[duck];[0:a][duck]amix=inputs=2:duration=first:normalize=0[a]",
        "nota": "Timeline generado algorítmicamente. Usar sidechaincompress para ducking."
    }
    
    datos["plan_montaje"] = plan
    prod_file.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"[plan] ✅ Plan guardado: {len(timeline)} eventos", flush=True)
    return plan

if __name__ == "__main__":
    planificar(sys.argv[1] if len(sys.argv) > 1 else None)
