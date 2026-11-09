"""notificador_encuadre.py v2 - Wrapper thin sobre notificador_top1.
Mantiene la API pública idéntica. Cambia internals:
  - publicar_* → CANAL público (@somoselencuadre)
  - avisar_* / completado → CHAT privado (alertas)
Cero spam. Throttle automático.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from notificador_top1 import (
    publicar_canal as _canal,
    canal_nuevo_video as _canal_video,
    alerta as _alerta,
    resumen_diario as _resumen,
    info_tecnica as _info,
    _post, TOKEN,
)

def _escapar(texto):
    if not texto: return ""
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

# ═══════════════════════════════════════════════════════════
# CONTENIDO → CANAL PÚBLICO
# ═══════════════════════════════════════════════════════════

def publicar_analisis(titulo, slug, resumen="", url_fuente="", nicho="el_encuadre", imagen=None):
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"📰 <b>Nuevo análisis</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if resumen:
        msg += f"\n\n{_escapar(resumen[:300])}"
    msg += f"\n\n🔗 {url}"
    if url_fuente:
        msg += f"\n📎 Fuente: {url_fuente}"
    return _canal(msg)

def publicar_dossier(titulo, slug, resumen="", url_fuente=""):
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"📁 <b>Dossier del día</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if resumen:
        msg += f"\n\n{_escapar(resumen[:300])}"
    msg += f"\n\n🔗 {url}"
    return _canal(msg)

def publicar_short(titulo, url_youtube=None, url_tiktok=None):
    msg = f"📱 <b>Nuevo short</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if url_youtube: msg += f"\n\n▶️ YouTube: {url_youtube}"
    if url_tiktok: msg += f"\n🎵 TikTok: {url_tiktok}"
    return _canal(msg)

def publicar_podcast(titulo, url):
    msg = f"🎧 <b>Podcast del día</b>\n\n<b>{_escapar(titulo[:200])}</b>\n\n▶️ {url}"
    return _canal(msg)

# ═══════════════════════════════════════════════════════════
# ALERTAS → CHAT PRIVADO
# ═══════════════════════════════════════════════════════════

def publicar_pipeline_completado(n_analisis, n_shorts, n_posts, metrics=None):
    msg = f"✅ <b>Pipeline completado</b>\n\n"
    msg += f"• {n_analisis} análisis\n• {n_shorts} shorts\n• {n_posts} posts"
    if metrics:
        msg += f"\n\n📊 {metrics}"
    return _resumen(msg)

def avisar_videos_privados(videos):
    if not videos: return False
    msg = "🎬 <b>Vídeos privados listos para revisar</b>\n\n"
    for v in videos[:5]:
        titulo = (v.get("titulo") or "")[:60]
        vid = v.get("video_id", "")
        tipo = v.get("tipo", "video")
        msg += f"• [{tipo}] <b>{_escapar(titulo)}</b>\n  https://youtu.be/{vid}\n"
    return _alerta("videos_privados", msg, nivel="info")

# ═══════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════

def test():
    r1 = _canal("🧪 Test canal público (contenido)")
    r2 = _alerta("test_notif", "🧪 Test chat privado (alerta)", nivel="info")
    return {"canal": r1, "privado": r2}
