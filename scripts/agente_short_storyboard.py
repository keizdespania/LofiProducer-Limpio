"""Agente 1: Elige el hook y crea el storyboard de VIDEO (Beats) para un Short."""
import sys, json, pathlib, re, traceback
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))
from especialistas import pedir_a_especialista

OUT_DIR = ROOT / "data/agent/shorts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CATS = ["bunker_operativo", "callejon_lluvia", "detalle_glove", "hacker_movil", "hacker_frente", "investigacion_forense", "monitor_amenaza", "oficina_corp", "pantalla_codigo", "pantalla_datos", "periodico_fisico", "servidores", "zoom_codigo"]

PROMPT = """Eres un Director de Cine experto en YouTube Shorts.
Escribe un guion de 30 segundos (máximo 75 palabras) analizando este dossier: {dossier}
Estructura: Hook de impacto (0-3s), Desarrollo (3-25s), Cierre (25-30s).
Luego, divide el guion en BEATS narrativos (frases de 3 a 5 palabras).
Asigna a cada beat una categoría visual de esta lista: {cats}.
Regla 1: No repitas la misma categoría dos veces seguidas.
Regla 2: El primer beat debe ser visualmente impactante.
Regla 3: Las duraciones de los beats deben sumar entre 25 y 30 segundos.
Devuelve ÚNICAMENTE un JSON con este formato exacto:
{{
  "texto_completo": "El guion entero para la voz",
  "beats": [
    {{"texto": "Frase corta", "categoria": "hacker_frente", "duracion": 3}}
  ]
}}"""

def run():
    try:
        dossiers = sorted(list((ROOT / "output/encuadre").glob("dossier_*enriquecido.json")), reverse=True)
        if not dossiers:
            print("❌ ERROR: No hay archivos dossier_*.json en data/agent/")
            return

        dossier_path = dossiers[0]
        print(f"📄 Usando dossier: {dossier_path.name}")
        dossier = dossier_path.read_text()[:3000]
        
        print("⏳ Llamando al LLM (esto puede tardar 10-20s)...")
        prompt_final = PROMPT.format(dossier=dossier, cats=", ".join(CATS))
        
        raw = pedir_a_especialista("guionista_short_v3", prompt_final)
        
        if not raw:
            print("❌ ERROR: El LLM devolvió una respuesta vacía.")
            return
            
        print(f"✅ Respuesta recibida ({len(raw)} chars). Buscando JSON...")
        
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match: 
            print("❌ ERROR: No se encontró un JSON válido en la respuesta:")
            print(raw[:500])
            return
            
        data = json.loads(match.group(0))
        
        # Validar categorías
        for b in data.get("beats", []):
            if b.get("categoria") not in CATS: 
                b["categoria"] = "hacker_frente"
                
        data["outro"] = {"duracion": 3, "texto": "Visita somoselencuadre.com"}
        
        out = OUT_DIR / "test_storyboard_video.json"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        
        print(f"\n✅ Guardado: {out.name} ({len(data.get('beats', []))} beats)")
        print(json.dumps(data.get("beats", []), indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\n❌ ERROR FATAL: {type(e).__name__}: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    run()
