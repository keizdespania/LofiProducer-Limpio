"""comparar_ltx.py - Compara calidad/tamaño de vídeos LTX (steps 12 vs 20).
Uso: python3 scripts/comparar_ltx.py capibara_4 test_steps12_a
"""
import subprocess, sys, pathlib, json, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
GH_BASE = "https://raw.githubusercontent.com/keizdespania/LofiProducer-Limpio/main/output/videos/"
TMP = pathlib.Path.home() / "tmp" / "ltx_compare"


def descargar(nombre):
    TMP.mkdir(parents=True, exist_ok=True)
    dest = TMP / (nombre + ".mp4")
    if dest.exists():
        print(f"  {nombre}: ya en {dest}")
        return dest
    try:
        urllib.request.urlretrieve(GH_BASE + nombre + ".mp4", dest)
        print(f"  {nombre}: {dest.stat().st_size // 1024} KB")
        return dest
    except Exception as e:
        print(f"  {nombre}: FAIL ({e})")
        return None


def probe(mp4):
    """ffprobe: duración, resolución, bitrate, codec."""
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,bit_rate,size:stream=codec_name,width,height,nb_frames",
         "-of", "json", str(mp4)],
        capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        return {"error": r.stderr[:200]}
    return json.loads(r.stdout)


def main():
    if len(sys.argv) < 3:
        print("Uso: comparar_ltx.py NOMBRE_A NOMBRE_B [NOMBRE_C ...]")
        return 1

    print("=== Descargando ===")
    files = []
    for nombre in sys.argv[1:]:
        f = descargar(nombre)
        if f:
            files.append((nombre, f))

    if not files:
        print("Sin ficheros")
        return 1

    print("\n=== Metadata ===")
    rows = []
    for nombre, f in files:
        m = probe(f)
        if "error" in m:
            print(f"{nombre}: PROBE FAIL: {m['error']}")
            continue
        fmt = m.get("format", {})
        st = (m.get("streams") or [{}])[0]
        rows.append({
            "nombre": nombre,
            "size_kb": int(fmt.get("size", 0)) // 1024,
            "dur_s": round(float(fmt.get("duration", 0)), 2),
            "bitrate_kbps": int(fmt.get("bit_rate", 0)) // 1000,
            "codec": st.get("codec_name", "?"),
            "res": f"{st.get('width', '?')}x{st.get('height', '?')}",
            "frames": st.get("nb_frames", "?"),
        })

    print(f"{'nombre':<25} {'KB':>8} {'dur':>6} {'kbps':>7} {'codec':>8} {'res':>10} {'frames':>7}")
    for r in rows:
        print(f"{r['nombre']:<25} {r['size_kb']:>8} {r['dur_s']:>6} {r['bitrate_kbps']:>7} {r['codec']:>8} {r['res']:>10} {str(r['frames']):>7}")

    # Comparativa si hay >=2
    if len(rows) >= 2:
        base = rows[0]
        print(f"\n=== vs {base['nombre']} (baseline) ===")
        for r in rows[1:]:
            ds = (r['size_kb'] / base['size_kb'] - 1) * 100 if base['size_kb'] else 0
            db = (r['bitrate_kbps'] / base['bitrate_kbps'] - 1) * 100 if base['bitrate_kbps'] else 0
            print(f"  {r['nombre']}: size {ds:+.1f}% | bitrate {db:+.1f}%")

    print(f"\nMP4s en: {TMP}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
