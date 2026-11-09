#!/usr/bin/env python3
"""dios_autonomo.py - Daemon que detecta oportunidades y propone acciones por Telegram.
Reglas V1 (15). Cada 30min revisa, throttle 6h por regla. Solo propone, tú apruebas.
"""
import sys, pathlib, json, datetime, subprocess, time
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))

import dios_sugerencias_db as DB
from notificador_top1 import _post, TOKEN, CHAT_PRIVADO

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(f"{k}="): return line.split("=",1)[1].strip().strip('"').strip("'")
    return ""

def _hoy():
    return datetime.date.today().isoformat()

# ═══════════════════════════ REGLAS ═══════════════════════════
# Cada regla devuelve list[dict] con: regla, categoria, titulo, mensaje, payload, accion_tool, prioridad

def r01_seo_flojo():
    out = []
    f = _hoy()
    p = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
    if not p.exists(): return out
    try:
        d = json.loads(p.read_text())
        viral = (d.get("viralidad") or {}).get("score", 0)
        if viral > 0 and viral < 4:
            out.append({"regla": "r01_seo_flojo", "categoria": "contenido", "prioridad": 0.75,
                "titulo": f"Viralidad {viral}/10 hoy", "mensaje": f"Viralidad muy baja: {viral}/10.\nTitular: {d.get('dossier',{}).get('titular_brutal','(sin)')[:100]}\n\nPropongo regenerar SEO con títulos más punchy.",
                "payload": {"fecha": f}, "accion_tool": "generar_seo"})
    except: pass
    return out

def r02_ultimo_video_sin_yt():
    out = []
    f = _hoy()
    yt = ROOT / "data" / "agent" / f"youtube_urls_{f}.json"
    prod = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
    if prod.exists() and not yt.exists():
        hora = datetime.datetime.now().hour
        if hora >= 11:
            out.append({"regla": "r02_ultimo_video_sin_yt", "categoria": "youtube", "prioridad": 0.9,
                "titulo": f"Vídeo {f} NO subido a YouTube", "mensaje": f"Hay producción de hoy pero no youtube_urls.\nProbable fallo de subida.\n\nPropongo: re-subir todo con publish_at escalonado.",
                "payload": {"fecha": f}, "accion_tool": "subir_youtube_dia"})
    return out

def r03_disco_lleno():
    out = []
    try:
        r = subprocess.run(["df", "-h", str(ROOT)], capture_output=True, text=True, timeout=5)
        lines = r.stdout.strip().split("\n")
        if len(lines) > 1:
            uso = int(lines[1].split()[4].replace("%",""))
            if uso > 85:
                out.append({"regla": "r03_disco_lleno", "categoria": "operacional", "prioridad": 0.95,
                    "titulo": f"Disco al {uso}%", "mensaje": f"Disco lleno al {uso}%.\n\nPropongo: limpieza profunda (borrar MP4, logs viejos, render_work).",
                    "payload": {}, "accion_tool": "ejecutar_limpieza"})
    except: pass
    return out

def r04_pipeline_fallo():
    out = []
    log = ROOT / "data" / "logs" / "pipeline.log"
    if not log.exists(): return out
    try:
        r = subprocess.run(["tail", "-50", str(log)], capture_output=True, text=True, timeout=5)
        tail = r.stdout
        if "❌" in tail and ("ERROR" in tail or "FAIL" in tail or "Timeout" in tail):
            out.append({"regla": "r04_pipeline_fallo", "categoria": "operacional", "prioridad": 0.9,
                "titulo": "Pipeline con errores recientes", "mensaje": f"Últimos errores del log:\n\n{tail[-400:]}\n\nPropongo: revisar y diagnosticar.",
                "payload": {}, "accion_tool": "pipeline_status"})
    except: pass
    return out

def r05_podcast_falta():
    out = []
    f = _hoy()
    hora = datetime.datetime.now().hour
    if hora >= 12:
        pod = ROOT / "web" / "docs" / "podcast" / f"{f}.mp3"
        if not pod.exists():
            out.append({"regla": "r05_podcast_falta", "categoria": "contenido", "prioridad": 0.7,
                "titulo": f"Podcast {f} no generado", "mensaje": f"Ya son las {hora}h y no hay podcast de hoy.\n\nPropongo: generar podcast MP3 desde producción del día.",
                "payload": {"fecha": f}, "accion_tool": "generar_podcast_dia"})
    return out

