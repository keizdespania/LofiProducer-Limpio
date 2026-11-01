# HANDOFF — SOMOS EL ENCUADRE · 2026-11-01

## ESTADO EN 30 SEGUNDOS

Pipeline engrasado con 9 pasos nuevos. 2 posts web del 31-O publicados en Cloudflare. Auto-corrector idempotente. Cero alucinaciones. 3 fallos externos (YouTube limit, Blogger anti-spam, R2 sin configurar) — ninguno se arregla con código.

## COMMITS DE HOY

- 54c5330 chore: contrato posts_web v1.0 + musica_libre + blogger fix
- 4e7770c feat(pipeline): flujo web v3 engrasado (9 pasos nuevos)
- ebe6782 content: analisis/index.md
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

## PRIMEROS PASOS PROXIMA IA

1. Leer HANDOFF completo
2. tail -100 data/logs/pipeline.log
3. ls -lh output/cola_web/$(date +%Y-%m-%d)*
4. Preguntar al usuario:
   - Pipeline completo?
   - Videos YouTube o uploadLimitExceeded?
   - Posts web en Cloudflare?
5. Si fallo codigo: diagnosticar sin improvisar
6. No tocar lo que funciona

## REGLAS APRENDIDAS HOY

- #29 NUNCA cat > con triple comillas anidadas
- #30 Regex peligrosos: comillas tipograficas, doble espacio, mayuscula post-punto rompen HTML
- #31 _medios_con_tecnica debe devolver url + texto
- #32 Autocorrector debe ser idempotente
- #33 grep -c href antes de publicar

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
