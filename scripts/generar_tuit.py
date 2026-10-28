"""generar_tuit.py - Genera tuit para X (sin API de pago)."""

import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"


def generar_tuit(fecha=None):
    fecha = fecha or __import__("datetime").date.today().isoformat()
    ret_path = OUT / f"retencion_{fecha}.json"
    if not ret_path.exists():
        print("[tuit] No hay retención")
        return None
    ret = json.loads(ret_path.read_text())
    hook = ret.get("hook", "")
    giro = ret.get("giro", "")
    cta = ret.get("cta", "")
    
    # Tuit: hook + giro + enlace
    tuit = f"{hook}\n\n{giro}\n\n{cta}\n\nhttps://elencuadre.pages.dev"
    if len(tuit) > 280:
        tuit = tuit[:277] + "..."
    
    # Guardar
    out = OUT / f"tuit_{fecha}.txt"
    out.write_text(tuit)
    print(f"[tuit] Generado: {out}")
    print(f"[tuit] Texto:\n{tuit}")
    return str(out)


if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    generar_tuit(fecha)
