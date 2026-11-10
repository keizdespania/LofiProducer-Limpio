# METODOLOGÍA IA — Cómo trabajar en LOFIPRODUCER
> Documento de comportamiento. Léelo ANTES de tocar código.
> Creado 2026-11-09 tras sesión épica (18h) con aciertos y fracasos documentados.

## 1. QUÉ ES ESTE ECOSISTEMA (30 segundos)
Sistema local-first que produce, traduce y distribuye contenido multimedia monetizable.
Corre en Termux (Samsung A25). Músculo en Kaggle T4 x2. Web en Cloudflare Pages.
Todo orquestado por Dios (76 tools, ReAct). Todo documentado en contratos.
Filosofía: "El ecosistema crece por config, no por código".

## 2. REGLA #0 (LA MÁS IMPORTANTE)
LEE ANTES DE TOCAR. NO IMPROVISES.

Orden de lectura obligatorio:
1. HANDOFF.md (estado actual, ~170L)
2. BOOT_PROMPT.md (arquitectura, ~174L)
3. METODOLOGIA_IA.md (este fichero)
4. data/agent/dios_contract.json (76 tools)
5. Contrato específico del motor que vayas a tocar

Si algo no está en contrato → pregunta al humano. No asumas.

## 3. CÓMO HABLA EL HUMANO (y cómo debes responder)

### Por defecto (modo normal)
- Explicas qué vas a hacer (breve)
- Lo haces en 1-3 cajones
- Verificas
- Reportas con salida pegada

### Modo FLASH (cuando dice "modo flash" o "flash concatenado")
- UNA respuesta con UN cajón de bash que hace TODO
- CERO preámbulos, cero "primero voy a..."
- Sin heredocs gigantes (>50L → script externo en $HOME/tmp)
- Sin nano, sin editores interactivos
- Verificación integrada al final
- Formato: encabezado 1L + cajón + (pregunta solo si bloqueante)

### El humano habla claro y rápido
- "dale caña", "arreglalo", "hazlo top 1", "no me lies con texto"
- Significa: ejecuta, no expliques
- Si dices "voy a hacer X" 3 veces sin hacerlo → te corta

## 4. CICLO DE TRABAJO GANADOR (Plan-Before-Code)

1. Diagnóstico (read-only): leer ficheros, grep, curl, ps, logs
2. Plan (breve): 1-3 líneas de qué vas a tocar
3. Backup (si zona sagrada): .bak_<fecha> o git stash
4. Parche (quirúrgico, mínimo)
5. Compilar (py_compile si .py, node --check si JS)
6. Servir (sv restart keiz-web o equivalente)
7. Test (curl, dios.py, o test directo de la función)
8. Commit (mensaje claro)
9. Push (con --no-verify si smoke test falla por Cloudflare)

Si falla el paso 5 o 7: NO sigas parcheando. Vuelve al paso 1 con diagnóstico dirigido.

## 5. PARCHES vs REESCRITURA (Regla Frodo #20)

Parche quirúrgico cuando:
- Cambias 1 función, 1 variable, 1 línea
- Fichero <300L y funciona bien
- Tienes el bloque exacto
- Herramienta: python3 -c "p=Path('x'); t=p.read_text(); t=t.replace(OLD, NEW); p.write_text(t)"

Reescribir entero cuando:
- 3+ parches encadenados sobre el mismo fichero/función
- Fichero >300L y ya has tocado 2 veces
- SyntaxError que no resuelves con 1 replace
- El humano dice "reescríbelo" o "hazlo nuevo"
- Cambias la arquitectura (no solo valores)

Cómo reescribir sin romper:
1. cp fichero.py $HOME/tmp/backup_$(date +%s).py
2. cat > $HOME/tmp/nuevo.py << 'PYEOF' ... PYEOF
3. python3 -c "import py_compile; py_compile.compile('$HOME/tmp/nuevo.py', doraise=True)"
4. cp $HOME/tmp/nuevo.py fichero.py
5. sv restart <servicio> + test + commit

NO reescribir sin backup. NO reescribir sin py_compile previo.

## 6. TERMUX SURVIVAL (crítico)

### Heredocs: máximo 50 líneas
- MAL: 200 líneas inline en python3 -c "..." → Termux se atasca/rompe
- BIEN: cat > $HOME/tmp/patch.py << 'PYEOF' ... PYEOF && python3 $HOME/tmp/patch.py

### \n en heredocs es una trampa
- MAL: f"texto\n\n" → el \n se convierte en salto real → SyntaxError unterminated string
- BIEN: NL = chr(10) + chr(10) o splitlines() o variables

### Rutas
- /tmp NO escribible en Termux → usa $HOME/tmp/
- mkdir -p $HOME/tmp antes de escribir
- Rutas relativas al ROOT del repo, no al cwd

