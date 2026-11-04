# HANDOFF — SOMOS EL ENCUADRE · 2026-11-04

## ESTADO EN 30 SEGUNDOS (2026-11-04)

**Guion monólogo limpio (1534 palabras, 18 escenas, 9/9 checks).** Editor Jefe v2 (4 capas + cap entidad + dedup Jaccard). Forense 19/19 medios con técnica (antes 3/19). Sanitizador determinista (no solo verificador). **Podcast en Cloudflare** con feed RSS de 3 episodios. Pipeline engrasado. 3 fallos externos siguen (YouTube uploadLimit, Blogger 403, R2 sin configurar) — ninguno se arregla con código.

**Lo nuevo respecto al 01/11:**
- Editor Jefe v2: variedad real de medios y temas (antes fallback Python sin variedad)
- Forense few-shot: 19/19 medios con técnica (antes 3/19)
- Sanitizador determinista: 15+ reglas (antes solo verificador)
- Podcast con feed RSS en Cloudflare Pages (antes sin distribución)
- 5 hacks antialucinación en LEY_ESTILO
- Anécdota rotativa con noticias reales (antes inventaba noticias del día)

## COMMITS DE HOY (2026-11-04)

- db7be1b chore(podcast): borrar 2026-11-04 y 2026-11-07 falsos, feed con 3 items
- 5cfde17 feat(podcast): MP3 a git (fallback temporal hasta R2)
- 477b3fa feat(monologo): 5 fixes auditoría (anécdota real, geografía, doble cierre, exmandatario, si-no-no)
- 5822f0c fix(podcast): reescritura limpia (búsqueda música + feed RSS + sin música)
- bfdad6c feat(monologo): 19 reglas Alsina + sanitizador determinista
- ac2c6a8 fix(medios): 19/19 con técnica tras few-shot + robusto + limpieza
- b5dc710 feat(editor-jefe): v2 top1 - 4 capas + rúbrica LLM + cap entidad + dedup Jaccard

### Commits anteriores (2026-11-01)
- 54c5330 chore: contrato posts_web v1.0 + musica_libre + blogger fix
- 4e7770c feat(pipeline): flujo web v3 engrasado (9 pasos nuevos)
- ce58a65 feat(web): post largo 8 fuentes + dossier v2 publicados
- 40e927a feat(web): 5 scripts anti-alucinaciones
- 0ca12cb feat(web): auto-corrector idempotente

## PIPELINE ACTUAL (cron 06:00)

recolector -> analista -> sintetizador -> dossier
-> enriquecer_dossier (51 tecnicas)
-> scrapear_medios_completo (texto real 4K)
-> fase2_produccion (18 escenas + articulo)
-> voz + musica + imagenes + render_robusto
-> render_shorts_batch (4 shorts)
-> generar_seo (10 capitulos)
-> generar_redes (24 bloques + filtro legal)
-> _subir_youtube (largo + 4 shorts publishAt)
-> generar_web_v3 (largo + mediano)
-> generar_web_dossier (dossier v2)
-> verificar_alucinaciones
-> auto_corregir_post (9 correcciones)
-> _publicar_web (mkdocs build + git push + Cloudflare)

## LO QUE FUNCIONA

- Recoleccion 40+ medios
- Analista Fase 1 + Editor Jefe
- Dossier enriquecido 51 tecnicas
- Scrapeado 8-10 medios texto real
- Video largo 12 min + 4 shorts
- 24 bloques redes + filtro legal
- 2 posts web publicados en Cloudflare
- Auto-corrector idempotente
- Verificador alucinaciones
- Dashboard /encuadre

### NUEVO 2026-11-04
- **Guion monólogo limpio**: 1534 palabras, 18 escenas, 9/9 checks sanitizador
- **Editor Jefe v2**: 4 capas (pre-filtro + scoring + LLM rúbrica + dedup Jaccard + cap entidad)
- **Forense 19/19**: prompt few-shot + `_pick()` robusto con tildes/plurales
- **Sanitizador determinista**: 15+ reglas (verbos+que, sino que, exmandatario, doble cierre...)
- **5 hacks antialucinación** en LEY_ESTILO: anclaje extracto, checklist, cierre por medio, prohibir sugiere, si no hay conexión dilo
- **Anécdota rotativa** con noticias reales (no inventa noticias)
- **Podcast en Cloudflare**: `https://elencuadre.pages.dev/podcast/2026-11-03.mp3` HTTP/2 200
- **Feed RSS**: 3 episodios (2026-10-31, 11-01, 11-03) con URLs Cloudflare Pages
- **Fallback sin música**: si lofi del día no existe, descarga pool CC o solo voz

