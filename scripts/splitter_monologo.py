#!/usr/bin/env python3
"""splitter_monologo.py - Divide 1 monólogo largo en 18 escenas.
Corta por párrafos, agrupa ~90 palabras/escena, detecta tipo_visual.
Garantiza EXACTAMENTE 18 escenas: 1 intro + 16 desarrollo + 1 outro.
"""
import re, sys, json

def _detectar_tipo(texto, idx, total):
    """Detecta tipo_visual de la escena (mismo que segmentar_imagenes.py)."""
    t = (texto or "").lower().strip()
    if idx == 0:
        return "hook"
    if idx >= total - 1:
        return "cierre"
    if any(x in t for x in ["tituló", "titular de", "publicó", "reza:"]):
        return "cita"
    if any(x in t for x in ["framing", "sesgo", "técnica", "manipulación", "significa", "implica"]):
        return "explicacion"
    if any(x in t for x in ["en cambio", "por su parte", "sin embargo", "mientras", "contrasta"]):
        return "contraste"
    if any(c.isdigit() for c in t) and any(x in t for x in ["%", "millones", "mil ", "dato", "cifra"]):
        return "dato"
    return "default"

def _concepto_visual_para(tipo, texto):
    """Concepto visual fallback por tipo (si el LLM no responde)."""
    fallbacks = {
        "hook": "dramatic newsroom at night, single spotlight, cinematic",
        "cita": "newspaper headline close up, red accent, dramatic lighting",
        "explicacion": "abstract mechanism, gears turning, dark background",
        "contraste": "split screen contrast, two worlds, dramatic lighting",
        "dato": "data visualization, red numbers, dark background",
        "cierre": "lone figure walking away, sunset, cinematic",
        "default": "cinematic newspaper scene, dramatic light, no text",
    }
    return fallbacks.get(tipo, fallbacks["default"])

def splitter(texto, num_escenas=18):
    """Divide texto en N escenas por párrafos. Garantiza N exactas.
    
    Returns: lista de dicts {id, texto, concepto_visual, mood_musical, tipo_visual}
    """
    if not texto or not texto.strip():
        return []
    
    # 1. Split por dobles saltos (párrafos) o por frases si no hay párrafos
    parrafos = [p.strip() for p in re.split(r'\n\s*\n', texto) if p.strip()]
    if len(parrafos) < 3:
        # Fallback: split por frases
        parrafos = re.split(r'(?<=[.!?])\s+', texto.strip())
    
    # 2. Calcular palabras objetivo por escena
    total_palabras = sum(len(p.split()) for p in parrafos)
    objetivo = max(60, total_palabras // num_escenas)  # mínimo 60 palabras por escena
    
    # 3. Agrupar párrafos hasta objetivo
    escenas_texto = []
    buffer = []
    buffer_palabras = 0
    
    for p in parrafos:
        palabras_p = len(p.split())
        if buffer_palabras + palabras_p <= objetivo * 1.3 or not buffer:
            buffer.append(p)
            buffer_palabras += palabras_p
        else:
            escenas_texto.append(" ".join(buffer))
            buffer = [p]
            buffer_palabras = palabras_p
    
    if buffer:
        escenas_texto.append(" ".join(buffer))
    
    # 4. Ajustar a N exactas
    if len(escenas_texto) > num_escenas:
        # Fusionar sobrantes al final
        sobrantes = escenas_texto[num_escenas-1:]
        escenas_texto = escenas_texto[:num_escenas-1] + [" ".join(sobrantes)]
    elif len(escenas_texto) < num_escenas:
        # Subdividir los más largos
        while len(escenas_texto) < num_escenas:
            # Encontrar el más largo
            idx_mas_largo = max(range(len(escenas_texto)), key=lambda i: len(escenas_texto[i].split()))
            p = escenas_texto[idx_mas_largo]
            palabras = p.split()
            mitad = len(palabras) // 2
            if mitad < 30:
                # No se puede subdividir más, duplicar con variación
                escenas_texto.insert(idx_mas_largo, p)
                break
            primera = " ".join(palabras[:mitad])
            segunda = " ".join(palabras[mitad:])
            escenas_texto = escenas_texto[:idx_mas_largo] + [primera, segunda] + escenas_texto[idx_mas_largo+1:]
    
    # 5. Construir escenas con metadata
    escenas = []
    for i, txt in enumerate(escenas_texto[:num_escenas]):
        tipo = _detectar_tipo(txt, i, num_escenas)
        escenas.append({
            "id": i + 1,
            "texto": txt,
            "concepto_visual": _concepto_visual_para(tipo, txt),
            "mood_musical": "tension" if tipo in ("hook", "dato", "explicacion") else "relax" if tipo == "cierre" else "misterio",
            "tipo_visual": tipo,
        })
    
    return escenas

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 splitter_monologo.py <fichero_texto_o_json>")
        sys.exit(1)
    
    from pathlib import Path
    src = Path(sys.argv[1])
    if src.suffix == ".json":
        d = json.loads(src.read_text())
        texto = d.get("texto_voz_largo") or " ".join(e.get("texto","") for e in d.get("escenas",[]))
    else:
        texto = src.read_text()
    
    escenas = splitter(texto)
    print(f"=== {len(escenas)} ESCENAS ===")
    for e in escenas:
        print(f"[{e['id']}] {e['tipo_visual']:12} {len(e['texto'].split()):3} palabras | {e['texto'][:80]}")
    
    # Guardar
    out = src.parent / (src.stem + "_split.json")
    out.write_text(json.dumps(escenas, indent=2, ensure_ascii=False))
    print(f"\n💾 {out}")
