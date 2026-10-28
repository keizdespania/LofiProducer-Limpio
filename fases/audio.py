"""
Cajon 15 - Descarga de audio real desde CCMixter (v2 - Bypass 403).
"""
from __future__ import annotations
import random
from pathlib import Path
from urllib.parse import quote
import requests
from core.config import OUTPUT_DIR
from core.logger import get_logger

log = get_logger("fases.audio")
AUDIO_DIR = OUTPUT_DIR / "audio_real"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Mascara de navegador para evitar el bloqueo 403 de CCMixter
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://ccmixter.org/",
    "Accept": "*/*",
}
def descargar_audio_ccmixter(tags: str = "lofi,chill", limite: int = 5) -> Path | None:
    log.info("Buscando audio real en CCMixter con tags: %s", tags)
    tags_query = quote(tags.replace(",", "+"))
    url_api = f"http://ccmixter.org/api/query?f=json&limit={limite}&tags={tags_query}&lic=open"

    try:
        # Añadimos HEADERS también aquí por si acaso
        resp = requests.get(url_api, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        tracks = resp.json()
    except Exception as e:
        log.error("Error consultando CCMixter: %s", e)
        return None

    if not tracks:
        log.warning("CCMixter no devolvio resultados.")
        return None

    random.shuffle(tracks)

    for track in tracks:
        nombre = track.get("upload_name", "Desconocido")
        autor = track.get("user_name", "Desconocido")
        archivos = track.get("files", [])
        mp3_info = next((f for f in archivos if f.get("file_nicname") == "mp3"), None)

        if not mp3_info:
            continue

        url_mp3 = mp3_info.get("download_url")
        if not url_mp3:
            continue

        ruta_destino = AUDIO_DIR / f"ccmixter_{track['upload_id']}.mp3"
        if ruta_destino.exists() and ruta_destino.stat().st_size > 100_000:
            log.info("Audio ya en local: %s", ruta_destino.name)
            return ruta_destino

        log.info("Descargando: '%s' por %s", nombre, autor)
        try:
            # AQUI ESTA LA MAGIA: pasamos los HEADERS en la descarga
            with requests.get(url_mp3, headers=HEADERS, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(ruta_destino, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            if ruta_destino.stat().st_size < 100_000:
                ruta_destino.unlink()
                continue

            log.info("Audio OK: %s", ruta_destino.name)
            return ruta_destino
        except Exception as e:
            log.warning("Fallo al descargar %s: %s", url_mp3, e)
            continue

    return None

if __name__ == "__main__":
    ruta = descargar_audio_ccmixter("lofi,chill")
    if ruta:
        print(f"\n[OK] Audio listo en: {ruta}")
    else:
        print("\n[!] Fallo la descarga.")
