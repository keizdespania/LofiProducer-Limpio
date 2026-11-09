"""Gemini como fallback LLM. Retry exponencial + cascada multi-modelo."""
import json, os, time, urllib.request, urllib.error

MODEL_DEFAULT = "gemini-3.8-flash"
# Cascada de modelos: el primero que funcione gana
MODELOS_CASCADA = [
    "gemini-3.8-flash",
    "gemini-4-argon",
    "gemini-pro-latest",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
]
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


def _post_one(model, body, timeout=20):
    """Una llamada HTTP. Lanza HTTPError si falla."""
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


def _post(model, body, timeout=20, intentos=3):
    """Retry exponencial para 503/429/500. Otros errores: raise inmediato."""
    last_err = None
    for i in range(intentos):
        try:
            return _post_one(model, body, timeout)
        except urllib.error.HTTPError as e:
            code = e.code
            body_err = e.read().decode()[:200] if e.fp else ""
            if code in (429, 503, 500) and i < intentos - 1:
                espera = 2 ** i  # 1s, 2s, 4s
                time.sleep(espera)
                last_err = f"HTTP {code} (retry {i+1}/{intentos}, +{espera}s)"
                continue
            last_err = f"HTTP {code}: {body_err}"
            raise RuntimeError(last_err)
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if i < intentos - 1:
                time.sleep(1)
                continue
            raise RuntimeError(last_err)
    raise RuntimeError(last_err or "desconocido")


def generar(prompt, model=None, timeout=20):
    """Prueba modelo + fallback cascada. Devuelve (texto, modelo_usado)."""
    candidatos = [model] if model else MODELOS_CASCADA[:]
    if model and model not in MODELOS_CASCADA:
        candidatos = [model] + MODELOS_CASCADA
    errores = []
    for m in candidatos:
        try:
            d = _post(m, {"contents": [{"parts": [{"text": prompt}]}]}, timeout)
            parts = d.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            for p in parts:
                if "text" in p and p["text"].strip():
                    return p["text"], m
            errores.append(f"{m}: sin texto")
        except RuntimeError as e:
            errores.append(f"{m}: {e}")
            continue
    raise RuntimeError("Todos los modelos fallaron:\n  " + "\n  ".join(errores))


if __name__ == "__main__":
    try:
        txt, mdl = generar("Responde solo: GEMINI_OK")
        print(f"[{mdl}] {txt}")
    except Exception as e:
        print(f"ERROR: {e}")
