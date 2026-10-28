from pathlib import Path
p = Path("web_dashboard.py")
s = p.read_text(encoding="utf-8")

# Reemplazar la función serve_media para buscar en subcarpetas con rglob
old_func = '''@app.route("/media/<path:filename>")
def serve_media(filename):
    """Sirve archivos estáticos de la carpeta output/ o assets/ con soporte de Range."""
    from flask import send_file, request
    for base in [ROOT / "output", ROOT / "assets"]:
        file_path = base / filename
        if file_path.exists() and file_path.is_file():'''

new_func = '''@app.route("/media/<path:filename>")
def serve_media(filename):
    """Sirve archivos estáticos de la carpeta output/ o assets/ con soporte de Range."""
    from flask import send_file, request
    # Buscamos en output/ y assets/ directamente
    for base in [ROOT / "output", ROOT / "assets"]:
        file_path = base / filename
        # Si no existe en la raíz, buscamos recursivamente en subcarpetas
        if not file_path.exists():
            for candidate in base.rglob(filename):
                if candidate.is_file():
                    file_path = candidate
                    break
        if file_path.exists() and file_path.is_file():'''

if old_func in s:
    s = s.replace(old_func, new_func)
    p.write_text(s, encoding="utf-8")
    print("✅ Endpoint /media/ parcheado para buscar en subcarpetas.")
elif "rglob(filename)" in s:
    print("⚠️ El endpoint ya estaba parcheado.")
else:
    print("❌ No se encontró la función serve_media original.")
