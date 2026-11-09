#!/usr/bin/env python3
"""bot_dios.py v2 - Fast: clasifica → chat directo (Groq) o agente (dios.py).
Chat rápido responde en 2-3s. Agente solo si verbos de acción.
"""
import sys, pathlib, time, subprocess, json, re
import urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))

def _env(k):
    p = ROOT / ".env"
    if not p.exists(): return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{k}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

TOKEN = _env("TELEGRAM_BOT_TOKEN")
CHAT_PRIVADO = _env("TELEGRAM_CHAT_ID")
API = f"https://api.telegram.org/bot{TOKEN}"

# Cache modelos + keys
_GROQ_KEYS = []
for line in (ROOT / ".env").read_text().splitlines():
    if line.startswith("GROQ_API_KEY"):
        v = line.split("=", 1)[1].strip().strip('"').strip("'")
        if v.startswith("gsk_") and 40 <= len(v) < 200: _GROQ_KEYS.append(v)

CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def _post(method, data):
    try:
        req = urllib.request.Request(f"{API}/{method}",
            data=urllib.parse.urlencode(data).encode(), method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"[bot] {method} err: {e}", flush=True)
        return None

def responder(chat_id, texto, reply_to=None):
    data = {"chat_id": chat_id, "text": texto[:4000], "parse_mode": "HTML", "disable_web_page_preview": "true"}
    if reply_to: data["reply_to_message_id"] = reply_to
    return _post("sendMessage", data)

def _typing():
    _post("sendChatAction", {"chat_id": CHAT_PRIVADO, "action": "typing"})

def _groq_fast(prompt, system="", max_tokens=500):
    """Chat directo a Groq. ~2s. Sin tools, sin agente."""
    import requests
    sys_msg = system or "Eres Dios, asistente de KeiZ. Directo, breve, español. Máximo 3 frases salvo que te pidan detalle."
    for key in _GROQ_KEYS[:2]:
        for modelo in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]:
            try:
                r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": CHROME_UA},
                    json={"model": modelo, "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": prompt}
                    ], "temperature": 0.5, "max_tokens": max_tokens},
                    timeout=20)
                if r.status_code == 200:
                    j = r.json()
                    msg = j.get("choices", [{}])[0].get("message", {})
                    txt = (msg.get("content") or "").strip()
                    if not txt and msg.get("reasoning"): txt = msg["reasoning"][:500].strip()
                    if txt: return txt
            except: continue
    return None

def _clasificar(texto):
    """Devuelve 'chat' o 'agent'. Cualquier cosa que pida datos reales → agent."""
    low = texto.lower()
    if texto.startswith("#"): return "agent"
    if texto.startswith("!"): return "chat"
    
    # Verbos de acción
    verbos = ["crea", "crear", "genera", "generar", "haz", "hacer", "lanza", "lanzar",
              "busca", "buscar", "instala", "instalar", "ejecuta", "ejecutar",
              "sube", "subir", "publica", "publicar", "arregla", "arreglar", "corrige",
              "descarga", "descargar", "mata", "matar", "limpia", "limpiar",
              "programa", "programar", "analiza", "analizar", "revisa", "revisar",
              "modifica", "modificar", "borra", "borrar", "actualiza", "actualizar"]
    
    # Verbos de consulta de datos reales
    consultas = ["cuantos", "cuántos", "listame", "lista", "muestrame", "muéstrame", "dime",
                 "cual", "cuál", "que", "qué", "quien", "quién", "donde", "dónde", "cuando", "cuándo",
                 "ayer", "hoy", "mañana", "semana", "mes",
                 "video", "vídeo", "short", "youtube", "podcast", "post", "blog", "web",
                 "visitas", "vistas", "viral", "trending", "tendencia", "noticia"]
    
    # Si tiene verbo de acción O de consulta → agent
    if any(v in low for v in verbos) or any(v in low for v in consultas):
        return "agent"
    
    # Saludos puros → chat
    saludos = ["hola", "buenas", "hey", "gracias", "ok", "genial", "bien", "mal", "tal"]
    if low.strip() in saludos or len(low.split()) <= 2:
        return "chat"
    
    # Default: agent (más seguro para no perder datos)
    return "agent"

def _comando_status():
    r = subprocess.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    proc = r.stdout.strip() or "(nada corriendo)"
    log = ROOT / "data" / "logs" / "pipeline.log"
    ult = ""
    if log.exists():
        mins = (time.time() - log.stat().st_mtime) / 60
        ult = f"Hace {mins:.0f}min"
    return f"<b>📊 Estado</b>\n<b>Pipeline:</b>\n<code>{proc[:300]}</code>\n<b>Log:</b> {ult}"

