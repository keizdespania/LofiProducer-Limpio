"""pipeline_encuadre.py - Orquestador Maestro Definitivo (Blindado)."""
import subprocess, sys, pathlib, datetime, json, asyncio, time, unicodedata
from pathlib import Path
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 2026-11-09: notificador top-1 centralizado
import sys as _sys_notif
_sys_notif.path.insert(0, str(ROOT / "brain"))
try:
    from notificador_top1 import alerta as _alerta_t1, resumen_diario as _resumen_t1, canal_nuevo_video as _canal_video_t1
except Exception as _e:
    _alerta_t1 = _resumen_t1 = _canal_video_t1 = lambda *a, **k: None
    print(f"   [notif] no cargado: {_e}", flush=True)

OUT = ROOT / "output" / "encuadre"
TOKEN_ENC = ROOT / "data" / "youtube_encuadre_token.json"

# PAUSA BLOGGER por baneo (reactivar 2026-11-11)
# 2026-11-09: overrides custom desde dashboard (Crear Custom)
CUSTOM_OVERRIDES = {}
try:
    import json as _json
    _fecha_hoy = datetime.date.today().isoformat()
    _req_path = ROOT / "output" / "encuadre" / f"custom_request_{_fecha_hoy}.json"
    if _req_path.exists():
        CUSTOM_OVERRIDES = _json.loads(_req_path.read_text())
        print(f"Custom request detectado: nicho={CUSTOM_OVERRIDES.get('nicho')}, tema_tipo={CUSTOM_OVERRIDES.get('tema_tipo')}, tema={CUSTOM_OVERRIDES.get('tema','')[:60]}", flush=True)
        _ctx_path = ROOT / "output" / "encuadre" / f"custom_context_{_fecha_hoy}.json"
        _ctx_path.write_text(_json.dumps({
            "nicho": CUSTOM_OVERRIDES.get("nicho"),
            "tema": CUSTOM_OVERRIDES.get("tema"),
            "tema_tipo": CUSTOM_OVERRIDES.get("tema_tipo"),
            "num_shorts": CUSTOM_OVERRIDES.get("num_shorts"),
            "formatos": CUSTOM_OVERRIDES.get("formatos", []),
            "forzar": True,
        }, ensure_ascii=False, indent=2))
except Exception as _e:
    print(f"custom_request: {_e}", flush=True)

BLOGGER_PAUSADO = True
BLOGGER_DESBLOQUEO = "2026-11-11"

# 2026-11-09: snapshot rollback antes de pipeline
try:
    import sys as _sys_snap
    _sys_snap.path.insert(0, str(ROOT / "scripts"))
    from rollback import snapshot as _snap
    _snap("pre-pipeline")
except Exception as _e:
    print(f"   [snapshot] {_e}", flush=True)

def _run(script, args=None, timeout=1200, retries=3):
    cmd = ["python3", f"scripts/{script}"] + (args or [])
    for intento in range(retries):
        print(f"\n{'='*60}\n▶️  EJECUTANDO: {script} {' '.join(args or [])} (Intento {intento+1}/{retries})\n{'='*60}", flush=True)
        try:
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=False, text=True, timeout=timeout)
            if r.returncode == 0: return True
            print(f"⚠️  {script} falló (código {r.returncode}).", flush=True)
        except subprocess.TimeoutExpired:
            print(f"❌ TIMEOUT: {script} tardó más de {timeout}s.", flush=True)
        except Exception as e:
            print(f"❌ ERROR: {e}", flush=True)
        time.sleep(3)
    return False

_VIDEOS_SUBIDOS = []  # Acumula IDs de vídeos subidos para avisar por Telegram

