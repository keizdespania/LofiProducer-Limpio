#!/usr/bin/env python3
"""Auto-genera PROYECTO.md escaneando el proyecto."""
import json, subprocess, os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "PROYECTO.md"

def linea_archivo(p: Path) -> str:
    try:
        n = sum(1 for _ in p.open('r', encoding='utf-8', errors='ignore'))
    except Exception:
        n = 0
    return n

def docstring_archivo(p: Path) -> str:
    try:
        for linea in p.open('r', encoding='utf-8', errors='ignore'):
            linea = linea.strip()
            if linea.startswith('"""') or linea.startswith("'''"):
                return linea.strip('"\' ')[:120]
            if linea and not linea.startswith('#'):
                break
    except Exception:
        pass
    return ""

def listar(carpeta: str, patron: str = "*.py") -> list:
    d = ROOT / carpeta
    return sorted(d.glob(patron)) if d.exists() else []

def git_info() -> dict:
    try:
        r = subprocess.run(["git","log","-1","--format=%H|%s|%ci"],
                          capture_output=True, text=True, cwd=ROOT)
        if r.stdout.strip():
            h, msg, fecha = r.stdout.strip().split("|", 2)
            return {"hash": h[:8], "mensaje": msg, "fecha": fecha}
    except Exception:
        pass
    return {"hash": "?", "mensaje": "?", "fecha": "?"}

def canales() -> list:
    p = ROOT / "config" / "channels.json"
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8')).get("channels", [])
    return []

def ultimos_uploads(n: int = 5) -> list:
    todos = []
    for f in (ROOT / "data").glob("*/uploads.json"):
        try:
            todos.extend(json.loads(f.read_text(encoding='utf-8')).get("uploads", []))
        except Exception:
            pass
    return sorted(todos, key=lambda x: x.get("subido",""), reverse=True)[:n]

def timestamps_logs() -> dict:
    logs_dir = ROOT / "data" / "logs"
    if not logs_dir.exists():
        return {"backup": "sin log"}
    b = logs_dir / "backup.log"
    if b.exists():
        lineas = b.read_text(encoding='utf-8').strip().split("\n")
        return {"backup": lineas[-1] if lineas else "vacio"}
    return {"backup": "sin log"}

def generar():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git = git_info()
    lineas = []

    lineas.append("# 🎬 PROYECTO.md — LofiProducer")
    lineas.append(f"\n*Auto-generado: {ahora}*")
    lineas.append(f"*Último commit: `{git['hash']}` — {git['mensaje']} ({git['fecha']})*\n")

    lineas.append("---\n")
    lineas.append("## 🎯 Estado del proyecto\n")
    lineas.append("Sistema multi-canal automatizado para YouTube + redes sociales.")
    lineas.append("Ejecutado desde Android + Termux, sin root, sin servidores.\n")

    lineas.append("### 📊 Canales activos\n")
    lineas.append("| ID | Nombre | Nicho | Duración | Paleta | Estado |")
    lineas.append("|---|---|---|---|---|---|")
    for c in canales():
        estado = "✅" if c.get("enabled") else "⏸️"
        lineas.append(f"| `{c.get('id')}` | {c.get('nombre')} | {c.get('nicho')} "
                     f"| {c.get('duracion_default')} | {c.get('paleta_default')} | {estado} |")
    lineas.append("")

    lineas.append("### 🎬 Últimas 5 subidas\n")
    ups = ultimos_uploads(5)
    if ups:
        lineas.append("| Fecha | Título | URL |")
        lineas.append("|---|---|---|")
        for u in ups:
            lineas.append(f"| {u.get('subido','')[:16]} | {u.get('titulo','')[:50]} | {u.get('url','')} |")
    else:
        lineas.append("_Sin subidas registradas todavía._")
    lineas.append("")

    lineas.append("### 🔄 Backup automático\n")
    lineas.append(f"- Último backup: `{timestamps_logs()['backup']}`")
    lineas.append("- Frecuencia: cada 10 min mientras se programa")
    lineas.append("- Repo: `github.com/keizdespania/LofiProducer-backup` (privado)")
    lineas.append("")

    lineas.append("---\n")
    lineas.append("## 📁 Estructura de módulos\n")

    for carpeta, emoji in [("core","🏗️"), ("fases","⚙️"), ("config","⚙️"), ("scripts","🛠️")]:
        archivos = listar(carpeta)
        if not archivos:
            continue
        lineas.append(f"\n### {emoji} `{carpeta}/`\n")
        for a in archivos:
            if a.name.startswith("__"):
                continue
            doc = docstring_archivo(a)
            lineas.append(f"- **`{a.name}`** ({linea_archivo(a)} líneas)" + (f" — {doc}" if doc else ""))
    lineas.append("")

    lineas.append("---\n")
    lineas.append("## 🧠 Stack técnico\n")
    lineas.append("| Componente | Tecnología |")
    lineas.append("|---|---|")
    lineas.append("| Entorno | Android 14 + Termux (sin root) |")
    lineas.append("| Lenguaje | Python 3.14 |")
    lineas.append("| Multimedia | FFmpeg 8.1.3 + Pillow |")
    lineas.append("| LLM Gateway | OmniRoute local (`localhost:20128`) |")
    lineas.append("| Imágenes IA | Cloudflare Workers AI (FLUX.1 Schnell) |")
    lineas.append("| Música | ACE-Step vía Colab (pendiente) + CCMixter fallback |")
    lineas.append("| Subida | YouTube Data API v3 + OAuth 2.0 |")
    lineas.append("| Backup | GitHub privado cada 10 min |")
    lineas.append("")

    lineas.append("---\n")
    lineas.append("## 🚧 Roadmap\n")
    lineas.append("- [x] Pipeline multi-canal")
    lineas.append("- [x] Cloudflare imágenes")
    lineas.append("- [x] Atribuciones TASL + tracklist")
    lineas.append("- [x] Marca IA en YouTube")
    lineas.append("- [x] Backup automático GitHub")
    lineas.append("- [ ] ACE-Step vía Colab (en curso)")
    lineas.append("- [ ] Cross-posting Instagram + TikTok + X")
    lineas.append("- [ ] Analytics diario 5 AM")
    lineas.append("- [ ] WordPress MCP")
    lineas.append("- [ ] Widget Tasker")
    lineas.append("")
    lineas.append("---")
    lineas.append(f"*Generado automáticamente desde `scripts/generar_docs.py`*")

    OUT.write_text("\n".join(lineas), encoding='utf-8')
    return OUT

if __name__ == "__main__":
    ruta = generar()
    print(f"OK -> {ruta} ({ruta.stat().st_size} bytes)")
