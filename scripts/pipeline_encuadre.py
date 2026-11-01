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

def _subir_youtube(archivo, titulo, desc, tags=None, publish_at=None, retries=3):
    sys.path.insert(0, str(ROOT / "scripts"))
    from subir_youtube import subir
    for intento in range(retries):
        try:
            r = subir(archivo, titulo, desc, tags=tags, privacidad="private", publish_at=publish_at, token_file=TOKEN_ENC)
            print(f"✅ YouTube: https://youtu.be/{r['id']}")
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
        ("analista_fase1.py", None, 1200, False),
        ("scraper_articulos.py", [fecha], 300, True),
        ("sintetizador.py", None, 600, False),
        ("fase2_produccion.py", None, 1200, False),
        ("director_arte.py", None, 1800, True),
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
    from voz_edge import _limpiar as _limpiar_texto_voz

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
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            from gestor_musica import obtener_musica
            _m = obtener_musica(mood=mood, duracion_objetivo=40, contexto=f"short_{num}")
            musica_short = _m["archivo"]
            print(f"     ✅ {musica_short.name} ({_m.get("licencia","?")})", flush=True)
        except Exception as e:
            print(f"     ⚠️ gestor_musica short falló: {e}", flush=True)
            # Fallback Tunetank directo
            try:
                r = descargar_por_mood(mood, 1)
                if r: musica_short = ROOT / "output" / "musica_temp" / r[0]["archivo"]
            except: pass
        musica_arg = str(musica_short) if musica_short else ""

        # Imagen vertical con fallback (SIEMPRE debe haber una)
        img_vertical = ROOT / "web" / "media" / "imagenes" / "short_bg_01.png"
        
        if not img_vertical.exists():
            imgs = list((ROOT / "web" / "media" / "imagenes").glob("escena_*.png"))
            if imgs:
                img_vertical = imgs[0]
            else:
                # No hay ninguna imagen: GENERAR UNA NUEVA con SDXL
                print(f"     🖼️ No hay imagen para el short {num}. Generando una nueva con SDXL...", flush=True)
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
                            print(f"     ✅ Imagen generada: {destino.name}", flush=True)
                except Exception as e:
                    print(f"     ⚠️ SDXL falló: {e}", flush=True)
                
                # Si SDXL también falla, generar un fondo negro de emergencia
                if not img_vertical.exists() or img_vertical == (ROOT / "web" / "media" / "imagenes" / "short_bg_01.png"):
                    print(f"     ⚠️ Usando fondo de emergencia (negro).", flush=True)
                    img_vertical = ROOT / "output" / "render_tmp" / f"emergencia_{num}.png"
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
                        "-frames:v", "1", str(img_vertical)
                    ], capture_output=True)

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
    _run("enriquecer_dossier.py", [fecha], 300, 1)
    _run("scrapear_medios_completo.py", [fecha], 300, 1)
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
    _run("rollback_auto.py", None, 300, 1)

    import datetime as _dt
    if _dt.date.today().weekday() == 6:
        print("\n[domingo] Feedback loop + meta-agentes...", flush=True)
        _run("analytics_youtube.py", None, 600, 1)
        _run("auto_ajuste_prompts.py", None, 600, 1)
        _run("rotador_ab.py", None, 300, 1)
        _run("meta_agentes_semanal.py", None, 900, 1)

    print(f"\n✅ PIPELINE MASIVO {fecha} COMPLETADO CON ÉXITO")

if __name__ == "__main__":
    main()
