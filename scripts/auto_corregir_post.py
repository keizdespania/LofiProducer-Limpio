"""auto_corregir_post.py - Corrige errores deterministas en posts generados.
NO toca el generador. Solo post-procesa el .md final.
"""
import sys, json, pathlib, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA = ROOT / "output" / "cola_web"

# Diccionario de nombres correctos (ampliable)
NOMBRES_CORRECTOS = {
    "oscar puente": "Óscar Puente",
    "pedro sanchez": "Pedro Sánchez",
    "jose luis puente": "Óscar Puente",
    "jose luis abalos": "José Luis Ábalos",
    "doctrina mar": "doctrina Marlaska",
    "doctrina marlaska": "doctrina Marlaska",
    "marlaska": "Marlaska",
    "blocus": "Blocus",
}

# Frases inventadas comunes que hay que corregir o eliminar
CORRECCIONES_FRASES = {
    "justicia valenciana": "la justicia de Torrent (Valencia)",
    "en rueda de prensa": "en declaraciones públicas",
    "antiguo funcionario": "un trabajador",
}

# Palabras que se censuran (reemplazo por sinónimo neutro)
CENSURA = {
    "muertos": "afectados", "muerto": "fallecido", "muerta": "fallecida",
    "muerte": "suceso", "sangre": "violencia",
    "tragedia": "suceso", "saqueo": "disturbio", "saqueos": "disturbios",
    "victima": "afectado", "victimas": "afectados",
    "asesinato": "caso grave", "crimen": "caso",
    "corrupcion": "irregularidad", "fraude": "irregularidad",
    "guerra": "conflicto", "nazi": "extremista", "fascista": "extremista",
}

# Concordancia de género (la/el + sustantivo masculino)
CONCORDANCIA = {
    r"\bde el suceso\b": "del suceso",
    r"\bde el caso\b": "del caso",
    r"\bde el tema\b": "del tema",
    r"\bde el informe\b": "del informe",
    r"\bde el gobierno\b": "del gobierno",
    r"\bde el medio\b": "del medio",
    r"\bde el proceso\b": "del proceso",
    r"\bde el grupo\b": "del grupo",
    r"\bde el país\b": "del país",
    r"\bde el mundo\b": "del mundo",
    r"\bla suceso\b": "el suceso",
    r"\bla problema\b": "el problema",
    r"\bla tema\b": "el tema",
    r"\bla sistema\b": "el sistema",
    r"\bla programa\b": "el programa",
    r"\bla drama\b": "el drama",
    r"\bla mapa\b": "el mapa",
    r"\bla planeta\b": "el planeta",
    r"\bla análisis\b": "el análisis",
    r"\bla énfasis\b": "el énfasis",
    r"\bla conflicto\b": "el conflicto",
    r"\bla gobierno\b": "el gobierno",
    r"\bla estado\b": "el estado",
    r"\bla caso\b": "el caso",
    r"\bla artículo\b": "el artículo",
    r"\bla grupo\b": "el grupo",
    r"\bla equipo\b": "el equipo",
    r"\bla proceso\b": "el proceso",
    r"\bla resultado\b": "el resultado",
    r"\bla debate\b": "el debate",
    r"\bla ataque\b": "el ataque",
    r"\bla informe\b": "el informe",
    r"\bla evento\b": "el evento",
    r"\bla momento\b": "el momento",
    r"\bla titular\b": "el titular",
    r"\bla medio\b": "el medio",
    r"\bla datos\b": "los datos",
    r"\bla medios\b": "los medios",
    r"\bla titulares\b": "los titulares",
    r"\blos suceso\b": "los sucesos",
    r"\blos problema\b": "los problemas",
}

# Ortografía común
ORTOGRAFIA = {
    # Tildes faltantes en palabras comunes
    r"\bmas\b": "más",
    r"\bsolo\b": "sólo",  # opcional: RAE prefiere "solo", lo dejo comentado
    r"\baun\b": "aún",
    r"\b dia\b": "día",
    r"\btambien\b": "también",
    r"\baqui\b": "aquí",
    r"\basi\b": "así",
    r"\bdespues\b": "después",
    r"\bademas\b": "además",
    r"\bpolitica\b": "política",
    r"\bnoticia\b": "noticia",
    r"\bperiodismo\b": "periodismo",
    r"\btecnica\b": "técnica",
    r"\btecnicas\b": "técnicas",
    r"\bmanipulacion\b": "manipulación",
    r"\bcorrupcion\b": "corrupción",
    r"\bvictima\b": "víctima",
    r"\bvictimas\b": "víctimas",
    # (mayúscula después de punto ELIMINADO por seguridad HTML)
        # Espacio antes de coma/punto
    r" ([,.;:!?])": lambda m: m.group(1),
    # Puntos suspensivos mal
    r"\.\.\.\.": "...",
    # (comillas tipográficas ELIMINADO: rompía atributos HTML)
    # Guiones mal
    r" -- ": " — ",
}

