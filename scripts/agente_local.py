"""
Agente local minimo - Python + OmniRoute.
Pide al LLM que use las tools 'read_file' y 'write_file'.
Se detiene automaticamente en cuanto escribe un archivo para evitar bucles.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import requests

OMNIROUTE = "http://localhost:20128/v1/chat/completions"
API_KEY = ""
for line in Path(".env").read_text().splitlines():
    if line.startswith("OMNIROUTE_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
        break
if not API_KEY:
    raise SystemExit("Falta OMNIROUTE_API_KEY en .env")

# Usamos auto/gemini que responde rapido y soporta tools
MODEL = "gemini/gemini-3-flash-preview"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee el contenido de un archivo.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Escribe o sobrescribe un archivo con el contenido completo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        }
    }
]

def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python scripts/agente_local.py \"tu peticion\"")
        return 2

    prompt = " ".join(sys.argv[1:]).strip()
    print(f"[agente] Prompt: {prompt}")

    messages = [{"role": "user", "content": prompt}]
    step = 0

    # Maximo 4 pasos para evitar bucles infinitos
    while step < 4:
        step += 1
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "temperature": 0.1,
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        
        try:
            r = requests.post(OMNIROUTE, headers=headers, json=payload, timeout=180)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"[agente] Error LLM: {e}")
            return 1

        msg = data["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        messages.append(msg)

        # Si el modelo no pide tools, ha terminado
        if not tool_calls:
            print("\n[agente] Tarea completada. El modelo dice:")
            print(msg.get("content", "")[:500])
            return 0

        # Ejecutar las tools que pida
        for tc in tool_calls:
            fn = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            print(f"\n[agente] Tool call [{step}]: {fn} -> {args.get('path')}")

            if fn == "read_file":
                p = Path(args["path"])
                if p.exists():
                    contenido = p.read_text(encoding="utf-8")
                    print(f"  -> Leído ({len(contenido)} bytes)")
                    messages.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "name": fn, "content": contenido
                    })
                else:
                    print(f"  -> Error: no existe {p}")
                    messages.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "name": fn, "content": f"Error: {p} no existe."
                    })

            elif fn == "write_file":
                p = Path(args["path"])
                if not p.resolve().is_relative_to(Path.cwd().resolve()):
                    print(f"  -> BLOQUEADO: fuera del repo.")
                    messages.append({
                        "role": "tool", "tool_call_id": tc["id"],
                        "name": fn, "content": "Error: ruta bloqueada."
                    })
                    continue
                
                # Crear directorios si no existen
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(args["content"], encoding="utf-8")
                
                print(f"  -> ESCRITO: {p} ({len(args['content'])} bytes)")
                print("[agente] Tarea completada tras escritura. Deteniendo.")
                
                # FRENO DE EMERGENCIA: Salimos del script tras escribir
                return 0

    print("\n[agente] Límite de pasos alcanzado.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
