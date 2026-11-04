"""notificar_resumen_dia.py - Lee todos los JSON del día + verifica outputs reales,
construye métricas y envía resumen rico a Telegram.

Uso: python3 scripts/notificar_resumen_dia.py [fecha]
"""
import json, pathlib, subprocess, sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))
sys.path.insert(0, str(ROOT / "scripts"))

OUT = ROOT / "output" / "encuadre"
PODCAST = ROOT / "web" / "docs" / "podcast"
DATA = ROOT / "data" / "agent"

FECHA = sys.argv[1] if len(sys.argv) > 1 else date.today().isoformat()


def _duracion_seg(path):
    """Duración en segundos vía ffprobe. 0 si falla."""
    if not path.exists():
        return 0.0
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0.0


def _cargar_json(path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _contar_video_largo():
    """Devuelve (existe, duracion_min)."""
    p = OUT / f"video_largo_{FECHA}.mp4"
    if not p.exists():
        return False, 0.0
    dur = _duracion_seg(p) / 60.0
    return True, round(dur, 1)


def _contar_shorts():
    """Devuelve (n_mp4, total_bytes)."""
    shorts = sorted(OUT.glob(f"short_*_{FECHA}.mp4"))
    shorts = [s for s in shorts if "_with_logo" not in s.name]  # excluir temporales
    total = sum(s.stat().st_size for s in shorts)
    return len(shorts), total


def _info_podcast():
    """Devuelve (existe, duracion_min, size_mb)."""
    p = PODCAST / f"{FECHA}.mp3"
    if not p.exists():
        return False, 0.0, 0.0
    dur_min = _duracion_seg(p) / 60.0
    size_mb = p.stat().st_size / 1024 / 1024
    return True, round(dur_min, 1), round(size_mb, 1)


def _youtube_urls():
    """Lee data/agent/youtube_urls_{fecha}.json si existe."""
    p = DATA / f"youtube_urls_{FECHA}.json"
    return _cargar_json(p, {})


def _contar_seo_capitulos(seo):
    """Cuenta capítulos del SEO mirando la descripción."""
    if not seo:
        return 0
    desc = seo.get("largo", {}).get("descripcion", "")
    return desc.count("🟠") + desc.count("🟡") + desc.count("🔴") + desc.count("🟤")


def _contar_redes_bloques(redes):
    """Cuenta bloques con LLM vs total."""
    if not redes:
        return 0
    shorts = redes.get("shorts", [])
    if not shorts:
        return 0
    return len(shorts) * 6  # 6 redes por short


def main():
    print(f"[resumen] Generando resumen del {FECHA}")

    prod = _cargar_json(OUT / f"produccion_{FECHA}.json", {})
    seo = _cargar_json(OUT / f"seo_{FECHA}.json", {})
    redes = _cargar_json(OUT / f"redes_{FECHA}.json", {})
    yt = _youtube_urls()

    # Métricas del monólogo
    texto = prod.get("texto_voz_largo", "")
    palabras = len(texto.split())
    escenas = prod.get("escenas", [])
    shorts_finales = prod.get("shorts_finales", [])

    # Vídeo + shorts + podcast (real en disco)
    video_existe, dur_video_min = _contar_video_largo()
    n_shorts_mp4, shorts_bytes = _contar_shorts()
    podcast_existe, pod_min, pod_mb = _info_podcast()

    # SEO + redes
    n_capitulos = _contar_seo_capitulos(seo)
    n_bloques_redes = _contar_redes_bloques(redes)

    # YouTube URLs
    yt_largo = yt.get("largo", "")
    yt_shorts = yt.get("shorts", [])

    # Título del vídeo
    titulo = seo.get("largo", {}).get("titulo", "Análisis del día")

    # Warnings: cosas que faltan
    warnings = []
    if not video_existe:
        warnings.append("Vídeo largo NO generado")
    if n_shorts_mp4 < 4:
        warnings.append(f"Solo {n_shorts_mp4}/4 shorts renderizados")
    if not podcast_existe:
        warnings.append("Podcast NO generado")
    if not yt_largo:
        warnings.append("Vídeo largo NO subido a YouTube")
    if len(yt_shorts) < 4:
        warnings.append(f"Solo {len(yt_shorts)}/4 shorts subidos a YT")
    if n_capitulos < 2:
        warnings.append("SEO sin capítulos")
    if not escenas:
        warnings.append("Producción sin escenas")

    metrics = {
        "fecha": FECHA,
        "titulo_video": titulo,
        "palabras": palabras,
        "escenas": len(escenas),
        "duracion_video_min": dur_video_min,
        "n_shorts_mp4": n_shorts_mp4,
        "shorts_mb": round(shorts_bytes / 1024 / 1024, 1),
        "podcast_min": pod_min,
        "podcast_mb": pod_mb,
        "n_capitulos": n_capitulos,
        "n_redes_bloques": n_bloques_redes,
        "yt_largo_url": yt_largo,
        "yt_shorts_urls": yt_shorts,
        "warnings": warnings,
    }

    # Print para log
    print(f"[resumen] Palabras: {palabras}")
    print(f"[resumen] Vídeo: {'OK' if video_existe else 'NO'} ({dur_video_min} min)")
    print(f"[resumen] Shorts: {n_shorts_mp4}/4")
    print(f"[resumen] Podcast: {'OK' if podcast_existe else 'NO'} ({pod_min} min, {pod_mb} MB)")
    print(f"[resumen] SEO capítulos: {n_capitulos}")
    print(f"[resumen] Redes bloques: {n_bloques_redes}")
    print(f"[resumen] YouTube largo: {yt_largo or '(no subido)'}")
    print(f"[resumen] YouTube shorts: {len(yt_shorts)}")
    if warnings:
        print(f"[resumen] ⚠️ Warnings: {len(warnings)}")
        for w in warnings:
            print(f"  · {w}")

    # Enviar Telegram
    try:
        from notificador_encuadre import publicar_pipeline_completado
        r = publicar_pipeline_completado(
            n_analisis=len(escenas) if escenas else 0,
            n_shorts=n_shorts_mp4,
            n_posts=0,  # se actualiza con pub_count del pipeline
            metrics=metrics,
        )
        if r.get("ok"):
            print(f"✅ Resumen enviado a Telegram")
            return True
        else:
            print(f"⚠️ Telegram: {r.get('error', 'desconocido')}")
            return False
    except Exception as e:
        print(f"❌ Error Telegram: {e}")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
