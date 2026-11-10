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
    return _canal(msg, throttle_override=1)

def publicar_dossier(titulo, slug, resumen="", url_fuente=""):
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"📁 <b>Dossier del día</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if resumen:
        msg += f"\n\n{_escapar(resumen[:300])}"
    msg += f"\n\n🔗 {url}"
    return _canal(msg, throttle_override=1)

def publicar_short(titulo, url_youtube=None, url_tiktok=None):
    msg = f"📱 <b>Nuevo short</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if url_youtube: msg += f"\n\n▶️ YouTube: {url_youtube}"
    if url_tiktok: msg += f"\n🎵 TikTok: {url_tiktok}"
    return _canal(msg)

def publicar_podcast(titulo, url):
    msg = f"🎧 <b>Podcast del día</b>\n\n<b>{_escapar(titulo[:200])}</b>\n\n▶️ {url}"
    return _canal(msg)

def publicar_programacion(tipo, titulo, cuando, url_yt="", url_post="", url_largo="", num=None, fecha=""):
    """Notifica al canal @somoselencuadre la programación de un vídeo/short.
    Sin throttle (permite ráfaga de programaciones). Dedupe por (tipo+fecha+num)
    para evitar duplicados si el pipeline se relanza.
    tipo: 'largo' | 'short'
    cuando: datetime con la hora de publicación
    """
    import datetime as _dt
    from notificador_top1 import _debe_enviar, _post, CANAL_PUBLICO

    hora_str = cuando.strftime("%H:%M") if isinstance(cuando, _dt.datetime) else str(cuando)
    dedupe = f"prog_{tipo}_{fecha}_{num or 0}"

    if tipo == "largo":
        msg = f"🎬 <b>HOY {hora_str} · El Encuadre</b>\n\n"
        msg += f"<b>{_escapar(titulo[:200])}</b>\n\n"
        if url_yt:   msg += f"▶️ Ver: {url_yt}\n"
        if url_post: msg += f"📄 Análisis: {url_post}\n"
        msg += f"\n💬 @somoselencuadre"
    elif tipo == "short":
        msg = f"📱 <b>HOY {hora_str} · Short {num}</b>\n\n"
        msg += f"{_escapar(titulo[:200])}\n\n"
        if url_yt:    msg += f"▶️ Ver: {url_yt}\n"
        if url_largo: msg += f"🎬 Análisis: {url_largo}\n"
        msg += f"\n💬 @somoselencuadre"
    else:
        return False

    return _debe_enviar("canal_prog", CANAL_PUBLICO, dedupe_key=dedupe, throttle_override=1) and _post(CANAL_PUBLICO, msg)


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
