"""verificar_alucinaciones.py - Detecta alucinaciones en posts generados."""
import sys, json, pathlib, re, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_web"
FECHA = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()

# Nombres propios conocidos (lista blanca ampliable)
NOMBRES_CORRECTOS = {
    "óscar puente": ["oscar puente", "josé luis puente", "jose luis puente", "josé luis", "oscar luis"],
    "pedro sánchez": ["pedro sanchez", "pedro sánchez"],
    "doctrina marlaska": ["doctrina marlaska", "marlaska"],
}

# Medios válidos (deben estar en el desglose)

def _es_falso_positivo(cita):
    """True si la cita es CSS/URL/HTML/basura, no un titular real."""
    if not cita or len(cita) < 20:
        return True
    # URLs
    if cita.startswith(('http://', 'https://', 'www.')):
        return True
    # CSS
    if any(x in cita for x in ['background:', 'border-', 'padding:', 'margin:', 'font-size:', 'color:', 'display:', 'position:', '.highlight{', 'style="']):
        return True
    # HTML
    if any(x in cita for x in ['<a ', '</a>', '<div ', '<span ', '<p ', '<ul>', '<li>', '<strong>', '</strong>', 'class=', 'href=', 'src=']):
        return True
    # URLs en medio
    if re.search(r'https?://', cita):
        return True
    # Redes sociales
    if any(x in cita for x in ['youtube.com/', 'tiktok.com/', 'instagram.com/', 'x.com/', 'threads.net/', 'twitter.com/']):
        return True
    # Fragmentos que empiezan con puntuación
    if cita.strip()[0] in ',.;:)]}':
        return True
    # Solo números / símbolos
    if not any(c.isalpha() for c in cita):
        return True
    return False

def _medios_validos(fecha):
    enr = OUT / f"dossier_{fecha}_enriquecido.json"
    d_path = enr if enr.exists() else (OUT / f"dossier_{fecha}.json")
    if not d_path.exists(): return set()
    d = json.loads(d_path.read_text())
    desglose = d.get("dossier", {}).get("desglose_medios", "")
    medios = set()
    for line in desglose.split("\n"):
        m = re.match(r"\*\*([^*]+)\*\*", line)
        if m: medios.add(m.group(1).strip().lower())
    return medios

def _titulares_reales(fecha):
    """{medio_lower: {"titular": "...", "extracto": "..."}}"""
    rec = OUT / f"recoleccion_{fecha}.json"
    if not rec.exists(): return {}
    data = json.loads(rec.read_text())
    titulares = {}
    for cat, medios in data.items():
        if cat == "audios": continue
        if isinstance(medios, dict):
            for medio, noticias in medios.items():
                if isinstance(noticias, list):
                    for n in noticias:
                        if isinstance(n, dict) and n.get("titular"):
                            titulares[medio.lower()] = {
                                "titular": n.get("titular", ""),
                                "extracto": n.get("extracto", "") or n.get("texto", ""),
                            }
                            break
    
    # Cargar scrapeado (texto completo real) y fusionar con titulares
    scrapeado_file = OUT / f"scrapeado_{fecha}.json"
    if scrapeado_file.exists():
        try:
            import json as _json
            scrapeado = _json.loads(scrapeado_file.read_text())
            for medio, datos in scrapeado.items():
                medio_low = medio.lower()
                if medio_low in titulares:
                    # Añadir texto completo al extracto
                    texto_extra = datos.get("texto_completo", "") or datos.get("texto", "")
                    if texto_extra:
                        titulares[medio_low]["extracto"] += " " + texto_extra
                else:
                    # Medio nuevo solo del scrapeado
                    titulares[medio_low] = {
                        "titular": datos.get("titular", ""),
                        "extracto": datos.get("texto_completo", "") or datos.get("texto", ""),
                    }
        except Exception as e:
            print(f"⚠️ scrapeado: {e}", flush=True)
    
    return titulares

