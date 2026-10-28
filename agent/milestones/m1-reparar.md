# M1 - Reparar

## Tareas
1. dios_indonesio_fix
   - Anadir al system prompt: Responde SIEMPRE en espanol
   - temperature=0 en llamadas LLM
   - Test: pedir OK -> verificar que responde en espanol

2. verificar_combo_deepseek
   - Test curl: model=combo/deepseek-first con deepseek/deepseek-v4-flash:free
   - Si falla, revertir dios.py a model=auto

3. health_check_worker
   - En task_worker.py: cada iteracion, buscar tareas running >2h -> error

## Verificacion
- Chat con Dios: responde en espanol
- Combo deepseek responde o fallback a Groq
- task_worker sin zombies

## Despues
- Actualizar progress.yaml: m1_reparar -> completado
- Pasar a m2_conectar