def _comando_yt():
    import datetime
    hoy = datetime.date.today().isoformat()
    p = ROOT / "data" / "agent" / f"youtube_urls_{hoy}.json"
    if not p.exists(): return f"❌ Sin youtube_urls_{hoy}.json"
    try:
        d = json.loads(p.read_text())
        txt = f"<b>🎬 YT {hoy}</b>\n\n"
        l = d.get("largo") or {}
        if l.get("video_id"): txt += f"<b>Largo:</b> https://youtu.be/{l['video_id']}\n"
        for i, s in enumerate(d.get("shorts", [])):
            txt += f"<b>S{i+1}:</b> https://youtu.be/{s['video_id']}\n"
        return txt
    except Exception as e: return f"Error: {e}"

def _comando_logs():
    log = ROOT / "data" / "logs" / "pipeline.log"
    if not log.exists(): return "(sin log)"
    r = subprocess.run(["tail", "-15", str(log)], capture_output=True, text=True, timeout=5)
    return f"<b>📋 Log</b>\n<pre>{r.stdout[-3000:]}</pre>"

def _comando_hoy():
    import datetime
    hoy = datetime.date.today().isoformat()
    p = ROOT / "output" / "encuadre" / f"produccion_{hoy}.json"
    if not p.exists(): return f"❌ Sin producción hoy"
    try:
        d = json.loads(p.read_text())
        dos = d.get("dossier", {})
        return f"<b>📅 {hoy}</b>\n\n<b>Tema:</b> {dos.get('titular_brutal','(sin)')[:100]}\n<b>Palabras:</b> {d.get('palabras_totales',0)}\n<b>Viralidad:</b> {d.get('viralidad',{}).get('score',0)}/10\n<b>Shorts:</b> {len(d.get('shorts_finales',[]))}"
    except Exception as e: return f"Error: {e}"

def _comando_pipeline():
    _post("sendMessage", {"chat_id": CHAT_PRIVADO, "text": "🚀 Lanzando pipeline (30-40min)..."})
    log_f = open(ROOT / "data" / "logs" / "pipeline_bot.log", "w")
    subprocess.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log_f, stderr=subprocess.STDOUT)
    return "✅ Lanzado. Usa /status."

def _comando_matar():
    subprocess.run(["pkill", "-9", "-f", "pipeline_encuadre"], timeout=10, check=False)
    return "✅ Detenido"

def _comando_help():
    return """<b>🤖 Dios Bot</b>

<b>Rápido (2s):</b> cualquier pregunta normal
<b>Agente (30s):</b> acciones (crear, generar, subir...)

<b>Comandos:</b>
/status /yt /logs /hoy /pipeline /matar /help

<b>Ejemplos chat:</b>
"qué se rompió ayer"
"cuántos vídeos se subieron"
"resumen de hoy"

<b>Ejemplos agente:</b>
"lanza el pipeline"
"limpia el disco"
"busca tendencias de youtube"
"programa los vídeos de hoy" """

COMANDOS = {"/status": _comando_status, "/yt": _comando_yt, "/logs": _comando_logs,
            "/hoy": _comando_hoy, "/pipeline": _comando_pipeline, "/matar": _comando_matar,
            "/help": _comando_help, "/start": _comando_help}

