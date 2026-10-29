"""analista_fase1.py - Cadena de análisis con el Consejo de Inteligencia."""
import sys, json, pathlib, datetime, re, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))
from especialistas import pedir_a_especialista

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"


def _parse_json_seguro(texto):
    if not texto: return {}
    t = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).replace('```', '').strip()
    try: return json.loads(t)
    except: pass
    for m in sorted(re.findall(r'\{.*?\}', texto, re.DOTALL), key=len, reverse=True):
        try: return json.loads(m)
        except: pass
    for block in re.findall(r'```(?:json)?(.*?)```', texto, re.DOTALL):
        try: return json.loads(block.strip())
        except: pass
    return {}


def _sanitizar_top3(top3, titulares_disponibles):
    """Sustituye items del top3 con temas trágicos por alternativas seguras."""
    try:
        from filtro_seguridad import PAT as _FP
        CRIT = _FP["critica"] + _FP["moderada"]
    except Exception:
        CRIT = [r"\bmuert", r"\basesin", r"\btiroteo", r"\bsiniestro", r"\btragedia", r"\bse[nñ]alizaci"]
    def _malo(txt):
        s = (txt or "").lower()
        return any(re.search(p, s) for p in CRIT)
    items = []
    if isinstance(top3, dict):
        if "top3" in top3 and isinstance(top3["top3"], list):
            for it in top3["top3"]:
                items.append(it.get("titulo") or it.get("title") or str(it))
        else:
            for k in sorted(top3.keys()):
                v = top3[k]
                items.append(v if isinstance(v, str) else str(v))
    elif isinstance(top3, list):
        for it in top3:
            items.append(it.get("titulo") or it.get("title") or str(it))
    subs = 0
    for i, t in enumerate(items):
        if _malo(t):
            for cand in titulares_disponibles:
                if cand and not _malo(cand):
                    items[i] = cand; subs += 1; break
    if subs: print(f"[fase1] sanitizados {subs} items del top3", flush=True)
    return {f"noticia_{i+1}": t for i, t in enumerate(items[:3])}


def _titulares_de(datos):
    out = []
    for sec in ("prensa", "agencias"):
        for lst in (datos.get(sec) or {}).values():
            for x in lst:
                if isinstance(x, dict) and x.get("titular"):
                    out.append(x["titular"])
    return out


def analizar_fase1(fecha=None):
    fecha = fecha or datetime.date.today().isoformat()
    limpia = OUT / f"recoleccion_{fecha}_limpia.json"
    rec_json = limpia if limpia.exists() else (OUT / f"recoleccion_{fecha}.json")
    print(f"[fase1] leyendo {rec_json.name}", flush=True)
    if not rec_json.exists():
        print(f"[fase1] No existe {rec_json}"); return None
    datos = json.loads(rec_json.read_text())

    # 1. Top 3
    print("[fase1] Detectando Top 3 noticias...", flush=True)
    ctx = "TITULARES DE PRENSA:\n"
    for medio, noticias in (datos.get("prensa") or {}).items():
        ctx += f"\n[{medio}]\n"
        for n in noticias:
            if isinstance(n, dict): ctx += f"- {n.get('titular','')}\n"
    for sec in ("tv", "radio"):
        for medio, vids in (datos.get(sec) or {}).items():
            ctx += f"\n[{medio}]\n"
            for v in vids:
                if isinstance(v, dict): ctx += f"- {v.get('titulo','')}\n"

    top3 = _parse_json_seguro(pedir_a_especialista(
        "detective_tendencias_v2", "Detecta el Top 3 de noticias del día.", contexto=ctx[:4000]))
    if not top3:
        print("[fase1] ⚠️ Detective falló. Reintento simplificado...", flush=True)
        top3 = _parse_json_seguro(pedir_a_especialista(
            "detective_tendencias_v2",
            'Devuelve SOLO JSON: {"noticia_1":"","noticia_2":"","noticia_3":""}',
            contexto=ctx[:2000]))
        if not top3:
            print("[fase1] ❌ Reintento fallido. Fallback manual.", flush=True)
            top3 = {"noticia_1": "Actualidad nacional", "noticia_2": "Política", "noticia_3": "Economía"}

    top3 = _sanitizar_top3(top3, _titulares_de(datos))
    print(f"[fase1] ✅ Top 3 detectado: {list(top3.values())}", flush=True)

    # 2. Análisis por medio
    print("[fase1] Analizando cada medio...", flush=True)
    todos = {}
    medios = list((datos.get("prensa") or {}).keys()) + list((datos.get("agencias") or {}).keys()) \
           + list((datos.get("tv") or {}).keys()) + list((datos.get("radio") or {}).keys())
    noticia = list(top3.values())[0] if isinstance(top3, dict) else "noticias del día"

    for medio in medios:
        textos = []
        for sec in ("prensa", "agencias"):
            for n in (datos.get(sec) or {}).get(medio, []):
                if isinstance(n, dict) and n.get("titular"): textos.append(n["titular"])
        for sec in ("tv", "radio"):
            for v in (datos.get(sec) or {}).get(medio, []):
                if isinstance(v, dict) and v.get("titulo"): textos.append(v["titulo"])
        for a in datos.get("audios", []):
            if a.get("medio") == medio and a.get("transcripcion"):
                textos.append(a["transcripcion"][:2000])
        if not textos: continue

        ctx_medio = f"MEDIO: {medio}\nTITULARES:\n" + "\n".join(textos[:3])
        print(f"  🔍 {medio}...", flush=True)
        r = pedir_a_especialista("forense_medios",
            f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON con: nombre, titular_real, titular_traducido, imd_local, framing, palabra_cuchillo, tecnica_principal, omision.",
            contexto=ctx_medio[:800])
        an = _parse_json_seguro(r)
        if not an: continue
        r_emo = pedir_a_especialista("analista_emocional", f"Analiza las emociones de {medio}", contexto=ctx_medio[:2000])
        emo = _parse_json_seguro(r_emo)
        if emo: an["emociones"] = emo
        r_ses = pedir_a_especialista("detector_sesgos_cognitivos", f"Detecta sesgos en {medio}", contexto=ctx_medio[:2000])
        ses = _parse_json_seguro(r_ses)
        if ses: an["sesgos_cognitivos"] = ses
        todos[medio] = [an]
        time.sleep(1)

    # 3. Guardar
    res = {"fecha": fecha, "top3": top3, "analisis": todos, "recoleccion": datos}
    out = OUT / f"analisis_fase1_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out}", flush=True)
    return res


if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
