#!/usr/bin/env python3
"""Gestor de búsqueda en repositorios (GitHub, PyPI, F-Droid)."""
import os, json, requests

def _get_token():
    # Lee el token de .env de forma segura
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if line.startswith("GITHUB_TOKEN="):
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return token

def buscar(plataforma: str, query: str) -> str:
    plataforma = plataforma.lower()
    
    if plataforma == "github":
        headers = {"Accept": "application/vnd.github.v3+json"}
        token = _get_token()
        if token:
            headers["Authorization"] = f"token {token}"
        
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            items = r.json().get("items", [])
            if not items:
                return f"No se encontraron repositorios de GitHub para '{query}'."
            
            res = [f"Resultados de GitHub para '{query}':"]
            for i in items:
                res.append(f"- {i['full_name']} (⭐ {i['stargazers_count']}): {i['description'] or 'Sin descripción'}. URL: {i['clone_url']}")
            return "\n".join(res)
        except Exception as e:
            return f"Error buscando en GitHub: {e}"
            
    elif plataforma == "pypi":
        url = f"https://pypi.org/pypi/{query}/json"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 404:
                return f"El paquete '{query}' no existe en PyPI."
            r.raise_for_status()
            info = r.json().get("info", {})
            return f"PyPI - {info.get('name')} (v{info.get('version')}): {info.get('summary')}\nInstalación: pip install {info.get('name')}"
        except Exception as e:
            return f"Error buscando en PyPI: {e}"

    elif plataforma == "fdroid":
        # F-Droid no tiene una API de búsqueda directa robusta, usamos su endpoint de paquetes
        url = f"https://f-droid.org/api/v1/packages/{query}"
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return f"F-Droid - {data.get('id')} (v{data.get('suggestedVersionCode')}): Disponible para Termux/Android.\nInstalación: pkg install {query}"
            return f"El paquete '{query}' no se encontró en F-Droid o no es compatible."
        except Exception as e:
            return f"Error buscando en F-Droid: {e}"
            
    return "Plataforma no soportada. Usa: github, pypi, o fdroid."
