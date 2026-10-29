"""filtro_seguridad.py v3 - severidades + ctx + word-boundaries."""
import json, pathlib, re, sys, argparse
from collections import Counter
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
PAT = {
 "critica": [r"\bsuicid\w*",r"\bmasacre\w*",r"\btiroteo\w*",r"\basesinat\w*",r"\bhomicidi\w*",r"\bterroris\w*",r"\batentad\w*",r"\bviolaci[oó]n\w*",r"\bsecuestr\w*",r"\bcat[aá]strofe\w*",r"\bapuñalamient\w*",r"\bautolesi\w*"],
 "moderada": [r"\bfallecid\w*",r"\bmuert[oa]s?\b",r"\bfatal\b",r"\btragedia\w*",r"\bv[ií]ctima\w*",r"\baccident\w*",r"\bchoque\b",r"\bcolisi[oó]n\w*",r"\batropell\w*",r"\bincendio\w*",r"\bexplosi[oó]n\w*",r"\bderrumbe\w*",r"\bbombarde\w*",r"\bguerra\s+(civil|mundial|de\s+ucrania|de\s+gaza|en\s+ucrania|en\s+gaza|de\s+siria)",r"\bconflicto\s+armado",r"\bpandemia\w*",r"\bterremoto\w*",r"\btsunami\w*",r"\bofensiva\s+militar",r"\bherid[oa]\s+grave\w*"],
 "baja": [r"\bmuerte\b"],
 "sensac": [r"\bimpactante\w*",r"\bescalofriante\w*",r"\bsobrecogedor\w*",r"\bterror[ií]fic\w*",r"\bhorroros\w*",r"\bsangrient\w*",r"\bbrutal\w*",r"\bshock\w*"],
}
CTX = [r"\ban[aá]lisis\b",r"\bcobertura\s+medi[aá]tica",r"\btratamiento\s+medi[aá]tico",r"\bframing\b",r"\bsesgo\w*",r"\bmanipulaci[oó]n\w*",r"\bencuadre\b",r"\bc[oó]mo\s+los\s+medios",r"\bc[oó]mo\s+se\s+cubre"]
def _m(t,ps): return [p for p in ps if re.search(p,t,re.I)]
def _evaluar(it):
    ti=(it.get("titulo") or it.get("title") or "").lower()
    de=(it.get("descripcion") or it.get("summary") or it.get("texto") or "").lower()
    cu=(it.get("contenido") or it.get("body") or "").lower()
    fu=f"{ti} {de} {cu}"
    cr,mo,se=_m(fu,PAT["critica"]),_m(fu,PAT["moderada"]),_m(fu,PAT["sensac"])
    ba=_m(fu,PAT["baja"])
    crt=_m(ti,PAT["critica"]); mot=_m(ti,PAT["moderada"]); bat=_m(ti,PAT["baja"])
    ctx=bool(_m(fu,CTX))
    if crt and not ctx: return {"segura":False,"sev":"critica","razon":"critica+titulo sin ctx","m":crt,"ctx":ctx}
    if len(cr)>=2 and not ctx: return {"segura":False,"sev":"critica","razon":"2+criticas sin ctx","m":cr,"ctx":ctx}
    if cr and not ctx: return {"segura":False,"sev":"alta","razon":"critica sin ctx","m":cr,"ctx":False}
    if mot and not ctx: return {"segura":False,"sev":"media","razon":"moderada+titulo","m":mot,"ctx":False}
    if len(mo)>=2 and not ctx: return {"segura":False,"sev":"media","razon":"2+moderadas","m":mo,"ctx":False}
    if bat and (mo or se) and not ctx: return {"segura":False,"sev":"media","razon":"baja+refuerzo","m":bat+mo+se,"ctx":False}
    if se and not ctx: return {"segura":False,"sev":"media","razon":"sensac","m":se,"ctx":False}
    return {"segura":True,"sev":"ok","razon":"ok","m":(cr+mo+se+ba)[:5],"ctx":ctx,"advertencia":bool(cr+mo+se+ba)}
def _cargar(f):
    p=OUT/f"recoleccion_{f}.json"
    if p.exists(): return p,json.loads(p.read_text())
    for q in sorted(OUT.glob(f"recoleccion_{f}*.json")): return q,json.loads(q.read_text())
    raise FileNotFoundError(f"sin recoleccion {f}")
def filtrar(f,dry=False,verb=False):
    p,d=_cargar(f)
    items=d if isinstance(d,list) else (d.get("noticias") or d.get("items") or d.get("articulos") or [])
    if not items: print("WARN sin noticias"); return
    ok=[];ko=[]
    for it in items:
        r=_evaluar(it); it["_filtro"]=r
        (ok if r["segura"] else ko).append(it)
    print(f"OK {p.name}: {len(items)} -> keep {len(ok)} drop {len(ko)}")
    if verb:
        for it in ko: print(f"  X [{it['_filtro']['sev']}] {(it.get('titulo') or '?')[:70]}")
    st=dict(Counter(it["_filtro"]["sev"] for it in ko))
    if st: print(f"  sev: {st}")
    if not dry:
        o=OUT/f"filtrado_{f}.json"; o.write_text(json.dumps({"seguras":ok,"descartadas":ko,"stats":st},ensure_ascii=False,indent=2)); print(f"  saved {o}")
def _test():
    cs=[({"titulo":"La muerte de la democracia"},True),({"titulo":"Muere un hombre en accidente"},False),({"titulo":"Análisis: cómo los medios cubren el tiroteo","descripcion":"framing"},True),({"titulo":"Tiroteo en escuela"},False),({"titulo":"Guerra de aranceles EEUU China"},True),({"titulo":"Masacre en Gaza","descripcion":"conflicto"},False),({"titulo":"Impactante vídeo"},False),({"titulo":"IA transforma economía"},True),({"titulo":"Suicidio adolescente"},False),({"titulo":"Análisis del sesgo cobertura suicidio","descripcion":"framing"},True),({"titulo":"Guerrero de la libertad","descripcion":"política"},True)]
    ok=0
    for it,exp in cs:
        r=_evaluar(it)
        if r["segura"]==exp: ok+=1
        else: print(f"  FAIL {it.get('titulo')} exp={exp} got={r['segura']} ({r['razon']})")
    print(f"TEST {ok}/{len(cs)}"); return ok==len(cs)
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("fecha",nargs="?"); ap.add_argument("--dry-run",action="store_true"); ap.add_argument("--verbose","-v",action="store_true"); ap.add_argument("--test",action="store_true")
    a=ap.parse_args()
    if a.test: sys.exit(0 if _test() else 1)
    if not a.fecha:
        js=sorted(OUT.glob("recoleccion_*.json"))
        if not js: print("ERR sin recolecciones"); sys.exit(1)
        a.fecha=js[-1].stem.replace("recoleccion_",""); print(f"date {a.fecha}")
    filtrar(a.fecha,a.dry_run,a.verbose)
