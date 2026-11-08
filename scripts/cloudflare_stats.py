"""cloudflare_stats.py - Lee Web Analytics (RUM) vía GraphQL."""
import os, requests, pathlib
from datetime import date, timedelta

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://api.cloudflare.com/client/v4/graphql"
HOST = "elencuadre.pages.dev"

def _env(k):
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith(f"{k}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(k, "")

TOKEN = _env("CLOUDFLARE_ANALYTICS_TOKEN")
ACCOUNT = _env("CLOUDFLARE_ACCOUNT_ID") or "IDRn33gh4WCzZNDq850qPIT7W75yD6Ek0CGBNIf55fae16f7"

def _query(gql: str) -> dict:
    r = requests.post(URL,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        json={"query": gql}, timeout=20)
    r.raise_for_status()
    j = r.json()
    if j.get("errors"):
        raise RuntimeError(j["errors"])
    return j

def resumen(dias=7):
    """Page views, visitas, top páginas y países (últimos N días)."""
    inicio = (date.today() - timedelta(days=dias)).isoformat()
    gql = """
    {
      viewer {
        accounts(filter: {accountTag: "%s"}) {
          rumPageloadEventsAdaptiveGroups(
            filter: {date_geq: "%s", requestHost: "%s"}
            limit: 20
            orderBy: [count_DESC]
          ) {
            count
            dimensions { requestPath countryName }
            sum { visits }
          }
        }
      }
    }
    """ % (ACCOUNT, inicio, HOST)
    data = _query(gql)
    grupos = data["data"]["viewer"]["accounts"][0]["rumPageloadEventsAdaptiveGroups"] or []
    vistas = sum(g.get("count", 0) for g in grupos)
    visitas = sum(g.get("sum", {}).get("visits", 0) for g in grupos)
    top_pag = [(g["dimensions"]["requestPath"], g["count"]) for g in grupos[:5]]
    top_pais = [(g["dimensions"]["countryName"], g["count"]) for g in grupos[:5]]
    return {
        "dias": dias,
        "page_views": vistas,
        "visitas": visitas,
        "top_paginas": top_pag,
        "top_paises": top_pais,
    }

if __name__ == "__main__":
    import json
    print(json.dumps(resumen(7), indent=2, ensure_ascii=False))
