#!/usr/bin/env python3
"""Inyecta estado dinámico en colab/README.md entre marcadores."""
import json, subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "colab" / "README.md"
AUTO_START = "<!-- AUTO-START -->"
AUTO_END = "<!-- AUTO-END -->"

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

def contar_musica_local() -> int:
    total = 0
    for carpeta in (ROOT / "assets").glob("*/audio/local"):
        total += len(list(carpeta.glob("*.wav"))) + len(list(carpeta.glob("*.mp3")))
    return total

def git_info() -> str:
    try:
        r = subprocess.run(["git","log","-1","--format=%h|%s"],
                          capture_output=True, text=True, cwd=ROOT)
        if r.stdout.strip():
            h, msg = r.stdout.strip().split("|", 1)
            return f"`{h}` — {msg}"
    except Exception:
        pass
    return "sin commits"

def bloque_dinamico() -> str:
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas = [AUTO_START, ""]
    lineas.append("## 📊 Estado actual del proyecto (auto-actualizado)")
    lineas.append(f"\n*Última actualización: {ahora}*")
    lineas.append(f"*Último commit: {git_info()}*\n")

    lineas.append("### Canales activos\n")
    lineas.append("| ID | Nombre | Nicho | Duración | Paleta |")
    lineas.append("|---|---|---|---|---|")
    for c in canales():
        estado = "✅" if c.get("enabled") else "⏸️"
        lineas.append(f"| `{c.get('id')}` | {c.get('nombre')} | {c.get('nicho')} "
                     f"| {c.get('duracion_default')} | {c.get('paleta_default')} {estado} |")
    lineas.append("")

    lineas.append("### Últimas subidas\n")
    ups = ultimos_uploads(5)
    if ups:
        for u in ups:
            fecha = u.get("subido","")[:16]
            titulo = u.get("titulo","")[:55]
            url = u.get("url","")
            lineas.append(f"- `{fecha}` — {titulo} → {url}")
    else:
        lineas.append("_Sin subidas registradas._")
    lineas.append("")

    lineas.append(f"### 🎵 Música local disponible\n")
    n = contar_musica_local()
    lineas.append(f"- Archivos WAV/MP3 en `assets/*/audio/local/`: **{n}**")
    lineas.append(f"- Estado ACE-Step: {'✅ suficiente' if n >= 5 else '⏳ regenerar'}")
    lineas.append("")

    lineas.append(AUTO_END)
    return "\n".join(lineas)

def actualizar():
    if not README.exists():
        print("ERROR: README.md no existe")
        return None
    contenido = README.read_text(encoding='utf-8')
    bloque = bloque_dinamico()

    if AUTO_START in contenido and AUTO_END in contenido:
        inicio = contenido.find(AUTO_START)
        fin = contenido.find(AUTO_END) + len(AUTO_END)
        nuevo = contenido[:inicio] + bloque + contenido[fin:]
    else:
        nuevo = contenido.rstrip() + "\n\n" + bloque + "\n"

    README.write_text(nuevo, encoding='utf-8')
    return README

if __name__ == "__main__":
    r = actualizar()
    if r:
        print(f"OK -> {r} ({r.stat().st_size} bytes)")