def _subir_youtube(archivo, titulo, desc, tags=None, publish_at=None, retries=3):
    sys.path.insert(0, str(ROOT / "scripts"))
    from subir_youtube import subir, token
    # REFRESH OBLIGATORIO antes de subir (2026-11-03: token revocado por Google)
    try:
        token("data/youtube_encuadre_token.json")
        print(f"   ✅ Token refrescado antes de subir", flush=True)
    except Exception as _e:
        print(f"   ❌ Token refresh falló: {_e}. Ejecuta scripts/reautorizar_youtube.py", flush=True)
        print(f"   ⚠️ Saltando subida a YouTube (token inválido)", flush=True)
        return False
    for intento in range(retries):
        try:
            r = subir(archivo, titulo, desc, tags=tags, privacidad="private", publish_at=publish_at, token_file=TOKEN_ENC)
            print(f"✅ YouTube: https://youtu.be/{r['id']}")
            _VIDEOS_SUBIDOS.append({
                "titulo": titulo,
                "video_id": r['id'],
                "tipo": "video_largo" if "largo" in str(archivo) else "short"
            })
            return True
        except Exception as e:
            print(f"⚠️ YouTube falló (intento {intento+1}/{retries}): {e}")
            time.sleep(5)
    return False

async def _gen_voz(txt, salida):
    c = edge_tts.Communicate(txt, "es-ES-AlvaroNeural", rate="-5%")
    with open(salida, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])

def _normalizar(s):
    return unicodedata.normalize("NFKD", str(s)).encode("ASCII", "ignore").decode("ASCII").lower()

def _publicar_web(fecha):
    """Copia posts a web/docs/analisis/ + build + git push (Cloudflare despliega solo)."""
    import shutil as _shutil
    cola = ROOT / "output" / "cola_web"
    dest = ROOT / "web" / "docs" / "analisis"
    dest.mkdir(parents=True, exist_ok=True)
    
    # Ficheros a publicar: TODOS los del día (fix 2026-11-04)
    ficheros = list(cola.glob(f"{fecha}-*.md"))
    publicar = ficheros
    
    # Copiar podcast también
    podcast_src = ROOT / "output" / "encuadre" / "podcast"
    podcast_dst = ROOT / "web" / "docs" / "podcast"
    podcast_dst.mkdir(parents=True, exist_ok=True)
    if podcast_src.exists():
        for ep in podcast_src.glob("*.mp3"):
            _shutil.copy(ep, podcast_dst / ep.name)
            print(f"   ✅ Podcast copiado: {ep.name}", flush=True)
        idx = podcast_src / "index.md"
        if idx.exists():
            _shutil.copy(idx, podcast_dst / "index.md")
    
    if not publicar:
        print(f"   ⚠️ _publicar_web: no hay posts para {fecha}", flush=True)
        return False
    
    for f in publicar:
        _shutil.copy(f, dest / f.name)
        print(f"   ✅ Copiado: {f.name}", flush=True)
    
    # Actualizar mkdocs.yml si falta
    mkdocs = ROOT / "web" / "mkdocs.yml"
    if mkdocs.exists():
        mtxt = mkdocs.read_text()
        for f in publicar:
            slug = f.stem
            if f"analisis/{f.name}" not in mtxt:
                titulo = slug.replace(f"{fecha}-", "").replace("-", " ").title()
                entrada = f'    - "{titulo}": analisis/{f.name}\n'
                if '    - Índice: analisis/index.md\n' in mtxt:
                    mtxt = mtxt.replace('    - Índice: analisis/index.md\n', f'    - Índice: analisis/index.md\n{entrada}', 1)
                elif '  - Análisis: analisis/index.md\n' in mtxt:
                    mtxt = mtxt.replace('  - Análisis: analisis/index.md\n', f'  - Análisis:\n    - Índice: analisis/index.md\n{entrada}', 1)
        mkdocs.write_text(mtxt)
    
    # Regenerar home + analisis/index.md (antes del build)
    try:
        import subprocess as _sp
        _sp.run([sys.executable, "scripts/actualizar_web_index.py"], cwd=str(ROOT), timeout=60, check=False)
        print(f"   ✅ Home + análisis regenerados", flush=True)
    except Exception as _e:
        print(f"   ⚠️ actualizar_web_index falló: {_e}", flush=True)
    
    # Build
    try:
        import subprocess as _sp
        r = _sp.run(["mkdocs", "build"], cwd=str(ROOT / "web"), capture_output=True, timeout=120)
        if r.returncode == 0:
            print(f"   ✅ mkdocs build OK", flush=True)
        else:
            print(f"   ⚠️ mkdocs build falló (código {r.returncode})", flush=True)
            return False
    except Exception as e:
        print(f"   ⚠️ mkdocs build exception: {e}", flush=True)
        return False
    
    # Git add + commit + push (solo ficheros web)
    try:
        import subprocess as _sp
        _sp.run(["git", "add", "web/docs/analisis/", "web/mkdocs.yml", "web/media/imagenes/"], cwd=str(ROOT), timeout=60)
        rc_commit = _sp.run(["git", "commit", "-m", f"content: posts web {fecha} (largo + dossier + mediano)"], cwd=str(ROOT), timeout=30, capture_output=True)
        # Rebase silencioso si remote avanzó (kernel LTX pushea clips por la noche)
        rc_pull = _sp.run(["git", "pull", "--rebase", "--autostash"], cwd=str(ROOT), timeout=60, capture_output=True, text=True)
        if rc_pull.returncode != 0:
            print(f"   ⚠️ pull --rebase falló: {rc_pull.stderr[:200]}", flush=True)
        # Push CON comprobación real de resultado
        rc_push = _sp.run(["git", "push", "origin", "main"], cwd=str(ROOT), timeout=60, capture_output=True, text=True)
        if rc_push.returncode == 0:
            print(f"   ✅ Push OK (Cloudflare despliega en 1-2 min)", flush=True)
        else:
            print(f"   ❌ Push FALLÓ (rc={rc_push.returncode}): {rc_push.stderr[:300]}", flush=True)
            print(f"   → Los posts están en local pero NO en la web", flush=True)
        
        # Generar informe PDF (opcional, no rompe el pipeline si falla)
        try:
            print(f"   📄 Generando informe PDF...", flush=True)
            _sp.run([sys.executable, "scripts/generar_informe_pdf.py", fecha],
                    cwd=str(ROOT), timeout=120, check=False)
        except Exception as _e:
            print(f"   ⚠️ Informe PDF falló: {_e}", flush=True)
        
        return True
    except Exception as e:
        print(f"   ⚠️ git exception: {e}", flush=True)
        return False

