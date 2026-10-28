"""
Cajon 24.B - Agente conversacional read-only (Nivel 3 fase 1).

Modo actual: solo lectura. NO ejecuta comandos peligrosos.
Los comandos de ejecución llegan en cajones posteriores.

Comandos:
  /ayuda         - Lista comandos
  /estado        - Snapshot del ecosistema
  /logs [n]      - Ultimas n lineas del log principal
  /modelos       - Modelos disponibles via core.llm
  /ultimo        - Ultimo video subido
  /pendientes    - Acciones pendientes de aprobar
  /salir / /q    - Salir

Cualquier otro texto -> consulta libre a core.llm.ask()
"""

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
if str(_Path(__file__).resolve().parent.parent) not in _sys.path:
    _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))


import json
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from core.config import DATA_DIR
from core.logger import get_logger
from core.llm import ask


console = Console()
log = get_logger("scripts.chat_agent")

AGENT_DIR = DATA_DIR / "agent"
AGENT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = DATA_DIR / "logs" / "lofiproducer.log"
UPLOADS_FILE = DATA_DIR / "uploads.json"


SYSTEM_PROMPT = """Eres el asistente tecnico del proyecto LofiProducer.
Contexto:
- Proyecto Python en Termux (Android, ARM64, sin root).
- Pipeline: tendencias YouTube -> SEO -> imagen -> portada -> video -> intro/outro -> ensamblado -> subida.
- Respondes de forma concisa, tecnica, en espanol.
- Si no sabes algo del estado del sistema, di "no tengo esa informacion".
- Nunca inventes rutas ni comandos que no te hayan pasado en contexto.
"""


def _estado_sistema() -> dict:
    def pgrep(pat: str) -> list[str]:
        r = subprocess.run(["pgrep", "-af", pat], capture_output=True, text=True)
        return [l for l in r.stdout.strip().split("\n") if l]

    kaggle = pgrep("mcp-server-kaggle-exec")
    musica = pgrep("fases.musica_ace")
    sched = pgrep("termux-job-scheduler")

    ultimo_upload = None
    if UPLOADS_FILE.exists():
        try:
            data = json.loads(UPLOADS_FILE.read_text(encoding="utf-8"))
            ups = data.get("uploads", [])
            if ups:
                ultimo_upload = ups[-1]
        except Exception:
            pass

    return {
        "musica_viva": bool(musica),
        "kaggle_vivo": bool(kaggle),
        "scheduler": sched,
        "ultimo_upload": ultimo_upload,
    }


def cmd_estado() -> None:
    e = _estado_sistema()
    table = Table(title="Estado del Ecosistema", show_header=False)
    table.add_column("Componente", style="cyan")
    table.add_column("Estado")

    table.add_row(
        "ACE-Step (musica)",
        "[green]corriendo[/green]" if e["musica_viva"] else "[dim]parado[/dim]",
    )
    table.add_row(
        "MCP Kaggle",
        "[green]vivo[/green]" if e["kaggle_vivo"] else "[dim]parado[/dim]",
    )
    table.add_row(
        "Backup scheduler",
        f"[green]{len(e['scheduler'])} procesos[/green]"
        if e["scheduler"] else "[dim]no configurado[/dim]",
    )

    u = e["ultimo_upload"]
    if u:
        table.add_row("Ultimo video", u["titulo"][:60])
    else:
        table.add_row("Ultimo video", "[dim]ninguno[/dim]")

    console.print(table)


def cmd_logs(n: int = 20) -> None:
    if not LOG_FILE.exists():
        console.print("[yellow]Sin log todavia.[/yellow]")
        return
    lineas = LOG_FILE.read_text(encoding="utf-8").splitlines()[-n:]
    for l in lineas:
        console.print(l, markup=False)


def cmd_ultimo() -> None:
    if not UPLOADS_FILE.exists():
        console.print("[yellow]Sin uploads registrados.[/yellow]")
        return
    data = json.loads(UPLOADS_FILE.read_text(encoding="utf-8"))
    ups = data.get("uploads", [])
    if not ups:
        console.print("[yellow]Sin uploads.[/yellow]")
        return
    for u in ups[-5:]:
        console.print(f"[cyan]{u['subido'][:19]}[/cyan] | {u['titulo'][:60]}")
        console.print(f"  {u['url']}")


