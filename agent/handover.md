# HANDOVER

## Empezar sesion
1. Leer BOOT_PROMPT.md + agent/progress.yaml + este fichero.
2. Verificar estado: bash ~/.shortcuts/despertar.sh && curl -s http://127.0.0.1:8001/api/dashboard
3. Empezar por proximo_paso de progress.yaml.

## Reglas
- Verificar LLM con curl directo antes de tocar dios.py
- System prompt SIEMPRE con Responde en espanol
- Actualizar progress.yaml tras cada milestone
- 23 reglas Frodo del BOOT_PROMPT v6.0

## Comandos
bash ~/.shortcuts/despertar.sh
python3 brain/investigador_redes.py ia_news
python3 scripts/short_engine.py TEMA ia_news
python3 scripts/crear_paquete_blog.py TEMA
curl -s http://127.0.0.1:8001/api/factory

## Logs si falla
data/logs/worker.log
data/logs/omniroute.log
data/agent/cola.db
data/agent/cola_publicacion.db