def main():
    # 2026-11-09: regenerar manual primero (refleja todo lo actual)
    import subprocess as _sp_man
    try:
        _sp_man.run([sys.executable, "scripts/gen_manual.py"], cwd=str(ROOT), timeout=60, check=False, capture_output=True)
        print("   [manual] regenerado", flush=True)
    except Exception as _e_man:
        print(f"   [manual] {_e_man}", flush=True)

    # 2026-11-09: limpieza diaria primero (reset total <ayer)
    import subprocess as _sp_limp
    try:
        _sp_limp.run([sys.executable, "scripts/limpieza_pipeline.py"],
                     cwd=str(ROOT), timeout=120, check=False, capture_output=True)
        print("   [limpieza] reset diario OK", flush=True)
    except Exception as _e_limp:
        print(f"   [limpieza] {_e_limp}", flush=True)

    fecha = datetime.date.today().isoformat()
    print(f"🚀 INICIANDO PIPELINE MASIVO - {fecha}", flush=True)

    pasos = [
        ("recolector.py", None, 1200, False),
        ("filtro_seguridad.py", [fecha], 300, False),
        ("transcribir_groq.py", None, 1200, True),
        ("scraper_articulos.py", [fecha], 600, False),
        ("analista_fase1.py", None, 1200, False),
        ("sintetizador.py", None, 600, False),
        ("enriquecer_dossier.py", [fecha], 300, False),
        ("scrapear_medios_completo.py", [fecha], 300, False),
        ("fase2_produccion.py", ["--modo", "monologo", fecha], 1800, False),  # monologo (2026-11-04)
        ("generar_imagenes_web.py", [fecha], 600, False),
        ("voz_edge.py", None, 600, False),
        ("director_arte.py", [fecha], 2400, False),  # 2026-11-04: fusionado (72 imgs + timeline)
        ("render_robusto.py", [fecha], 1800, False),
        ("generar_podcast.py", [fecha], 600, True),  # podcast (2026-11-04)
        ("sincronizar_podcasts.py", [], 120, True),  # 2026-11-09: feed+index+copy robusto
    ]

    for script, args, t, opcional in pasos:
        exito = _run(script, args, t)
        if not exito:
            if opcional:
                print(f"⚠️ {script} falló definitivamente (opcional). Continuando...", flush=True)
            else:
                print(f"\n🛑 PIPELINE DETENIDO: {script} es CRÍTICO.", flush=True)
                return

    video_path = OUT / f"video_largo_{fecha}.mp4"
    if not video_path.exists():
        print("\n🛑 PIPELINE DETENIDO: El vídeo largo no se generó.", flush=True)
        return

    # LIMPIAR música externa (YouTube CC, Tunetank); conservar ACE-Step
    _run("limpiar_musica_render.py", [fecha], 300, 1)

    # Preparar LOFI LARGO del día (pool CC + rotador)
    print("\n" + "="*60 + "\nPREPARANDO LOFI LARGO DEL DÍA\n" + "="*60, flush=True)
    lofi_largo = None
    try:
        from lofi_largo_del_dia import preparar as preparar_lofi_largo
        lofi_largo = preparar_lofi_largo()
        if lofi_largo:
            print(f"✅ Lofi largo del día: {Path(lofi_largo).name}", flush=True)
        else:
            print("⚠️ Sin lofi largo del pool. Podcast irá SIN MÚSICA si es necesario.", flush=True)
    except Exception as _e:
        print(f"⚠️ Lofi largo falló ({_e})", flush=True)

    # Preparar música del día para SHORTS (rotador de pool CC)
    print("\n" + "="*60 + "\nPREPARANDO MÚSICA DEL DÍA\n" + "="*60, flush=True)
    musica_dia = None
    try:
        from musica_short_del_dia import preparar as preparar_musica
        musica_dia = preparar_musica()
        if musica_dia:
            print(f"✅ Música del día: {Path(musica_dia).name}", flush=True)
        else:
            print("⚠️ Sin música del día (shorts se renderizarán sin música)", flush=True)
    except Exception as _e:
        print(f"⚠️ Música del día falló: {_e}", flush=True)

    # Render Shorts (2026-11-04 audit: usa 3 imagenes + logo + musica por mood)
    print("\n" + "="*60 + "\nRENDERIZANDO SHORTS (multi-imagen + logo)\n" + "="*60, flush=True)
    from render_short_rot import generar_short, generar_short_multi
    from pathlib import Path as _Path

    def _limpiar_texto_voz(texto):
        import re as _re_local
        if not texto: return ""
        texto = _re_local.sub(r'\[[^\]]*\]', '', texto)
        texto = _re_local.sub(r'\([^\)]*\)', '', texto)
        texto = _re_local.sub(r'\*[^\*]*\*', '', texto)
        texto = _re_local.sub(r'#+\s*', '', texto)
        texto = _re_local.sub(r'\s+', ' ', texto).strip()
        return texto

    MOODS_SHORTS = {"dato": "tension", "contradiccion": "epico", "prediccion": "electronico", "tutorial": "relax"}
    prod_file = OUT / f"produccion_{fecha}.json"
    datos = json.loads(prod_file.read_text()) if prod_file.exists() else {}
    shorts = datos.get("shorts_finales", [])[:4]
    # 2026-11-08: factory shorts primario, render antiguo fallback
    _factory_marker = OUT / f"factory_done_{fecha}.txt"
    _factory_ok = _factory_marker.exists()
    if not _factory_ok:
        print(f"   [shorts] Ejecutando factory_shorts.py {fecha}...", flush=True)
        try:
            import subprocess as _sp_fact
            _sp_fact.run([sys.executable, str(ROOT / "scripts" / "factory_shorts.py"), fecha], cwd=str(ROOT), timeout=2400)
            _factory_ok = _factory_marker.exists()
        except Exception as _e_fact:
            print(f"   ⚠️ Factory error: {_e_fact}", flush=True)
        if prod_file.exists():
            try:
                datos = json.loads(prod_file.read_text())
                shorts = datos.get("shorts_finales", [])[:4]
            except Exception:
                pass
    if _factory_ok:
        print(f"   ✅ Factory OK ({len(shorts)} shorts)", flush=True)
    else:
        print(f"   ⚠️ Factory falló, render antiguo", flush=True)
        # 2026-11-09: imágenes solo si factory falla (fallback al render antiguo)
        print(f"   [shorts fallback] Generando 12 imágenes...", flush=True)
        try:
            import subprocess as _sp_img
            _sp_img.run([sys.executable, str(ROOT / "scripts" / "generar_imagenes_shorts.py"), fecha], cwd=str(ROOT), timeout=600)
        except Exception as _e_img:
            print(f"   ⚠️ generar_imagenes_shorts: {_e_img}", flush=True)

    # Cargar mapa de 12 imagenes (3 por short) de generar_imagenes_shorts.py
    mapa_imgs = {}
    mapa_path = ROOT / "web" / "media" / "imagenes" / f"short_urls_{fecha}.json"
    if mapa_path.exists() and not _factory_ok:
        try:
            mapa_imgs = json.loads(mapa_path.read_text())
            print(f"   [shorts] Mapa de imagenes cargado: {sum(len(v) for v in mapa_imgs.values())} imagenes", flush=True)
        except Exception as _e:
            print(f"   ⚠️ Mapa de imagenes: {_e}", flush=True)

    # Logo
    logo_path = ROOT / "web" / "media" / "logo_elencuadre.jpg"
    logo_arg = str(logo_path) if logo_path.exists() else None
    if logo_arg:
        print(f"   [shorts] Logo: {logo_path.name}", flush=True)

    # Musica por mood (preparar 4 moods si no existen)
    musica_por_mood = {}
    try:
        from musica_short_del_dia import preparar as prep_musica_mood
        for _tipo, _mood in MOODS_SHORTS.items():
            _mp = ROOT / "output" / "musica_temp" / f"short_dia_{fecha}_{_mood}.mp3"
            if not _mp.exists():
                try:
                    _r = prep_musica_mood(_mood)
                    if _r: _mp = _Path(_r)
                except Exception as _e:
                    print(f"   ⚠️ Musica {_mood}: {_e}", flush=True)
            if _mp.exists():
                musica_por_mood[_mood] = str(_mp)
        print(f"   [shorts] Musicas: {len(musica_por_mood)}/4 moods", flush=True)
    except Exception as _e:
        print(f"   ⚠️ musica_short_del_dia: {_e}", flush=True)

    for i, short in enumerate(shorts):
        if _factory_ok:
            break
        num = i + 1
        tipo = _normalizar(short.get("tipo", "dato"))
        texto = _limpiar_texto_voz(short.get("guion") or short.get("hook", ""))
        palabras_txt = texto.split()
        if len(palabras_txt) > 50:
            texto = " ".join(palabras_txt[:50]) + "..."
        if not texto:
            texto = "Analisis del dia en Somos El Encuadre."

        voz_path = OUT / f"short_{num}_voz_{fecha}.mp3"
        if not voz_path.exists():
            asyncio.run(_gen_voz(texto, voz_path))

        mood = MOODS_SHORTS.get(tipo, "epico")
        musica_arg = musica_por_mood.get(mood) or (str(musica_dia) if musica_dia else "")

        # 3 imagenes del mapa (fallback a 1 imagen vertical si el mapa no existe)
        imgs = [p for p in mapa_imgs.get(str(num), [])[:3] if Path(p).exists()]

        salida_short = OUT / f"short_{num}_{fecha}.mp4"
        print(f"  [{num}/{len(shorts)}] {tipo} → {mood} | {len(imgs)} imgs | música: {Path(musica_arg).name if musica_arg else 'NO'}", flush=True)

        try:
            if len(imgs) >= 2:
                generar_short_multi(imgs, texto, str(voz_path), musica_arg, str(salida_short), logo_path=logo_arg)
            elif len(imgs) == 1:
                generar_short(imgs[0], texto, str(voz_path), musica_arg, str(salida_short))
            else:
                print(f"     ⚠️ Short {num} sin imagenes, saltando", flush=True)
                continue
            if salida_short.exists():
                print(f"     ✅ {salida_short.name} ({salida_short.stat().st_size//1024//1024}MB)", flush=True)
        except Exception as _e:
            print(f"     ⚠️ Short {num} fallo: {_e}", flush=True)

