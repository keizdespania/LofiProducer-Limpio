"""notificador_encuadre.py - Publica análisis de El Encuadre en el canal de Telegram."""
import json, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def _env(k):
    for l in (ROOT/".env").read_text().splitlines():
        if l.startswith(k+"="):
            return l.split("=",1)[1].strip().strip('"').strip("'")
    return ""

def _post(method, data):
    token = _env("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"ok": False, "error": "Sin TELEGRAM_BOT_TOKEN"}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode(),
            headers={"Content-Type":"application/json"}, method="POST")
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()[:200]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _canal_id():
    return _env("TELEGRAM_CHANNEL_ID")

def _escapar(texto):
    """Escapa Markdown V2 (más estricto, pero el Markdown clásico basta)."""
    # Usamos Markdown clásico, no V2. Solo escapar _ * [ ] ( ) ~ ` > # + - = | { } . !
    return texto

def publicar_analisis(titulo, slug, resumen="", url_fuente="", nicho="el_encuadre", imagen=None):
    """Publica un análisis nuevo en el canal con formato bonito + botón."""
    cid = _canal_id()
    if not cid:
        return {"ok": False, "error": "Sin TELEGRAM_CHANNEL_ID"}

    url_analisis = f"https://elencuadre.pages.dev/analisis/{slug}/"

    # Mensaje con formato
    texto = f"📰 *{titulo}*\n\n"
    if resumen:
        texto += f"{resumen[:400]}\n\n"
    texto += f"📅 {_fecha_hoy()}\n"
    texto += f"#ElEncuadre #Análisis"

    # Botones inline
    botones = [[
        {"text": "🔗 Leer análisis", "url": url_analisis}
    ]]
    if url_fuente:
        botones[0].append({"text": "📎 Noticia original", "url": url_fuente})

    data = {
        "chat_id": cid,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
        "reply_markup": json.dumps({"inline_keyboard": botones})
    }

    # Si hay imagen, usar sendPhoto en vez de sendMessage
    if imagen:
        data["photo"] = imagen
        data["caption"] = texto
        return _post("sendPhoto", data)
    else:
        return _post("sendMessage", data)

def publicar_dossier(titulo, slug, resumen="", url_fuente=""):
    """Publica el dossier ejecutivo del día."""
    cid = _canal_id()
    url_analisis = f"https://elencuadre.pages.dev/analisis/{slug}/"
    texto = f"📁 *DOSSIER EJECUTIVO*\n*{titulo}*\n\n"
    if resumen: texto += f"{resumen[:300]}\n\n"
    texto += f"📅 {_fecha_hoy()}\n\n#ElEncuadre #Dossier"
    botones = [[{"text": "📁 Leer dossier", "url": url_analisis}]]
    if url_fuente:
        botones[0].append({"text": "📎 Fuente", "url": url_fuente})
    return _post("sendMessage", {
        "chat_id": cid, "text": texto, "parse_mode": "Markdown",
        "reply_markup": json.dumps({"inline_keyboard": botones})
    })

def publicar_short(titulo, url_youtube=None, url_tiktok=None):
    """Avisa de un short nuevo."""
    cid = _canal_id()
    texto = f"🎬 *Short nuevo*\n*{titulo}*\n\n📅 {_fecha_hoy()}\n\n#Shorts #ElEncuadre"
    botones = []
    if url_youtube: botones.append({"text": "▶️ YouTube", "url": url_youtube})
    if url_tiktok: botones.append({"text": "📱 TikTok", "url": url_tiktok})
    data = {"chat_id": cid, "text": texto, "parse_mode": "Markdown"}
    if botones: data["reply_markup"] = json.dumps({"inline_keyboard": [botones]})
    return _post("sendMessage", data)

def publicar_podcast(titulo, url):
    """Avisa de un podcast nuevo."""
    cid = _canal_id()
    texto = f"🎙️ *Podcast del día*\n*{titulo}*\n\n📅 {_fecha_hoy()}\n\n#Podcast #ElEncuadre"
    return _post("sendMessage", {
        "chat_id": cid, "text": texto, "parse_mode": "Markdown",
        "reply_markup": json.dumps({"inline_keyboard": [[{"text": "🎧 Escuchar", "url": url}]]})
    })

def publicar_pipeline_completado(n_analisis, n_shorts, n_posts):
    """Mensaje resumen tras pipeline completo."""
    cid = _canal_id()
    texto = (
        f"✅ *Pipeline del día completado*\n\n"
        f"📰 {n_analisis} análisis publicados\n"
        f"🎬 {n_shorts} shorts generados\n"
        f"📝 {n_posts} posts web\n\n"
        f"🔗 [Ver todo en elencuadre.com](https://elencuadre.pages.dev/analisis/)\n\n"
        f"#ElEncuadre #ProduccionDiaria"
    )
    return _post("sendMessage", {
        "chat_id": cid, "text": texto, "parse_mode": "Markdown",
        "disable_web_page_preview": True
    })

def _fecha_hoy():
    from datetime import date
    return date.today().isoformat()



def avisar_videos_privados(videos):
    """Avisa por Telegram de vídeos subidos en privado. HTML robusto."""
    cid = _env("TELEGRAM_CHAT_ID")
    if not cid:
        print("⚠️ Sin TELEGRAM_CHAT_ID")
        return {"ok": False}
    if not videos:
        return {"ok": True}

    def esc(t):
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    lineas = ["🎬 <b>Vídeos subidos en PRIVADO</b>\n"]
    lineas.append("La API de YouTube no está auditada. Publica manualmente:\n")
    botones = []
    for v in videos:
        vid = v.get("video_id")
        titulo = esc(v.get("titulo", "Sin título")[:50])
        tipo = esc(v.get("tipo", "video"))
        lineas.append(f"• <b>{tipo}</b>: {titulo}")
        if vid:
            botones.append([{
                "text": f"📺 Abrir {v.get('tipo', 'video')} en Studio",
                "url": f"https://studio.youtube.com/video/{vid}/edit"
            }])
    lineas.append("\n👉 Toca un botón para publicar en 1 minuto.")

    data = {
        "chat_id": cid,
        "text": "\n".join(lineas),
        "parse_mode": "HTML",
    }
    if botones:
        data["reply_markup"] = json.dumps({"inline_keyboard": botones})
    return _post("sendMessage", data)


def test():
    """Envía un mensaje de test al canal."""
    cid = _canal_id()
    if not cid:
        print("❌ Sin TELEGRAM_CHANNEL_ID")
        return
    r = _post("sendMessage", {
        "chat_id": cid,
        "text": "🧪 *Test del notificador*\n\nSi ves esto, todo funciona.\n\n#ElEncuadre",
        "parse_mode": "Markdown"
    })
    print("✅ Test enviado" if r.get("ok") else f"❌ {r}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test()
    else:
        print("Uso: python3 brain/notificador_encuadre.py test")