## LO QUE NO FUNCIONA (externo, no codigo)

### 1. YouTube uploadLimitExceeded
- Canal nuevo sin verificar, limite 10-15/dia
- Solucion: youtube.com/verify (telefono + documento)
- Impacto: largo + shorts del 1-NOV pueden fallar
- NO se arregla con codigo

### 2. Blogger anti-spam 403
- API bloquea posts.insert en blogs nuevos
- Solucion: esperar 7-14 dias, o manual desde output/cola_blogger/
- Impacto: 5 posts Blogger no se publican por API
- NO se arregla con codigo

### 3. R2 sin configurar
- No hay bucket R2 (pide tarjeta)
- Solucion: seguir con catbox hasta monetizar
- Impacto: imagenes del blog usan catbox
- NO se arregla con codigo

## CONTRATO

data/agent/posts_web_contract.json v1.0 (15 secciones)

## COMANDOS DIAGNOSTICO

    crontab -l | grep pipeline
    tail -100 data/logs/pipeline.log
    cd ~/LofiProducer && git status --short
    ls -lh output/cola_web/$(date +%Y-%m-%d)*
    python3 scripts/verificar_alucinaciones.py $(date +%Y-%m-%d)

### NUEVO 2026-11-04

    # Podcast
    ls -lh web/docs/podcast/*.mp3
    curl -I https://elencuadre.pages.dev/podcast/2026-11-03.mp3
    grep -E "<title>El Encuadre" web/docs/podcast/feed.xml
    
    # Monólogo (verificar 9/9 checks)
    python3 -c "import json,re;d=json.load(open('output/encuadre/produccion_'+__import__('datetime').date.today().isoformat()+'.json'));t=d.get('texto_voz_largo','');print(f'PALABRAS:{len(t.split())}');print('sugiere:', 'sugiere' in t.lower())"
    
    # Sanitizador aislado
    python3 -c "import sys;sys.path.insert(0,'scripts');from fase2_produccion import _sanitizar_monologo;print(_sanitizar_monologo('No se menciona que,. Pero sugiere algo.', '2026-11-04'))"
    
    # Editor jefe v2 aislado
    python3 -c "import sys,json;sys.path.insert(0,'scripts');sys.path.insert(0,'.');from editor_jefe_v2 import _editor_jefe_v2;d=json.load(open('output/encuadre/recoleccion_'+__import__('datetime').date.today().isoformat()+'_scrapeada.json'));t=_editor_jefe_v2(d.get('pool',[]),lambda *a,**k:'{}',verbose=True);print(len(t))"

    

## PRIMEROS PASOS PROXIMA IA (2026-11-04)

1. Leer HANDOFF completo (este fichero) + BOOT_PROMPT.md (sección 2026-11-04)
2. `git log --oneline -10` + `git status -sb`
3. `tail -100 data/logs/pipeline.log | grep -E 'error|ERROR|✅|podcast|video_largo'`
4. `ls -lh web/docs/podcast/*.mp3` + `curl -I https://elencuadre.pages.dev/podcast/2026-11-03.mp3`
5. Verificar cron 06:00 de hoy: ¿video_largo_2026-11-04.mp4? ¿4 shorts? ¿blog? ¿podcast?
6. Preguntar al usuario:
   - ¿Cron 06:00 completó OK?
   - ¿Videos YouTube subieron o uploadLimitExceeded?
   - ¿Posts web en Cloudflare?
   - ¿Configurar Spotify for Podcasters (10 min)?
7. Si fallo código: diagnosticar sin improvisar (Regla #18)
8. No tocar lo que funciona (Regla #8)

## REGLAS APRENDIDAS

### 2026-11-01
- #29 NUNCA cat > con triple comillas anidadas
- #30 Regex peligrosos: comillas tipograficas, doble espacio, mayuscula post-punto rompen HTML
- #31 _medios_con_tecnica debe devolver url + texto
- #32 Autocorrector debe ser idempotente
- #33 grep -c href antes de publicar

### 2026-11-04
- #49 LLM alucina conexiones con "¿por qué este medio cuenta esto HOY?" → hacks 3 y 4 mitigan
- #50 LLM inventa noticias del día en anécdotas → SIEMPRE pasar medios_validos a la anécdota
- #51 MP3 podcast en git TEMPORAL (<25MB, límite Cloudflare Pages) hasta R2
- #52 `_cargar_extractos(fecha)` → extractos scrapeados inyectados en ACTO 2 y ACTO 3
- #53 Sanitizador en `producir_fase2` Y `producir_monologo` (no solo uno)
- #54 Cloudflare Pages despliega al push. No hay push forzado. `curl -I` para verificar.
- #55 Sin DDG: `contexto_verificado.py` v3 usa Wikipedia + RSS agencias (DDG bloquea con 202)

## FILOSOFIA

- Top-1 mundial, no MVP
- Cero alucinaciones
- Citas verificables + enlaces
- Descargo legal art. 32 LPI
- 2 posts/dia = 60/mes = AdSense en 2-4 semanas

## CONTACTO

- Repo: ~/LofiProducer -> keizdespania/LofiProducer-Limpio
- Web: https://elencuadre.pages.dev
- Blog: https://iaglobalnews.blogspot.com (ID 5810739452530624729)
- Dashboard: http://127.0.0.1:8001/encuadre

---

Fin del handoff.


## ESTADO WEB FINAL (2026-11-01 05:15)

- 18 irregularidades corregidas (enlaces rotos, placeholders, dominio, logo, robots, 404)
- HTTP 200 en: home, post largo, robots.txt
- Commit: 1e50539
- Plugins: minify + social + rss
- Features modernos: navigation.instant, tracking, search.share, annotate

## PENDIENTE NIVEL 2 + 3 (próxima sesión)

### Nivel 2 — Blog real (2-3h)
- Listado automático de posts
- Tags/categorías navegables
- RSS feed (plugin ya instalado, falta configurar)
- Related posts + breadcrumbs + autor page
- Reading time + analytics privacy-friendly

### Nivel 3 — Universo holográfico (3-4h)
- Fondo 3D partículas (three.js)
- Glassmorphism + gradientes holográficos
- View Transitions API + cursor custom
- Scroll animations + tipografía futurista
- Micro-interacciones

## NOTA CRÍTICA PARA PRÓXIMA IA

El usuario quiere rediseño web tipo "blog más visto del mundo" con estética
"universo holográfico". Mezcla de Medium + Ghost + The Verge + Awwwards.
No es MVP: es top 1 mundial. Invertir tiempo en Nivel 2 y 3.

**NUEVO 2026-11-04:** hay una **sección SESIÓN 2026-11-04** al final de este
fichero con todos los fixes del día. NO los toques sin leerla primero.
Los ficheros más tocados hoy son:
- `scripts/fase2_produccion.py` (sanitizador + LEY_ESTILO + 5 fixes)
- `scripts/editor_jefe_v2.py` (NUEVO, 437L)
- `scripts/generar_podcast.py` (reescrito resiliente)
- `scripts/analista_fase1.py` (usa editor_jefe_v2)
- `scripts/sintetizador.py` (_pick robusto)
- `brain/especialistas.py` (forense few-shot)

## ANEXO — SESIÓN 2026-11-04 (resumen)

Ver `BOOT_PROMPT.md` sección 2026-11-04 + los 7 commits del día.

**Hecho:** Editor Jefe v2, Forense 19/19, Sanitizador determinista, 5 hacks
antialucinación, Podcast feed RSS en Cloudflare, Anécdota con noticias reales,
Geografía Urda≠Atocha, Doble cierre cortado, exmandatario→Trump.

**Pendiente P1 (crítico):** verificar cron 06:00 hoy + Spotify for Podcasters
+ Cloudflare R2 (para no meter más MP3 en git).

**Pendiente P2:** pulir ACTO 3 con técnicas reales del dossier, verificar
predictor viralidad, analytics YouTube.

**No tocar:** producir_fase2, render_short_rot, pipeline_encuadre, web/dashboard.

## ÚNICO BLOQUEANTE EXTERNO QUE PUEDE QUITAR EL USUARIO HOY

Verificar canal YouTube en youtube.com/verify (teléfono + documento).
Sin esto, mañana el pipeline fallará al subir vídeos (uploadLimitExceeded).
