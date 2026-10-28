"""
Cajon 04b - Cliente LLM con fallback.

Ruta 1: OmniRoute -> usa OMNIROUTE_MODELS (combos auto/*)
Ruta 2: Google directo -> usa GOOGLE_MODELS (gemini-*)
"""

from __future__ import annotations

import json
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import (
    GOOGLE_API_KEY,
    GOOGLE_MODELS,
    GOOGLE_OPENAI_URL,
    OMNIROUTE_API_KEY,
    OMNIROUTE_CHAT_URL,
    OMNIROUTE_MODELS,
)
from core.logger import get_logger


log = get_logger("core.llm")


def _build_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=2, connect=0, read=0, status=2,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["POST"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


_SESSION = _build_session()


class RotarModelo(Exception):
    pass


class Abortar(Exception):
    pass


def _call(url: str, api_key: str, model: str,
          prompt: str, system: str, temperature: float) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {"model": model, "messages": messages,
               "temperature": temperature}

    try:
        resp = _SESSION.post(url, headers=headers, json=payload, timeout=90)
    except requests.RequestException as exc:
        raise RotarModelo(f"conexion: {exc}") from exc

    if resp.status_code in (401, 403):
        raise Abortar(f"Auth {resp.status_code}: {resp.text[:200]}")

    if resp.status_code in (400, 404, 422, 429, 500, 502, 503, 504):
        log.warning("  %s HTTP %s -> siguiente. %s",
                    model, resp.status_code, resp.text[:150])
        raise RotarModelo(f"{resp.status_code} en {model}")

    if resp.status_code >= 400:
        raise Abortar(f"HTTP {resp.status_code}: {resp.text[:200]}")

    try:
        data = resp.json()
    except json.JSONDecodeError as exc:
        raise Abortar(f"no-JSON: {resp.text[:200]}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise Abortar(f"formato: {data}") from exc


def _rotar(url: str, key: str, label: str, modelos: list[str],
           prompt: str, system: str, temp: float) -> str:
    ultimo = None
    for m in modelos:
        log.info("%s -> %s", label, m)
        try:
            return _call(url, key, m, prompt, system, temp)
        except Abortar:
            raise
        except RotarModelo as e:
            ultimo = e
    raise RuntimeError(f"{label}: todos fallaron ({ultimo})")


def ask(prompt: str, system: str = "", temperature: float = 0.9) -> str:
    try:
        return _rotar(OMNIROUTE_CHAT_URL, OMNIROUTE_API_KEY, "OmniRoute",
                      OMNIROUTE_MODELS, prompt, system, temperature)
    except (RotarModelo, RuntimeError) as e:
        log.warning("OmniRoute fallo (%s). Cayendo a Google...", e)

    return _rotar(GOOGLE_OPENAI_URL, GOOGLE_API_KEY, "Google",
                  GOOGLE_MODELS, prompt, system, temperature)


if __name__ == "__main__":
    log.info("--- Test 04b ---")
    print(ask("Responde solo: PONG",
              system="Eres un servidor de ping.",
              temperature=0.0))
