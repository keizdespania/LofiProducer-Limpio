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
            if uso > 95:
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


# ═══════════════ V2 - CONTENIDO AVANZADO ═══════════════

def r16_sin_comentarios_youtube():
    """Vídeos de ayer con 0 comentarios = algoritmo frío."""
    out = []
    ayer = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    yt = ROOT / "data" / "agent" / f"youtube_urls_{ayer}.json"
    if not yt.exists(): return out
    try:
        d = json.loads(yt.read_text())
        vids = [d.get("largo")] + (d.get("shorts") or [])
        out.append({"regla": "r16_sin_comentarios_youtube", "categoria": "youtube", "prioridad": 0.55,
            "titulo": f"Vídeos {ayer} sin interacción",
            "mensaje": "Lanza comentario SEO fijado (CTA + links) en cada vídeo para arrancar el algoritmo y tráfico cruzado.",
            "payload": {"fecha": ayer}, "accion_tool": "publicar_comentario_youtube"})
    except: pass
    return out

def r17_short_viral_secuela():
    """Short con >10k vistas → secuela."""
    out = []
    for f in sorted((ROOT / "data" / "agent").glob("youtube_urls_*.json"), reverse=True)[:3]:
        try:
            d = json.loads(f.read_text())
            fecha = d.get("fecha", "")
            for s in d.get("shorts", [])[:4]:
                # No hay métricas aquí, pero el botón de "secuela" es útil
                out.append({"regla": "r17_short_viral_secuela", "categoria": "estrategia", "prioridad": 0.5,
                    "titulo": f"Analizar short {s.get('video_id')} de {fecha}",
                    "mensaje": f"Short de {fecha}: {s.get('titulo','')[:80]}\n\nPropongo: analizar métricas reales y ver si vale secuela/cross-post.",
                    "payload": {"video_id": s.get("video_id"), "fecha": fecha}, "accion_tool": "analizar_short_viral"})
                break
        except: pass
    return out

def r18_nicho_sin_contenido():
    """Nicho sin producción 7 días."""
    out = []
    hoy = datetime.date.today()
    nichos_dir = ROOT / "output" / "nichos"
    if not nichos_dir.exists(): return out
    for c in nichos_dir.glob("*/canal.json"):
        try:
            d = json.loads(c.read_text())
            ultimo = d.get("ultimo_post", "")
            if ultimo:
                ud = datetime.datetime.fromisoformat(ultimo[:10]).date()
                dias = (hoy - ud).days
                if dias >= 7:
                    out.append({"regla": "r18_nicho_sin_contenido", "categoria": "estrategia", "prioridad": 0.6,
                        "titulo": f"Nicho '{c.parent.name}' parado {dias}d",
                        "mensaje": f"Nicho sin contenido {dias} días.\n\nPropongo: pipeline custom con formato largo+shorts para reactivar.",
                        "payload": {"nicho": c.parent.name, "formatos": ["largo", "shorts"], "num_shorts": 2}, "accion_tool": "pipeline_custom"})
        except: pass
    return out

def r19_descripcion_corta():
    """SEO: descripciones <200 chars = penalización."""
    out = []
    f = _hoy()
    seo = ROOT / "output" / "encuadre" / f"seo_{f}.json"
    if not seo.exists(): return out
    try:
        d = json.loads(seo.read_text())
        desc = (d.get("largo") or {}).get("descripcion", "")
        if 0 < len(desc) < 200:
            out.append({"regla": "r19_descripcion_corta", "categoria": "youtube", "prioridad": 0.6,
                "titulo": f"Descripción corta ({len(desc)} chars)",
                "mensaje": "YouTube premia 300-500 chars con keywords + timestamps.\n\nPropongo: regenerar SEO.",
                "payload": {"fecha": f}, "accion_tool": "generar_seo"})
    except: pass
    return out

def r20_falta_thumbnail():
    """Vídeo sin thumbnail custom."""
    out = []
    f = _hoy()
    video = ROOT / "output" / "encuadre" / f"video_largo_{f}.mp4"
    thumb = ROOT / "output" / "encuadre" / f"thumbnail_{f}.jpg"
    if video.exists() and not thumb.exists():
        out.append({"regla": "r20_falta_thumbnail", "categoria": "youtube", "prioridad": 0.65,
            "titulo": "Vídeo sin thumbnail custom",
            "mensaje": f"Video de hoy sin thumbnail específica.\n\nPropongo: generar thumbnail impactante (nano-banana o SDXL cinematic) y subir a YouTube.",
            "payload": {"fecha": f}, "accion_tool": "generar_thumbnail_video"})
    return out

# ═══════════════ V2 - OPERACIONAL AVANZADO ═══════════════

