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
    """{medio_lower: titular_real}"""
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
                            titulares[medio.lower()] = n["titular"]
                            break
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
        medio_lower = medio.strip().lower()
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
    
    # 4. Verificar que los titulares citados existen
    titulares = _titulares_reales(fecha)
    # Buscar frases entre comillas que parezcan titulares
    citas = re.findall(r'[«"\']([^«»"\']{30,150})[»"\']', texto)
    for cita in citas:
        cita_lower = cita.lower()
        # Si la cita no está en ningún titular real, alertar
        encontrada = any(cita_lower[:30] in t.lower() for t in titulares.values())
        if not encontrada and len(cita) > 40:
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