# Semántica: frases redundantes o absurdas
SEMANTICA = {
    r"\bviolencia violenta\b": "violencia",
    r"\bmuerte mortal\b": "muerte",
    r"\bsuceso que ocurrió\b": "suceso",
    r"\bnoticia noticiosa\b": "noticia",
    r"\bmuy extremadamente\b": "extremadamente",
    r"\bbastante muy\b": "muy",
    r"\bprimera vez inicial\b": "primera vez",
}

def _normalizar(s):
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.lower()

def _corregir_nombres(texto):
    """Corrige nombres mal escritos o cortados."""
    cambios = []
    for mal, bien in NOMBRES_CORRECTOS.items():
        # Buscar variantes (con y sin tilde)
        patron = r'\b' + re.escape(mal) + r'\b'
        if re.search(patron, texto, re.IGNORECASE):
            texto = re.sub(patron, bien, texto, flags=re.IGNORECASE)
            cambios.append(f"Nombre: '{mal}' -> '{bien}'")
    return texto, cambios

def _corregir_frases(texto):
    """Corrige frases inventadas comunes."""
    cambios = []
    for mal, bien in CORRECCIONES_FRASES.items():
        if mal in texto.lower():
            texto = re.sub(re.escape(mal), bien, texto, flags=re.IGNORECASE)
            cambios.append(f"Frase: '{mal}' -> '{bien}'")
    return texto, cambios

def _censurar_palabras(texto):
    """Censura palabras prohibidas."""
    cambios = []
    for prohibida, neutra in CENSURA.items():
        patron = r'\b' + re.escape(prohibida) + r'\b'
        if re.search(patron, texto, re.IGNORECASE):
            texto = re.sub(patron, neutra, texto, flags=re.IGNORECASE)
            cambios.append(f"Censura: '{prohibida}' -> '{neutra}'")
    return texto, cambios

