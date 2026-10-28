# Brain — Cerebro Analitico KeiZ

Agentes que analizan mercados, generan ideas y reportan al movil.

## Agentes
- agent_tendencias.py  -> Analisis YouTube Trends
- agent_ideas.py       -> Brainstorming de nichos
- agent_reporte.py     -> Genera reportes Markdown

## Uso
    python -m brain.agent_tendencias data/keiz_productions/tendencias_*.json
    python -m brain.agent_ideas "trading apps"
    python -m brain.agent_reporte

## Proximos
- agent_mercado.py       -> Google Trends en vivo
- agent_competencia.py   -> Analisis competidores
- agent_pdf.py           -> PDF al movil
