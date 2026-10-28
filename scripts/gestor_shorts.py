"""gestor_shorts.py - Sube shorts a Drive, los indexa y borra los locales."""
import subprocess, pathlib, json, sys, os

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
INDEX_FILE = ROOT / "data" / "agent" / "shorts_index.json"
REMOTE = "gdrive:SomosElEncuadre_Shorts"

def cargar_index():
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return []

def guardar_index(data):
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def archivar_shorts(fecha):
    print(f"📦 Archivando shorts de {fecha}...")
    # Cargar metadatos
    prod_file = OUT / f"produccion_{fecha}.json"
    if not prod_file.exists():
        print("❌ No hay JSON de producción"); return
    datos = json.loads(prod_file.read_text())
    shorts_meta = datos.get("shorts_finales", [])
    
    index = cargar_index()
    nuevos = 0

    for i, meta in enumerate(shorts_meta):
        short_path = OUT / f"short_{i+1}_{fecha}.mp4"
        if not short_path.exists():
            continue
        
        # Si ya está en el índice, lo saltamos
        if any(x["fecha"] == fecha and x["id"] == f"short_{i+1}" for x in index):
            continue

        print(f"  ☁️ Subiendo {short_path.name} a Drive...")
        # Crear carpeta por fecha en Drive
        remote_path = f"{REMOTE}/{fecha}"
        subprocess.run(["rclone", "copy", str(short_path), remote_path, "--quiet"], check=False)
        
        # Registrar en el índice
        index.append({
            "fecha": fecha,
            "id": f"short_{i+1}",
            "titulo": meta.get("titulo", "Sin título"),
            "tipo": meta.get("tipo", "Short"),
            "hook": meta.get("hook", ""),
            "drive_path": f"{fecha}/{short_path.name}",
            "local_disponible": False,
            "subido_a": [] # Aquí se apuntará a qué red se subió
        })
        nuevos += 1
        
        # Borrar local tras subir a Drive
        try:
            short_path.unlink()
            print(f"  🗑️ Borrado local: {short_path.name}")
        except Exception as e:
            print(f"  ⚠️ Error borrando local: {e}")

    guardar_index(index)
    print(f"✅ {nuevos} shorts archivados en Drive e indexados.")

if __name__ == "__main__":
    fecha = sys.argv[1] if len(sys.argv) > 1 else None
    if fecha:
        archivar_shorts(fecha)
    else:
        # Si no hay fecha, archiva todo lo que encuentre
        for p in OUT.glob("produccion_*.json"):
            f = p.stem.replace("produccion_", "")
            archivar_shorts(f)
