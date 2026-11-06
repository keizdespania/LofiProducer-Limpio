"""NOTA: dios.py._call_llm tiene su propia cascada con tools/cooldowns.
Este helper es para scripts que NO necesitan eso (prompts simples, JSON, etc.).
NO migrar dios.py a este helper. Coexisten a proposito.

Cascada LLM unificada: Groq#1-#4 → Gemini#5 → especialistas. Fuente única."""
import json, os, sys, time, urllib.request, urllib.error, pathlib

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "brain"))

GROQ_MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b",
               "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
GEMINI_MODEL = "gemini-flash-lite-latest"


def _env(k):
    for line in (_ROOT / ".env").read_text().splitlines():
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _groq(prompt, idx, timeout=30):
    key = _env(f"GROQ_API_KEY{'' if idx == 1 else f'_{idx}'}")
    if not key:
        raise RuntimeError(f"GROQ_API_KEY_{idx} no existe")
    body = json.dumps({"model": GROQ_MODELS[idx - 1],
                       "messages": [{"role": "user", "content": prompt}],
                       "max_tokens": 1500, "temperature": 0.7}).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0 Chrome/131"},
        method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]


def _gemini(prompt, timeout=20):
    from llm_gemini import generar
    return generar(prompt, model=GEMINI_MODEL, timeout=timeout)


def call_llm(prompt, max_retries_groq=True, skip_groq=False, skip_gemini=False,
             skip_especialistas=False):
    """Cascada. Devuelve (texto, origen). Lanza RuntimeError si todo falla."""
    errors = []
    if not skip_groq:
        for i in range(1, 5):
            try:
                return _groq(prompt, i), f"groq_{i}"
            except Exception as e:
                errors.append(f"groq_{i}:{type(e).__name__}")
                if max_retries_groq and i < 4:
                    time.sleep(2)
    if not skip_gemini:
        try:
            return _gemini(prompt), "gemini"
        except Exception as e:
            errors.append(f"gemini:{type(e).__name__}")
    if not skip_especialistas:
        try:
            from especialistas import especialista_generico
            return especialista_generico(prompt), "especialistas"
        except Exception as e:
            errors.append(f"esp:{type(e).__name__}")
    raise RuntimeError("cascada agotada → " + ", ".join(errors))


if __name__ == "__main__":
    txt, src = call_llm("Responde solo: hola cabeza huevo")
    print(f"[{src}] {txt[:80]}")