def _limpiar_html_basura(texto):
    """Quita <html>, <head>, <body>, <style> del cuerpo."""
    cambios = []
    original = texto
    texto = re.sub(r'<!DOCTYPE[^>]*>', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'<html[^>]*>', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'</html>', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'<head[^>]*>.*?</head>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    texto = re.sub(r'<body[^>]*>', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'</body>', '', texto, flags=re.IGNORECASE)
    texto = re.sub(r'<style[^>]*>.*?</style>', '', texto, flags=re.DOTALL | re.IGNORECASE)
    if texto != original:
        cambios.append("HTML: limpiado <html>/<head>/<body>/<style>")
    return texto, cambios

def _arreglar_yaml(texto):
    """Reconstruye frontmatter limpio: sin comillas anidadas rotas."""
    cambios = []
    fm_match = re.match(r'^---\n(.*?)\n---\n', texto, re.DOTALL)
    if not fm_match:
        return texto, cambios
    
    fm = fm_match.group(1)
    lineas = fm.split("\n")
    nuevas = []
    cambios_aplicados = False
    
    for l in lineas:
        if l.startswith(("title:", "description:")):
            clave = l.split(":", 1)[0]
            contenido = l.split(":", 1)[1].strip()
            # Limpiar TODAS las comillas externas e internas
            contenido = contenido.strip('"').strip("'")
            # Escapar comillas internas como apóstrofes
            contenido = contenido.replace('"', "'").replace("''", "'")
            # Dejar UN solo espacio si hay varios
            contenido = re.sub(r'\s+', ' ', contenido)
            nuevas.append(f'{clave}: "{contenido}"')
            cambios_aplicados = True
        else:
            nuevas.append(l)
    
    if cambios_aplicados:
        texto_nuevo = texto.replace(fm, "\n".join(nuevas), 1)
        cambios.append("YAML: frontmatter reconstruido limpio")
        return texto_nuevo, cambios
    
    return texto, cambios

def _arreglar_frase_cortada(texto):
    """Si el último párrafo termina sin puntuación, añadir punto."""
    cambios = []
    # Quitar el bloque de redes/descargo del final para comprobar el último párrafo real
    # Buscar el último </p> o </div> antes de <hr>
    m = re.search(r'(<p>[^<]+)</p>\s*(?:\n\n<hr|\Z)', texto)
    if m:
        parrafo = m.group(1)
        ultimo_char = parrafo.rstrip()[-1]
        if ultimo_char not in ".!?»\"'":
            texto = texto.replace(m.group(0), m.group(1) + ".</p>" + m.group(0)[m.group(0).rfind('</p>')+4:], 1)
            cambios.append("Frase: punto final añadido al último párrafo")
    return texto, cambios

def _corregir_concordancia(texto):
    """Corrige concordancia de género: la suceso -> el suceso."""
    cambios = []
    for patron, correcto in CONCORDANCIA.items():
        if re.search(patron, texto, re.IGNORECASE):
            texto = re.sub(patron, correcto, texto, flags=re.IGNORECASE)
            cambios.append(f"Concordancia: '{patron}' -> '{correcto}'")
    return texto, cambios

def _corregir_ortografia(texto):
    """Corrige tildes, mayúsculas, espacios, comillas."""
    cambios = []
    # Aplicar solo al cuerpo HTML, no al frontmatter
    fm_match = re.match(r'^(---\n.*?\n---\n)(.*)$', texto, re.DOTALL)
    if fm_match:
        fm, cuerpo = fm_match.groups()
    else:
        fm, cuerpo = "", texto
    
    cuerpo_original = cuerpo
    for patron, reemplazo in ORTOGRAFIA.items():
        if callable(reemplazo):
            nuevo = re.sub(patron, reemplazo, cuerpo)
        else:
            nuevo = re.sub(patron, reemplazo, cuerpo)
        if nuevo != cuerpo:
            cuerpo = nuevo
    
    if cuerpo != cuerpo_original:
        cambios.append("Ortografía: tildes/mayúsculas/espacios/comillas corregidos")
    
    return fm + cuerpo, cambios

def _corregir_semantica(texto):
    """Elimina redundancias y frases absurdas."""
    cambios = []
    for patron, correcto in SEMANTICA.items():
        if re.search(patron, texto, re.IGNORECASE):
            texto = re.sub(patron, correcto, texto, flags=re.IGNORECASE)
            cambios.append(f"Semántica: '{patron}' -> '{correcto}'")
    return texto, cambios

def corregir(archivo_md, verbose=True):
    """Aplica todas las correcciones a un post .md."""
    archivo = pathlib.Path(archivo_md)
    if not archivo.exists():
        print(f"❌ No existe: {archivo}")
        return False
    
    texto = archivo.read_text()
    original = texto
    todos_cambios = []
    
    # Aplicar correcciones en orden
    texto, c1 = _arreglar_yaml(texto)
    todos_cambios.extend(c1)
    
    texto, c2 = _limpiar_html_basura(texto)
    todos_cambios.extend(c2)
    
    texto, c3 = _corregir_nombres(texto)
    todos_cambios.extend(c3)
    
    texto, c4 = _corregir_frases(texto)
    todos_cambios.extend(c4)
    
    texto, c5 = _censurar_palabras(texto)
    todos_cambios.extend(c5)
    
    texto, c6 = _arreglar_frase_cortada(texto)
    todos_cambios.extend(c6)
    
    texto, c7 = _corregir_concordancia(texto)
    todos_cambios.extend(c7)
    
    texto, c8 = _corregir_ortografia(texto)
    todos_cambios.extend(c8)
    
    texto, c9 = _corregir_semantica(texto)
    todos_cambios.extend(c9)
    
    # Guardar si hay cambios
    if texto != original:
        archivo.write_text(texto)
        if verbose:
            print(f"✅ {archivo.name}: {len(todos_cambios)} cambios")
            for c in todos_cambios:
                print(f"   - {c}")
        return True
    else:
        if verbose:
            print(f"✅ {archivo.name}: sin cambios necesarios")
        return True

def main():
    if len(sys.argv) < 2:
        # Corregir todos los posts del día
        print("Uso: python3 scripts/auto_corregir_post.py [fecha|archivo.md]")
        print("Si no hay argumento, corrige todos los .md en output/cola_web/")
        for f in sorted(COLA.glob("*.md")):
            print(f"\n📄 {f.name}")
            corregir(f)
    else:
        arg = sys.argv[1]
        # ¿Es un fichero o una fecha?
        if arg.endswith(".md"):
            corregir(arg)
        else:
            # Es una fecha
            fecha = arg
            archivos = list(COLA.glob(f"{fecha}-*.md"))
            if not archivos:
                print(f"❌ No hay posts de {fecha}")
                return
            for f in sorted(archivos):
                print(f"\n📄 {f.name}")
                corregir(f)

if __name__ == "__main__":
    main()
