#!/usr/bin/env python3
"""generate_skill_md.py — Genera SKILL.md unificado desde contratos + nichos + tools."""
import json, pathlib, re

ROOT = pathlib.Path.home() / "LofiProducer"
OUT = ROOT / "SKILL.md"

def load(name):
    p = ROOT / "data" / "agent" / f"{name}_contract.json"
    return json.loads(p.read_text()) if p.exists() else {}

CONTRACTS = {
    "musica":  ("acestep",  "generar_cancion_kaggle"),
    "voz":     ("sherpa",   "generar_narracion"),
    "imagen":  ("image",    "generar_imagen"),
    "video":   ("video",    "generar_video"),
    "ffmpeg":  ("ffmpeg",   "ensamblar_video_final"),
    "youtube": ("youtube",  "subir_youtube"),
    "blogger": ("blogger",  "—"),
    "pixabay": ("pixabay",  "generar_video_rapido"),
}

def load_nicho(nicho):
    d = json.loads((ROOT / "config" / "nichos.json").read_text())
    base = d.get(nicho, {}).get("extends")
    if base and base in d.get("_bases", {}):
        merged = dict(d["_bases"][base]); merged.update(d.get(nicho, {})); return merged
    return d.get(nicho, {})

def get_all_nichos():
    d = json.loads((ROOT / "config" / "nichos.json").read_text())
    return [k for k in d if not k.startswith("_")]

def get_skills_for(nicho):
    cfg = load_nicho(nicho)
    return cfg.get("skills", {"presets": {}, "pipeline": []})



ERRORES = [
    {"error": "403 quotaExceeded", "motor": "YouTube", "fix": "Esperar 24h (reset medianoche PT) o rotar proyecto Google Cloud"},
    {"error": "403 forbidden (sin auditar)", "motor": "YouTube", "fix": "Sin auditoría Google, TODO sale privado aunque pidas public"},
    {"error": "400 invalidTitle", "motor": "YouTube", "fix": "Título 1-100 chars, sin < > ni saltos"},
    {"error": "403 Blogger", "motor": "Blogger", "fix": "Blogger API NO habilitada en Google Cloud Console"},
    {"error": "429 rate limit", "motor": "Pixabay/Groq", "fix": "Esperar 60s. Si persistente, rotar modelo/proveedor"},
    {"error": "OOM T4", "motor": "Wan 2.2", "fix": "Bajar resolution a 832x480, num_frames a 33, o usar turbo_4steps"},
    {"error": "1280x720 distorsiona", "motor": "Wan 2.2", "fix": "720 NO es múltiplo de 32. Usar 1280x704"},
    {"error": "num_frames inválido", "motor": "Wan 2.2", "fix": "Debe ser 4n+1 (8,13,17,21,25,33,41,49,65,81,97,121)"},
    {"error": "status='public' Blogger", "motor": "Blogger", "fix": "Blogger usa draft/live/scheduled. NO existe public"},
    {"error": "kernel cuelga >55min", "motor": "Kaggle", "fix": "Timeout interno del template. Reintentar o bajar batch size"},
]

def build_motor_table():
    lines = ["| Motor | Contrato | Tool de Dios | Presets (nombres) |", "|-------|----------|--------------|-------------------|"]
    for motor, (cname, tool) in CONTRACTS.items():
        c = load(cname)
        presets = list(c.get("presets", {}).keys())
        presets_str = ", ".join(presets[:6]) + ("..." if len(presets) > 6 else "")
        lines.append(f"| **{motor}** | `{cname}_contract.json` | `{tool}` | {presets_str} |")
    return "\n".join(lines)

def build_nicho_section():
    lines = []
    for nicho in get_all_nichos():
        cfg = load_nicho(nicho)
        lines.append(f"\n### 🏛️ {nicho} — {cfg.get('nombre', nicho)}")
        lines.append(f"**Formato**: {cfg.get('formato', '?')} · **Duración**: {cfg.get('duracion', '?')}s · **Tono**: {cfg.get('tono', '?')}")
        lines.append("\n**Presets recomendados:**")
        for motor, preset in get_skills_for(nicho).get("presets", {}).items():
            if preset: lines.append(f"- {motor}: `{preset}`")
        pipeline = get_skills_for(nicho).get("pipeline", [])
        pipeline_md = "\n".join(pipeline) if pipeline else "(sin pipeline)"
        lines.append(f"\n**Pipeline:**\n```\n{pipeline_md}\n```")
    return "\n".join(lines)


def build_tools_section():
    src = (ROOT / "scripts" / "dios.py").read_text()
    tools = sorted(set(re.findall(r'"name": "([a-z_]+)"', src)))
    cat = {
        "🎵 Música": ["generar_cancion_kaggle"],
        "🎙️ Voz": ["generar_narracion"],
        "🎨 Imagen": ["generar_imagen"],
        "🎬 Vídeo": ["generar_video", "generar_video_rapido", "ensamblar_video_final", "producir_video"],
        "📤 Publicar": ["subir_youtube", "publicar_en_redes"],
        "☁️ Kaggle": ["lanzar_notebook_kaggle", "lanzar_pipeline_kaggle"],
        "📋 Orquestación": ["producir_nicho"],
        "🧠 Memoria": ["recordar_hecho", "consultar_hechos"],
        "🔍 Búsqueda": ["buscar_en_web", "buscar_youtube", "buscar_repositorio", "leer_rss"],
        "🛠️ Sistema": ["ejecutar_comando", "estado_sistema", "sanar_sistema", "notificar_movil", "instalar_dependencia"],
        "📂 Archivos": ["read_file", "write_file", "validate_file", "promote_file"],
        "📚 Docs": ["leer_documentacion", "documentar_aprendizaje", "consultar_manual_python"],
        "🤖 Agentes": ["pedir_a_especialista", "delegar_tareas_paralelas", "analizar_video_competencia", "list_canales"],
    }
    lines = []
    for grupo, tools_grupo in cat.items():
        lines.append(f"\n**{grupo}**: " + ", ".join(f"`{t}`" for t in tools_grupo if t in tools))
    return "\n".join(lines)