def verificar(texto, fecha):
    """Devuelve lista de alucinaciones detectadas."""
    problemas = []
    texto_lower = texto.lower()
    
    # 1. Nombres propios mal escritos
    for correcto, incorrectos in NOMBRES_CORRECTOS.items():
        for incorrecto in incorrectos:
            if incorrecto in texto_lower and correcto not in texto_lower:
                problemas.append(f"NOMBRE MAL: dice '{incorrecto}' pero debería ser '{correcto}'")
    
    # 2. Medios mencionados que no están en el desglose
    medios_validos = _medios_validos(fecha)
    medios_mencionados = re.findall(r"<strong>([^<]+)</strong>", texto)
    for medio in medios_mencionados:
        medio_lower = medio.strip().lower().rstrip(":").strip()
        # Normalizar plurales y variantes
        medio_lower = medio_lower.replace("the objective", "objective").replace("el país", "el pais")
        if medio_lower not in medios_validos and len(medio_lower) > 2:
            # Solo alertar si parece un medio (contiene palabras tipo diario, mundo, país...)
            if any(w in medio_lower for w in ["diario", "mundo", "país", "pais", "abc", "ser", "cope", "sexta", "monde", "bbc", "jazeera", "huffpost", "okdiario", "objective", "independiente", "vanguardia"]):
                problemas.append(f"MEDIO SOSPECHOSO: menciona '{medio}' que no está en el desglose")
    
    # 3. Frases de alucinación típicas
    frases_alucinacion = [
        "introdujo a un chef",
        "precio del oro",
        "partido de fútbol de segunda",
        "tradujeron un titular al inglés",
        "crisis en polonia",
    ]
    for frase in frases_alucinacion:
        if frase in texto_lower:
            problemas.append(f"FRASE SOSPECHOSA: '{frase}' (¿es real?)")
    
    # 4. Verificar que los titulares citados existen (VERSIÓN MEJORADA 2026-11-03)
    titulares = _titulares_reales(fecha)
    
    # Filtrar textos que NO son citas reales (CSS, HTML, URLs, código)
    FALSOS_POSITIVOS = [
        'background:', 'border-', 'padding:', 'margin:', 'font-size:', 'color:',
        'https://', 'http://', 'www.', '.com/', '.es/', '.org/', '.net/',
        '<a ', '</a>', '<div ', '</div>', '<ul>', '</ul>', '<li>', '</li>',
        '<p ', '</p>', '<span', '</span>', '<em>', '</em>', '<strong>', '</strong>',
        'href=', 'src=', 'class=', 'id=', 'style=', 'alt=', 'title=',
        'youtube.com/', 'tiktok.com/', 'instagram.com/', 'x.com/', 'threads.net/',
        'elencuadre.pages.dev', 'Somos El Encuadre', 'SomosElEncuadre',
        'data:image/', 'loading="lazy"', 'target="_blank"', 'rel="noopener"',
        '&amp;', '&lt;', '&gt;', '&quot;', '&#',
    ]
    
    def _es_cita_valida(txt):
        """Devuelve True si el texto parece una cita real (no CSS/HTML/URL)."""
        if not txt or len(txt) < 40:
            return False
        txt_low = txt.lower()
        for fp in FALSOS_POSITIVOS:
            if fp.lower() in txt_low:
                return False
        # Si tiene más de 3 caracteres raros, descartar
        raros = sum(1 for c in txt if c in '{}<>;=`\n\t')
        if raros > 3:
            return False
        return True
    
    # Buscar citas entre comillas (más conservador: mínimo 40 chars)
    # Extracción SEMÁNTICA: solo citas precedidas por un medio conocido
    medios_lista = list(_medios_validos(fecha))
    if not medios_lista:
        medios_lista = ['el país', 'el mundo', 'abc', 'the objective', 'el español',
                        'okdiario', 'huffpost', 'libertad digital', 'eldiario',
                        'infollibre', 'ara', 'bbc', 'le monde', 'nytimes', 'al jazeera',
                        'antena 3', 'la sexta', 'cadena ser', 'onda cero', 'cope',
                        'telecinco', 'cuatro', 'la vanguardia', '20 minutos', 'expansión']
    
    # Buscar patrón: [Medio] + 0-10 palabras + «cita» o "cita"
    # Ejemplo: "El País titula: «cita»" o "según The Objective: 'cita'"
    citas = []
    patron_semantico = r'(?:' + '|'.join(re.escape(m) for m in medios_lista) + r')[^«"\']{0,80}[«"\']([^«»"\']{40,200})[»"\']'
    for match in re.finditer(patron_semantico, texto, re.IGNORECASE):
        citas.append(match.group(1))
    
    # Si no hay citas semánticas pero hay bloques con «», caer al patrón antiguo
    # pero SOLO para texto que aparezca en titulares reales (tolerante)
    if not citas:
        citas_amplias = re.findall(r'[«"\']([^«»"\']{40,200})[»"\']', texto)
        # Filtrar por falsos positivos primero
        citas_amplias = [c for c in citas_amplias if not _es_falso_positivo(c)]
        # Filtrar por parecido a algún titular real (tolerancia 40%)
        titulares = _titulares_reales(fecha).values()
        for c in citas_amplias:
            c_low = c.lower()
            for tit in titulares:
                tit_low = tit.lower() if isinstance(tit, str) else tit.get('titular', '').lower()
                if tit_low and (c_low[:20] in tit_low or tit_low[:20] in c_low):
                    citas.append(c)
                    break
    
    for cita in citas:
        if not _es_cita_valida(cita):
            continue

        cita_low = cita.lower().strip()

        # Verificación tolerante contra titular + extracto
        encontrada = False
        for t in titulares.values():
            # t puede ser dict {titular, extracto} o str (retrocompat)
            if isinstance(t, dict):
                texto_comparar = (t.get("titular", "") + " " + t.get("extracto", "")).lower().strip()
            else:
                texto_comparar = str(t).lower().strip()

            if not texto_comparar:
                continue

            # Match exacto de 30 chars
            if cita_low[:30] in texto_comparar or texto_comparar[:30] in cita_low:
                encontrada = True
                break

            # Match de palabras clave (>60% coincidencia)
            palabras_cita = set(w for w in cita_low.split() if len(w) > 4)
            palabras_tit = set(w for w in texto_comparar.split() if len(w) > 4)
            if palabras_cita and palabras_tit:
                comunes = palabras_cita & palabras_tit
                if len(comunes) / max(len(palabras_cita), 1) > 0.6:
                    encontrada = True
                    break

        if not encontrada:
            problemas.append(f"CITA NO VERIFICADA: '{cita[:80]}...' no está en ningún titular real")

    return problemas


def main(fecha=None):
    fecha = fecha or FECHA
    print(f"Verificando posts de {fecha}...\n")
    
    archivos = list(COLA.glob(f"{fecha}-*.md"))
    if not archivos:
        print(f"❌ No hay posts de {fecha} en {COLA}")
        return False
    
    total_problemas = 0
    for f in archivos:
        txt = f.read_text()
        # Quitar frontmatter
        cuerpo = re.sub(r"^---.*?---", "", txt, count=1, flags=re.DOTALL)
        
        problemas = verificar(cuerpo, fecha)
        print(f"📄 {f.name} ({len(cuerpo)} chars)")
        if problemas:
            for p in problemas:
                print(f"   ⚠️ {p}")
            total_problemas += len(problemas)
        else:
            print(f"   ✅ Sin alucinaciones detectadas")
        print()
    
    print("=" * 60)
    if total_problemas == 0:
        print("✅ Todos los posts limpios")
        return True
    else:
        print(f"⚠️ {total_problemas} problemas detectados. Revisar antes de publicar.")
        return False

if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1] if len(sys.argv) > 1 else None) else 1)