def cmd_modelos() -> None:
    from core.config import MODEL_NAME, MODEL_FALLBACKS
    console.print(f"Primario: [green]{MODEL_NAME}[/green]")
    console.print("Fallbacks:")
    for m in MODEL_FALLBACKS:
        console.print(f"  - {m}")


def cmd_pendientes() -> None:
    pend = list(AGENT_DIR.glob("pending_*.json"))
    if not pend:
        console.print("[dim]Sin acciones pendientes.[/dim]")
        return
    for p in pend[-5:]:
        d = json.loads(p.read_text(encoding="utf-8"))
        console.print(f"[yellow]{p.name}[/yellow]: {d.get('descripcion', '?')}")


def cmd_ayuda() -> None:
    console.print(Panel.fit(
        "[bold]Comandos disponibles (Nivel 3 fase 1 - read-only)[/bold]\n\n"
        "[cyan]/ayuda[/cyan]        - Esta ayuda\n"
        "[cyan]/estado[/cyan]       - Snapshot del ecosistema\n"
        "[cyan]/logs [n][/cyan]     - Ultimas n lineas del log (default 20)\n"
        "[cyan]/modelos[/cyan]      - Modelos LLM disponibles\n"
        "[cyan]/ultimo[/cyan]       - Ultimo video subido\n"
        "[cyan]/pendientes[/cyan]   - Acciones pendientes de aprobar\n"
        "[cyan]/salir[/cyan] / [cyan]/q[/cyan] - Salir\n\n"
        "Cualquier otra cosa -> pregunta libre al LLM.",
        title="Chat Agent",
        border_style="blue",
    ))


def _consulta_libre(texto: str) -> None:
    console.print("[dim]Consultando LLM...[/dim]")
    try:
        e = _estado_sistema()
        u = e["ultimo_upload"]
        contexto = (
            "Estado actual del sistema:\n"
            f"- ACE-Step: {'corriendo' if e['musica_viva'] else 'parado'}\n"
            f"- MCP Kaggle: {'vivo' if e['kaggle_vivo'] else 'parado'}\n"
            f"- Ultimo video: {u['titulo'] if u else 'ninguno'}\n"
        )
        respuesta = ask(
            f"{contexto}\n\nPregunta del usuario: {texto}",
            system=SYSTEM_PROMPT,
            temperature=0.6,
        )
        console.print(Panel(respuesta, border_style="green", title="LLM"))
    except Exception as exc:
        console.print(f"[red]Error LLM: {exc}[/red]")


def main() -> None:
    console.print(Panel.fit(
        "[bold green]LofiProducer Chat Agent[/bold green]\n"
        "Nivel 3 fase 1 - read-only\n"
        "Escribe [cyan]/ayuda[/cyan] para ver comandos.",
        border_style="green",
    ))
    cmd_estado()

    while True:
        try:
            entrada = Prompt.ask("\n[bold cyan]tu[/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Hasta luego.[/dim]")
            break

        if not entrada:
            continue

        if entrada in ("/salir", "/q", "/quit", "/exit"):
            console.print("[dim]Hasta luego.[/dim]")
            break

        if entrada in ("/ayuda", "/?"):
            cmd_ayuda()
        elif entrada == "/estado":
            cmd_estado()
        elif entrada.startswith("/logs"):
            partes = entrada.split()
            n = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 20
            cmd_logs(n)
        elif entrada == "/modelos":
            cmd_modelos()
        elif entrada == "/ultimo":
            cmd_ultimo()
        elif entrada == "/pendientes":
            cmd_pendientes()
        elif entrada.startswith("/"):
            console.print(f"[yellow]Comando desconocido: {entrada}[/yellow]. Prueba /ayuda.")
        else:
            _consulta_libre(entrada)


if __name__ == "__main__":
    main()
