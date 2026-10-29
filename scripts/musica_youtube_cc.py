"""musica_youtube_cc.py - Solo descarga tracks CC (sin analizar)."""
import subprocess, json, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_temp"
OUT.mkdir(parents=True, exist_ok=True)

def buscar_y_descargar(query, max_results=1):
    print(f"🔍 Buscando CC: '{query}'...")
    q = urllib.parse.quote(query)
    url_busqueda = f"https://www.youtube.com/results?search_query={q}&sp=EgIwAQ%253D%253D"
    
    cmd_ids = ["yt-dlp", url_busqueda, "--flat-playlist", "--print", "%(id)s|%(title)s|%(duration)s", "--playlist-end", "3", "--no-warnings", "--no-part", "--socket-timeout", "15", "--no-check-certificates", "--extractor-args", "youtube:skip=hls,dash"]
    try:
        r = subprocess.run(cmd_ids, capture_output=True, text=True, timeout=60)
        lineas = r.stdout.strip().splitlines()
    except: return []
    
    descargas = []
    for linea in lineas:
        partes = linea.split("|")
        if len(partes) < 3: continue
        vid_id, titulo, duracion = partes[0], partes[1], partes[2]
        try:
            dur = int(float(duracion))
            if dur < 180: continue  # minimo 3 min, sin maximo
        except: continue
        
        url_video = f"https://www.youtube.com/watch?v={vid_id}"
        cmd_info = ["yt-dlp", url_video, "--print", "%(license)s|%(uploader)s|%(description)s", "--skip-download", "--no-warnings"]
        r_info = subprocess.run(cmd_info, capture_output=True, text=True, timeout=30)
        if r_info.returncode != 0: continue
        info = r_info.stdout.strip().split("|")
        if len(info) < 2: continue
        licencia, uploader = info[0], info[1]
        _desc = info[2] if len(info) > 2 else ""
        _es_cc = ("Creative Commons" in licencia or "Creative Commons" in _desc or "CC BY" in _desc or "cc by" in _desc.lower() or "creative commons" in _desc.lower())
        if not _es_cc: continue
        
        print(f"  ✅ CC: {titulo[:40]}... ({dur}s)")
        nombre = f"yt_cc_{vid_id}.mp3"
        destino = OUT / nombre
        if not destino.exists():
            cmd_dl = ["yt-dlp", url_video, "-x", "--audio-format", "mp3", "--audio-quality", "5", "-o", str(destino.with_suffix("")), "--no-warnings", "--no-part", "--socket-timeout", "15", "--max-filesize", "150M"]
            subprocess.run(cmd_dl, capture_output=True, timeout=180)
        
        if destino.exists():
            descargas.append({"archivo": nombre, "titulo": titulo, "autor": uploader, "url": url_video, "licencia": licencia, "duracion": dur})
            print(f"  ✅ Descargado: {nombre}")
    return descargas

if __name__ == "__main__":
    todos = []
    for q in ["epic instrumental track", "cinematic soundtrack short"]:
        todos.extend(buscar_y_descargar(q, 1))
    (OUT / "index_musica_cc.json").write_text(json.dumps(todos, indent=2, ensure_ascii=False))
    print(f"\n✅ {len(todos)} pistas CC descargadas.")
