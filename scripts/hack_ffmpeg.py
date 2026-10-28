#!/usr/bin/env python3
"""hack_ffmpeg.py — Extrae comandos FFmpeg de tus scripts y los clasifica."""
import ast, json, re, shlex
from pathlib import Path

ROOT = Path.home() / "LofiProducer"
OUT = ROOT / "data/agent/ffmpeg_contract.json"

# Scripts donde vive FFmpeg en tu stack
TARGETS = [
    "scripts/ensamblar_video.py",
    "fases/ensamblado.py",
    "scripts/generar_video_rapido.py",
]

# Flags que nos interesan (los que usan tus pipelines)
FLAGS_VIDEO = ["-vf", "-filter:v", "-c:v", "-crf", "-preset", "-pix_fmt", "-r", "-s"]
FLAGS_AUDIO = ["-c:a", "-b:a", "-ar", "-ac", "-af", "-filter:a", "-acodec"]
FLAGS_GLOBAL = ["-y", "-i", "-t", "-ss", "-to", "-shortest", "-movflags", "-f"]
FILTROS_CLAVE = ["scale", "pad", "crop", "fade", "subtitles", "concat", "overlay",
                 "amix", "loudnorm", "setpts", "atempo", "drawtext", "loop"]

def extraer_comandos(tree):
    """Busca strings que empiecen con ffmpeg/ffprobe en el AST."""
    cmds = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value.strip()
            if s.startswith(("ffmpeg ", "ffprobe ")):
                cmds.append(s)
            # también listas tipo ["ffmpeg", "-i", ...]
        if isinstance(node, ast.List):
            elems = [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if elems and elems[0] in ("ffmpeg", "ffprobe"):
                cmds.append(" ".join(elems))
    return cmds

def parsear_comando(cmd):
    """Extrae flags y valores de un comando FFmpeg."""
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        return {"raw": cmd, "error": "shlex_fail"}
    info = {"raw": cmd, "flags": {}, "filtros": []}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in FLAGS_VIDEO + FLAGS_AUDIO + FLAGS_GLOBAL:
            val = tokens[i+1] if i+1 < len(tokens) else ""
            info["flags"][t] = val
            i += 2
            continue
        # detectar filtros dentro de -vf / -af / filter_complex
        if t in ("-vf", "-af", "-filter_complex") and i+1 < len(tokens):
            expr = tokens[i+1]
            for f in FILTROS_CLAVE:
                if f in expr:
                    info["filtros"].append({"nombre": f, "expr": expr})
            i += 2
            continue
        i += 1
    return info

def main():
    contract = {
        "motor": "FFmpeg",
        "version_local": "9.0.2",
        "donde": "Termux local",
        "scripts_analizados": [],
        "comandos_detectados": [],
        "flags_agregados": {},
        "filtros_agregados": {},
        "reglas_anti_alucinacion": [
            "NO inventar flags: solo usar los extraidos de tus scripts o los documentados aquí.",
            "Para vertical 9:16: scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "Para loop 1h: generar 10-60 clips cortos y concatenar con -f concat -safe 0 -c copy",
            "Codec video: libx264 con -crf 18-23 (menor=mejor calidad, más peso)",
            "Codec audio: aac -b:a 128k-192k para redes; libopus para webm",
            "Subtítulos: -vf subtitles=archivo.srt:force_style='FontSize=24'",
            "Fade: -vf fade=t=in:st=0:d=0.5,fade=t=out:st={duracion-0.5}:d=0.5",
            "NO usar -c copy si se aplican filtros (obliga a re-encodear)",
            "Validar output con ffprobe: duración>0, resolución esperada, codec correcto",
            "En Termux: -preset veryfast o ultrafast para no saturar CPU",
        ],
        "recetas_recomendadas": {
            "vertical_shorts": "ffmpeg -i in.mp4 -vf scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k out.mp4",
            "horizontal_youtube": "ffmpeg -i in.mp4 -vf scale=1920:1080 -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 192k out.mp4",
            "loop_lofi_1h": "ffmpeg -f concat -safe 0 -i lista.txt -c copy -t 3600 loop.mp4",
            "audio_only": "ffmpeg -i in.mp4 -vn -c:a libmp3lame -b:a 192k out.mp3",
        }
    }

    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            contract["scripts_analizados"].append({"script": rel, "existe": False})
            continue
        tree = ast.parse(p.read_text())
        cmds = extraer_comandos(tree)
        contract["scripts_analizados"].append({"script": rel, "existe": True, "comandos": len(cmds)})
        for c in cmds:
            parsed = parsear_comando(c)
            contract["comandos_detectados"].append(parsed)
            for flag, val in parsed.get("flags", {}).items():
                contract["flags_agregados"].setdefault(flag, set()).add(val)
            for f in parsed.get("filtros", []):
                contract["filtros_agregados"].setdefault(f["nombre"], set()).add(f["expr"])

    # convertir sets a listas para JSON
    contract["flags_agregados"] = {k: sorted(v) for k, v in contract["flags_agregados"].items()}
    contract["filtros_agregados"] = {k: sorted(v) for k, v in contract["filtros_agregados"].items()}

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  scripts analizados: {sum(1 for s in contract['scripts_analizados'] if s['existe'])}/{len(TARGETS)}")
    print(f"  comandos detectados: {len(contract['comandos_detectados'])}")
    print(f"  flags distintos: {list(contract['flags_agregados'].keys())}")
    print(f"  filtros distintos: {list(contract['filtros_agregados'].keys())}")

if __name__ == "__main__":
    main()
