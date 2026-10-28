#!/usr/bin/env python3
"""hack_ffmpeg_v2.py — Extractor FFmpeg turbo: AST + binario + anti-patterns."""
import ast, json, re, shlex, subprocess
from pathlib import Path

ROOT = Path.home() / "LofiProducer"
OUT  = ROOT / "data/agent/ffmpeg_contract.json"

FLAGS_V = {"-vf","-filter:v","-c:v","-crf","-preset","-pix_fmt","-r","-s","-movflags"}
FLAGS_A = {"-c:a","-b:a","-ar","-ac","-af","-filter:a","-acodec","-q:a"}
FLAGS_G = {"-y","-i","-t","-ss","-to","-shortest","-f","-map","-safe","-tune","-profile:v"}
FILTROS_CLAVE = ["scale","pad","crop","fade","subtitles","concat","overlay","amix",
                 "loudnorm","setpts","atempo","drawtext","loop","zoompan","xfade",
                 "colorbalance","eq","hue","unsharp","gblur","boxblur","rotate","transpose"]

# anti-patterns (lo que NO debe hacer el agente)
ANTI = {
    "-crf 0": "perdida cero = archivos gigantes, usar 18-23",
    "-preset placebo": "eterno, usar veryfast/ultrafast en Termux",
    "-c copy + -vf": "incompatible: filtros obligan re-encode",
    "-c copy + -af": "incompatible: filtros obligan re-encode",
    "-b:a 320k": "excesivo para redes, 128-192k suficiente",
    "-s 3840x2160": "4K en Termux = OOM, usar 1080p",
    "scale=1920:1080 sin force_original_aspect_ratio": "puede deformar la imagen",
}

def capturar_binario():
    """Extrae filtros y codecs REALES de tu ffmpeg 9.0.2."""
    out = {"version":"?", "filtros":[], "codecs_video":[], "codecs_audio":[], "formatos":[]}
    try:
        v = subprocess.run("ffmpeg -version | head -1", shell=True, capture_output=True, text=True, timeout=8)
        out["version"] = v.stdout.strip().split()[2] if v.stdout else "?"
    except Exception: pass
    try:
        f = subprocess.run("ffmpeg -hide_banner -filters 2>&1", shell=True, capture_output=True, text=True, timeout=10)
        out["filtros"] = sorted(set(re.findall(r"^\s*[TSC.]{3}\s+(\w+)", f.stdout, re.M)))[:120]
    except Exception: pass
    try:
        c = subprocess.run("ffmpeg -hide_banner -codecs 2>&1", shell=True, capture_output=True, text=True, timeout=10)
        for line in c.stdout.splitlines():
            if " libx264 " in line or " libx265 " in line: out["codecs_video"].append(line.split()[1])
            if " aac " in line or " libopus " in line or " libmp3lame " in line: out["codecs_audio"].append(line.split()[1])
    except Exception: pass
    try:
        fm = subprocess.run("ffmpeg -hide_banner -formats 2>&1", shell=True, capture_output=True, text=True, timeout=10)
        out["formatos"] = sorted(set(re.findall(r"\s(E mp4|E mov|E webm|E matroska|E mp3|E wav)\b", fm.stdout)))
    except Exception: pass
    return out

def extraer_cmds(tree):
    """Extrae comandos FFmpeg de strings, f-strings, listas, tuples, concat, subprocess, os.system."""
    cmds = []
    for node in ast.walk(tree):
        # strings literales
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value.strip()
            if s.startswith(("ffmpeg ", "ffprobe ")): cmds.append(s)
        # f-strings: reconstruir con placeholders
        if isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant): parts.append(str(v.value))
                elif isinstance(v, ast.FormattedValue): parts.append("{VAR}")
            joined = "".join(parts).strip()
            if joined.startswith(("ffmpeg ", "ffprobe ")): cmds.append(joined)
        # listas y tuplas tipo ["ffmpeg","-i",...]
        if isinstance(node, (ast.List, ast.Tuple)):
            elems = []
            for e in node.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str): elems.append(e.value)
                else: elems.append("{VAR}")
            if elems and elems[0] in ("ffmpeg","ffprobe"): cmds.append(" ".join(elems))
        # concatenación "ffmpeg " + args
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            try:
                left = ast.unparse(node.left); right = ast.unparse(node.right)
                if "ffmpeg" in left or "ffmpeg" in right:
                    cmds.append((left + " " + right).replace('"','').replace("'",""))
            except Exception: pass
        # subprocess.run/os.system/os.popen
        if isinstance(node, ast.Call):
            fname = ast.unparse(node.func)
            if fname in ("subprocess.run","subprocess.call","subprocess.Popen","os.system","os.popen"):
                if node.args:
                    try:
                        arg = ast.unparse(node.args[0])
                        if "ffmpeg" in arg or "ffprobe" in arg:
                            cmds.append(arg.replace('"','').replace("'",""))
                    except Exception: pass
        # ffmpeg-python: ffmpeg.input(...).output(...)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in ("output","run","overwrite_output"):
                parent = ast.unparse(node)
                if "ffmpeg" in parent: cmds.append(parent[:300])
    return list(dict.fromkeys(cmds))  # dedup preservando orden

