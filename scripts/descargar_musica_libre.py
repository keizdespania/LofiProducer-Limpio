import os, json, urllib.request, urllib.parse, random, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "musica_libre"
OUT.mkdir(parents=True, exist_ok=True)

def _cargar_env():
    env = {}
    for l in (ROOT / ".env").read_text().splitlines():
        if "=" in l and not l.startswith("#"):
            k,v = l.split("=",1); env[k.strip()] = v.strip()
    return env

def elegir_musica_por_texto(texto_post, env):
    """El Dios lee el post y elige el mood."""
    texto = texto_post.lower()
    if any(w in texto for w in ["guerra", "crisis", "peligro", "alarma", "conflicto"]):
        mood = "dark tension cinematic"
    elif any(w in texto for w in ["futuro", "tecnologia", "ia", "datos", "robot"]):
        mood = "electronic synth futuristic"
    elif any(w in texto for w in ["analisis", "sesgo", "encuadre", "noticia"]):
        mood = "documentary thoughtful"
    else:
        mood = "ambient chill"
    print(f"[musica] Mood elegido por Dios: {mood}")
    return mood

def descargar_pixabay(query, env):
    key = env.get("PIXABAY_API_KEY")
    if not key: return None
    url = f"https://pixabay.com/api/audio/?key={key}&q={urllib.parse.quote(query)}&per_page=10"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        hits = data.get("hits", [])
        if hits:
            hit = random.choice(hits)
            return hit.get("audio"), f"Pixabay - {hit.get('tags')}"
    except: pass
    return None, None

def descargar_fma(query, env):
    """Free Music Archive: búsqueda pública vía API web."""
    url = f"https://freemusicarchive.org/api/get/tracks.json?q={urllib.parse.quote(query)}&limit=5"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = json.loads(urllib.request.urlopen(req, timeout=15).read())
        if data.get("dataset"):
            track = random.choice(data["dataset"])
            return track.get("track_file_url"), f"FMA - {track.get('track_title')} by {track.get('artist_name')}"
    except: pass
    return None, None

def descargar_youtube_audiolib(env):
    """YouTube Audio Library: solo si hay fallback manual (no API pública)."""
    return None, None

def descargar(texto_post=""):
    env = _cargar_env()
    mood = elegir_musica_por_texto(texto_post, env)
    
    # 1. Intentar Pixabay
    audio_url, atribucion = descargar_pixabay(mood, env)
    # 2. Fallback a FMA
    if not audio_url:
        audio_url, atribucion = descargar_fma(mood, env)
    
    if not audio_url:
        print("⚠️  No se encontró música libre. Se usará silencio.")
        return None

    destino = OUT / f"libre_{int(random.random()*10000)}.mp3"
    try:
        urllib.request.urlretrieve(audio_url, destino)
        print(f"✅ Música descargada: {destino.name}")
        with open(OUT / "atribucion.txt", "a") as f:
            f.write(f"{atribucion}\n")
        return destino
    except Exception as e:
        print(f"❌ Error descargando: {e}")
        return None

if __name__ == "__main__":
    import sys
    texto = sys.argv[1] if len(sys.argv) > 1 else ""
    descargar(texto)
