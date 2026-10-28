"""Naming consistente: {canal}-{tipo}-{NNN}-{titulo-slug}.{ext}"""
import json, pathlib, re, time

def slugify(texto, max_chars=40):
    """Convierte 'Hola Mundo!' a 'hola-mundo'."""
    texto = texto.lower().strip()
    texto = re.sub(r'[^a-z0-9\s-]', '', texto)
    texto = re.sub(r'\s+', '-', texto)
    texto = re.sub(r'-+', '-', texto).strip('-')
    return texto[:max_chars] or "sin-titulo"

def _manifiesto_path(canal):
    return pathlib.Path.home() / "LofiProducer" / "output" / "nichos" / canal / "manifiesto.json"

def cargar_manifiesto(canal):
    """Carga o crea el manifiesto del canal."""
    p = _manifiesto_path(canal)
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: pass
    return {"canal": canal, "ultimo_numero": {}, "archivos": []}

def guardar_manifiesto(canal, manifiesto):
    p = _manifiesto_path(canal)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(manifiesto, indent=2, ensure_ascii=False))

def generar_nombre(canal, tipo, titulo, ext):
    """Devuelve (nombre_completo, numero). Auto-incrementa el manifiesto."""
    m = cargar_manifiesto(canal)
    numero = m["ultimo_numero"].get(tipo, 0) + 1
    m["ultimo_numero"][tipo] = numero
    slug = slugify(titulo)
    nombre = f"{canal}-{tipo}-{numero:03d}-{slug}.{ext.lstrip('.')}"
    m["archivos"].append({
        "id": f"{canal}-{tipo}-{numero:03d}-{slug}",
        "tipo": tipo, "numero": numero, "titulo": titulo,
        "ruta": f"{tipo}/{nombre}",
        "creado": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "estado": "activo"
    })
    guardar_manifiesto(canal, m)
    return nombre, numero

def marcar_en_papelera(canal, nombre_archivo):
    """Marca un archivo como borrado en el manifiesto (soft delete)."""
    m = cargar_manifiesto(canal)
    for a in m["archivos"]:
        if a["ruta"].endswith(nombre_archivo) or nombre_archivo in a["ruta"]:
            a["estado"] = "papelera"
            a["deleted_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
            guardar_manifiesto(canal, m)
            return True
    return False
