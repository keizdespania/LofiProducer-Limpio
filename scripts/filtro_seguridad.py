"""filtro_seguridad.py v3 - severidades + ctx + word-boundaries."""
import json, pathlib, re, sys, argparse
from collections import Counter
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
PAT = {
 "critica": [r"\bsuicid\w*",r"\bmasacre\w*",r"\btiroteo\w*",r"\basesinat\w*",r"\bhomicidi\w*",r"\bterroris\w*",r"\batentad\w*",r"\bviolaci[oó]n\w*",r"\bsecuestr\w*",r"\bcat[aá]strofe\w*",r"\bapuñalamient\w*",r"\bautolesi\w*"],
 "moderada": [r"\bfallecid\w*",r"\bmuert[oa]s?\b",r"\bfatal\b",r"\btragedia\w*",r"\bv[ií]ctima\w*",r"\baccident\w*",r"\bchoque\b",r"\bcolisi[oó]n\w*",r"\batropell\w*",r"\bincendio\w*",r"\bexplosi[oó]n\w*",r"\bderrumbe\w*",r"\bbombarde\w*",r"\bguerra\s+(civil|mundial|de\s+ucrania|de\s+gaza|en\s+ucrania|en\s+gaza|de\s+siria)",r"\bconflicto\s+armado",r"\bpandemia\w*",r"\bterremoto\w*",r"\btsunami\w*",r"\bofensiva\s+militar",r"\bherid[oa]\s+grave\w*",r"\bsiniestro\w*",r"\bduelo\b",r"\bvidas\s+truncadas",r"\bdescarril\w*",r"\baccidente\s+ferroviario",r"\bcolisi[oó]n\s+(de\s+)?trenes?",r"\btragedia\s+ferroviaria",r"\bmorgue\b",r"\bllanto\b",r"\bvia\s+dolorosa",r"\bfuneral",r"\bpostrimer[ií]as",r"\bvelatorio",r"\bpesar\s+por",r"\bsolidaridad\s+(de|con)\s+las\s+v[ií]ctimas",r"\bhospital\s+a\s+la\s+morgue",r"\bherid[oa]s?\b",r"\bv[ií]ctimas?\b",r"\bfallecid[oa]s?\b",r"\bcat[aá]strofe"],
 "baja": [r"\bmuerte\b"],
 "sensac": [r"\bimpactante\w*",r"\bescalofriante\w*",r"\bsobrecogedor\w*",r"\bterror[ií]fic\w*",r"\bhorroros\w*",r"\bsangrient\w*",r"\bbrutal\w*",r"\bshock\w*"],
}
TEMAS_FUERA = {
 "deportes": [r"\bm[aá]rquez\b",r"\balcaraz\b",r"\bnadal\b",r"\bmotogp\b",r"\bmoto\s*gp\b",r"\blaliga\b",r"\bla\s+liga\b",r"\bmundial\b",r"\bchampions\b",r"\bcopa\s+del\s+rey\b",r"\beuropa\s+league\b",r"\bfichaj\w*",r"\bentrenador\b",r"\bdelantero\b",r"\bportero\b",r"\bgol(es)?\b",r"\bimbatibilid\w*",r"\bimbatible\b",r"\bpartido\s+de\s+f[uú]tbol",r"\bjugador\b",r"\bbal[oó]n\b",r"\bmbapp[eé]\b",r"\bpucela\b",r"\bracing\b",r"\bathletic\b",r"\breal\s+madrid\b",r"\bbar[cç]a\b",r"\batleti\b",r"\bbetis\b",r"\bsevilla\s+fc\b",r"\bvalencia\s+cf\b",r"\bpremier\b",r"\bbundesliga\b",r"\bserie\s+a\b",r"\bpichichi\b",r"\bdelantera\b",r"\bcentrocampista\b",r"\bdefensa\s+central\b"],
 "farandula": [r"\bjavis\b",r"\bcarrasco\b",r"\bs[aá]lvame\b",r"\bsupervivientes\b",r"\bgran\s+hermano\b",r"\boperaci[oó]n\s+triunfo\b",r"\bmasterchef\b",r"\bbake\s*off\b",r"\bgui[nñ]o\b",r"\bdisfraz\b",r"\bhalloween\b",r"\binfluencer\b",r"\binstagram\b",r"\btiktok\b",r"\bfamoso\b",r"\bcelebridad\b",r"\breconciliaci[oó]n\b",r"\bruptura\b",r"\bembarazo\b",r"\bboda\b",r"\bdivorcio\b",r"\bcoraz[oó]n\b",r"\bprensa\s+rosa\b",r"\bactor\b",r"\bactriz\b",r"\bcine\b",r"\bcineasta\b",r"\bpel[ií]cula\b",r"\bconcierto\b",r"\bm[uú]sica\b"],
 "sucesos": [r"\bargelin[oa]s?\b",r"\bmarroqu[ií]es?\b",r"\bmigrante\b",r"\binmigrante\b",r"\basalt\w*",r"\brobo\b",r"\brobar\b",r"\batrac\w*",r"\bapu[nñ]al\w*",r"\bagred\w*",r"\bherid[oa]s?\b",r"\bmorgue\b",r"\bcad[aá]ver\b",r"\bapag[oó]n\b",r"\bsin\s+suministro\b",r"\bsin\s+luz\b",r"\bdetenid[oa]\b",r"\bpolic[ií]a\b",r"\bguardia\s+civil\b"],
}
CTX = [
 r"\bfraude\b", r"\bnegligencia\b", r"\bpresupuesto\b", r"\binversi[oó]n\b",
 r"\bcontrato\b", r"\bmala\s+gesti[oó]n\b", r"\bahorr(o|ó)\b", r"\bmillones\b",
 r"\bdespilfarro\b", r"\bcorrupci[oó]n\b", r"\bsobrecoste\b", r"\bmafia\b",
 r"\blobby\b", r"\bprivati[zc]aci[oó]n\b", r"\bconcesi[oó]n\b", r"\bpeaje\b",r"\ban[aá]lisis\b",r"\bcobertura\s+medi[aá]tica",r"\btratamiento\s+medi[aá]tico",r"\bframing\b",r"\bsesgo\w*",r"\bmanipulaci[oó]n\w*",r"\bencuadre\b",r"\bc[oó]mo\s+los\s+medios",r"\bc[oó]mo\s+se\s+cubre"]
