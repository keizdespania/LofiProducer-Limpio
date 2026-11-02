"""pipeline_encuadre.py - Orquestador Maestro Definitivo (Blindado)."""
import subprocess, sys, pathlib, datetime, json, asyncio, time, unicodedata
from pathlib import Path
import edge_tts

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
TOKEN_ENC = ROOT / "data" / "youtube_encuadre_token.json"

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
    from subir_youtube import subir
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
    
    # Ficheros a publicar: largo + dossier-v2 + mediano-*
    ficheros = list(cola.glob(f"{fecha}-*.md"))
    publicar = [f for f in ficheros if any(k in f.name for k in ["-largo", "-dossier-v2", "-mediano-"])]
    
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
        _sp.run(["git", "add", "web/docs/analisis/", "web/mkdocs.yml"], cwd=str(ROOT), timeout=30)
        _sp.run(["git", "commit", "-m", f"content: posts web {fecha} (largo + dossier + mediano)"], cwd=str(ROOT), timeout=30, capture_output=True)
        _sp.run(["git", "push", "origin", "main"], cwd=str(ROOT), timeout=60)
        print(f"   ✅ Push OK (Cloudflare despliega en 1-2 min)", flush=True)
        
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
        ("fase2_produccion.py", None, 1200, False),
        ("director_arte.py", None, 1800, True),
        ("generar_imagenes_web.py", [fecha], 600, False),
        ("generar_imagenes_shorts.py", [fecha], 600, False),
        ("descargar_lofi.py", None, 600, True),
        ("voz_edge.py", None, 600, False),
        ("segmentar_imagenes.py", [fecha], 1800, False),
        ("render_robusto.py", [fecha], 1800, False)
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

    # Render Shorts
    print("\n" + "="*60 + "\nRENDERIZANDO SHORTS CON ROT\n" + "="*60, flush=True)
    from render_short_rot import generar_short
    from descargar_musica_dinamica import descargar_por_mood
    # Cleaner local (voz_edge ya no tiene _limpiar)
    import re as _re_local
    def _limpiar_texto_voz(texto):
        if not texto: return ""
        texto = _re_local.sub(r'\[[^\]]*\]', '', texto)   # [Fade out], [Pausa]
        texto = _re_local.sub(r'\([^\)]*\)', '', texto)   # (silencio), (énfasis)
        texto = _re_local.sub(r'\*[^\*]*\*', '', texto)   # *cursiva*
        texto = _re_local.sub(r'#+\s*', '', texto)        # markdown headers
        texto = _re_local.sub(r'\s+', ' ', texto).strip()
        return texto

    MOODS_SHORTS = {"dato": "tension", "contradiccion": "epico", "prediccion": "electronico", "tutorial": "relax"}
    prod_file = OUT / f"produccion_{fecha}.json"
    datos = json.loads(prod_file.read_text()) if prod_file.exists() else {}
    shorts = datos.get("shorts_finales", [])[:4]

    for i, short in enumerate(shorts):
        num = i + 1
        tipo = _normalizar(short.get("tipo", "dato"))
        texto = short.get("guion") or short.get("hook", "")
        texto = _limpiar_texto_voz(texto)
        # Truncar a 50 palabras máximo (rot necesita textos cortos)
        palabras_txt = texto.split()
        if len(palabras_txt) > 50:
            texto = " ".join(palabras_txt[:50]) + "..."
            print(f"     ✂️ Texto truncado a 50 palabras para rot")
        if not texto: texto = "Análisis del día en Somos El Encuadre."

        voz_path = OUT / f"short_{num}_voz_{fecha}.mp3"
        if not voz_path.exists(): asyncio.run(_gen_voz(texto, voz_path))

        # Música: gestor_musica → YouTube CC primero, Tunetank fallback interno
        musica_short = None
        mood = MOODS_SHORTS.get(tipo, "epico")
        print(f"  [{num}/{len(shorts)}] Música ({mood}) [contexto=short_{num}]...", flush=True)
        # Música CORTA para short (40-60s) — CLAVE: no usar lofi_base de 15min
        musica_short = None
        # 1. Intentar short_musica_peak.mp3 (ya existe, funciona)
        peak = ROOT / "output" / "musica_temp" / "short_musica_peak.mp3"
        if peak.exists():
            musica_short = peak
            print(f"     🎵 Música: short_musica_peak.mp3", flush=True)
        else:
            # 2. gestor_musica
            try:
                sys.path.insert(0, str(ROOT / "scripts"))
                from gestor_musica import obtener_musica
                _m = obtener_musica(mood=mood, duracion_objetivo=40, contexto=f"short_{num}")
                musica_short = _m["archivo"]
                print(f"     🎵 {musica_short.name}", flush=True)
            except Exception as e:
                print(f"     ⚠️ gestor_musica: {e}", flush=True)
                # 3. Fallback Tunetank
                try:
                    r = descargar_por_mood(mood, 1)
                    if r: musica_short = ROOT / "output" / "musica_temp" / r[0]["archivo"]
                except: pass
        musica_arg = str(musica_short) if musica_short else ""

        # ═══════════════════════════════════════════════════════════════
        # IMAGEN VERTICAL: PRIORIDAD ESTRICTA (Regla #45)
        # 1. short_{num}_*{fecha}* (imágenes específicas del short) — OBLIGATORIO
        # 2. short_bg_{num}.png (fondo genérico por short)
        # 3. short_bg_01.png (fondo global) — solo si es vertical
        # 4. Generar con SDXL 9:16 si no hay nada
        # 5. Fondo negro de emergencia
        # ═══════════════════════════════════════════════════════════════
        from PIL import Image as _Img
        def _es_vertical(_p):
            try:
                _im = _Img.open(_p)
                return _im.size[1] > _im.size[0]
            except: return False

        img_vertical = None
        # 1. PRIORIDAD MÁXIMA: imágenes específicas del short
        imgs_short_especificas = sorted(
            (ROOT / "web" / "media" / "imagenes").glob(f"short_{num}_*{fecha}*")
        )
        if imgs_short_especificas:
            for candidata in imgs_short_especificas:
                if _es_vertical(candidata):
                    img_vertical = candidata
                    print(f"     🖼️ [P1] Imagen propia del short: {candidata.name}", flush=True)
                    break
            if img_vertical is None:
                # hay imágenes del short pero ninguna vertical → usar la primera y forzar
                img_vertical = imgs_short_especificas[0]
                print(f"     ⚠️ [P1] Ninguna vertical, forzando: {img_vertical.name}", flush=True)
                # Forzar a 9:16 con ffmpeg
                try:
                    vertical_temp = ROOT / "output" / "render_tmp" / f"forzada_{num}.png"
                    vertical_temp.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run([
                        "ffmpeg", "-y", "-loglevel", "quiet", "-i", str(img_vertical),
                        "-vf", "scale=768:1344:force_original_aspect_ratio=increase,crop=768:1344",
                        str(vertical_temp)
                    ], capture_output=True, timeout=30)
                    if vertical_temp.exists():
                        img_vertical = vertical_temp
                        print(f"     ✅ [P1] Forzada a 9:16", flush=True)
                except Exception as _e:
                    print(f"     ⚠️ Forzado falló: {_e}", flush=True)

        # 2. FALLBACK: short_bg_{num}.png específico
        if img_vertical is None:
            bg_especifico = ROOT / "web" / "media" / "imagenes" / f"short_bg_{num:02d}.png"
            if bg_especifico.exists() and _es_vertical(bg_especifico):
                img_vertical = bg_especifico
                print(f"     🖼️ [P2] Fondo específico short: {bg_especifico.name}", flush=True)

        # 3. FALLBACK: short_bg_01.png global (si es vertical)
        if img_vertical is None:
            bg_global = ROOT / "web" / "media" / "imagenes" / "short_bg_01.png"
            if bg_global.exists() and _es_vertical(bg_global):
                img_vertical = bg_global
                print(f"     🖼️ [P3] Fondo global short_bg_01.png", flush=True)

        # 4. FALLBACK: escenas verticales
        if img_vertical is None:
            escenas = sorted((ROOT / "web" / "media" / "imagenes").glob("escena_*.png"))
            for e in escenas:
                if _es_vertical(e):
                    img_vertical = e
                    print(f"     🖼️ [P4] Escena vertical: {e.name}", flush=True)
                    break

        # 5. ÚLTIMO RECURSO: generar con SDXL 9:16
        if img_vertical is None:
            print(f"     🖼️ [P5] Sin imágenes verticales. Generando con SDXL 9:16...", flush=True)
            try:
                sys.path.insert(0, str(ROOT / "scripts"))
                from generar_imagen import generar
                r = generar(
                    f"cinematic dark news analysis, vertical composition, {tipo} concept, dramatic lighting, no text",
                    preset="cinematic", aspect="9:16", canal="encuadre"
                )
                if 'OK: ' in r:
                    ruta = r.split('OK: ')[1].split(' ')[0]
                    if Path(ruta).exists():
                        import shutil
                        destino = ROOT / "web" / "media" / "imagenes" / f"short_bg_{num:02d}.png"
                        shutil.copy2(ruta, destino)
                        img_vertical = destino
                        print(f"     ✅ [P5] Generada: {destino.name}", flush=True)
            except Exception as e:
                print(f"     ⚠️ [P5] SDXL falló: {e}", flush=True)

        # 6. EMERGENCIA: fondo negro 1080x1920
        if img_vertical is None or not Path(img_vertical).exists():
            print(f"     ⚠️ [P6] Fondo negro de emergencia", flush=True)
            emergencia = ROOT / "output" / "render_tmp" / f"emergencia_{num}.png"
            emergencia.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
                "-frames:v", "1", str(emergencia)
            ], capture_output=True)
            img_vertical = emergencia

        print(f"     ✅ [FINAL] Usando: {Path(img_vertical).name}", flush=True)
        salida_short = OUT / f"short_{num}_{fecha}.mp4"
        print(f"  [{num}/{len(shorts)}] Renderizando short...", flush=True)
        for intento in range(2):
            try:
                generar_short(str(img_vertical), texto, str(voz_path), musica_arg, str(salida_short))
                print(f"     ✅ {salida_short.name}", flush=True)
                break
            except Exception as e:
                print(f"     ⚠️ rot falló (intento {intento+1}/2): {e}", flush=True)
                time.sleep(2)

    # Publicación
    print("\n" + "="*60 + "\nPUBLICACIÓN MASIVA\n" + "="*60, flush=True)
    # ===== NUEVO FLUJO WEB (v3 + dossier + verificación + publicación) =====
    _run("generar_podcast.py", [fecha], 600, 1)
    _run("generar_web_v3.py", [fecha], 900, 1)
    _run("generar_web_dossier.py", [fecha], 600, 1)
    _run("verificar_alucinaciones.py", [fecha], 120, 1)
    _publicar_web(fecha)
    # ===== FIN NUEVO FLUJO WEB =====
    
    _run("generar_blogs_blogger.py", [fecha], 600, 1)
    _run("generar_redes.py", [fecha], 300, 1)

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

    if _score >= _umbral:
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
        s_path = OUT / f"short_{num}_{fecha}.mp4"
        if s_path.exists():
            if num <= 2:
                pub_at = ahora + datetime.timedelta(hours=1 + (num-1)*0.5)
            else:
                base = hoy_dt.replace(hour=13, minute=0) + datetime.timedelta(days=1)
                pub_at = max(base, ahora + datetime.timedelta(hours=1)) + datetime.timedelta(hours=(num-3)*0.5)
            _ss = next((s for s in _seo.get("shorts", []) if s.get("num") == num), {})
            _subir_youtube(str(s_path), _ss.get("titulo", f"Short {num} {fecha}"), _ss.get("descripcion", "Análisis rápido."), publish_at=pub_at.strftime('%Y-%m-%dT%H:%M:%SZ'))

    _run("community_manager_auto.py", [fecha], 300, 1)
    _run("detector_tendencias_vivas.py", [fecha], 300, 1)

    try:
        subprocess.run(["termux-notification", "-t", "🎬 Encuadre " + fecha, "-c", "Pipeline completado.", "--priority", "high"], check=False)
    except: pass

    state = {"fecha": fecha, "completado": True, "video": str(video_path)}
    (OUT / f"pipeline_{fecha}.json").write_text(json.dumps(state, indent=2))
    # CAPA 4: Post-producción inteligente
    _run("calendario_editorial.py", [fecha], 300, 1)
    _run("detector_evergreen.py", [fecha], 300, 1)
    _run("optimizador_adsense.py", [fecha], 300, 1)
    
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
                excluir = ['youtube.com/@SomosElEncuadre', 'tiktok.com/@somoselencuadre',
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

        # Resumen del pipeline
        n_short = len(list((ROOT / "output" / "encuadre").glob(f"short_*_{fecha}.mp4")))
        n_post = pub_count
        r = publicar_pipeline_completado(pub_count, n_short, n_post)
        if r.get("ok"):
            print(f"   ✅ Resumen publicado ({pub_count} análisis, {n_short} shorts)")

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
