"""meta_agentes_semanal.py - 3 meta-agentes domingo 03:00."""
import sys, json, pathlib, datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
HOY = datetime.date.today().isoformat()

def _logs():
    ls = [f.read_text()[-2500:] for f in sorted((ROOT/"output"/"logs").glob("pipeline_*.log"))[-3:] if f.exists()]
    return "\n---\n".join(ls)

def main():
    print(f"[meta] {HOY}", flush=True)
    logs = _logs()
    a = pedir_a_especialista("auditor_codigo",
        "Analiza logs. Bug repetido #1 + fix de 1 linea.",
        contexto=logs[:5000], proveedor="omni")
    (OUT/f"meta_auditoria_{HOY}.txt").write_text(a or ""); print(f"  auditoria {len(a or '')} chars", flush=True)
    ana = ROOT/"data"/"agent"/"analytics_aprendizaje.json"
    ana_txt = ana.read_text()[:2500] if ana.exists() else "Sin analytics"
    e = pedir_a_especialista("estratega_negocio",
        "UN nicho a abrir + UNA accion esta semana.",
        contexto=ana_txt, proveedor="omni")
    (OUT/f"meta_estrategia_{HOY}.txt").write_text(e or ""); print(f"  estrategia {len(e or '')} chars", flush=True)
    ar = pedir_a_especialista("arquitecto_sistema",
        "UN nuevo agente/script concreto a crear.",
        contexto=f"AUD:\n{(a or '')[:800]}\n\nEST:\n{(e or '')[:800]}", proveedor="omni")
    (OUT/f"meta_arquitecto_{HOY}.txt").write_text(ar or ""); print(f"  arquitecto {len(ar or '')} chars", flush=True)
    print("[meta] OK", flush=True)

if __name__ == "__main__":
    main()
