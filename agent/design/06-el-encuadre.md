# El Encuadre — Diseño Técnico

## Tesis
Análisis técnico de manipulación mediática via sesgos cognitivos y framing.
EDUCATIVO, NO CRÍTICO, NO PARTIDISTA.

## Nombres
- ES: El Encuadre (elencuadre.com)
- EN: The Framing Effect (framingeffect.com)
- Futuro: PT, FR, DE

## Pipeline
1. RSS 3 medios divergentes
2. Filtro mismo hecho (NLP similarity)
3. analista_medios → matriz carga emocional JSON
4. graficos_sesgo.py → índice comparativo 0-100
5. abogado_medios → filtro legal pre-publicación
6. Generación: artículo largo (web) + corto (Blogger) + short 30s + Telegram

## Datos Kaggle
- MediaSpin (13 categorías sesgo)
- How Biased Is Your Thinking (6344 personas, 10 sesgos)
- news-deframe (librería comparativa framing)

## Agentes nuevos
- analista_medios: análisis framing/priming/anclaje
- abogado_medios: filtro legal

## Monetización
- Fase 0 (0€): Blogger, GitHub Pages, AdSense, afiliados, Telegram
  - Fase 1 (0€): Printify, KDP
  - Fase 2 (~40€): AdMob (25€) + dominio (15€/año)

## Competencia
NO industrial automatizada. Manuales: NewsCord, IndiTag, MediaSpin, Helium MCP.