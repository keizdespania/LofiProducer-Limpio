"""informe_detective.py - Genera un informe editorial visual (HTML) sobre qué publicar."""
import sys, json, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

from investigador_redes import investigar
from predictor_viralidad import score_tema
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent

def generar_informe_visual(nicho):
    print(f"[informe] Investigando {nicho}...", flush=True)
    inv = investigar(nicho)
    
    # Extraer datos
    yts = sorted(inv.get("youtube", []), key=lambda x: x.get("vistas", 0), reverse=True)[:5]
    trends = [t.get("keyword", "") for t in inv.get("trends", [])][:5]
    
    contexto = f"Nicho: {nicho}\nFecha: {datetime.date.today()}\n\n"
    contexto += "TOP 5 VIDEOS EN YOUTUBE:\n"
    for v in yts:
        contexto += f"- {v.get('titulo')} ({v.get('vistas')} vistas)\n"
    contexto += "\nTOP TENDENCIAS EN GOOGLE TRENDS (ESPAÑA):\n"
    for t in trends:
        contexto += f"- {t}\n"
    
    print("[informe] Redactando informe periodístico...", flush=True)
    
    prompt = """Eres el Redactor Jefe de IA Global News. 
Tu trabajo es escribir un INFORME EDITORIAL (formato HTML) para el equipo de producción, analizando las tendencias actuales para decidir qué publicar hoy.

ESTRUCTURA OBLIGATORIA (todo dentro de etiquetas HTML <h1>, <h2>, <p>, <ul>, <li>, <strong>):
1. <h1>Informe Editorial: [Fecha de hoy]</h1>
2. <h2>1. El Pulso del Mercado</h2> (Análisis de los videos top de YouTube. ¿Qué está funcionando? ¿Qué formatos?)
3. <h2>2. Tendencias Emergentes</h2> (Análisis de Google Trends en España. ¿Qué busca la gente? ¿Hay algún tema local o de actualidad?)
4. <h2>3. Recomendación Principal de Hoy</h2> (Elige UN tema exacto para producir, justifica por qué, y define el ángulo).
5. <h2>4. Plan de Producción Sugerido</h2> (Lista de 4 shorts sugeridos y 1 artículo de blog).

REGLAS:
- NO uses markdown (no uses #, *, etc). Usa SOLO etiquetas HTML.
- Tono profesional, analítico y directo.
- No inventes datos. Usa los que te paso en el contexto.
- Si las tendencias de Google no tienen nada que ver con IA (ej. Dani Martín), indica que es un tema de actualidad general y sugiere cómo hacer un puente con la IA, o descártalo.
"""
    
    html_informe = pedir_a_especialista("redactor_seo", prompt, contexto=contexto)
    
    # Limpiar posibles bloques ```html que el LLM meta por error
    if html_informe.startswith("```html"): html_informe = html_informe[7:]
    if html_informe.endswith("```"): html_informe = html_informe[:-3]
    
    # Guardar como HTML puro
    out_html = ROOT / "data" / "agent" / f"informe_{nicho}.html"
    out_html.write_text(html_informe, encoding="utf-8")
    
    # Guardar también un JSON para que la web sepa que existe y cuándo se hizo
    meta = {
        "nicho": nicho,
        "fecha": datetime.datetime.now().isoformat(),
        "url_html": str(out_html)
    }
    out_meta = ROOT / "data" / "agent" / f"informe_{nicho}.json"
    out_meta.write_text(json.dumps(meta), encoding="utf-8")
    
    print(f"[informe] ✅ Generado: {out_html}", flush=True)
    return html_informe

if __name__ == "__main__":
    nicho = sys.argv[1] if len(sys.argv) > 1 else "ia_news"
    generar_informe_visual(nicho)
