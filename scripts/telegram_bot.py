"""telegram_bot.py - Publica El Encuadre en Telegram."""
import sys, pathlib, json, datetime, urllib.request, urllib.parse
ROOT = pathlib.Path(__file__).resolve().parent.parent

def _leer_env(k):
    p = ROOT / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith(k + "="):
                return line.split("=", 1)[1].strip().strip(chr(34)).strip(chr(39))
    return None

def enviar_mensaje(texto):
    token = _leer_env("TELEGRAM_BOT_TOKEN")
    chat = _leer_env("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return "ERROR: falta TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({"chat_id": chat, "text": texto, "parse_mode": "HTML", "disable_web_page_preview": "false"}).encode()
    try:
        r = urllib.request.urlopen(url, data=data, timeout=15)
        d = json.loads(r.read())
        return "OK" if d.get("ok") else f"ERROR: {d}"
    except Exception as e:
        return f"ERROR: {e}"

def publicar_encuadre(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    j = ROOT / "output" / "encuadre" / f"encuadre_{fecha}.json"
    if not j.exists(): return f"ERROR: no existe {j}"
    d = json.loads(j.read_text())
    analisis = d.get("analisis", {})
    medios = analisis.get("medios", [])
    msg = f"<b>📊 El Encuadre — {fecha}</b>" + chr(10) * 2
    msg += f"<i>{d.get(chr(116)+chr(101)+chr(109)+chr(97), chr(63))}</i>" + chr(10) * 2
    for m in medios:
        msg += f"• <b>{m.get(chr(110)+chr(111)+chr(109)+chr(98)+chr(114)+chr(101), chr(63))}</b>: alarmismo {m.get(chr(97)+chr(108)+chr(97)+chr(114)+chr(109)+chr(105)+chr(115)+chr(109)+chr(111), 0)}/100 · omision {m.get(chr(111)+chr(109)+chr(105)+chr(115)+chr(105)+chr(111)+chr(110), 0)}/100" + chr(10)
    msg += chr(10) * 2 + "📖 Lee el analisis completo: elencuadre.com"
    return enviar_mensaje(msg)

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    print(publicar_encuadre(fecha))