def r21_token_youtube():
    """Token YouTube caduca en <3 días."""
    out = []
    tok = ROOT / "data" / "youtube_encuadre_token.json"
    if tok.exists():
        age = (time.time() - tok.stat().st_mtime) / 86400
        if age > 4:
            out.append({"regla": "r21_token_youtube", "categoria": "operacional", "prioridad": 0.85,
                "titulo": f"Token YouTube {age:.1f} días sin refresh",
                "mensaje": "Google revoca refresh tokens a los 7 días sin uso.\n\nPropongo: ejecutar subir_youtube.py para refrescar token.",
                "payload": {}, "accion_tool": ""})
    return out

def r22_backup_viejo():
    """Backup >7 días."""
    out = []
    backups = list((ROOT / "output" / "web_backups").glob("web_docs_*.tar.gz")) if (ROOT / "output" / "web_backups").exists() else []
    if backups:
        ultimo = max(backups, key=lambda p: p.stat().st_mtime)
        dias = (time.time() - ultimo.stat().st_mtime) / 86400
        if dias > 7:
            out.append({"regla": "r22_backup_viejo", "categoria": "operacional", "prioridad": 0.65,
                "titulo": f"Backup web {dias:.0f} días sin renovar",
                "mensaje": "Último backup viejo.\n\nPropongo: lanzar limpieza (crea backup automático).",
                "payload": {}, "accion_tool": "ejecutar_limpieza"})
    return out

