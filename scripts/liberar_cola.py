"""liberar_cola.py - Publica los posts (web y blogger) cuando llega su hora."""
import json, pathlib, datetime, shutil, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "encuadre"
COLA_FILE = ROOT / "output" / "cola_publicacion.json"
WEB_POSTS = ROOT / "web" / "docs" / "analisis"
COLA_WEB = ROOT / "output" / "cola_web"
COLA_BLOGGER = ROOT / "output" / "cola_blogger"

def liberar():
    if not COLA_FILE.exists(): return
    cola = json.loads(COLA_FILE.read_text())
    ahora = datetime.datetime.now()
    liberados = 0
    
    for item in cola:
        if item.get("publicado"): continue
        hora_pub = datetime.datetime.fromisoformat(item["hora_publicacion"])
        
        if ahora >= hora_pub:
            if item["tipo"] == "web":
                src = COLA_WEB / item["filename"]
                if src.exists():
                    shutil.copy2(src, WEB_POSTS / item["filename"])
                    print(f"  🌐 Web: {item['filename']}")
                    item["publicado"] = True
                    liberados += 1
            elif item["tipo"] == "blogger":
                src = COLA_BLOGGER / item["filename"]
                if src.exists():
                    from publicar_blogger import publicar
                    data = json.loads(src.read_text())
                    blog_id = None
                    for line in (ROOT / ".env").read_text().splitlines():
                        if line.startswith("EL_ENCUADRE_BLOG_ID="):
                            blog_id = line.split("=",1)[1].strip()
                    try:
                        publicar(data["titulo"], data["html"], blog_id=blog_id)
                        print(f"  📰 Blogger: {data['titulo'][:40]}...")
                        item["publicado"] = True
                        liberados += 1
                    except Exception as e:
                        print(f"  ❌ Error publicando en Blogger: {e}")
    
    COLA_FILE.write_text(json.dumps(cola, indent=2))
    if liberados > 0:
        print(f"✅ {liberados} posts liberados.")

if __name__ == "__main__":
    liberar()
