"""filtro_rojo.py - Aduana determinista definitiva. 0% basura."""
import re

# Lista negra ultra-estricta (si contiene esto, FUERA)
BLACKLIST = [
    r'\burda\b', r'\btoledo\b', r'\btren\b', r'\bave\b', r'\badif\b', r'\brenfe\b',
    r'\bmuert', r'\bfallecid', r'\bcuerpo', r'\bdesaparecid', r'\bherid', r'\baccident',
    r'\bincendio', r'\barrestad', r'\bdetenid', r'\bmenor', r'\babuso',
    r'\bfutbol', r'\bpucela', r'\bracing', r'\bdgt\b', r'\bbustamante', r'\bmsi\b',
    r'\bprestige', r'\bhuafa', r'\bbloomberg', r'\bchocolatier', r'\bambulance',
    r'cdata', r'\bporno', r'\bmarroqu[ií]', r'\bpillan', r'\bcomedia\b', r'\bxavier\b',
    r'\bviendo\b', r'\bautob[uú]s\b', r'\bpalma\b', r'\bmallorca\b', r'\bendesa\b',
    r'\bhidrocarburo\b', r'\belectricidad\b', r'\blluvia\b', r'\btemperatura\b',
]

# Lista blanca de medios (si no es de estos, FUERA)
WHITELIST = [
    "El País", "El Mundo", "ABC", "La Vanguardia", "elDiario.es",
    "El Confidencial", "El Español", "OkDiario", "The Objective",
    "HuffPost", "Europa Press", "20 Minutos", "Ara", "El Independiente"
]

REGEX_BLACKLIST = re.compile('|'.join(BLACKLIST), re.IGNORECASE)

def limpiar_texto(txt):
    if not txt: return ""
    # Quitar CDATA, HTML y espacios raros
    t = re.sub(r'<!\[CDATA\[|\]\]>', '', txt)
    t = re.sub(r'<[^>]+>', '', t)
    t = re.sub(r'&#\d+;', '', t) # Quitar entidades HTML como &#8216;
    t = re.sub(r'&\w+;', '', t)
    return t.strip()

def es_valida(titular, medio):
    if not any(w in medio for w in WHITELIST):
        return False
    if REGEX_BLACKLIST.search(titular):
        return False
    return True

def extraer_top16(datos_recoleccion, max_noticias=16):
    top16 = []
    vistos = set()
    
    for sec in ("prensa", "agencias"):
        for medio, noticias in (datos_recoleccion.get(sec) or {}).items():
            if not any(w in medio for w in WHITELIST): continue
            for n in noticias:
                if not isinstance(n, dict): continue
                titulo = limpiar_texto(n.get("titular", ""))
                if not titulo or titulo in vistos: continue
                
                if es_valida(titulo, medio):
                    vistos.add(titulo)
                    top16.append({
                        "titular": titulo,
                        "url": n.get("url", ""),
                        "medio": medio
                    })
                    if len(top16) >= max_noticias: return top16
    return top16
