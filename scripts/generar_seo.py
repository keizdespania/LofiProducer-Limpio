import json, pathlib, sys, datetime, re

ROOT = pathlib.Path.home() / "LofiProducer"
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

EMOJIS = {"controversia": "🔴", "urgencia": "🟠", "justicia": "🟡", "curiosidad": "🟢"}

MESES = {"01":"enero","02":"febrero","03":"marzo","04":"abril","05":"mayo","06":"junio",
         "07":"julio","08":"agosto","09":"septiembre","10":"octubre","11":"noviembre","12":"diciembre"}

def _limpiar(t, max_chars=55):
    if not t: return ""
    if ":" in t[:40]:
        t = t.split(":", 1)[1].strip()
    if len(t) > max_chars:
        t = t[:max_chars].rsplit(" ", 1)[0] + "..."
    return t

def _hook_a_titulo(hook, max_chars=55):
    """Coge el hook completo y lo limpia para título de short."""
    if not hook: return "la noticia del día"
    # Quitar punto final
    h = hook.strip().rstrip(".")
    # Si cabe, usar tal cual
    if len(h) <= max_chars:
        return h
    # Si no, cortar por palabras sin partir
    return h[:max_chars].rsplit(" ", 1)[0] + "..."

def _fmt_ts(seg):
    m = int(seg // 60); s = int(seg % 60)
    return f"{m:02d}:{s:02d}"

def _match_timeline(timeline, texto_escena, min_chars=10):
    """Busca el seg del timeline cuyo texto comparta >=min_chars chars con la escena."""
    if not texto_escena: return None
    # Probar varias longitudes de prefijo
    for n in [40, 30, 25, 20, 15, min_chars]:
        prefijo = texto_escena[:n]
        if len(prefijo) < min_chars: continue
        for seg in timeline:
            if prefijo in seg.get("texto", ""):
                return seg["inicio"]
    # Fallback: buscar por palabras clave (las 3 más largas de la escena)
    palabras = [p for p in re.findall(r"\w{5,}", texto_escena)][:3]
    if palabras:
        for seg in timeline:
            txt = seg.get("texto", "")
            if any(p in txt for p in palabras):
                return seg["inicio"]
    return None

def generar():
    dossier_path = OUT / f"dossier_{FECHA}.json"
    prod_path = OUT / f"produccion_{FECHA}.json"
    tl_path = OUT / f"timeline_{FECHA}.json"
    if not dossier_path.exists() or not prod_path.exists():
        print("❌ Faltan dossier o produccion"); return False

    d = json.loads(dossier_path.read_text())
    prod = json.loads(prod_path.read_text())
    timeline = json.loads(tl_path.read_text()) if tl_path.exists() else []
    top3 = d.get("top3", {})
    hooks = d.get("guiones", {}).get("hooks_totales", [])[:4]
    escenas = prod.get("escenas", [])
    if not hooks: print("❌ No hay hooks"); return False

    # Lógica experta 2026-11-04: Leer del monólogo, no del pipeline viejo
    import json
    from pathlib import Path
    prod_path = OUT / f"produccion_{fecha}.json"
    if prod_path.exists():
        prod = json.loads(prod_path.read_text())
        texto = prod.get("texto_voz_largo", "")
        
        # Buscar el primer titular real mencionado en el monólogo (El Mundo, OkDiario, etc.)
        match = re.search(r'Fíjate en ([^,.]+),? que publicó «([^»]+)»', texto)
        if match:
            medio = match.group(1).strip()
            titular = match.group(2).strip()
            # Título magnético: "El Mundo oculta esto sobre [titular]"
            titulo_largo = f"Lo que {medio} no te cuenta: {titular[:45]}..."
        else:
            # Si no hay titular, usar la fecha
            titulo_largo = f"El Encuadre | Análisis mediático del {fecha_bonita}"
    else:
        # Fallback de seguridad (no debería pasar)
        titulo_largo = f"El Encuadre | Análisis mediático del {fecha_bonita}"

    # Capítulos con matching robusto
    labels_bloques = ["🟠 HuffPost: el teatro de Delgado",
                      "🟡 Expansión: la fábula bursátil",
                      "🔴 OkDiario: el precio de 'gratis'",
                      "🟤 Plutarco: el miedo premium",
                      "🟢 PP y luto: la maniobra",
                      "🔵 Sonrisa corporativa",
                      "🟣 Big Tech: los cuatro gigantes",
                      "⚫ Cortina de humo y hombre de paja"]
    capitulos = [(0.0, "🎬 Intro: el mecanismo del día")]
    if timeline:
        for i, label in enumerate(labels_bloques):
            num_escena = (i + 1) * 2  # 2, 4, 6, 8, 10, 12, 14, 16
            if num_escena > len(escenas): break
            texto = escenas[num_escena - 1].get("texto", "")
            inicio = _match_timeline(timeline, texto)
            if inicio is not None:
                capitulos.append((inicio, label))
        capitulos.append((timeline[-1]["fin"] - 30, "🎯 Conclusión: qué mirar mañana"))
    capitulos = sorted(set(capitulos), key=lambda x: x[0])

    # Descripción
    noticias = list(top3.values()) if isinstance(top3, dict) else list(top3)
    desc = f"🚨 El análisis de hoy: cómo los medios construyen el relato. Un monólogo de El Encuadre.\n\n"
    desc += "━━━━━━━━━━━━━━━━━━━━\n📌 BLOQUES DEL VÍDEO\n━━━━━━━━━━━━━━━━━━━━\n"
    for _, label in capitulos[1:-1]:
        desc += f"{label}\n"
    desc += "\n━━━━━━━━━━━━━━━━━━━━\n⏱️ CAPÍTULOS\n━━━━━━━━━━━━━━━━━━━━\n"
    for ts, label in capitulos:
        desc += f"{_fmt_ts(ts)} {label}\n"
    desc += """
━━━━━━━━━━━━━━━━━━━━
🔔 SUSCRÍBETE para aprender a leer entre líneas.
━━━━━━━━━━━━━━━━━━━━

📌 Somos El Encuadre. Análisis técnico del relato mediático.

#AnálisisMediático #Framing #ElEncuadre
"""
    tags_largo = f"análisis mediático, framing, manipulación, El Encuadre, {fecha}"

    # Shorts con hooks completos
    shorts = []
    for i, h in enumerate(hooks):
        tipo = h.get("tipo", "dato").lower()
        hook_txt = h.get("hook", "")
        emoji = EMOJIS.get(tipo, "🎬")
        shorts.append({
            "num": i + 1, "tipo": tipo,
            "titulo": f"{emoji} {_hook_a_titulo(hook_txt, 55)}",
            "descripcion": f"{hook_txt}\n\n🔔 Suscríbete.\n\n#Shorts #AnálisisMediático #ElEncuadre",
            "hashtags": "#Shorts #AnálisisMediático #ElEncuadre"
        })

    seo = {"fecha": FECHA,
           "largo": {"titulo": titulo_largo, "descripcion": desc, "tags": tags_largo},
           "shorts": shorts,
           "canal": {"keywords": "análisis mediático, framing, sesgo informativo, El Encuadre"}}
    out = OUT / f"seo_{FECHA}.json"
    out.write_text(json.dumps(seo, indent=2, ensure_ascii=False))

    print(f"✅ Generado: {out}")
    print(f"\nTÍTULO LARGO: {titulo_largo} ({len(titulo_largo)} chars)")
    print(f"\nCAPÍTULOS ({len(capitulos)}):")
    for ts, label in capitulos:
        print(f"  {_fmt_ts(ts)} {label}")
    print(f"\nSHORTS:")
    for s in shorts:
        print(f"  Short {s['num']} ({s['tipo']}): {s['titulo']} ({len(s['titulo'])} chars)")
    return True

if __name__ == "__main__":
    sys.exit(0 if generar() else 1)