def _m(t,ps): return [p for p in ps if re.search(p,t,re.I)]
def _evaluar(it):
    ti=(it.get("titulo") or it.get("titular") or it.get("title") or "").lower()
    de=(it.get("descripcion") or it.get("resumen") or it.get("summary") or it.get("texto") or "").lower()
    cu=(it.get("contenido") or it.get("body") or "").lower()
    fu=f"{ti} {de} {cu}"
    cr,mo,se=_m(fu,PAT["critica"]),_m(fu,PAT["moderada"]),_m(fu,PAT["sensac"])
    ba=_m(fu,PAT["baja"])
    crt=_m(ti,PAT["critica"]); mot=_m(ti,PAT["moderada"]); bat=_m(ti,PAT["baja"])
    ctx=bool(_m(fu,CTX))
    # TEMAS FUERA: deportes, farandula, sucesos (nunca válidos, salvo con contexto de análisis)
    if not ctx:
        for tema, ps in TEMAS_FUERA.items():
            mat = _m(ti, ps)  # solo en titular
            if mat:
                return {"segura":False,"sev":tema,"razon":f"tema_fuera:{tema}","m":mat,"ctx":False}
    if crt and not ctx: return {"segura":False,"sev":"critica","razon":"critica+titulo sin ctx","m":crt,"ctx":ctx}
    if len(cr)>=2 and not ctx: return {"segura":False,"sev":"critica","razon":"2+criticas sin ctx","m":cr,"ctx":ctx}
    if cr and not ctx: return {"segura":False,"sev":"alta","razon":"critica sin ctx","m":cr,"ctx":False}
    if mot and not ctx: return {"segura":False,"sev":"media","razon":"moderada+titulo","m":mot,"ctx":False}
    if len(mo)>=2 and not ctx: return {"segura":False,"sev":"media","razon":"2+moderadas","m":mo,"ctx":False}
    if bat and (mo or se) and not ctx: return {"segura":False,"sev":"media","razon":"baja+refuerzo","m":bat+mo+se,"ctx":False}
    if se and not ctx: return {"segura":False,"sev":"media","razon":"sensac","m":se,"ctx":False}
    return {"segura":True,"sev":"ok","razon":"ok","m":(cr+mo+se+ba)[:5],"ctx":ctx,"advertencia":bool(cr+mo+se+ba)}

def _flatten(recol):
    if isinstance(recol, list): return recol
    items = []
    for sec in ("prensa","agencias"):
        for med, lst in (recol.get(sec) or {}).items():
            if not isinstance(lst, list): continue
            for n in lst:
                if isinstance(n, dict):
                    n = dict(n); n["_medio"]=med; n["_seccion"]=sec
                    items.append(n)
    return items

def _refold(recol, seguros):
    out = dict(recol); out["prensa"]={}; out["agencias"]={}
    for it in seguros:
        sec=it.get("_seccion","prensa"); med=it.get("_medio","unknown")
        clean={k:v for k,v in it.items() if not k.startswith("_")}
        out[sec].setdefault(med,[]).append(clean)
    return out

def _cargar(f):
    p=OUT/f"recoleccion_{f}.json"
    if p.exists(): return p,json.loads(p.read_text())
    for q in sorted(OUT.glob(f"recoleccion_{f}*.json")): return q,json.loads(q.read_text())
    raise FileNotFoundError(f"sin recoleccion {f}")
def filtrar(f,dry=False,verb=False):
    p,d=_cargar(f)
    items=_flatten(d)
    if not items:
        print(f"WARN sin noticias en {p.name}"); return
    ok,ko=[],[]
    for it in items:
        r=_evaluar(it); it["_filtro"]=r
        (ok if r["segura"] else ko).append(it)
    print(f"OK {p.name}: {len(items)} -> keep {len(ok)} drop {len(ko)}")
    if verb:
        for it in ko:
            ttl=(it.get("titulo") or it.get("title") or "?")[:75]
            print(f"  X [{it['_filtro']['sev']}] {ttl} -> {it['_filtro']['razon']}")
    st=dict(Counter(it["_filtro"]["sev"] for it in ko))
    if st: print(f"  sev: {st}")
    if not dry:
        limpia=_refold(d, ok)
        (OUT/f"recoleccion_{f}_limpia.json").write_text(json.dumps(limpia,ensure_ascii=False,indent=2))
        audit={"seguras":[{k:v for k,v in it.items() if not k.startswith("_")} for it in ok],
               "descartadas":[{k:v for k,v in it.items() if not k.startswith("_")} for it in ko],
               "stats":st}
        (OUT/f"filtrado_{f}.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2))
        print(f"  saved _limpia + filtrado")

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