def parsear(cmd):
    info = {"raw": cmd, "flags": {}, "filtros": [], "anti": []}
    try: tokens = shlex.split(cmd)
    except ValueError: return info
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in FLAGS_V | FLAGS_A | FLAGS_G:
            val = tokens[i+1] if i+1 < len(tokens) else ""
            info["flags"][t] = val
            for ap, why in ANTI.items():
                flag, _, pattern = ap.partition(" ")
                if t == flag and pattern and pattern in str(val):
                    info["anti"].append({"pattern": ap, "why": why})
            i += 2; continue
        if t in ("-vf","-af","-filter_complex") and i+1 < len(tokens):
            expr = tokens[i+1]
            for f in FILTROS_CLAVE:
                if f in expr: info["filtros"].append({"nombre": f, "expr": expr})
            i += 2; continue
        i += 1
    return info

def main():
    binario = capturar_binario()
    contract = {
        "motor": "FFmpeg", "version": binario["version"], "donde": "Termux local",
        "binario": {
            "filtros_disponibles": len(binario["filtros"]),
            "codecs_video": binario["codecs_video"],
            "codecs_audio": binario["codecs_audio"],
            "formatos": binario["formatos"],
        },
        "scripts_analizados": [], "comandos": [],
        "flags_agregados": {}, "filtros_agregados": {}, "anti_patterns": [],
        "salud": {"score": 100, "problemas": []},
        "recetas_recomendadas": {
            "vertical_shorts": "ffmpeg -y -i {in} -vf 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2' -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 128k {out}",
            "horizontal_youtube": "ffmpeg -y -i {in} -vf 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2' -c:v libx264 -crf 20 -preset veryfast -c:a aac -b:a 192k {out}",
            "loop_lofi_1h": "ffmpeg -y -f concat -safe 0 -i {lista} -c copy -t 3600 {out}",
            "audio_only": "ffmpeg -y -i {in} -vn -c:a libmp3lame -b:a 192k {out}",
            "subtitulos_quemados": "ffmpeg -y -i {in} -vf \"subtitles={srt}:force_style='FontSize=24,Outline=2'\" -c:v libx264 -crf 20 {out}",
            "fade_in_out": "ffmpeg -y -i {in} -vf 'fade=t=in:st=0:d=0.5,fade=t=out:st={dur}-0.5:d=0.5' {out}",
            "loop_10_clips": "for i in {1..10}; do ffmpeg -y -i clip$i.mp4 -c copy -t 360 out$i.mp4; done && ffmpeg -y -f concat -safe 0 -i lista.txt -c copy loop1h.mp4",
        },
        "reglas_anti_alucinacion": [
            "CRF 18-23 para calidad/peso equilibrado; NUNCA 0",
            "preset veryfast o ultrafast en Termux; NUNCA placebo",
            "scale SIEMPRE con force_original_aspect_ratio=decrease + pad para no deformar",
            "Vertical: 1080x1920 | Horizontal: 1920x1080 | Cuadrado: 1080x1080",
            "Para loop 1h: 10-60 clips cortos + concat -c copy (NO re-encodear el loop entero)",
            "-c copy solo si NO hay -vf ni -af",
            "Audio redes: aac 128-192k | audio archivo: libmp3lame 192k",
            "Subtítulos: -vf subtitles=file.srt:force_style='FontSize=24,Outline=2'",
            "Validar SIEMPRE con ffprobe: duración>0, resolución, codec",
            "fade out: st = duración_total - 0.5 (nunca st > duración)",
        ],
    }

    # analizar todos los scripts del repo (no solo 3)
    for p in list((ROOT/"scripts").glob("*.py")) + list((ROOT/"fases").glob("*.py")):
        try: tree = ast.parse(p.read_text(errors="ignore"))
        except Exception: continue
        cmds = extraer_cmds(tree)
        if not cmds: continue
        contract["scripts_analizados"].append({"script": str(p.relative_to(ROOT)), "comandos": len(cmds)})
        for c in cmds:
            parsed = parsear(c)
            contract["comandos"].append(parsed)
            for flag, val in parsed["flags"].items():
                contract["flags_agregados"].setdefault(flag, set()).add(val)
            for f in parsed["filtros"]:
                contract["filtros_agregados"].setdefault(f["nombre"], set()).add(f["expr"])
            for ap in parsed["anti"]:
                contract["anti_patterns"].append({"script": str(p.relative_to(ROOT)), **ap})

    contract["flags_agregados"] = {k: sorted(v) for k,v in contract["flags_agregados"].items()}
    contract["filtros_agregados"] = {k: sorted(v) for k,v in contract["filtros_agregados"].items()}

    # score de salud
    problemas = []
    if contract["anti_patterns"]: problemas.append(f"{len(contract['anti_patterns'])} anti-patterns detectados")
    if "-crf" in contract["flags_agregados"]:
        crfs = [int(x) for x in contract["flags_agregados"]["-crf"] if x.isdigit()]
        if crfs and min(crfs) < 15: problemas.append(f"-crf muy bajo: {min(crfs)}")
    if not contract["comandos"]: problemas.append("0 comandos detectados")
    contract["salud"]["problemas"] = problemas
    contract["salud"]["score"] = max(0, 100 - 20*len(problemas))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2, ensure_ascii=False))
    print(f"OK {OUT}")
    print(f"  ffmpeg {contract['version']} | filtros: {contract['binario']['filtros_disponibles']}")
    print(f"  scripts analizados: {len(contract['scripts_analizados'])}")
    print(f"  comandos detectados: {len(contract['comandos'])}")
    print(f"  flags distintos: {len(contract['flags_agregados'])} | filtros: {len(contract['filtros_agregados'])}")
    print(f"  anti-patterns: {len(contract['anti_patterns'])}")
    print(f"  SALUD: {contract['salud']['score']}/100 | {problemas}")

if __name__ == "__main__":
    main()
