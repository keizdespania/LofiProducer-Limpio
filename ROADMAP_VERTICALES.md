## ESTRATEGIA VERTICALES + YOUTUBE MONETIZACION (2026-10-29)

### REGLA DE ORO

1 largo + 2-3 shorts + 12 web + 5 blogger + 4 redes al dia.
NO 12 videos/dia = ban.

Limites YouTube: >2 largos/dia shadowban, >6 shorts/dia ban.
YPP: 1000 subs + (4000h O 10M Shorts).


### 12 VERTICALES

1. Politica Nacional (El Pais, ABC, OkDiario) ⭐
2. Geopolitica (Reuters, Foreign Affairs, Economist) ⭐⭐
3. Economia (Expansion, Cinco Dias, Bloomberg) ⭐
4. Tecnologia/IA (TechCrunch, Wired, Xataka) ⭐⭐
5. Cultura/Medios META (Variety, CJR, Nieman Lab) ⭐⭐⭐
6. Energia/Clima (Climate Home, Carbon Brief)
7. Union Europea (Politico EU, Euractiv)
8. America Latina (El Pais America, La Nacion, Folha)
9. Justicia/Corrupcion (El Confidencial, elDiario, Vozpopuli)
10. Vivienda/Laboral (elDiario, El Salto, Cinco Dias)
11. Salud (El Global, Redaccion Medica, The Lancet)
12. Sociedad/Migracion (elDiario, La Marea, The Guardian UK)

Deportes NO.

### INVESTIGACION 3 CAPAS

Capa 1: RSS filtrado por vertical (10-20 medios especificos, no los 36).
Capa 2: Scraping selectivo top-3 del dia (36 articulos/dia, no 432).
Capa 3: Lectura profunda LLM texto completo (36 llamadas/dia).

Por vertical: ~1 min, ~5000 tokens. 12 verticales: ~12 min, ~60000 tokens.


### ROADMAP 9 MESES

Mes 1-2 Fundacion (0-200 subs): 3 largos/sem, 2 shorts/dia, 2 verticales (Cultura+Politica). Obj: 500h watch, 1 short >50k.

Mes 3-4 Crecimiento (200-700 subs): 4 largos/sem, 3 shorts/dia, serie "Anatomia de un titular", 4 verticales (+Geopol+Economia). Obj: 1500h, 1 video >10k.

Mes 5-6 Aceleracion (700-1500 subs): 5 largos/sem, 3-4 shorts/dia, colaboraciones, 6 verticales (+Tech+Justicia). OBJ: 1000 subs + 4000h = MONETIZACION.

Mes 7-9 Escalado (1500-5000 subs): 7 largos/sem (1/dia), 4 shorts/dia, primer patrocinio, 12 verticales. Obj: 15000h, AdSense+patrocinios.

### CPM POR VERTICAL

Tecnologia/IA: 8-15 EUR
Economia: 6-12 EUR
Geopolitica: 5-10 EUR
Politica: 3-6 EUR
Cultura/Medios: 2-4 EUR
Sociedad: 2-4 EUR

Estrategia: 1 vertical crecimiento (Politica) + 1 monetizacion (Tech/IA).

### CRON REALISTA

06:00 Recolector + analista (36 medios, 1 vez)
06:30 Analisis verticales activos (3-6 segun mes)
07:00 Render 1 largo estrella (mejor viralidad)
08:00 Render 2-3 shorts
09:00 Publicar largo YouTube (publish_at 18:00)
10:00 Publicar shorts (13:00, 16:00, 20:00)
11:00 Web masiva (12 posts cada 2h)
12:00 Blogger (5 posts cada 3h)
13:00 Redes (X, IG, LinkedIn, Threads)

YouTube: 1 largo + 3 shorts/dia. Web 12. Blogger 5. Redes 4.

### NO HACER

- Scrapear 36x12=432 fuentes -> RAM explota
- Leer 45 titulares completos -> 540 llamadas para descartar
- Mismo pool medios todos verticales -> redundancia x12
- Paralelizar 12 verticales Termux -> 432 hilos -> swap
- Scraping sin deduplicar -> 10 medios = 10x mismo analisis

### SI HACER

1. config/verticales.json (12 con medios, keywords, tonos)
2. recolector.py --vertical X (filtra medios)
3. scraper_articulos.py (texto completo top-3, cache 24h)
4. analista_fase1.py --vertical X (titular + cuerpo + contraste)
5. Deduplicacion simhash (10 medios = 1 noticia -> 3 analisis izq/centro/der)

### PROXIMA SESION

1 vertical end-to-end (Politica Nacional):
- config/verticales.json
- recolector filtrado
- scraper_articulos
- analista profundo
- Pipeline 1 vertical -> 1 largo + 2 shorts + 12 web

Si funciona 1 -> replicar a los 11.
