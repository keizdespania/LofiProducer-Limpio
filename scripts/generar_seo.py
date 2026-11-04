"""generar_seo.py - Genera SEO del vídeo y shorts desde el MONÓLOGO + top16 real."""
from datetime import date
import json, pathlib, sys, datetime, re

ROOT = pathlib.Path.home() / "LofiProducer"
OUT = ROOT / "output" / "encuadre"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

MESES_ES = ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"]

EMOJIS_TIPO = {"dato": "🟠", "contradiccion": "🎬", "prediccion": "🔮", "tutorial": "🎯"}
EMOJI_POOL = ["🟠", "🟡", "🔴", "🟤"]


def _fmt_ts(seg):
    m = int(seg // 60); s = int(seg % 60)
    return f"{m:02d}:{s:02d}"


def _fecha_bonita(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} de {MESES_ES[d.month-1]} de {d.year}"


def _match_timeline(timeline, texto_escena):
    """Busca el seg del timeline que contenga el prefijo del texto de la escena."""
    if not texto_escena or not timeline:
        return None
    for n in (60, 50, 40, 30, 20, 15):
        prefijo = texto_escena[:n]
        if len(prefijo) < 15:
            continue
        for seg in timeline:
            if prefijo in seg.get("texto", ""):
                return seg["inicio"]
    # Fallback: 4 palabras largas
    palabras = [p for p in re.findall(r"\w{5,}", texto_escena)][:4]
    if palabras:
        for seg in timeline:
            txt = seg.get("texto", "")
            if sum(1 for p in palabras if p in txt) >= 2:
                return seg["inicio"]
    return None


def _escena_con_medio(escenas, medio_n):
    """Devuelve la primera escena que menciona 'Fíjate en [Medio]' o 'Mira a [Medio]'."""
    for esc in escenas:
        txt = esc.get("texto", "")
        if f"Fíjate en {medio_n}" in txt or f"Mira a {medio_n}" in txt:
            return txt
    # Fallback: escena que contiene el nombre del medio
    for esc in escenas:
        txt = esc.get("texto", "")
        if medio_n in txt:
            return txt
    return None


def _capitulos(prod, top16, timeline):
    """Genera capítulos con los 3-4 primeros medios del top16 (los que el monólogo usa)."""
    escenas = prod.get("escenas", [])
    capitulos = [(0.0, "🎬 Intro: el mecanismo del día")]
    usados = 0

    for m in top16[:4]:
        medio_n = m.get("medio", "").strip()
        titular = m.get("titular", "").strip()[:45]
        if not medio_n:
            continue
        texto_escena = _escena_con_medio(escenas, medio_n)
        if not texto_escena:
            continue
        inicio = _match_timeline(timeline, texto_escena)
        if inicio is None:
            continue
        emoji = EMOJI_POOL[usados % 4]
        label = f"{emoji} {medio_n}: {titular}"
        capitulos.append((inicio, label))
        usados += 1

    if timeline:
        final_ts = max(0, timeline[-1].get("fin", 0) - 20)
        capitulos.append((final_ts, "🎯 Conclusión: qué mirar mañana"))
    return sorted(set(capitulos), key=lambda x: x[0])


def _titulo(top16, texto):
    """Título del primer medio del top16 que aparezca en el monólogo."""
    for m in top16[:3]:
        medio_n = m.get("medio", "").strip()
        titular = m.get("titular", "").strip()[:55]
        if medio_n and titular and (f"Fíjate en {medio_n}" in texto or f"Mira a {medio_n}" in texto):
            return f"{medio_n}: {titular}"
    if top16:
        m = top16[0]
        return f"{m.get('medio', 'Medios')}: {m.get('titular', 'análisis del día')[:55]}"
    return "El Encuadre | Análisis mediático del día"


def _shorts(prod):
    shorts_finales = prod.get("shorts_finales", [])
    shorts = []
    for i, s in enumerate(shorts_finales[:4]):
        tipo = (s.get("tipo") or "dato").lower()
        guion = s.get("guion") or s.get("hook") or "Análisis del día"
        emoji = EMOJIS_TIPO.get(tipo, "🎬")
        titulo_txt = guion.strip().rstrip(".")[:55]
        if len(guion) > 55:
            titulo_txt = titulo_txt.rsplit(" ", 1)[0] + "..."
        shorts.append({
            "num": i + 1,
            "tipo": tipo,
            "titulo": f"{emoji} {titulo_txt}",
            "descripcion": f"{guion}\n\n🔔 Suscríbete.\n\n#Shorts #AnálisisMediático #ElEncuadre",
            "hashtags": "#Shorts #AnálisisMediático #ElEncuadre",
        })
    return shorts


def _descripcion(titulo, capitulos):
    bloques = [label for _, label in capitulos[1:-1]]
    desc = "🚨 El análisis de hoy: cómo los medios construyen el relato. Un monólogo de El Encuadre.\n\n"
    desc += "━━━━━━━━━━━━━━━━━━━━\n📌 BLOQUES DEL VÍDEO\n━━━━━━━━━━━━━━━━━━━━\n"
    for label in bloques:
        desc += f"{label}\n"
    desc += "\n━━━━━━━━━━━━━━━━━━━━\n⏱️ CAPÍTULOS\n━━━━━━━━━━━━━━━━━━━━\n"
    for ts, label in capitulos:
        desc += f"{_fmt_ts(ts)} {label}\n"
    desc += "\n━━━━━━━━━━━━━━━━━━━━\n🔔 SUSCRÍBETE para aprender a leer entre líneas.\n━━━━━━━━━━━━━━━━━━━━\n\n"
    desc += "📌 Somos El Encuadre. Análisis técnico del relato mediático.\n\n"
    desc += "#AnálisisMediático #Framing #ElEncuadre"
    return desc


def generar():
    prod_path = OUT / f"produccion_{FECHA}.json"
    analisis_path = OUT / f"analisis_fase1_{FECHA}.json"
    tl_path = OUT / f"timeline_{FECHA}.json"

    if not prod_path.exists():
        print(f"❌ No existe produccion_{FECHA}.json")
        return False
    prod = json.loads(prod_path.read_text())
    analisis = json.loads(analisis_path.read_text()) if analisis_path.exists() else {}
    timeline = json.loads(tl_path.read_text()) if tl_path.exists() else []
    top16 = analisis.get("top16", [])
    texto = prod.get("texto_voz_largo", "")
    fecha_larga = _fecha_bonita(FECHA)

    print(f"[seo] Top16 disponible: {len(top16)} medios")
    print(f"[seo] Timeline: {len(timeline)} segmentos")

    # 1) Título
    titulo_largo = _titulo(top16, texto)

    # 2) Capítulos
    capitulos = _capitulos(prod, top16, timeline)

    # 3) Descripción
    desc = _descripcion(titulo_largo, capitulos)
    tags_largo = f"análisis mediático, framing, manipulación, El Encuadre, {FECHA}"

    # 4) Shorts (del monólogo)
    shorts = _shorts(prod)

    # 5) Guardar
    seo = {
        "fecha": FECHA,
        "largo": {"titulo": titulo_largo, "descripcion": desc, "tags": tags_largo},
        "shorts": shorts,
        "canal": {"keywords": "análisis mediático, framing, sesgo informativo, El Encuadre"},
    }
    out = OUT / f"seo_{FECHA}.json"
    out.write_text(json.dumps(seo, indent=2, ensure_ascii=False))

    # 6) Reporte
    print(f"\n✅ Generado: {out}")
    print(f"\nTÍTULO LARGO: {titulo_largo} ({len(titulo_largo)} chars)")
    print(f"\nCAPÍTULOS ({len(capitulos)}):")
    for ts, label in capitulos:
        print(f"  {_fmt_ts(ts)} {label}")
    print(f"\nSHORTS ({len(shorts)}):")
    for s in shorts:
        print(f"  Short {s['num']} ({s['tipo']}): {s['titulo']} ({len(s['titulo'])} chars)")
    return True


if __name__ == "__main__":
    sys.exit(0 if generar() else 1)