### Python
- Siempre python3 -u (unbuffered, verás prints)
- py_compile tras CADA .py tocado

### Node/JS
- node --check sobre el output: curl -s URL > $HOME/tmp/x.js && node --check $HOME/tmp/x.js
- Si falla → línea exacta → fix quirúrgico

### Servicios
- sv restart <nombre> — NUNCA pkill a ciegas
- sv status <nombre> — verificar corriendo
- Si no arranca: tail -20 $PREFIX/var/log/sv/<nombre>/current

## 7. ANTI-PATRONES REALES (errores que NO repetir)

### Heredoc gigante inline
- Se atasca Termux, se corrompe el paste
- Fix: cat > $HOME/tmp/x.py << 'PYEOF' ... PYEOF && python3 $HOME/tmp/x.py

### \n literales dentro de python3 -c "..."
- El \n se convierte en salto real → SyntaxError unterminated string
- Fix: chr(10) o NL = chr(10) o splitlines()

### sed -i sobre .py con strings complejas
- Regla Frodo #13. Rompe. Siempre.
- Fix: python3 -c "p.write_text(t.replace(OLD, NEW, 1))"

### 3+ parches encadenados sin reescribir
- Cada parche deja residuos huérfanos
- Ejemplo real: _abrir_en_navegador quedó huérfano tras 4 parches → TypeError en producción
- Fix: reescribir entero (Regla #20)

### Decorador de ruta pegado sobre función auxiliar
- Si @encuadre_bp.route queda encima de def _aux(): → Flask llama a esa con 0 args → TypeError
- Verificación: grep -B1 -A2 "@.*route" fichero.py

### Confundir HTML_FACTORY con FACTORY_JS
- HTML_FACTORY = estructura estática (una vez al cargar)
- FACTORY_JS = JS servido en /encuadre/factory.js (dinámico)
- Si parcheas en HTML algo que es de JS → no aparece
- Fix: grep -n "<bloque>" fichero.py para saber dónde está

### No hacer hard refresh
- JS cacheado = código viejo → confusión "el patch no se aplicó"
- Fix: factory.js?v=N (cache-buster) o incógnito o "Vaciar caché y recargar"

### git push sin pull --rebase
- Kaggle pushea clips cada 10min → rechazo garantizado
- Fix: git pull --rebase --autostash origin main && git push --no-verify

## 8. PATRONES GANADORES (lo que SÍ hacer)

### Anclar por línea exacta con contexto
- MAL: replace("largo", "...") → puede matchear 20 sitios
- BIEN: replace('    "num": 0, "tipo": "largo",', '...', 1)

### Verificar antes de afirmar
grep -n "OLD_STRING" fichero.py | head -3
Si no sale → NO parchear, primero entender por qué

### Script externo para parches >20L
cat > $HOME/tmp/patch.py << 'PYEOF'
import pathlib, py_compile
P = pathlib.Path('/ruta/fichero.py')
t = P.read_text()
OLD = '''...'''
NEW = '''...'''
if OLD not in t:
    print("ABORT: bloque no encontrado"); exit(1)
t = t.replace(OLD, NEW, 1)
P.write_text(t)
py_compile.compile(str(P), doraise=True)
print("OK")
PYEOF
python3 $HOME/tmp/patch.py

### Diagnosticar antes de cada cambio
grep -n "def _build\|def _extraer_todos" fichero.py
wc -l fichero.py

### Un cambio → un test
- py_compile (sintaxis)
- sv restart
- curl o dios.py (comportamiento)
- Si falla → diagnosticar, no parchear a ciegas

### Rollback disponible
git add . && git commit -m "wip: antes de tocar X"
Ahora puedes volver con: git reset --hard HEAD

### Smoke test pre-push
El hook .git/hooks/pre-push ya valida:
- 9 py compilan
- 4 JSON válidos
- 4 endpoints responden
- web/docs ≥3 posts
Si algo falla → bloquea push. Respétalo. Si falla por Cloudflare timeout → --no-verify y avisa.

## 9. ZONA SAGRADA vs ZONA SEGURA

Zona SAGRADA (pedir OK explícito antes de tocar):
- scripts/pipeline_encuadre.py (cron 06:00)
- data/agent/*_contract.json (los 41 contratos)
- scripts/agente_ltx_biblioteca.py (lotes LTX)
- .git/hooks/pre-push (bloquea push)
- brain/notificador_top1.py (throttle Telegram)
- web/docs/ (histórico web)
- output/videos/biblioteca/ (~117 clips LTX)
- scripts/generar_redes_cruzadas_llm.py (pre-filtro + hooks)
- scripts/generar_imagenes_sociales.py (8 imgs/día)

Zona SEGURA (tocar sin preguntar, pero con verificación):
- encuadre_routes.py (Factory backend)
- FACTORY_JS (Factory frontend)
- scripts/bot_dios.py
- scripts/dios_autonomo.py
- data/agent/dios_sugerencias.db (daemon)

## 12. CONTRATOS (41 ficheros en data/agent/)

Cada motor tiene contrato. Léelo ANTES de tocar.

Ejemplos:
- video_contract.json v3.1: pipeline vídeo + miniaturas + publishAt 2 pasos
- youtube_contract.json v2.1: 403 thumbnails = verificación canal
- ltx_continuidad_contract.json v3.3: 49f, sample_params anidado, base64 init_image
- dios_contract.json v2.0: 76 tools
- dios_autonomo_contract.json v1.0: 40 reglas
- shorts_contract.json v4.0: redes cruzadas
- thumbnails_contract.json v1.0: prompt top-1 + throttle
- notificador_telegram_contract.json v1.0: 2 canales separados

Si algo no está en contrato → preguntar. No inventar.

## 13. COMANDOS DE DIAGNÓSTICO (memorizar)

# Estado general
sv status keiz-web bot_dios dios_autonomo
pgrep -af pipeline_encuadre
curl -s http://127.0.0.1:8001/api/dashboard | python3 -m json.tool | head -30

# Logs
tail -30 data/logs/pipeline.log
tail -20 $PREFIX/var/log/sv/keiz-web/current
grep -iE "error|traceback|fail" data/logs/*.log | tail -20

# Kaggle
python3 -c "import sys; sys.path.insert(0,'scripts'); import kaggle_bearer as kb; print(kb.estado_kernel('keizproductions/ltx-biblioteca-v1-lote5'))"

# Git
git log --oneline -3
git status --short | head -10

# Web
curl -sI https://elencuadre.pages.dev/ | head -1
## 10. PROTOCOLO DE COMUNICACIÓN CON EL HUMANO

### Formato de respuesta
1. Encabezado 1 línea: qué vas a hacer
2. Cajón de bash: código exacto copy-paste
3. Pregunta final (SOLO si es bloqueante)

### Tono
- Directo, sin florituras
- Sin "Buena pregunta" ni "Claro, te ayudo"
- Sin disculpas repetidas
- Si te equivocas: 1 línea + fix inmediato

### Cuándo NO responder
- Sin contexto: pide diagnóstico read-only primero
- Si el humano dice "modo flash": 1 cajón, cero preámbulos
- Si algo falla 2 veces: parar, preguntar, no improvisar

### Cuándo preguntar
- Antes de tocar zona sagrada
- Antes de borrar ficheros
- Antes de git push sin --no-verify
- Antes de cambiar contratos
- Si contradice el contrato: preguntar


## 11. VERIFICACIÓN (no hay "ya está" sin prueba)

Cada cambio pasa por:
- py_compile si es .py
- node --check si es JS
- json.loads si es JSON
- curl si es endpoint
- sv status si es servicio
- test unitario si es función crítica

Si no puedes verificar, no está hecho. Punto.

Comandos:
  python3 -c "import py_compile; py_compile.compile('x.py', doraise=True); print('OK')"
  curl -s URL > $HOME/tmp/x.js && node --check $HOME/tmp/x.js
  python3 -c "import json; json.load(open('x.json')); print('OK')"
  curl -s -w "\n[%{http_code}]" URL | tail -2
  sv status <nombre> | head -2

## 14. CHECKLIST ANTES DE CERRAR UNA TAREA

- [ ] py_compile pasa (si .py)
- [ ] node --check pasa (si JS)
- [ ] sv status OK (si toqué servicio)
- [ ] Endpoint responde 200 (si toqué API)
- [ ] git commit con mensaje claro
- [ ] git push OK
- [ ] Si toqué contrato, actualizado también
- [ ] Si toqué pipeline, HANDOFF.md actualizado
- [ ] Si toqué nueva feature, BOOT_PROMPT.md actualizado


## 15. FILOSOFÍA FINAL

"El ecosistema crece por config, no por código."
Antes de escribir código nuevo: hay ya tool/script/contrato que lo hace?

"Lo que se regenera, se borra. Lo único, se pregunta."
Antes de borrar: es regenerable? Si sí, limpieza. Si no, preguntar.

"15 pasos por delante" (Frodo Bolsón mode).
Antes de tocar 1 fichero: piensa qué 3 ficheros dependen de él.

"Un output, 6 monetizaciones posibles."
Antes de crear contenido: piensa cómo se monetiza (AdSense, afiliados, Printify, KDP, Telegram, Spotify).

"Plan-Before-Code · Verificación · Test-First · Simplicidad · Contexto · Pushback · Fail Fast · Código Limpio · No Alucines"
Si no puedes explicarlo en 1 frase, no lo hagas.

---

Firma: si eres una IA leyendo esto, sabes cómo trabajar aquí. Si no lo sigues, el humano te cortará. No es personal, es eficiencia.

