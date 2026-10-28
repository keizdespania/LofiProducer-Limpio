"""Cajon 112.A - Ejecutor seguro de comandos con HITL (Human-in-the-loop)."""
from __future__ import annotations
import json
import subprocess
from core.logger import get_logger

log = get_logger("brain.ejecutor_seguro")

# Comandos que puede ejecutar sin preguntar
WHITELIST = (
    "pip install ",
    "free ",
    "df ",
    "uname ",
    "pip uninstall ",
    "pkg install ",
    "python ",
    "git status",
    "git diff",
    "git log",
    "ls ",
    "ls",
    "cat ",
    "pwd",
    "clear",
    "cd ",
    "echo ",
    "date",
    "head ",
    "tail ",
    "grep ",
    "find ",
    "which ",
    "whoami"
)

# Comandos prohibidos absolutamente (ni preguntando)
BLACKLIST = (
    "rm ", "rm -", "mv ", "chmod ", "chown ",
    "> ", ">>", "|", "&&", "||", "&",
    "curl ", "wget ", "nc ", "ssh "
)

def _pedir_aprobacion(cmd: str) -> bool:
    """Lanza un diálogo nativo de Android para pedir permiso."""
    try:
        # Usamos termux-dialog confirm
        res = subprocess.run(
            ["termux-dialog", "confirm", "-t", "🛡️ Aprobación Requerida", "-i", f"El Dios quiere ejecutar:\n\n{cmd}\n\n¿Permitir?"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(res.stdout.strip())
        return data.get("code") == 0
    except Exception as e:
        log.warning("Fallo al pedir aprobación: %s", e)
        return False # Si falla el diálogo, denegamos por seguridad

def ejecutar(cmd: str) -> str:
    """Evalúa y ejecuta un comando con seguridad."""
    cmd = cmd.strip()
    if not cmd:
        return "Error: comando vacío"

    # 1. Blacklist (peligro extremo)
    if any(b in cmd for b in BLACKLIST):
        return f"❌ BLOQUEADO: El comando contiene operadores o binarios peligrosos."

    # 2. Whitelist (ejecución directa)
    if any(cmd.startswith(w) for w in WHITELIST):
        log.info("Ejecutando (whitelist): %s", cmd)
        try:
            r = subprocess.run(cmd.split(), shell=False, capture_output=True, text=True, timeout=600)
            salida = (r.stdout + r.stderr).strip()
            return salida[:2000] if salida else "OK (sin salida)"
        except subprocess.TimeoutExpired:
            return "❌ Error: El comando tardó demasiado (Timeout 5 min)."
        except Exception as e:
            return f"❌ Error de ejecución: {e}"

    # 3. HITL (preguntar al usuario)
    if _pedir_aprobacion(cmd):
        log.info("Ejecutando (aprobado por HITL): %s", cmd)
        try:
            r = subprocess.run(cmd.split(), shell=False, capture_output=True, text=True, timeout=600)
            salida = (r.stdout + r.stderr).strip()
            return salida[:2000] if salida else "OK (sin salida)"
        except Exception as e:
            return f"❌ Error de ejecución: {e}"
    else:
        return "❌ DENEGADO: El usuario no aprobó la ejecución."

if __name__ == "__main__":
    print("── Test de whitelist ──")
    print(ejecutar("ls -la"))
    print("── Test de bloqueo ──")
    print(ejecutar("rm -rf /"))
