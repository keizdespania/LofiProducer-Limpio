"""Cajon 100.E/101.B - Auto-documentacion con Groq + AUTO_CHANGELOG separado.

Uso:
    python scripts/auto_docs.py            # normal (solo si hay diff)
    python scripts/auto_docs.py --force    # forzar aunque no haya diff
    python scripts/auto_docs.py --dry      # solo mostrar, no escribir
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STATE_FILE = ROOT / "data" / "auto_docs_state.json"
MARKER_START = "<!-- AUTO_DOCS_START -->"
MARKER_END = "<!-- AUTO_DOCS_END -->"
MAX_BLOQUES = 20

DOCS = []  # Desactivado: solo escribimos en AUTO_CHANGELOG.md (los maestros son manuales)
AUTO_CHANGELOG = "AUTO_CHANGELOG.md"
MAX_BLOQUES_CHANGELOG = 500
CARPETAS_CLAVE = ["brain", "scripts", "core", "fases"]

RUIDO = (".bak", ".bak2", ".bak3", ".bak.auto", ".bak.filtro", ".bak.changelog",
         ".pyc", ".env", "storage.sqlite", "__pycache__", "/data/", "data/ai_news/",
         "data/trending_", "data/canales_", "data/logs/", "data/call_logs/",
         ".local_tmp", ".colab_bak", "AUTO_CHANGELOG.md")


def _git(*args: str) -> str:
    r = subprocess.run(
        ["git", *args], cwd=str(ROOT),
        capture_output=True, text=True, timeout=20,
    )
    return r.stdout.strip()


def _estado_actual() -> dict:
    head = _git("rev-parse", "HEAD") or "no-head"
    status = _git("status", "--porcelain")
    return {"head": head, "status": status}


def _leer_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _guardar_state(data: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _hay_diff(estado: dict, previo: dict) -> bool:
    return (
        estado["head"] != previo.get("head")
        or estado["status"] != previo.get("status", "")
    )


def _limpiar(rutas: list[str]) -> list[str]:
    return [r for r in rutas if not any(x in r for x in RUIDO)]


def _recolectar_cambios(estado: dict) -> str:
    lineas = []
    if estado["status"]:
        nuevos = _limpiar([l[3:] for l in estado["status"].splitlines() if l.startswith("??")])
        modificados = _limpiar([l[3:] for l in estado["status"].splitlines() if l[:2].strip() == "M"])
        if nuevos:
            lineas.append("Archivos nuevos: " + ", ".join(nuevos[:20]))
        if modificados:
            lineas.append("Archivos modificados: " + ", ".join(modificados[:20]))

    ultimos = _git("log", "--oneline", "-5").splitlines()
    if ultimos:
        lineas.append("Ultimos commits: " + " | ".join(ultimos))

    for carpeta in CARPETAS_CLAVE:
        d = ROOT / carpeta
        if d.exists():
            pys = sorted(p.name for p in d.glob("*.py") if p.is_file())
            if pys:
                lineas.append(f"{carpeta}/: {', '.join(pys[:15])}")

    return "\n".join(lineas) if lineas else "(sin cambios detectables)"


def _leer_api_key(nombre: str) -> str:
    import os
    val = os.environ.get(nombre, "").strip()
    if val:
        return val
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{nombre}="):
                return line.strip().split("=", 1)[1].strip()
    return ""


def _resumen_llm(contexto: str) -> str:
    import requests

    api_key = _leer_api_key("GROQ_API_KEY")
    if not api_key:
        return "- (Fallo: GROQ_API_KEY no encontrada en .env)"

    system = (
        "Eres un asistente tecnico que resume cambios de un repo de codigo. "
        "Devuelve 3-5 vinetas muy concisas en espanol, sin preambulo, "
        "cada una empezando por '- '. No inventes archivos ni funciones."
    )
    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Resume estos cambios en 3-5 vinetas:\n\n{contexto}"},
        ],
        "temperature": 0.3,
    }
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload, timeout=60,
        )
        if r.status_code >= 400:
            return f"- (Fallo Groq HTTP {r.status_code}: {r.text[:200]})"
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"- (Fallo Groq: {e})"


def _bloque_nuevo(resumen: str) -> str:
    ahora = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    return f"\n### {ahora}\n\n{resumen}\n"


def _append_seccion(path: Path, bloque: str, dry: bool) -> bool:
    if not path.exists():
        return False
    contenido = path.read_text(encoding="utf-8")

    if MARKER_START not in contenido or MARKER_END not in contenido:
        contenido = (
            contenido.rstrip()
            + "\n\n---\n\n## Ultimos cambios automaticos (auto-generado)\n\n"
            + MARKER_START + "\n" + MARKER_END + "\n"
        )

    ini = contenido.find(MARKER_START)
    fin = contenido.find(MARKER_END)
    dentro = contenido[ini + len(MARKER_START): fin].strip()

    partes = [p.strip() for p in dentro.split("\n### ") if p.strip()]
    if dentro.startswith("### ") and partes:
        bloques = ["### " + partes[0]] + partes[1:]
    else:
        bloques = partes
    bloques = bloques[-MAX_BLOQUES:]

    if bloque.strip() not in [b.strip() for b in bloques]:
        bloques.append(bloque.strip())

    nuevo_dentro = "\n\n" + "\n\n".join(b.strip() for b in bloques) + "\n"
    contenido = contenido[: ini + len(MARKER_START)] + nuevo_dentro + contenido[fin:]

    if not dry:
        bak = path.with_suffix(
            path.suffix + f".bak.auto.{datetime.now().strftime('%Y%m%d_%H%M')}"
        )
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        path.write_text(contenido, encoding="utf-8")
    return True


def _append_changelog(bloque: str) -> None:
    """Anade el bloque al AUTO_CHANGELOG.md (crea si no existe, rota a MAX_BLOQUES_CHANGELOG)."""
    path = ROOT / AUTO_CHANGELOG
    cabecera = (
        "# AUTO_CHANGELOG\n\n"
        "> Generado automaticamente por `scripts/auto_docs.py` cada 15 min.\n"
        f"> Rotacion: se conservan los ultimos {MAX_BLOQUES_CHANGELOG} bloques.\n\n---\n"
    )

    if not path.exists():
        contenido = cabecera
    else:
        contenido = path.read_text(encoding="utf-8")

    cuerpo = contenido.split("---\n", 1)[-1] if "---\n" in contenido else ""
    if not cuerpo.strip():
        cuerpo = ""

    partes = [p.strip() for p in cuerpo.split("\n### ") if p.strip()]
    bloques = []
    for p in partes:
        p = p.strip()
        if not p:
            continue
        bloques.append(p if p.startswith("###") else "### " + p)
    bloques = [b for b in bloques if b.startswith("### ")]
    bloques = bloques[-MAX_BLOQUES_CHANGELOG:]

    if bloque.strip() not in [b.strip() for b in bloques]:
        bloques.append(bloque.strip())

    nuevo = cabecera + "\n" + "\n\n".join(b.strip() for b in bloques) + "\n"
    path.write_text(nuevo, encoding="utf-8")


def _commit_push() -> None:
    subprocess.run(["git", "add", "-A"], cwd=str(ROOT), capture_output=True, text=True, timeout=30)
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M")
    subprocess.run(
        ["git", "commit", "-m", f"docs(auto): {ts}"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,
    )
    # git push ELIMINADO (Frodo #7): solo commit local, push manual cuando el usuario decida


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    if not args.dry:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "scripts/auto_docs.py"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=10,
        )
        if tracked.returncode != 0:
            subprocess.run(
                ["git", "add", "scripts/auto_docs.py"],
                cwd=str(ROOT), capture_output=True, text=True, timeout=10,
            )

    estado = _estado_actual()
    previo = _leer_state()

    if not args.force and not _hay_diff(estado, previo):
        print("[auto_docs] Sin cambios. Nada que hacer.")
        return 0

    contexto = _recolectar_cambios(estado)
    print("[auto_docs] Contexto:\n" + contexto)

    resumen = _resumen_llm(contexto)
    bloque = _bloque_nuevo(resumen)
    print("[auto_docs] Bloque:\n" + bloque)

    if args.dry:
        print("[auto_docs] --dry: no se escriben archivos.")
        return 0

    escritos = []
    for name in DOCS:
        p = ROOT / name
        if _append_seccion(p, bloque, dry=False):
            escritos.append(name)

    _append_changelog(bloque)
    print("[auto_docs] AUTO_CHANGELOG.md actualizado")

    if escritos:
        print("[auto_docs] Actualizados: " + ", ".join(escritos))
    _commit_push()

    _guardar_state({
        "head": estado["head"],
        "status": estado["status"],
        "ts": datetime.now(timezone.utc).isoformat(),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())

# --- Hook: Actualizar Manual del Dios ---
try:
    import subprocess
    subprocess.run(["python", "scripts/auto_manual_dios.py"], check=True, capture_output=True)
except Exception:
    pass
