"""Gemini como fallback LLM vía HTTP puro (sin SDK, sin Rust, sin pydantic)."""
import json, os, urllib.request, urllib.error

MODEL_DEFAULT = "gemini-flash-lite-latest"
BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _key():
    for f in (".env", "../.env"):
        p = os.path.join(os.path.dirname(__file__), "..", f)
        if not os.path.exists(p):
            continue
        for line in open(p):
            if line.startswith("GEMINI_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("GEMINI_API_KEY", "")


def _post(model, body, timeout=20):
    key = _key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY no encontrada en .env")
    req = urllib.request.Request(
        f"{BASE}/{model}:generateContent",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": key,
                 "User-Agent": "Mozilla/5.0"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def generar(prompt, model=MODEL_DEFAULT, timeout=20):
    """Devuelve texto. Lanza RuntimeError si falla."""
    try:
        d = _post(model, {"contents": [{"parts": [{"text": prompt}]}]}, timeout)
        parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        for p in parts:
            if "text" in p:
                return p["text"]
        raise RuntimeError(f"respuesta sin texto: {json.dumps(d)[:200]}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:200]}")
    except Exception as e:
        raise RuntimeError(f"{type(e).__name__}: {e}")


if __name__ == "__main__":
    print(generar("Responde solo: ok"))
