"""notificador_top1.py - Sistema centralizado de notificaciones Telegram.
Separación estricta:
  - ALERTAS TÉCNICAS → chat privado del usuario (7307392120)
  - CONTENIDO CANAL → canal público @somoselencuadre (-1003932701023)
Throttle + dedupe + niveles evitan spam.
"""
import json, pathlib, time, hashlib, requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "data" / "agent"
STATE_DIR.mkdir(parents=True, exist_ok=True)
THROTTLE_FILE = STATE_DIR / "notif_throttle.json"
DEDUPE_FILE = STATE_DIR / "notif_dedupe.json"

def _env(key):
    p = ROOT / ".env"
    if not p.exists(): return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

TOKEN = _env("TELEGRAM_BOT_TOKEN")
CHAT_PRIVADO = _env("TELEGRAM_CHAT_ID")          # 7307392120 (alertas técnicas)
CANAL_PUBLICO = _env("TELEGRAM_CHANNEL_ID")      # -1003932701023 (contenido)

# ═══ Throttle por (tipo, canal) - ventana 2h ═══
THROTTLE_VENTANA = 2 * 3600

def _cargar(path):
    if not path.exists(): return {}
    try: return json.loads(path.read_text())
    except: return {}

def _guardar(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False))

def _debe_enviar(tipo, canal, dedupe_key="", throttle_override=None):
    """Devuelve True si debe enviarse. False si throttle o duplicado."""
    ahora = time.time()
    ventana = throttle_override or THROTTLE_VENTANA
    # Throttle
    t = _cargar(THROTTLE_FILE)
    clave = f"{tipo}:{canal}"
    if clave in t and (ahora - t[clave]) < ventana:
        return False
    t[clave] = ahora
    _guardar(THROTTLE_FILE, t)
    # Dedupe (24h)
    if dedupe_key:
        d = _cargar(DEDUPE_FILE)
        h = hashlib.md5(dedupe_key.encode()).hexdigest()[:16]
        if h in d and (ahora - d[h]) < 86400:
            return False
        d[h] = ahora
        # Limpiar > 7 días
        d = {k: v for k, v in d.items() if ahora - v < 604800}
        _guardar(DEDUPE_FILE, d)
    return True

def _post(chat_id, texto, parse_mode="HTML", disable_preview=False):
    if not TOKEN or not chat_id: return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": texto[:4000], "parse_mode": parse_mode,
                  "disable_web_page_preview": disable_preview},
            timeout=15
        )
        return r.status_code == 200
    except Exception:
        return False

# ═══════════════════════════════════════════════════════════
# API PÚBLICA
# ═══════════════════════════════════════════════════════════

def alerta(tipo, mensaje, nivel="warning"):
    """Alerta técnica al chat privado. tipos: pipeline_fail, youtube_fail, disco, zombie, etc."""
    emoji = {"critico": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(nivel, "⚠️")
    texto = f"{emoji} <b>[{nivel.upper()}]</b> {tipo}\n\n{mensaje}"
    enviado = _debe_enviar(f"alerta_{tipo}_{nivel}", CHAT_PRIVADO, dedupe_key=mensaje[:100])
    if enviado:
        return _post(CHAT_PRIVADO, texto)
    return False

def info_tecnica(mensaje):
    """Info técnica (no alerta) al chat privado. Throttle 4h."""
    return _debe_enviar("info_tecnica", CHAT_PRIVADO, dedupe_key=mensaje[:100]) and _post(
        CHAT_PRIVADO, f"ℹ️ {mensaje}", disable_preview=True
    )

def resumen_diario(texto_html):
    """Resumen del día al chat privado. Throttle 20h."""
    return _debe_enviar("resumen_diario", CHAT_PRIVADO, throttle_override=20*3600) and _post(
        CHAT_PRIVADO, texto_html
    )

def publicar_canal(texto_html, disable_preview=False):
    """Contenido para el canal público @somoselencuadre. Dedupe 24h, throttle 30min."""
    return _debe_enviar("canal_post", CANAL_PUBLICO, dedupe_key=texto_html[:150],
                        throttle_override=1800) and _post(
        CANAL_PUBLICO, texto_html, disable_preview=disable_preview
    )

def canal_nuevo_post(titulo, url, tipo="Análisis"):
    """Notificación de nuevo post/vídeo en el canal público."""
    texto = f"📰 <b>{tipo}</b>\n\n<b>{titulo[:200]}</b>\n\n🔗 {url}"
    return publicar_canal(texto)

def canal_nuevo_video(titulo, video_id, tipo="Vídeo"):
    """Nuevo vídeo YouTube al canal público."""
    texto = f"🎬 <b>Nuevo {tipo}</b>\n\n<b>{titulo[:200]}</b>\n\n▶️ https://youtu.be/{video_id}"
    return publicar_canal(texto)

def test_conexion():
    """Test de conexión con ambos canales."""
    r1 = _post(CHAT_PRIVADO, "🧪 Test alerta técnica (chat privado)")
    r2 = _post(CANAL_PUBLICO, "🧪 Test canal público")
    return {"privado": r1, "publico": r2}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print(test_conexion())
    elif len(sys.argv) > 1 and sys.argv[1] == "alerta":
        print(alerta("test", " ".join(sys.argv[2:]) or "test"))
    elif len(sys.argv) > 1 and sys.argv[1] == "canal":
        print(publicar_canal(" ".join(sys.argv[2:]) or "test"))
