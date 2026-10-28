# Arquitectura 6 capas

1. Cerebro: dios.py (43 tools, ReAct 25, memoria SQLite, pruner)
2. Detective: brain/investigador_redes.py (5 fuentes)
3. Productor: short_engine + crear_paquete_blog + motor_ensamblado
4. SEO Top 1: (pendiente m3) especialistas seo_youtube/podcast/blog + thumbnails
5. Distribuidor: cola_publicacion + subir_youtube + publicar_blogger
6. Web + Agent Protocol: web_dashboard.py (22 vistas) + agent/

## Flujo diario
INVESTIGADOR -> PREDICTOR -> INFORME -> PRODUCTOR -> COLA -> YOUTUBE/BLOG

## Motores (10)
ACE-Step, Sherpa, SDXL, Wan, Stock, FFmpeg, YouTube, Blogger, Cloudflare, Cooldowns.