def build_montajes_section():
    """Lee config/montajes/*.json y genera tabla de recetas."""
    montajes_dir = ROOT / "config" / "montajes"
    if not montajes_dir.exists():
        return "(sin recetas generadas)"
    rows = []
    for f in sorted(montajes_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text())
            fades = m.get("fades", {})
            rows.append({
                "nicho": f.stem,
                "duracion": m.get("duracion", "?"),
                "resolucion": f"{m.get('ancho', '?')}x{m.get('alto', '?')}",
                "crf": m.get("crf", "?"),
                "fades": f"{fades.get('in', 0)}/{fades.get('out', 0)}",
                "musica_vol": m.get("musica_vol", "?"),
                "loop": "✅" if m.get("loop_video") else "❌",
            })
        except Exception: continue
    if not rows: return "(sin recetas válidas)"
    lines = ["| Nicho | Duración | Resolución | CRF | Fades | Música vol | Loop |",
             "|-------|----------|------------|-----|-------|-----------|------|"]
    for r in rows:
        lines.append(f"| {r['nicho']} | {r['duracion']}s | {r['resolucion']} | {r['crf']} | {r['fades']} | {r['musica_vol']} | {r['loop']} |")
    return chr(10).join(lines)

def main():
    md = f"""# SKILL.md — Manual del Dios Orquestador

> **Auto-generado** por `scripts/generate_skill_md.py`.
> **NO editar a mano.** Cambia los contratos y regenera.

---

## ⚡ REGLA DE ORO

> **"Imposible romperlo."** Todos los motores validan backend. Params 'fijo' bloqueados. Si falla 2 veces, PARA y pregunta.

---

## 🎯 1. MAPA DE MOTORES

{build_motor_table()}

**Cómo consultar un contrato completo**: `leer_documentacion("data/agent/<motor>_contract.json")`

---

## 🎬 1.b RECETAS DE MONTAJE (auto-generadas)

Cada receta en `config/montajes/<canal>.json` define cómo se ensambla el vídeo final:

{build_montajes_section()}

**Motor**: `scripts/motor_ensamblado.py` (lee la receta + assets → MP4 final).
**Regenerar**: `python scripts/sincronizar_montajes.py`.

---

## 🏛️ 2. NICHOS Y SU PIPELINE

{build_nicho_section()}

---

## 🔧 3. TOOLS DE DIOS (34 activas)

{build_tools_section()}

---

## 🚨 4. DICCIONARIO DE ERRORES + FIX

| Error | Motor | Fix |
|-------|-------|-----|
""" + "\n".join(f"| `{e['error']}` | {e['motor']} | {e['fix']} |" for e in ERRORES) + f"""

---

## 📏 5. REGLAS GLOBALES

1. **Privacidad por defecto**: siempre `private` / `draft` hasta validar.
2. **Sin auditoría Google**: YouTube = todo privado aunque pidas public.
3. **Batch**: música 5/kernel, vídeo 3/kernel. Ahorro -72% cuota.
4. **Prompt vídeo**: Sujeto + Movimiento + Cámara + Iluminación. Una acción por clip.
5. **Imagen aspect**: 16:9 YouTube, 9:16 TikTok, 1:1 Instagram.
6. **FFmpeg**: `-y` siempre. `-ss` ANTES de `-i`. `pix_fmt yuv420p` para universal.
7. **Blogger**: `status` = draft/live/scheduled (NO public). Cuota 100k/día.
8. **Pixabay**: 100 req/min. B-roll en vídeo transformado OK. Redistribuir as-is NO.
9. **Preset desconocido**: consulta `/api/params/<motor>` o `leer_documentacion`.
10. **Si dudas, pregunta al usuario** (regla 7 del Manual Frodo).

---

## 🚦 6. DECISIÓN RÁPIDA: ¿Qué preset uso?

| Si el nicho es... | Música | Voz | Imagen | Vídeo |
|-------------------|--------|-----|--------|-------|
| IA News | `cinematic` | `noticias` | `cinematic` | `cinematic_480p` |
| Finanzas Barrio | `lofi` | `noticias` | `cinematic` | `cinematic_480p` |
| BOE | `ambient` | `audiobook` | `realistic` | `draft_rapido` |
| Lofi | `lofi` | — | `anime` | `draft_rapido` |

**Si el nicho no está aquí**: usar `cinematic` / `noticias` / `realistic` / `draft_rapido` por defecto.

---

*Auto-generado con {len(CONTRACTS)} motores, {len(get_all_nichos())} nichos, {len(ERRORES)} errores.*
"""
    OUT.write_text(md)
    print(f"OK {OUT}")
    print(f"  Motores: {len(CONTRACTS)} | Nichos: {len(get_all_nichos())} | Errores: {len(ERRORES)}")
    print(f"  Líneas: {len(md.splitlines())}")

if __name__ == "__main__":
    main()
