"""Genera el JSON de una landing page usando OmniRoute."""
import sys, os, json, pathlib, requests, time

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "output" / "webs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def generar_landing(descripcion):
    key = ""
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("OMNIROUTE_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

    prompt = f"Eres un disenador web experto. Genera la estructura JSON para una landing page sobre: {descripcion}. Devuelve SOLO un objeto JSON valido, sin markdown, con este formato exacto: {{\"hero\": {{\"title\": \"...\", \"subtitle\": \"...\", \"cta\": \"...\"}}, \"features\": [{{\"title\": \"...\", \"desc\": \"...\"}}], \"footer\": \"...\"}}"
    
    payload = {
        "model": "mi-groq/qwen/qwen3.8-27b",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    try:
        time.sleep(3)
        r = requests.post("http://localhost:20128/v1/chat/completions", json=payload, 
                          headers={"Authorization": f"Bearer {key}"}, timeout=60)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"]
        texto = texto.replace("```json", "").replace("```", "").strip()
        
        data = json.loads(texto)
        out_file = OUT_DIR / f"landing_{int(time.time())}.json"
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return f"OK: Web generada en {out_file}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python generar_web.py 'descripcion'")
        sys.exit(1)
    print(generar_landing(sys.argv[1]))
