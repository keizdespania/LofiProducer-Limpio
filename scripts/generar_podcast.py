"""generar_podcast.py - Mezcla voz + musica (WAV intermedio) y publica MP3 en web/docs/podcast/."""
import sys, pathlib, subprocess, datetime, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
PODCAST = ROOT / "web" / "docs" / "podcast"
PODCAST.mkdir(parents=True, exist_ok=True)
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

def _buscar_voz():
    candidatos = [OUT / f"voz_largo_{FECHA}.mp3", OUT / "voz_largo.mp3"]
    for c in candidatos:
        if c.exists() and c.stat().st_size > 10000:
            return c
    todos = sorted(OUT.glob("voz_largo*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    return todos[0] if todos else None

def _buscar_musica():
    c = ROOT / "output" / "musica_temp" / "lofi_base.mp3"
    if c.exists() and c.stat().st_size > 100000:
        return c
    return None

def _duracion(archivo):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(archivo)],
        capture_output=True, text=True, timeout=30
    )
    try:
        return float(r.stdout.strip())
    except:
        return 0.0

def _mezclar_wav(voz, musica, wav_temp):
    """Paso 1: mezclar voz + musica en WAV PCM (sin compresion)."""
    dur = _duracion(voz)
    if dur <= 0:
        raise Exception(f"No puedo leer duracion de {voz}")
    print(f"   Duracion voz: {dur:.1f}s ({dur/60:.1f} min)")
    filtro = (
        "[0:a]aresample=44100,volume=1.0[voz];"
        "[1:a]aresample=44100,volume=0.15[musica];"
        "[voz][musica]amix=inputs=2:duration=first:normalize=0[out]"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(voz),
        "-i", str(musica),
        "-filter_complex", filtro,
        "-map", "[out]",
        "-c:a", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        "-t", f"{dur:.2f}",
        str(wav_temp)
    ]
    subprocess.run(cmd, check=True, timeout=600)

def _wav_a_mp3(wav_temp, mp3_final):
    """Paso 2: convertir WAV a MP3 (una sola entrada, timestamps limpios)."""
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(wav_temp),
        "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "2",
        "-metadata", f"title=El Encuadre - {FECHA}",
        "-metadata", "artist=Somos El Encuadre",
        "-metadata", "album=El Encuadre",
        "-metadata", f"date={FECHA[:4]}",
        "-metadata", "genre=Podcast",
        str(mp3_final)
    ]
    subprocess.run(cmd, check=True, timeout=600)

def _regenerar_index():
    episodios = sorted(PODCAST.glob("*.mp3"), key=lambda p: p.stem, reverse=True)
    if not episodios:
        return
    meses = {"01":"enero","02":"febrero","03":"marzo","04":"abril","05":"mayo","06":"junio","07":"julio","08":"agosto","09":"septiembre","10":"octubre","11":"noviembre","12":"diciembre"}
    items_html = []
    for ep in episodios:
        fecha_str = ep.stem
        try:
            anio, mes, dia = fecha_str.split("-")
            fecha_legible = f"{int(dia)} de {meses.get(mes, mes)} de {anio}"
        except:
            fecha_legible = fecha_str
        tamano_mb = ep.stat().st_size / (1024 * 1024)
        dur_min = _duracion(ep) / 60
        item = ""
        item += "  <div class=\"holo-card\" style=\"cursor: default;\">\n"
        item += "    <div class=\"holo-badge badge-new\">Episodio</div>\n"
        item += f"    <h3>El Encuadre - {fecha_legible}</h3>\n"
        item += "    <p>Analisis del dia en audio. Voz de Alvaro + musica CC0 de fondo.</p>\n"
        item += "    <div style=\"background: rgba(0,0,0,0.5); padding: 12px; border-radius: 8px; border: 1px solid rgba(0, 240, 255, 0.2); margin-bottom: 1rem;\">\n"
        item += f"      <audio controls preload=\"none\" style=\"width: 100%;\"><source src=\"{ep.name}\" type=\"audio/mpeg\"></audio>\n"
        item += "    </div>\n"
        item += "    <div class=\"holo-meta\">\n"
        item += f"      <span>{dur_min:.0f} min | {tamano_mb:.1f} MB</span>\n"
        item += f"      <a href=\"{ep.name}\" download style=\"color: var(--holo-cyan); text-decoration: none;\">Descargar</a>\n"
        item += "    </div>\n"
        item += "  </div>\n"
        items_html.append(item)
    contenido = ""
    contenido += "---\nhide:\n  - navigation\n---\n\n"
    contenido += "<div class=\"holo-hero\">\n"
    contenido += "  <h1>El Podcast del Encuadre</h1>\n"
    contenido += "  <p>Los analisis diarios en formato audio. Voz de Alvaro + musica CC0.</p>\n"
    contenido += "</div>\n\n"
    contenido += f"<p style=\"text-align:center;color:#888;\"><b>{len(episodios)} episodios</b></p>\n\n"
    contenido += "<div class=\"holo-grid\">\n"
    contenido += "".join(items_html)
    contenido += "</div>\n"
    (PODCAST / "index.md").write_text(contenido)

def main(fecha=None):
    fecha = fecha or FECHA
    print(f"Generando podcast para {fecha}...")
    print("=" * 60)
    voz = _buscar_voz()
    if not voz:
        print("ERROR: no hay voz_largo_*.mp3")
        return False
    musica = _buscar_musica()
    if not musica:
        print("ERROR: no hay lofi_base.mp3")
        return False
    print(f"Voz:    {voz.name} ({voz.stat().st_size//1024//1024}MB)")
    print(f"Musica: {musica.name} ({musica.stat().st_size//1024//1024}MB)")
    wav_temp = OUT / f"_temp_podcast_{fecha}.wav"
    mp3_final = PODCAST / f"{fecha}.mp3"
    try:
        print("[1/2] Mezclando a WAV...")
        _mezclar_wav(voz, musica, wav_temp)
        if not wav_temp.exists() or wav_temp.stat().st_size < 1000000:
            print("ERROR: WAV vacio o corrupto")
            return False
        print(f"   WAV generado: {wav_temp.stat().st_size//1024//1024}MB")
        print("[2/2] Convirtiendo a MP3...")
        _wav_a_mp3(wav_temp, mp3_final)
    except subprocess.CalledProcessError as e:
        print(f"ERROR FFmpeg: {e}")
        return False
    except subprocess.TimeoutExpired:
        print("ERROR FFmpeg timeout")
        return False
    finally:
        if wav_temp.exists():
            wav_temp.unlink()
            print("   WAV temporal eliminado")
    if not mp3_final.exists() or mp3_final.stat().st_size < 100000:
        print("ERROR: MP3 vacio o corrupto")
        return False
    print(f"OK MP3: {mp3_final.name} ({mp3_final.stat().st_size//1024//1024}MB)")
    _regenerar_index()
    print("OK index.md actualizado")
    out_podcast = OUT / "podcast"
    out_podcast.mkdir(exist_ok=True)
    (out_podcast / f"{fecha}.mp3").write_bytes(mp3_final.read_bytes())
    (out_podcast / "index.md").write_text((PODCAST / "index.md").read_text())
    print("OK copia en output/encuadre/podcast/")
    print("=" * 60)
    print(f"PODCAST {fecha} OK")
    return True

if __name__ == "__main__":
    ok = main(sys.argv[1] if len(sys.argv) > 1 else None)
    sys.exit(0 if ok else 1)