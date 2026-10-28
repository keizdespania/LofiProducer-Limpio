"""rollback_auto.py - Snapshot y restauración de output/encuadre."""
import subprocess, sys, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
SNAP = ROOT / "output" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)

def snapshot():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = SNAP / f"snap_{ts}.tar.gz"
    subprocess.run(["tar", "-czf", str(dest), "-C", str(OUT), "."], check=False)
    print(f"✅ Snapshot: {dest.name}")

def restore(nombre):
    src = SNAP / nombre
    if not src.exists(): print("❌ No existe"); return
    subprocess.run(["tar", "-xzf", str(src), "-C", str(OUT)], check=False)
    print(f"✅ Restaurado: {nombre}")

if __name__ == "__main__":
    if len(sys.argv) > 1: restore(sys.argv[1])
    else: snapshot()
