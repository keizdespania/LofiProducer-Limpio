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


def _es_malo(txt):
    """Detecta si un titular es trágico."""
    if not txt: return False
    try:
        from filtro_seguridad import PAT as _FP
        patrones = _FP["critica"] + _FP["moderada"]
    except Exception:
        patrones = [r"\bmuert", r"\basesin", r"\btiroteo", r"\bsiniestro",
                    r"\btragedia", r"\bse[nñ]alizaci", r"\bmorgue\b", r"\bllanto\b"]
    s = txt.lower()
    return any(re.search(p, s) for p in patrones)


def _similares(a, b):
    """Jaccard: mismo tema con palabras distintas."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb: return False
    return len(wa & wb) / len(wa | wb) > 0.5


def _sanitizar_top3(top3, titulares_disponibles):
    """Sustituye tragedias + dedupe semántico. SIEMPRE devuelve 3 únicos."""
    # 1. Extraer items
    items = []
    if isinstance(top3, dict):
        if "top3" in top3 and isinstance(top3["top3"], list):
            for it in top3["top3"]:
                items.append(it.get("titulo") or it.get("title") or str(it))
        else:
            for k in sorted(top3.keys()):
                v = top3[k]
                items.append(v if isinstance(v, str) else (v.get("titulo") if isinstance(v, dict) else str(v)))
    elif isinstance(top3, list):
        for it in top3:
            items.append(it.get("titulo") or it.get("title") or str(it))

    # 2. Filtrar trágicos
    items = [x for x in items if x and not _es_malo(x)]

    # 3. Rellenar con limpios (sin trágicos)
    for cand in titulares_disponibles:
        if len(items) >= 3: break
        if cand and not _es_malo(cand):
            items.append(cand)

    # 4. Dedupe semántico
    unicos = []
    for it in items:
        if not any(_similares(it, u) for u in unicos):
            unicos.append(it)
    for cand in titulares_disponibles:
        if len(unicos) >= 3: break
        if cand and not _es_malo(cand) and not any(_similares(cand, u) for u in unicos):
            unicos.append(cand)

    # 5. Relleno genérico si no hay 3
    _GENERICOS = ["Actualidad nacional", "Política", "Economía", "Sociedad", "Internacional"]
    for g in _GENERICOS:
        if len(unicos) >= 3: break
        if not any(_similares(g, u) for u in unicos):
            unicos.append(g)

    return {f"noticia_{i+1}": t0 for i, t0 in enumerate(unicos[:3])}


def _titulares_de(datos):
    """Lista de titulares de prensa+agencias."""
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
        "detective_tendencias_v2", "Detecta el Top 3 de noticias del día.", contexto=ctx[:4000], proveedor="groq"))
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

    from concurrent.futures import ThreadPoolExecutor, as_completed
    total = len(medios)
    def _procesar(medio):
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
        if not textos: return medio, None
        ctx_medio = f"MEDIO: {medio}\nTITULARES:\n" + "\n".join(textos[:3])
        r = pedir_a_especialista("forense_medios",
            f"Analiza el sesgo de {medio} sobre: {noticia}. Devuelve SOLO JSON con: nombre, titular_real, titular_traducido, imd_local, framing, palabra_cuchillo, tecnica_principal, omision.",
            contexto=ctx_medio[:800], proveedor="auto")
        an = _parse_json_seguro(r)
        if not an: return medio, None
        import time as _t; _t.sleep(0.5)
        r_emo = pedir_a_especialista("analista_emocional", f"Analiza las emociones de {medio}", contexto=ctx_medio[:2000], proveedor="omni")
        emo = _parse_json_seguro(r_emo)
        if emo: an["emociones"] = emo
        _t.sleep(0.5)
        r_ses = pedir_a_especialista("detector_sesgos_cognitivos", f"Detecta sesgos en {medio}", contexto=ctx_medio[:2000], proveedor="omni")
        ses = _parse_json_seguro(r_ses)
        if ses: an["sesgos_cognitivos"] = ses
        return medio, an
    print(f"[fase1] Analizando {total} medios (5 en paralelo)...", flush=True)
    completados = 0
    with ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(_procesar, m): m for m in medios}
        for f in as_completed(futs):
            completados += 1
            try:
                medio, an = f.result()
                if an:
                    todos[medio] = [an]
                    print(f"  [{completados}/{total}] OK {medio} — framing: {str(an.get('framing',''))[:40]}", flush=True)
                else:
                    print(f"  [{completados}/{total}] -- {medio} (sin análisis)", flush=True)
            except Exception as e:
                print(f"  [{completados}/{total}] X error: {e}", flush=True)

    # 3. Guardar
    res = {"fecha": fecha, "top3": top3, "analisis": todos, "recoleccion": datos}
    out = OUT / f"analisis_fase1_{fecha}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"[fase1] ✅ Guardado en {out}", flush=True)
    return res


if __name__ == "__main__":
    analizar_fase1(sys.argv[1] if len(sys.argv) > 1 else None)