def _dios_agent(texto):
    try:
        r = subprocess.run(["python3", "scripts/dios.py", texto], cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        out = r.stdout or r.stderr or ""
        if "[dios] Tarea completada. Resumen:" in out:
            return out.split("[dios] Tarea completada. Resumen:")[-1].strip()
        return out.strip()[-2000:]
    except subprocess.TimeoutExpired:
        return "⏱ Timeout 180s"
    except Exception as e:
        return f"❌ {e}"

def main():
    print(f"[bot] Iniciando (chat {CHAT_PRIVADO})", flush=True)
    print(f"[bot] Groq keys cargadas: {len(_GROQ_KEYS)}", flush=True)
    _post("sendMessage", {"chat_id": CHAT_PRIVADO, "text": "🤖 Bot listo (modo rápido). /help para comandos."})

    offset = 0
    while True:
        try:
            req = urllib.request.Request(f"{API}/getUpdates?offset={offset}&timeout=25")
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
            if not data.get("ok"): time.sleep(2); continue
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                # 2026-11-09: callback_query (botones inline)
                cb = upd.get("callback_query")
                if cb:
                    cb_data = cb.get("data", "")
                    cb_id = cb.get("id")
                    cb_msg = cb.get("message", {})
                    cb_chat = str(cb_msg.get("chat", {}).get("id", ""))
                    cb_msg_id = cb_msg.get("message_id")
                    if cb_chat != str(CHAT_PRIVADO):
                        _post("answerCallbackQuery", {"callback_query_id": cb_id})
                        continue
                    _post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "Procesando..."})
                    try:
                        import dios_sugerencias_db as _db
                        if cb_data.startswith("dios_aceptar_"):
                            sid = int(cb_data.replace("dios_aceptar_", ""))
                            s = _db.por_id(sid)
                            if s:
                                _db.marcar(sid, "aceptada")
                                _post("editMessageText", {"chat_id": cb_chat, "message_id": cb_msg_id,
                                    "text": f"✅ Aceptada #{sid}: {s['titulo']}\n\n⚙️ Ejecutando {s['accion_tool'] or 'acción'}...",
                                    "parse_mode": "HTML"})
                                if s["accion_tool"]:
                                    _typing()
                                    # 2026-11-09: llamada DIRECTA a la tool, sin pasar por agente
                                    import json as _json
                                    import importlib, sys as _sys
                                    _sys.path.insert(0, str(ROOT / "scripts"))
                                    _sys.path.insert(0, str(ROOT / "brain"))
                                    try:
                                        import dios as _dios_mod
                                        importlib.reload(_dios_mod)
                                        tool_name = s["accion_tool"]
                                        args = _json.loads(s.get("payload") or "{}")
                                        if tool_name in _dios_mod.TOOL_FNS:
                                            responder(cb_chat, f"⚙️ Ejecutando <b>{tool_name}</b>...\nArgs: <code>{_json.dumps(args)[:200]}</code>")
                                            resultado = _dios_mod.TOOL_FNS[tool_name](args)
                                            responder(cb_chat, f"🤖 <b>#{sid} → {tool_name}</b>\n\n{str(resultado)[:3500]}")
                                        else:
                                            responder(cb_chat, f"❌ Tool '{tool_name}' no existe en TOOL_FNS")
                                    except Exception as e:
                                        responder(cb_chat, f"❌ Error ejecutando {s['accion_tool']}: {e}")
                                else:
                                    responder(cb_chat, f"ℹ️ #{sid} aceptada (sin tool asociada)")
                        elif cb_data.startswith("dios_ignorar_"):
                            sid = int(cb_data.replace("dios_ignorar_", ""))
                            s = _db.por_id(sid)
                            _db.marcar(sid, "ignorada")
                            _post("editMessageText", {"chat_id": cb_chat, "message_id": cb_msg_id,
                                "text": f"❌ Ignorada #{sid}: {s['titulo'] if s else ''}",
                                "parse_mode": "HTML"})
                        elif cb_data.startswith("dios_posponer_"):
                            sid = int(cb_data.replace("dios_posponer_", ""))
                            _post("editMessageText", {"chat_id": cb_chat, "message_id": cb_msg_id,
                                "text": f"⏰ Pospuesta #{sid} (1h)", "parse_mode": "HTML"})
                            _db.marcar(sid, "pospuesta")
                    except Exception as e:
                        responder(cb_chat, f"❌ Error callback: {e}")
                    continue
                if not msg: continue
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id != str(CHAT_PRIVADO): continue
                texto = (msg.get("text") or "").strip()
                if not texto: continue
                msg_id = msg.get("message_id")
                print(f"[bot] ← {texto[:80]}", flush=True)
                # Comando?
                if texto.startswith("/"):
                    cmd = texto.split()[0].lower()
                    if cmd in COMANDOS:
                        responder(chat_id, COMANDOS[cmd](), reply_to=msg_id)
                        continue
                # Clasificar
                tipo = _clasificar(texto)
                if tipo == "chat":
                    _typing()
                    resp = _groq_fast(texto)
                    if resp:
                        responder(chat_id, f"🤖 {resp[:3500]}", reply_to=msg_id)
                    else:
                        responder(chat_id, "⏳ Groq falló, usando agente...", reply_to=msg_id)
                        responder(chat_id, f"🤖 {_dios_agent(texto)[:3000]}", reply_to=msg_id)
                else:
                    responder(chat_id, f"⚙️ Agente procesando: <i>{texto[:80]}</i>", reply_to=msg_id)
                    _typing()
                    responder(chat_id, f"🤖 {_dios_agent(texto)[:3000]}", reply_to=msg_id)
        except Exception as e:
            print(f"[bot] loop err: {e}", flush=True)
            time.sleep(3)

if __name__ == "__main__":
    main()