def r06_2dias_sin_pipeline():
    out = []
    hoy = datetime.date.today()
    hace_2 = hoy - datetime.timedelta(days=2)
    prod_hoy = (ROOT / "output" / "encuadre" / f"produccion_{hoy.isoformat()}.json").exists()
    prod_h2 = (ROOT / "output" / "encuadre" / f"produccion_{hace_2.isoformat()}.json").exists()
    if not prod_hoy and not prod_h2:
        out.append({"regla": "r06_2dias_sin_pipeline", "categoria": "contenido", "prioridad": 0.85,
            "titulo": "2 días sin pipeline", "mensaje": f"No hay producción ni de {hoy.isoformat()} ni de {hace_2.isoformat()}.\n\nPropongo: lanzar pipeline completo ahora.",
            "payload": {}, "accion_tool": "pipeline_completo"})
    return out

def r07_shorts_tipo_repetido():
    out = []
    f = _hoy()
    p = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
    if not p.exists(): return out
    try:
        d = json.loads(p.read_text())
        tipos = [s.get("tipo") for s in (d.get("shorts_finales") or [])[:4]]
        if len(tipos) >= 2 and tipos[0] == tipos[1]:
            out.append({"regla": "r07_shorts_tipo_repetido", "categoria": "contenido", "prioridad": 0.5,
                "titulo": f"2 shorts seguidos tipo '{tipos[0]}'", "mensaje": f"Shorts: {tipos}\n\nPropongo: reordenar ángulos para variar hook inicial.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r08_competencia_trending():
    out = []
    try:
        r = subprocess.run(["python3", "brain/investigador_redes.py", "ia_news"],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=90)
        if r.returncode == 0 and r.stdout:
            data = json.loads(r.stdout[-3000:]) if r.stdout.strip().startswith("{") else {}
            trends = data.get("tendencias", [])[:1]
            if trends:
                t = trends[0].get("titulo", "")[:80]
                out.append({"regla": "r08_competencia_trending", "categoria": "estrategia", "prioridad": 0.65,
                    "titulo": f"Trending ahora: {t}", "mensaje": f"Detectado trending no cubierto:\n{t}\n\nPropongo: short rápido aprovechando el trend.",
                    "payload": {"tema": t, "nicho": "ia_news"}, "accion_tool": "generar_short"})
    except: pass
    return out

def r09_titulo_corto():
    out = []
    f = _hoy()
    seo = ROOT / "output" / "encuadre" / f"seo_{f}.json"
    if not seo.exists(): return out
    try:
        d = json.loads(seo.read_text())
        tit = (d.get("largo") or {}).get("titulo", "")
        if tit and len(tit) < 30:
            out.append({"regla": "r09_titulo_corto", "categoria": "youtube", "prioridad": 0.6,
                "titulo": f"Título muy corto ({len(tit)} chars)", "mensaje": f"Título: '{tit}'\n\nSEO premia 40-70 chars. Propongo regenerar con keyword + hook.",
                "payload": {"fecha": f}, "accion_tool": "generar_seo"})
    except: pass
    return out

def r10_web_sin_visitas():
    out = []
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from cloudflare_stats import resumen
        r = resumen(7)
        pv = r.get("page_views", 0)
        if pv > 0 and pv < 50:
            out.append({"regla": "r10_web_sin_visitas", "categoria": "web", "prioridad": 0.55,
                "titulo": f"Solo {pv} page_views en 7d", "mensaje": f"Tráfico bajo: {pv} views/semana.\n\nPropongo: publicar en más redes + revisar SEO títulos.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r11_historico_urls_404():
    out = []
    try:
        r = subprocess.run(["grep", "-c", "404", str(ROOT / "data" / "logs" / "keiz-web.log")],
                          capture_output=True, text=True, timeout=5)
        n = int(r.stdout.strip() or 0)
        if n > 20:
            out.append({"regla": "r11_historico_urls_404", "categoria": "web", "prioridad": 0.7,
                "titulo": f"{n} 404s en log web", "mensaje": f"{n} errores 404 en keiz-web.log.\n\nPropongo: revisar y añadir redirects.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r12_pipeline_zombie():
    out = []
    try:
        r = subprocess.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            log = ROOT / "data" / "logs" / "pipeline.log"
            if log.exists():
                mins = (time.time() - log.stat().st_mtime) / 60
                if mins > 90:
                    out.append({"regla": "r12_pipeline_zombie", "categoria": "operacional", "prioridad": 0.95,
                        "titulo": f"Pipeline zombie {mins:.0f}min sin log", "mensaje": f"Pipeline corriendo pero {mins:.0f}min sin escribir log.\n\nPropongo: matar y diagnosticar.",
                        "payload": {}, "accion_tool": "pipeline_kill"})
    except: pass
    return out

def r13_kaggle_huerfano():
    out = []
    # Si hay kernels LTX en running >6h sin push, sugerir cerrar
    try:
        r = subprocess.run(["python3", "-c",
            "import sys; sys.path.insert(0,'scripts'); import kaggle_bearer as kb; "
            "r=kb.estado_kernel('keizproductions/ltx-biblioteca-v1-lote4'); print(r.get('status',''))"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=20)
        if "running" in r.stdout.lower():
            out.append({"regla": "r13_kaggle_huerfano", "categoria": "operacional", "prioridad": 0.5,
                "titulo": "Kernel Kaggle LTX en running", "mensaje": "Kernel LTX lleva tiempo running.\n\nPropongo: revisar si terminó o cerrar para liberar cuota.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r14_domingo_cazar_musica():
    out = []
    hoy = datetime.date.today()
    if hoy.weekday() == 6 and datetime.datetime.now().hour == 4:
        out.append({"regla": "r14_domingo_cazar_musica", "categoria": "operacional", "prioridad": 0.4,
            "titulo": "Domingo: renovar pool música", "mensaje": "Es domingo. Toca renovar pool de música CC.\n\nPropongo: lanzar cazador de links.",
            "payload": {}, "accion_tool": ""})
    return out

def r15_post_largo_flojo():
    out = []
    f = _hoy()
    p = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
    if not p.exists(): return out
    try:
        d = json.loads(p.read_text())
        palabras = d.get("palabras_totales", 0)
        if 0 < palabras < 800:
            out.append({"regla": "r15_post_largo_flojo", "categoria": "contenido", "prioridad": 0.65,
                "titulo": f"Post corto ({palabras} palabras)", "mensaje": f"Post de hoy: {palabras} palabras.\n\nPropongo: regenerar con más profundidad (>1200).",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

REGLAS = [r01_seo_flojo, r02_ultimo_video_sin_yt, r03_disco_lleno, r04_pipeline_fallo,
          r05_podcast_falta, r06_2dias_sin_pipeline, r07_shorts_tipo_repetido, r08_competencia_trending,
          r09_titulo_corto, r10_web_sin_visitas, r11_historico_urls_404, r12_pipeline_zombie,
          r13_kaggle_huerfano, r14_domingo_cazar_musica, r15_post_largo_flojo]

def _enviar_sugerencia(sid, s):
    """Envía mensaje con botones inline."""
    emoji = "🚨" if s["prioridad"] >= 0.9 else ("⚠️" if s["prioridad"] >= 0.7 else "🧠")
    texto = f"{emoji} <b>Idea #{sid}</b>\n\n{s['titulo']}\n\n{s['mensaje']}"
    kb = {"inline_keyboard": [[
        {"text": "✅ Ejecutar", "callback_data": f"dios_aceptar_{sid}"},
        {"text": "❌ Ignorar", "callback_data": f"dios_ignorar_{sid}"},
        {"text": "⏰ 1h", "callback_data": f"dios_posponer_{sid}"}
    ]]}
    r = _post_buttons(texto, kb)
    if r and r.get("result"): DB.guardar_msg_id(sid, r["result"]["message_id"])

def _post_buttons(texto, kb):
    import urllib.request, urllib.parse, json as _j
    try:
        data = urllib.parse.urlencode({"chat_id": CHAT_PRIVADO, "text": texto[:4000],
                                       "parse_mode": "HTML", "reply_markup": _j.dumps(kb)}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                     data=data, method="POST")
        with urllib.request.urlopen(req, timeout=15) as r:
            return _j.loads(r.read())
    except Exception as e:
        print(f"  [tg] {e}", flush=True); return None

def ciclo():
    """1 pasada: ejecuta reglas, crea sugerencias, envía."""
    total_nuevas = 0
    for fn in REGLAS:
        try:
            results = fn()
            for r in results:
                sid = DB.crear(r["regla"], r["categoria"], r["titulo"], r["mensaje"],
                              r.get("payload"), r.get("accion_tool", ""), r.get("prioridad", 0.5))
                if sid:
                    total_nuevas += 1
                    _enviar_sugerencia(sid, r)
                    print(f"  ✅ [{sid}] {r['regla']}: {r['titulo'][:60]}", flush=True)
        except Exception as e:
            print(f"  ⚠️ {fn.__name__}: {e}", flush=True)
    print(f"[dios_autonomo] {total_nuevas} sugerencias nuevas ({datetime.datetime.now().strftime('%H:%M')})", flush=True)

if __name__ == "__main__":
    if "--once" in sys.argv:
        ciclo()
    else:
        print(f"[dios_autonomo] daemon iniciado. Cada 30min.", flush=True)
        while True:
            try:
                ciclo()
            except Exception as e:
                print(f"[loop] {e}", flush=True)
            time.sleep(1800)
