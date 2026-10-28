# Canal Nuevo (Auto-provision)

## Humano hace (5 min):
1. Crear cuenta YouTube + OAuth
2. Crear cuenta TikTok
3. Crear blog Blogger

## Web hace (POST /api/crear_canal):
1. Crea config/montajes/CANAL.json (receta FFmpeg)
2. Anade a config/nichos.json (presets + queries)
3. Crea output/nichos/CANAL/
4. Crea entrada cola_publicacion.db
5. Verifica OAuth YouTube (token valido)
6. Primer informe (informe_detective)

## Resultado
El canal es uno mas del pipeline. Sin codigo especifico.
