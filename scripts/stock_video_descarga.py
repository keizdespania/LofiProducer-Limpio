"""stock_video_descarga.py — Descarga clips de stock (Pexels/Coverr/Mixkit) vía yt-dlp.
Los clips son 100% comercializables (CC0). Transformados = obra nueva monetizable.
"""
import os, sys, json, pathlib, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "output" / "stock"
CACHE.mkdir(parents=True, exist_ok=True)


def _buscar_y_descargar(query, max_clips=3, orientacion="vertical"):
    q = f"pexels {query} vertical" if orientacion == "vertical" else f"pexels {query} horizontal"
    print(f"[stock] Buscando: '{q}'", flush=True)

    cmd_buscar = ["yt-dlp", f"ytsearch{max_clips * 2}:{q}", "--get-id", "--flat-playlist", "--no-warnings"]
    try:
        res = subprocess.run(cmd_buscar, capture_output=True, text=True, timeout=60)
        ids = [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception as e:
        print(f"[stock] Error busqueda: {e}", flush=True)
        return []

    if not ids:
        print("[stock] 0 resultados", flush=True)
        return []

    print(f"[stock] {len(ids)} candidatos", flush=True)
    clips = []
    for vid_id in ids:
        if len(clips) >= max_clips:
            break
        out_tmpl = str(CACHE / f"stock_{vid_id}.%(ext)s")
        fmt = "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=1080][ext=mp4]/b"
        cmd = [
            "yt-dlp", "-f", fmt, "--merge-output-format", "mp4",
            "-o", out_tmpl, "--no-playlist", "--no-warnings",
            "--max-filesize", "100M",
            "--download-sections", "*0-20",
            f"https://www.youtube.com/watch?v={vid_id}"
        ]
        print(f"[stock] Descargando {vid_id}...", flush=True)
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            final_file = CACHE / f"stock_{vid_id}.mp4"
            if final_file.exists() and final_file.stat().st_size > 100_000:
                clips.append(str(final_file))
                print(f"[stock] OK {vid_id} ({final_file.stat().st_size // 1024} KB)", flush=True)
        except Exception as e:
            print(f"[stock] Excepcion {vid_id}: {e}", flush=True)

    return clips


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: stock_video_descarga.py <query> [max_clips] [vertical|horizontal]")
        sys.exit(1)
    query = sys.argv[1]
    maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    orient = sys.argv[3] if len(sys.argv) > 3 else "vertical"
    print(json.dumps({"clips": _buscar_y_descargar(query, maxn, orient)}, indent=2, ensure_ascii=False))
