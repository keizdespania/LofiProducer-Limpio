from pathlib import Path
p = Path("assets/index.html")
s = p.read_text(encoding="utf-8")
# Forzar la recarga del JS añadiendo ?v=3
s = s.replace('src="/assets/app.js"', 'src="/assets/app.js?v=3"')
p.write_text(s, encoding="utf-8")
print("✅ index.html actualizado para forzar la recarga del JS.")
