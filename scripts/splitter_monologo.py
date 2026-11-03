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

def _intro_fija(fecha_str="hoy"):
    """Escena 1: gancho fuerte + somos el encuadre + fecha."""
    return (
        f"Mira, te lo voy a decir claro desde el principio. "
        f"Los medios no informan. Venden. "
        f"Y tú, y yo, y todos, nos lo tragamos. "
        f"Hasta hoy. "
        f"Somos El Encuadre, {fecha_str}. "
        f"Y vamos a abrir la cloaca. "
        f"Te voy a enseñar las técnicas que han usado hoy. "
        f"Quédate, porque esto te va a cambiar la forma de leer el periódico."
    )


def _outro_fijo():
    """Escena 18: CTA realista (like + sub + compartir + Telegram)."""
    return (
        "Si te ha servido, dale a like. "
        "Suscríbete si quieres más. "
        "Y comparte esto con ese amigo que todavía se cree la tele. "
        "Nos vemos en Telegram. "
        "Y en la web, elencuadre.com. "
        "Mañana volverán a intentarlo. "
        "La única diferencia es que ahora ya lo ves. "
        "Esto es El Encuadre."
    )


def splitter(texto, num_escenas=18, fecha_str="hoy"):
    """Divide texto en N escenas por FRASES (no por párrafos).
    Garantiza N exactas. Nunca corta a mitad de frase.
    """
    if not texto or not texto.strip():
        return []
    
    # 0. Limpiar texto (colapsar saltos, quitar acotaciones TTS)
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # 1. Limpiar: colapsar saltos dentro de frases, dejar 1 espacio
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    # 2. Split por frases (. ? !) preservando el signo
    frases = re.findall(r'[^.!?]+[.!?]+', texto)
    # Si el último trozo no tiene signo, añadirlo
    resto = texto[sum(len(f) for f in frases):].strip()
    if resto:
        frases.append(resto + ".")
    
    if not frases:
        return []
    
    # 3. Calcular palabras objetivo por escena
    total_palabras = sum(len(f.split()) for f in frases)
    objetivo = max(60, total_palabras // num_escenas)
    
    # 4. Agrupar frases hasta objetivo (SIN cortar frases)
    escenas_texto = []
    buffer = []
    buffer_palabras = 0
    
    for f in frases:
        palabras_f = len(f.split())
        if buffer_palabras + palabras_f <= objetivo * 1.3 or not buffer:
            buffer.append(f)
            buffer_palabras += palabras_f
        else:
            escenas_texto.append(" ".join(buffer))
            buffer = [f]
            buffer_palabras = palabras_f
    
    if buffer:
        escenas_texto.append(" ".join(buffer))
    
    # 5. Ajustar a N exactas SIN cortar frases
    if len(escenas_texto) > num_escenas:
        # Fusionar escenas sobrantes por pares (empezando por las más cortas)
        while len(escenas_texto) > num_escenas:
            # Encontrar la pareja adyacente más corta
            mejor_idx = 0
            mejor_len = float('inf')
            for i in range(len(escenas_texto) - 1):
                combined = len(escenas_texto[i].split()) + len(escenas_texto[i+1].split())
                if combined < mejor_len:
                    mejor_len = combined
                    mejor_idx = i
            escenas_texto[mejor_idx] = escenas_texto[mejor_idx] + " " + escenas_texto[mejor_idx + 1]
            del escenas_texto[mejor_idx + 1]
    elif len(escenas_texto) < num_escenas:
        # Añadir más escenas dividiendo la más larga por frases
        while len(escenas_texto) < num_escenas:
            # Coger la más larga
            idx_mas_larga = max(range(len(escenas_texto)), key=lambda i: len(escenas_texto[i].split()))
            p_larga = escenas_texto[idx_mas_larga]
            frases_p = re.findall(r'[^.!?]+[.!?]+', p_larga)
            if len(frases_p) < 2:
                # No se puede dividir: duplicar (raro pero evita bucle infinito)
                break
            mitad = len(frases_p) // 2
            primera = " ".join(frases_p[:mitad])
            segunda = " ".join(frases_p[mitad:])
            escenas_texto = escenas_texto[:idx_mas_larga] + [primera, segunda] + escenas_texto[idx_mas_larga+1:]
    
    # 6. Construir escenas con metadata (INTRO + desarrollo + OUTRO fijos)
    escenas = []
    
    # Escena 1: INTRO FIJA (hook + somos el encuadre + fecha)
    intro_txt = _intro_fija(fecha_str)
    escenas.append({
        "id": 1,
        "texto": intro_txt,
        "concepto_visual": "dramatic newsroom at night, single spotlight, cinematic",
        "mood_musical": "tension",
        "tipo_visual": "hook",
    })
    
    # Escenas 2 a N-1: desarrollo (del texto del monólogo)
    # Recortar el texto del monólogo: quitar primer y último párrafo si son intro/outro
    desarrollo = escenas_texto[:num_escenas-2]  # dejamos hueco para intro y outro
    while len(desarrollo) < num_escenas - 2:
        # Por si el monólogo es corto, añadir placeholder
        desarrollo.append("")
    
    for i, txt in enumerate(desarrollo):
        escena_num = i + 2
        tipo = _detectar_tipo(txt, escena_num, num_escenas)
        escenas.append({
            "id": escena_num,
            "texto": txt,
            "concepto_visual": _concepto_visual_para(tipo, txt),
            "mood_musical": "tension" if tipo in ("hook", "dato", "explicacion") else "relax" if tipo == "cierre" else "misterio",
            "tipo_visual": tipo,
        })
    
    # Escena N: OUTRO FIJO (CTA + apoyo)
    outro_txt = _outro_fijo()
    escenas.append({
        "id": num_escenas,
        "texto": outro_txt,
        "concepto_visual": "lone figure walking away, sunset, cinematic",
        "mood_musical": "relax",
        "tipo_visual": "cierre",
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
