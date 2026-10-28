"""analizar_musica_cc.py - Analiza tracks CC y actualiza el índice."""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from analista_audio import analizar_pista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
INDEX = OUT / "index_musica_cc.json"

def analizar_todo():
    if not INDEX.exists():
        print("❌ No existe index_musica_cc.json")
        return
    data = json.loads(INDEX.read_text())
    for item in data:
        if "analisis_audio" in item: continue
        archivo = OUT / item["archivo"]
        if not archivo.exists(): continue
        print(f"🔍 Analizando {item['archivo']}...")
        analisis = analizar_pista(archivo)
        if "error" not in analisis:
            item["analisis_audio"] = analisis
            print(f"   ✅ Pico: {analisis['peak_energy_time']}s")
    INDEX.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"✅ Índice actualizado con {len(data)} pistas analizadas.")

if __name__ == "__main__":
    analizar_todo()
