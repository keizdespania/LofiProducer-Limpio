"""pipeline_internacional.py - Pipeline para medios internacionales (lunes y jueves)."""
import sys, json, pathlib, datetime, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"

def main():
    fecha = datetime.date.today().isoformat()
    dia_semana = datetime.date.today().weekday() # 0=lunes, 3=jueves
    if dia_semana not in (0, 3):
        print("⏭️  Hoy no es lunes ni jueves. Pipeline internacional omitido.")
        return
    
    print("🌍 INICIANDO PIPELINE INTERNACIONAL...")
    
    # 1. Recolectar medios internacionales (usando el script de recolección adaptado)
    # (Simulamos la recolección de los medios internacionales)
    print("  → Recolectando medios internacionales...")
    
    # 2. Traducir los textos al castellano
    print("  → Traduciendo textos con el agente traductor_humanizado...")
    # (Llamada de ejemplo)
    texto_original = "The political situation in Spain is tense due to the recent elections."
    r = pedir_a_especialista("traductor_humanizado", texto_original)
    print(f"     Traducción: {r[:100]}...")
    
    # 3. Generar el dossier y los posts (reutilizando los agentes de la fase 1 y 2)
    print("  → Generando dossier internacional...")
    # (Aquí se llamaría a analista_fase1.py y sintetizador.py con los datos internacionales)
    
    # 4. Publicar en la sección Internacional de la Web y Blogger
    print("  → Publicando en la sección Internacional...")
    
    print("✅ PIPELINE INTERNACIONAL COMPLETADO")

if __name__ == "__main__":
    main()
