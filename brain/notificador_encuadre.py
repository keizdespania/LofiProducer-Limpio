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


# ═══════════════════════════════════════════════════════════
# HELPERS SEO + CROSS-TRAFFIC (flash5 telegram)
# ═══════════════════════════════════════════════════════════
_CROSS_URLS = {
    "web":      "https://elencuadre.pages.dev",
    "yt":       "https://youtube.com/@somoselencuadre.oficial",
    "tiktok":   "https://tiktok.com/@somoselencuadre",
    "ig":       "https://instagram.com/somoselencuadre",
    "x":        "https://x.com/SomosElEncuadre",
    "threads":  "https://threads.net/@somoselencuadre",
    "linkedin": "https://www.linkedin.com/in/somos-el-encuadre-undefined-62058a44a/",
    "telegram": "https://t.me/somoselencuadre",
}
_CROSS_HTML = (
    f'🌐 <a href="{_CROSS_URLS["web"]}">Web</a> · '
    f'▶️ <a href="{_CROSS_URLS["yt"]}">YouTube</a> · '
    f'📱 <a href="{_CROSS_URLS["tiktok"]}">TikTok</a> · '
    f'📷 <a href="{_CROSS_URLS["ig"]}">Instagram</a> · '
    f'🐦 <a href="{_CROSS_URLS["x"]}">X</a> · '
    f'🧵 <a href="{_CROSS_URLS["threads"]}">Threads</a> · '
    f'💼 <a href="{_CROSS_URLS["linkedin"]}">LinkedIn</a> · '
    f'📩 <a href="{_CROSS_URLS["telegram"]}">Telegram</a>'
)

def _extraer_tecnicas_cortas(fecha, max_items=3):
    """Extrae técnicas cortas (tag-like, <40 chars) del dossier enriquecido."""
    import json as _j, pathlib as _p
    _root = _p.Path(__file__).resolve().parent.parent
    p = _root / "output" / "encuadre" / f"dossier_{fecha}_enriquecido.json"
    if not p.exists(): return ""
    try:
        d = _j.loads(p.read_text()).get("dossier") or {}
    except: return ""
    tecnicas = d.get("tecnicas_manipulacion") or []
    if isinstance(tecnicas, str): tecnicas = [tecnicas]
    vistos = set(); cortas = []
    for tt in tecnicas:
        if not isinstance(tt, str): continue
        tt = tt.strip()
        if not tt or len(tt) > 40: continue
        key = tt.lower()
        if key in vistos: continue
        vistos.add(key); cortas.append(key)
        if len(cortas) >= max_items: break
    return ", ".join(cortas)

def _acortar_smart(texto, max_chars):
    """Corta en último . ! ? dentro del rango, o en palabra + elipsis."""
    texto = (texto or "").strip()
    if len(texto) <= max_chars: return texto
    minimo = int(max_chars * 0.6)
    mejor = -1
    for ch in ".!?":
        pos = texto.rfind(ch, minimo, max_chars)
        if pos > mejor: mejor = pos
    if mejor >= minimo:
        return texto[:mejor+1].strip()
    corte = texto[:max_chars].rstrip()
    sp = corte.rfind(' ')
    return (corte[:sp] if sp > minimo else corte).rstrip('.,;:') + "…"

# ═══════════════════════════════════════════════════════════

def _escapar(texto):
    if not texto: return ""
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

# ═══════════════════════════════════════════════════════════
# CONTENIDO → CANAL PÚBLICO
# ═══════════════════════════════════════════════════════════

def publicar_analisis(titulo, slug, resumen="", url_fuente="", nicho="el_encuadre", imagen=None):
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"📰 <b>NUEVO ARTÍCULO</b>\n\n"
    msg += f"<b>{_escapar(titulo[:180])}</b>\n\n"
    if resumen:
        msg += f"{_escapar(_acortar_smart(resumen, 240))}\n\n"
    msg += f"🔗 <b>Leer completo:</b> {url}\n"
    if url_fuente:
        msg += f"📎 <b>Fuente:</b> {url_fuente}\n"
    msg += f"\n{_CROSS_HTML}"
    return _canal(msg, throttle_override=1)

def publicar_dossier(titulo, slug, resumen="", url_fuente=""):
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"📁 <b>DOSSIER DEL DÍA</b>\n\n"
    msg += f"<b>{_escapar(titulo[:180])}</b>\n\n"
    if resumen:
        msg += f"{_escapar(_acortar_smart(resumen, 240))}\n\n"
    msg += f"🔗 <b>Dossier completo:</b> {url}\n"
    msg += f"\n{_CROSS_HTML}"
    return _canal(msg, throttle_override=1)

def publicar_short(titulo, url_youtube=None, url_tiktok=None):
    msg = f"📱 <b>Nuevo short</b>\n\n<b>{_escapar(titulo[:200])}</b>"
    if url_youtube: msg += f"\n\n▶️ YouTube: {url_youtube}"
    if url_tiktok: msg += f"\n🎵 TikTok: {url_tiktok}"
    return _canal(msg)



def publicar_mediano(titulo, slug, tecnicas=""):
    """Análisis técnico (mediano) al canal público. SEO + cross-traffic."""
    url = f"https://elencuadre.pages.dev/analisis/{slug}/"
    msg = f"🔍 <b>ANÁLISIS TÉCNICO</b>\n\n"
    msg += f"<b>{_escapar(titulo[:180])}</b>\n\n"
    if tecnicas:
        msg += f"📖 <b>Técnicas analizadas:</b> {_escapar(tecnicas)}\n\n"
    msg += f"🔗 <b>Leer:</b> {url}\n\n"
    msg += _CROSS_HTML
    return _canal(msg, throttle_override=1)


def publicar_podcast(titulo, url):
    msg = f"🎧 <b>Podcast del día</b>\n\n<b>{_escapar(titulo[:200])}</b>\n\n▶️ {url}"
    return _canal(msg)

def publicar_programacion(tipo, titulo, cuando, url_yt="", url_post="", url_largo="", num=None, fecha="", tecnicas=""):
    """Notifica al canal @somoselencuadre la programación de un vídeo/short.
    Sin throttle (permite ráfaga). Dedupe por (tipo+fecha+num). SEO + cross-traffic.
    """
    import datetime as _dt
    from notificador_top1 import _debe_enviar, _post, CANAL_PUBLICO

    hora_str = cuando.strftime("%H:%M") if isinstance(cuando, _dt.datetime) else str(cuando)
    dedupe = f"prog_{tipo}_{fecha}_{num or 0}"

    if tipo == "largo":
        msg = f"🎬 <b>HOY {hora_str} · El Encuadre</b>\n\n"
        msg += f"<b>{_escapar(titulo[:180])}</b>\n\n"
        if tecnicas: msg += f"🔍 <b>Técnicas:</b> {_escapar(tecnicas)}\n\n"
        if url_yt:   msg += f"▶️ <b>Vídeo:</b> {url_yt}\n"
        if url_post: msg += f"📄 <b>Análisis:</b> {url_post}\n"
        msg += f"\n{_CROSS_HTML}"
    elif tipo == "short":
        msg = f"📱 <b>HOY {hora_str} · Short {num}</b>\n\n"
        msg += f"{_escapar(_acortar_smart(titulo, 160))}\n\n"
        if url_largo: msg += f"🎬 <b>Largo:</b> {url_largo}\n"
        if url_yt:    msg += f"📊 <b>Short:</b> {url_yt}\n"
        msg += f"\n{_CROSS_HTML}"
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