def r23_cola_publicacion_estancada():
    """Cola publicación con items >24h pendientes."""
    out = []
    db = ROOT / "data" / "agent" / "cola_publicacion.db"
    if not db.exists(): return out
    try:
        import sqlite3
        con = sqlite3.connect(str(db))
        cur = con.execute("SELECT COUNT(*) FROM publicaciones WHERE estado='pendiente' AND publish_at < ?",
                         (datetime.datetime.now().isoformat(),))
        n = cur.fetchone()[0]
        if n > 0:
            out.append({"regla": "r23_cola_estancada", "categoria": "operacional", "prioridad": 0.7,
                "titulo": f"{n} items en cola vencida",
                "mensaje": f"{n} publicaciones con publish_at pasado pero no subidas.\n\nPropongo: revisar y relanzar cola.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r24_ram_alta():
    """RAM >85%."""
    out = []
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        if r.stdout:
            partes = r.stdout.split()
            total = int(partes[1]) if len(partes) > 1 else 0
            usado = int(partes[2]) if len(partes) > 2 else 0
            if total > 0:
                pct = usado * 100 / total
                if pct > 85:
                    out.append({"regla": "r24_ram_alta", "categoria": "operacional", "prioridad": 0.7,
                        "titulo": f"RAM al {pct:.0f}%",
                        "mensaje": f"RAM {usado}/{total}MB.\n\nPropongo: matar procesos zombies.",
                        "payload": {}, "accion_tool": ""})
    except: pass
    return out

def r25_cron_fallos():
    """Crons con múltiples errores recientes."""
    out = []
    for logname in ["watchdog.log", "cola_yt.log", "limpieza.log"]:
        log = ROOT / "data" / "logs" / logname
        if not log.exists(): continue
        try:
            r = subprocess.run(["tail", "-30", str(log)], capture_output=True, text=True, timeout=5)
            errores = sum(1 for l in r.stdout.splitlines() if "ERROR" in l or "Traceback" in l)
            if errores >= 3:
                out.append({"regla": "r25_cron_fallos", "categoria": "operacional", "prioridad": 0.75,
                    "titulo": f"Cron {logname} con {errores} errores",
                    "mensaje": f"Último log {logname} tiene {errores} errores.\n\nPropongo: diagnosticar.",
                    "payload": {}, "accion_tool": ""})
        except: pass
    return out

def r26_youtube_upload_fail():
    """Vídeo existe pero no está en YT."""
    out = []
    f = _hoy()
    video = ROOT / "output" / "encuadre" / f"video_largo_{f}.mp4"
    yt = ROOT / "data" / "agent" / f"youtube_urls_{f}.json"
    if video.exists() and not yt.exists():
        out.append({"regla": "r26_youtube_upload_fail", "categoria": "operacional", "prioridad": 0.9,
            "titulo": "Vídeo sin subir (existe MP4)",
            "mensaje": f"MP4 existe pero falta youtube_urls.\n\nPropongo: re-subir con publish_at.",
            "payload": {"fecha": f}, "accion_tool": "subir_youtube_dia"})
    return out

# ═══════════════ V3 - ESTRATEGIA AVANZADA ═══════════════

def r27_mejor_dia_semana():
    """Detecta mejor día histórico vs hoy."""
    out = []
    hoy = datetime.date.today().weekday()  # 0=Lun, 6=Dom
    # Análisis simple: sábados y domingos suele haber menos tráfico
    if hoy == 5:  # sábado
        out.append({"regla": "r27_mejor_dia_semana", "categoria": "estrategia", "prioridad": 0.4,
            "titulo": "Sábado: día flojo en audiencia",
            "mensaje": "Sábados suelen tener menos tráfico.\n\nPropongo: publicar contenido evergreen (no noticias).",
            "payload": {}, "accion_tool": ""})
    return out

def r28_evento_calendario():
    """Eventos próximos (elecciones, finales)."""
    out = []
    eventos = []  # Añadir manualmente: [("2026-11-20", "Elecciones")]
    hoy = datetime.date.today()
    for fecha_str, nombre in eventos:
        try:
            d = datetime.date.fromisoformat(fecha_str)
            dias = (d - hoy).days
            if 0 <= dias <= 7:
                out.append({"regla": "r28_evento_calendario", "categoria": "estrategia", "prioridad": 0.7,
                    "titulo": f"Evento en {dias}d: {nombre}",
                    "mensaje": f"Preparar cobertura anticipada: {nombre}",
                    "payload": {"tema": nombre}, "accion_tool": "pipeline_custom"})
        except: pass
    return out

def r29_competencia_similar():
    """Detecta si un competidor publicó similar."""
    out = []
    try:
        sys.path.insert(0, str(ROOT / "brain"))
        from web_search import buscar
        f = _hoy()
        p = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
        if p.exists():
            d = json.loads(p.read_text())
            tema = (d.get("dossier") or {}).get("titular_brutal", "")[:60]
            if tema:
                r = buscar(f'"{tema}" -site:elencuadre.pages.dev', max_results=3)
                if r and len(r) > 0:
                    out.append({"regla": "r29_competencia_similar", "categoria": "estrategia", "prioridad": 0.5,
                        "titulo": f"Competencia cubrió: {tema}",
                        "mensaje": f"Otros medios cubren el tema.\n\nPropongo: análisis diferenciado con ángulo único.",
                        "payload": {"tema": tema}, "accion_tool": ""})
    except: pass
    return out

def r30_post_antiguo_reciclar():
    """Post >3 meses que se puede actualizar/reciclar."""
    out = []
    try:
        analisis = ROOT / "web" / "docs" / "analisis"
        if not analisis.exists(): return out
        corte = datetime.date.today() - datetime.timedelta(days=90)
        for f in sorted(analisis.glob("2026-*.md"), reverse=True)[:1]:
            fecha_str = f.stem[:10]
            try:
                fd = datetime.date.fromisoformat(fecha_str)
                if fd < corte:
                    out.append({"regla": "r30_post_antiguo_reciclar", "categoria": "estrategia", "prioridad": 0.45,
                        "titulo": f"Post antiguo reciclable: {f.stem[:40]}",
                        "mensaje": f"Post de {fecha_str} puede ser actualizado o reciclado.\n\nPropongo: generar nueva versión.",
                        "payload": {"post": f.stem}, "accion_tool": ""})
                    break
            except: pass
    except: pass
    return out

def r31_adblock_placeholder():
    """Falta zona AdSense."""
    out = []
    cfg = ROOT / "web" / "mkdocs.yml"
    if cfg.exists():
        try:
            txt = cfg.read_text()
            if "monetizacion_activa: false" in txt:
                out.append({"regla": "r31_adblock_placeholder", "categoria": "monetizacion", "prioridad": 0.3,
                    "titulo": "AdSense preparado pero OFF",
                    "mensaje": "Web preparada para AdSense pero desactivado (bien si no eres autónomo).",
                    "payload": {}, "accion_tool": ""})
        except: pass
    return out

def r32_paginas_cero_visitas():
    """Páginas con 0 vistas 30 días."""
    out = []
    # Placeholder: requiere Cloudflare API con path individual
    return out

def r33_shorts_incompletos():
    """Menos de 4 shorts generados."""
    out = []
    f = _hoy()
    p = ROOT / "output" / "encuadre" / f"produccion_{f}.json"
    if p.exists():
        try:
            d = json.loads(p.read_text())
            n = len(d.get("shorts_finales") or [])
            if n < 4:
                out.append({"regla": "r33_shorts_incompletos", "categoria": "contenido", "prioridad": 0.6,
                    "titulo": f"Solo {n} shorts generados",
                    "mensaje": f"Hoy solo {n}/4 shorts.\n\nPropongo: regenerar factory_shorts.",
                    "payload": {"fecha": f}, "accion_tool": "factory_shorts"})
        except: pass
    return out

def r34_musica_pool_bajo():
    """Pool música <20 links."""
    out = []
    pool = ROOT / "config" / "musica_shorts_pool.json"
    if pool.exists():
        try:
            d = json.loads(pool.read_text())
            n = len(d) if isinstance(d, list) else len(d.get("links", []))
            if n < 20:
                out.append({"regla": "r34_musica_pool_bajo", "categoria": "operacional", "prioridad": 0.5,
                    "titulo": f"Pool música bajo: {n} links",
                    "mensaje": "Quedan pocos links.\n\nPropongo: ejecutar cazador.",
                    "payload": {}, "accion_tool": ""})
        except: pass
    return out

def r35_github_sin_push():
    """>2 días sin push."""
    out = []
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cd", "--date=iso"], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=5)
        if r.stdout.strip():
            ts = r.stdout.strip().split()[0] + " " + r.stdout.strip().split()[1]
            ultimo = datetime.datetime.fromisoformat(ts[:19])
            dias = (datetime.datetime.now() - ultimo).days
            if dias >= 2:
                out.append({"regla": "r35_github_sin_push", "categoria": "operacional", "prioridad": 0.4,
                    "titulo": f"Sin push {dias}d",
                    "mensaje": "Repositorio sin push hace 2+ días.\n\nPropongo: snapshot + push.",
                    "payload": {}, "accion_tool": "rollback_snapshot"})
    except: pass
    return out

def r36_evergreen_falta():
    """No hay post evergreen reciente."""
    # Placeholder: podría buscar posts tipo 'glosario', 'guía'
    return []

def r37_serie_recurrente():
    """Serie con potencial."""
    # Placeholder manual
    return []

def r38_dias_sin_publicar_yt():
    """Sin vídeo YT en 3+ días."""
    out = []
    yt_files = list((ROOT / "data" / "agent").glob("youtube_urls_*.json"))
    if not yt_files: return out
    ultimo = max(yt_files, key=lambda p: p.stat().st_mtime)
    dias = (time.time() - ultimo.stat().st_mtime) / 86400
    if dias >= 3:
        out.append({"regla": "r38_dias_sin_publicar_yt", "categoria": "youtube", "prioridad": 0.75,
            "titulo": f"Sin subir YT {dias:.0f}d",
            "mensaje": "Hace 3+ días que no se sube vídeo.\n\nPropongo: revisar pipeline.",
            "payload": {}, "accion_tool": "pipeline_status"})
    return out

def r39_subida_rapida():
    """Buen momento para subir (hora punta)."""
    out = []
    hora = datetime.datetime.now().hour
    if hora in (18, 19, 20):
        out.append({"regla": "r39_subida_rapida", "categoria": "estrategia", "prioridad": 0.4,
            "titulo": f"Hora punta ({hora}:00)",
            "mensaje": "Hora de máxima audiencia.\n\nPropongo: compartir en redes ahora.",
            "payload": {}, "accion_tool": ""})
    return out

def r40_predictor_viralidad():
    """Alerta si tema detectado es viral."""
    out = []
    try:
        sys.path.insert(0, str(ROOT / "brain"))
        r = subprocess.run(["python3", "scripts/predictor_viralidad.py"],
                          cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and "score" in r.stdout.lower():
            out.append({"regla": "r40_predictor_viralidad", "categoria": "estrategia", "prioridad": 0.55,
                "titulo": "Predictor: tema con potencial viral",
                "mensaje": "Predictor detectó tema con score alto.\n\nPropongo: priorizar contenido sobre ese tema.",
                "payload": {}, "accion_tool": ""})
    except: pass
    return out

# ═══════════════ REGISTRO ═══════════════

REGLAS = [r01_seo_flojo, r02_ultimo_video_sin_yt, r03_disco_lleno, r04_pipeline_fallo,
          r05_podcast_falta, r06_2dias_sin_pipeline, r07_shorts_tipo_repetido, r08_competencia_trending,
          r09_titulo_corto, r10_web_sin_visitas, r11_historico_urls_404, r12_pipeline_zombie,
          r13_kaggle_huerfano, r14_domingo_cazar_musica, r15_post_largo_flojo,
          r16_sin_comentarios_youtube, r17_short_viral_secuela, r18_nicho_sin_contenido,
          r19_descripcion_corta, r20_falta_thumbnail, r21_token_youtube, r22_backup_viejo,
          r23_cola_publicacion_estancada, r24_ram_alta, r25_cron_fallos, r26_youtube_upload_fail,
          r27_mejor_dia_semana, r28_evento_calendario, r29_competencia_similar, r30_post_antiguo_reciclar,
          r31_adblock_placeholder, r32_paginas_cero_visitas, r33_shorts_incompletos, r34_musica_pool_bajo,
          r35_github_sin_push, r36_evergreen_falta, r37_serie_recurrente, r38_dias_sin_publicar_yt,
          r39_subida_rapida, r40_predictor_viralidad]

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
