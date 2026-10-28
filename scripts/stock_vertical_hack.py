"""stock_vertical_hack.py — Caza clips verticales 9:16 con 4 trucos + auto-crop."""
import os, sys, json, pathlib, subprocess, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "output" / "stock"
CACHE.mkdir(parents=True, exist_ok=True)

# 4 trucos de búsqueda para forzar vertical
TRUCOS = [
    "pexels shorts {q}",
    "pexels {q} vertical",
]


def _buscar_ids(query, n=4):
    """Busca IDs de YouTube acumulando TODOS los trucos (sin duplicados)."""
    todos = []
    vistos = set()
    trucos_ok = []
    for truco in TRUCOS:
        q = truco.format(q=query)
        cmd = ["yt-dlp", f"ytsearch{n}:{q}", "--get-id", "--flat-playlist", "--no-warnings", "--socket-timeout", "10"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            ids = [l.strip() for l in res.stdout.splitlines() if l.strip()]
            nuevos = 0
            for vid in ids:
                if vid not in vistos:
                    vistos.add(vid)
                    todos.append(vid)
                    nuevos += 1
            if nuevos:
                trucos_ok.append(truco)
                print(f"[hack] '{truco}': +{nuevos} ids (total {len(todos)})", flush=True)
        except Exception:
            continue
    return todos, (trucos_ok[0] if trucos_ok else None)


def _es_vertical(path):
    """ffprobe: devuelve (ancho, alto) o None."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=15)
        parts = r.stdout.strip().split(",")
        if len(parts) >= 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return None


def _convertir_vertical(src, dst):
    """Crop FFmpeg: horizontal 16:9 → vertical 9:16 (centro)."""
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", "crop=ih*9/16:ih,scale=1080:1920:flags=lanczos,fps=30",
        "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p",
        "-an",
        str(dst)
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return dst.exists() and dst.stat().st_size > 100_000
    except Exception:
        return False


def descargar_vertical(query, max_clips=3):
    """Busca, descarga y fuerza vertical (crop si es horizontal)."""
    ids, truco = _buscar_ids(query, n=max_clips * 2)
    if not ids:
        return {"error": "sin resultados", "query": query}

    clips = []
    for vid_id in ids:
        if len(clips) >= max_clips:
            break
        out_tmpl = str(CACHE / f"v_{vid_id}.%(ext)s")
        fmt = "bv*[height<=1920][ext=mp4]+ba[ext=m4a]/b[height<=1920][ext=mp4]/b"
        cmd = [
            "yt-dlp", "-f", fmt, "--merge-output-format", "mp4",
            "-o", out_tmpl, "--no-playlist", "--no-warnings",
            "--max-filesize", "80M", "--socket-timeout", "15", "--fragment-retries", "2", "--socket-timeout", "15",
            f"https://www.youtube.com/watch?v={vid_id}"
        ]
        print(f"[hack] Descargando {vid_id}...", flush=True)
        try:
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        except Exception as e:
            print(f"[hack] Error {vid_id}: {e}", flush=True)
            continue

        raw = CACHE / f"v_{vid_id}.mp4"
        if not raw.exists() or raw.stat().st_size < 100_000:
            continue

        dims = _es_vertical(raw)
        if not dims:
            continue
        w, h = dims
        print(f"[hack] {vid_id}: {w}x{h}", flush=True)

        # ¿Ya es vertical?
        if h > w:
            final = CACHE / f"vert_{vid_id}.mp4"
            raw.rename(final)
            clips.append(str(final))
            print(f"[hack] OK vertical nativo ({final.stat().st_size//1024} KB)", flush=True)
        else:
            # Horizontal → crop a vertical
            final = CACHE / f"vert_{vid_id}_crop.mp4"
            if _convertir_vertical(raw, final):
                raw.unlink(missing_ok=True)
                clips.append(str(final))
                print(f"[hack] OK cropeado a 9:16 ({final.stat().st_size//1024} KB)", flush=True)
            else:
                raw.unlink(missing_ok=True)

    return {"clips": clips, "total": len(clips), "truco": truco, "query": query}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: stock_vertical_hack.py <query> [max_clips]")
        sys.exit(1)
    q = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    print(json.dumps(descargar_vertical(q, n), indent=2, ensure_ascii=False))