# Publicación
    print("\n" + "="*60 + "\nPUBLICACIÓN MASIVA\n" + "="*60, flush=True)
    # ===== NUEVO FLUJO WEB (v3 + dossier + verificación + publicación) =====
    # generar_podcast.py ya se ejecuta en pasos (no duplicar)
    _run("generar_web_v3.py", [fecha], 900, 1)
    _run("generar_web_dossier.py", [fecha], 600, 1)
    _run("generar_seo.py", [fecha], 300, 1)  # SEO explícito (2026-11-04)
    _run("generar_titulo_seo.py", [fecha, "video_largo"], 120, 1)  # A/B título (2026-11-04)
    _run("verificar_alucinaciones.py", [fecha], 120, 1)
    _publicar_web(fecha)
    # ===== FIN NUEVO FLUJO WEB =====
    
    if BLOGGER_PAUSADO:
        # Guardar posts en cola para publicación manual futura (2026-11-04)
        print(f"   [blogger] PAUSADO hasta {BLOGGER_DESBLOQUEO}. Guardando en cola...", flush=True)
        _run("generar_blogs_blogger.py", [fecha], 600, 1)
    else:
        _run("generar_blogs_blogger.py", [fecha], 600, 1)
    _run("generar_redes.py", [fecha], 300, 1)
    _run("generar_redes_cruzadas.py", [fecha], 60, 1)  # 2026-11-09: redes cruzadas largo+shorts+posts

    # YouTube (escalonado, sin fechas pasadas)
    ahora = datetime.datetime.now()
    hoy_dt = datetime.datetime.strptime(fecha, '%Y-%m-%d')
    manana = (hoy_dt + datetime.timedelta(days=1)).strftime('%Y-%m-%d')

    pub_v = max(hoy_dt.replace(hour=18, minute=0), ahora + datetime.timedelta(hours=1))
    # BRANCH: predictor_viralidad decide si publicar
    _viral = {}
    if prod_file.exists():
        try: _viral = json.loads(prod_file.read_text()).get("viralidad", {})
        except: pass
    _score = _viral.get("score", 0) if isinstance(_viral, dict) else 0
    _umbral = 50
    # Cargar/generar SEO ANTES del branch de viralidad (para que shorts también lo usen)
    _seo = {}
    _seo_path = OUT / f"seo_{fecha}.json"
    if not _seo_path.exists():
        try:
            import subprocess as _sp
            print(f"   Generando SEO con generar_seo.py...", flush=True)
            _sp.run([sys.executable, str(ROOT / "scripts" / "generar_seo.py"), fecha],
                    check=False, timeout=60, capture_output=True)
        except Exception as _e:
            print(f"   ⚠️ generar_seo falló: {_e}", flush=True)
    if _seo_path.exists():
        try: _seo = json.loads(_seo_path.read_text())
        except: pass

    # VALIDACIÓN VÍDEO (2026-11-04): si no cumple YouTube, no subir
    _video_ok = True
    try:
        import subprocess as _sp_val
        _val_r = _sp_val.run(
            [sys.executable, str(ROOT / "scripts" / "validar_video.py"), fecha],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60
        )
        if _val_r.returncode != 0:
            _video_ok = False
            print(f"   ❌ Validación vídeo FALLÓ (código {_val_r.returncode})", flush=True)
            print(_val_r.stdout[-500:], flush=True)
        else:
            print(f"   ✅ Vídeo válido para YouTube", flush=True)
    except Exception as _e:
        print(f"   ⚠️ Validación vídeo: {_e} (continuando)", flush=True)

    if not _video_ok:
        print(f"   ⚠️ Saltando subida YouTube (vídeo no válido)", flush=True)
    elif _score >= _umbral:
        print(f"   Viralidad {_score}/100 >= {_umbral} -> PUBLICAR YouTube", flush=True)
        _sl = _seo.get("largo", {})
        _subir_youtube(str(video_path), _sl.get("titulo", f"Vídeo Largo {fecha}"), _sl.get("descripcion", "Análisis completo."), tags=_sl.get("tags"), publish_at=pub_v.strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        print(f"   Viralidad {_score}/100 < {_umbral} -> NO publicar (cola evergreen)", flush=True)
        try:
            _cola = ROOT / "data" / "agent" / "cola_evergreen.jsonl"
            _cola.parent.mkdir(parents=True, exist_ok=True)
            with open(_cola, "a") as f:
                f.write(json.dumps({"fecha": fecha, "score": _score, "video": str(video_path)}) + "\n")
        except Exception as e: print(f"   cola error: {e}", flush=True)

    for i, short in enumerate(shorts):
        num = i+1
        _archivo = short.get("archivo") if isinstance(short, dict) else None
        s_path = (OUT / _archivo) if _archivo else (OUT / f"short_{num}_{fecha}.mp4")
        if s_path.exists():
            # Horarios óptimos: shorts 18:30, 19:00, 19:30, 20:00 ES del día
            _horas_short = [18, 19, 19, 20]
            _min_short = [30, 0, 30, 0]
            _idx = min(num-1, 3)
            _hoy_short = hoy_dt.replace(hour=_horas_short[_idx], minute=_min_short[_idx])
            if _hoy_short <= ahora:
                _hoy_short = _hoy_short + datetime.timedelta(days=1)
            pub_at = max(_hoy_short, ahora + datetime.timedelta(hours=1))
            _ss = next((s for s in _seo.get("shorts", []) if s.get("num") == num), {})
            _subir_youtube(str(s_path), _ss.get("titulo", f"Short {num} {fecha}"), _ss.get("descripcion", "Análisis rápido."), publish_at=pub_at.strftime('%Y-%m-%dT%H:%M:%SZ'))

    # [2026-11-04] ELIMINADO: _run("community_manager_auto.py", [fecha], 300, 1)
    # [2026-11-04] ELIMINADO: _run("detector_tendencias_vivas.py", [fecha], 300, 1)

    try:
        subprocess.run(["termux-notification", "-t", "🎬 Encuadre " + fecha, "-c", "Pipeline completado.", "--priority", "high"], check=False)
    except: pass

    state = {"fecha": fecha, "completado": True, "video": str(video_path)}
    (OUT / f"pipeline_{fecha}.json").write_text(json.dumps(state, indent=2))
    # CAPA 4: Post-producción inteligente
    # [2026-11-04] ELIMINADO: _run("calendario_editorial.py", [fecha], 300, 1)
    # [2026-11-04] ELIMINADO: _run("detector_evergreen.py", [fecha], 300, 1)
    # [2026-11-04] ELIMINADO: _run("optimizador_adsense.py", [fecha], 300, 1)
    
    # CAPA 1/3: Mantenimiento
    _run("monitor_salud.py", None, 300, 1)

    import datetime as _dt
    if _dt.date.today().weekday() == 6:
        print("\n[domingo] Feedback loop + meta-agentes...", flush=True)
        _run("analytics_youtube.py", None, 600, 1)
        _run("auto_ajuste_prompts.py", None, 600, 1)
        _run("rotador_ab.py", None, 300, 1)
        _run("meta_agentes_semanal.py", None, 900, 1)

    print(f"\n✅ PIPELINE MASIVO {fecha} COMPLETADO CON ÉXITO")
    # Marcar pipeline como completado (para recuperación)
    try:
        marker = ROOT / "data" / "agent" / f"pipeline_done_{fecha}.txt"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(f"{fecha} OK a las {datetime.datetime.now().isoformat()}")
        print(f"   ✅ Marcador: {marker.name}")
    except Exception as _e:
        print(f"   ⚠️ No se pudo crear marcador: {_e}")

    # Guardar URLs YouTube para el resumen (2026-11-04)
    try:
        _yt_data = {
            "fecha": fecha,
            "largo": next((v for v in _VIDEOS_SUBIDOS if v.get("tipo") in ("video_largo", "largo")), None),
            "shorts": [v for v in _VIDEOS_SUBIDOS if v.get("tipo") not in ("video_largo", "largo")][:4],
        }
        _yt_file = ROOT / "data" / "agent" / f"youtube_urls_{fecha}.json"
        _yt_file.parent.mkdir(parents=True, exist_ok=True)
        _yt_file.write_text(json.dumps(_yt_data, indent=2, ensure_ascii=False))
        print(f"   ✅ URLs YouTube guardadas: {_yt_file.name}", flush=True)
    except Exception as _e:
        print(f"   ⚠️ No pude guardar youtube_urls: {_e}", flush=True)

    # 📱 NOTIFICAR A TELEGRAM (canal público + admin)
    try:
        import sys as _sys
        _sys.path.insert(0, str(ROOT / "brain"))
        from notificador_encuadre import publicar_analisis, publicar_dossier, publicar_pipeline_completado

        print("\n[telegram] Publicando en el canal @somoselencuadre...")
        pub_count = 0

        # Buscar los .md recién generados hoy
        analisis_dir = ROOT / "web" / "docs" / "analisis"
        if analisis_dir.exists():
            for md in sorted(analisis_dir.glob(f"{fecha}-*.md")):
                slug = md.stem
                # Parsear frontmatter
                txt = md.read_text(encoding="utf-8")
                titulo = slug
                desc = ""
                if txt.startswith("---"):
                    try:
                        fm_end = txt.find("---", 3)
                        if fm_end > 0:
                            fm_txt = txt[3:fm_end].strip()
                            for line in fm_txt.split("\n"):
                                if line.startswith("title:"):
                                    titulo = line.split(":", 1)[1].strip().strip('"').strip("'")
                                elif line.startswith("description:"):
                                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                        # Fallback: si título vacío, usar slug legible
                        if not titulo or len(titulo) < 3:
                            titulo = slug.replace("-", " ").title()
                    except Exception:
                        titulo = slug.replace("-", " ").title()

                # Extraer URL fuente del cuerpo
                import re
                urls = re.findall(r'href="(https?://[^"]+)"', txt)
                excluir = ['youtube.com/@somoselencuadre.oficial', 'tiktok.com/@somoselencuadre',
                           'instagram.com/somoselencuadre', 'x.com/somoselencuadre',
                           'files.catbox.moe']
                fuente_url = ""
                for u in urls:
                    if not any(x in u for x in excluir):
                        fuente_url = u
                        break

                # Decidir tipo (dossier vs análisis normal)
                # Usar comentar_y_publicar.py (comentario Dios + post)
                import subprocess as _sp
                tipo = "dossier" if "dossier" in slug else "analisis"
                url_analisis = f"https://elencuadre.pages.dev/analisis/{slug}/"
                try:
                    _res = _sp.run(
                        ["python3", "scripts/comentar_y_publicar.py",
                         tipo, titulo, url_analisis, fuente_url],
                        cwd=str(ROOT), timeout=90, capture_output=True, text=True
                    )
                    r = {"ok": _res.returncode == 0, "error": _res.stderr[:200] if _res.returncode != 0 else ""}
                except _sp.TimeoutExpired:
                    r = {"ok": False, "error": "timeout 90s"}
                except Exception as _e:
                    r = {"ok": False, "error": str(_e)}

                if r.get("ok"):
                    pub_count += 1
                    print(f"   ✅ Publicado: {slug}")
                else:
                    print(f"   ❌ Falló: {slug} — {r.get('error', 'desconocido')[:100]}")

        # Resumen del pipeline (2026-11-04: usa notificar_resumen_dia con datos ricos)
        n_short = len([s for s in (ROOT / "output" / "encuadre").glob(f"short_*_{fecha}.mp4") if "_with_logo" not in s.name])
        n_post = pub_count
        try:
            import subprocess as _sp
            _sp.run(
                [sys.executable, str(ROOT / "scripts" / "notificar_resumen_dia.py"), fecha],
                cwd=str(ROOT), timeout=120, check=False
            )
            print(f"   ✅ Resumen rico enviado (via notificar_resumen_dia.py)", flush=True)
        except Exception as _e:
            print(f"   ⚠️ Fallback a resumen simple: {_e}", flush=True)
            r = publicar_pipeline_completado(pub_count, n_short, n_post)
            if r.get("ok"):
                print(f"   ✅ Resumen simple enviado ({pub_count} análisis, {n_short} shorts)")

        # Avisar de vídeos subidos en privado (API YouTube no auditada)
        if _VIDEOS_SUBIDOS:
            try:
                from notificador_encuadre import avisar_videos_privados
                r2 = avisar_videos_privados(_VIDEOS_SUBIDOS)
                if r2.get("ok"):
                    print(f"   ✅ Aviso YouTube Studio enviado ({len(_VIDEOS_SUBIDOS)} vídeos)")
                else:
                    print(f"   ⚠️ Aviso YouTube falló")
            except Exception as _e:
                print(f"   ⚠️ Aviso YouTube: {_e}")
        _VIDEOS_SUBIDOS.clear()

    except Exception as _e:
        print(f"   ⚠️ Telegram falló: {_e}")

if __name__ == "__main__":
    main()
