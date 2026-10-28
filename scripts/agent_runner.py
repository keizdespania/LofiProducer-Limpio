"""
Cliente del agente constructor en Kaggle.

Uso:
    python scripts/agent_runner.py "anade comentario al inicio de main.py"
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


TOKEN = os.popen("gh auth token").read().strip()
if not TOKEN:
    raise SystemExit("ERROR: gh auth token vacio")

AGENT_CODE = Path("kaggle_agent/agent_code.py").read_text(encoding="utf-8")


# Script que se ejecuta en Kaggle:
# 1. Clona el repo
# 2. Escribe el prompt a /tmp/prompt.txt
# 3. Ejecuta el agente
# 4. Devuelve el JSON por stdout
KERNEL_TEMPLATE = """import os, subprocess, sys

TOKEN = "__TOKEN__"
PROMPT = __PROMPT__

# 1. Clone
cred = os.path.expanduser('~/.git-credentials')
with open(cred, 'w') as f:
    f.write(f'https://x-access-token:{TOKEN}@github.com\\n')
os.chmod(cred, 0o600)
subprocess.run('git config --global credential.helper store', shell=True)

if not os.path.exists('/tmp/lofi'):
    subprocess.run(
        'git clone --depth 1 https://github.com/keizdespania/LofiProducer-backup.git /tmp/lofi 2>&1 | tail -2',
        shell=True,
    )

# 2. Escribir prompt
with open('/tmp/prompt.txt', 'w') as f:
    f.write(PROMPT)

# 3. Escribir el codigo del agente
with open('/tmp/agent_code.py', 'w') as f:
    f.write(r'''__AGENT_CODE__''')

# 4. Ejecutar
r = subprocess.run(
    'cd /tmp && python /tmp/agent_code.py /tmp/prompt.txt',
    shell=True, capture_output=True, text=True
)
print(r.stdout, flush=True)
if r.returncode != 0:
    print('STDERR:', r.stderr[-1000:], file=sys.stderr, flush=True)

# 5. Limpieza
try:
    os.remove(cred)
    subprocess.run('git config --global --unset credential.helper', shell=True)
except FileNotFoundError:
    pass
"""


def construir_kernel(prompt: str) -> str:
    # Importante: el orden de los replace es crítico
    k = KERNEL_TEMPLATE.replace("__AGENT_CODE__", AGENT_CODE)
    k = k.replace("__PROMPT__", json.dumps(prompt))
    k = k.replace("__TOKEN__", TOKEN)
    return k


async def main() -> int:
    if len(sys.argv) < 2:
        print("uso: python scripts/agent_runner.py \"tu peticion\"")
        return 2

    prompt = " ".join(sys.argv[1:]).strip()
    print(f"[runner] Prompt: {prompt[:100]}")
    print("[runner] Lanzando kernel en Kaggle GPU (3-6 min)...")

    kernel_code = construir_kernel(prompt)

    params = StdioServerParameters(
        command="mcp-server-kaggle-exec", args=[],
    )
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            result = await s.call_tool("kaggle_execute", {
                "code": kernel_code,
                "enable_gpu": True,
                "timeout": 600,
            })

            salida = ""
            for c in result.content:
                if hasattr(c, "text"):
                    salida += c.text

            # Redactar el token por si acaso
            salida = salida.replace(TOKEN, "***REDACTED***")

    # Intentar parsear el JSON del agente
    try:
        data = json.loads(salida)
        if isinstance(data, dict) and "status" in data:
            # Es el JSON del MCP, no del agente. Extraer stdout
            stdout = data.get("stdout", "")
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                print("\n[runner] Kernel termino pero stdout no es JSON del agente:")
                print(stdout[:2000])
                return 1
    except json.JSONDecodeError:
        print("\n[runner] Kernel termino pero no hubo JSON:")
        print(salida[:2000])
        return 1

    print("\n" + "=" * 60)
    print("PROPUESTA DEL AGENTE")
    print("=" * 60)
    if not data.get("ok"):
        print(f"ERROR: {data.get('error')}")
        return 1
    print(f"Archivo: {data.get('archivo')}")
    print(f"Razon  : {data.get('razon')}")
    print(f"Tiempo : {data.get('tiempo_total_s')}s")
    print()
    print("--- DIFF PROPUESTO ---")
    print(data.get("diff", "(vacio)"))
    print("=" * 60)
    print("\nEste diff NO se ha aplicado. Para aplicarlo en el repo local:")
    print(f"  git apply <<'EOF'\n{data.get('diff', '')}\nEOF")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
