#!/usr/bin/env python3
"""comentar_y_publicar.py - Genera comentario con Dios y publica en Telegram.
Uso: python3 scripts/comentar_y_publicar.py <tipo> <titulo> [url] [url_fuente]
Tipos: analisis | dossier | short | podcast | custom
"""
import sys, json, urllib.request, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "brain"))

def _env(k):
    for l in (ROOT/".env").read_text().splitlines():
        if l.startswith(k+"="):
            return l.split("=",1)[1].strip().strip('"').strip("'")
    return ""

def generar_comentario(titulo, tipo="análisis"):
    """Dios escribe 1-2 frases de gancho."""
    prompt = (
        f"Escribe UN SOLO párrafo corto (máximo 2 frases, 40 palabras) como gancho "
        f"para preceder la publicación de {tipo} titulado \"{titulo}\". "
        f"Tono: irónico, técnico, estilo Hunter S. Thompson. Sin hashtags. "
        f"Sin emojis al inicio. Solo el texto del párrafo, sin comillas ni preámbulos."
    )
    try:
        r = subprocess.run(
            ["python3", "scripts/dios.py", prompt],
            capture_output=True, text=True, cwd=str(ROOT), timeout=120
        )
        out = r.stdout
        if "[dios] Tarea completada. Resumen:" in out:
            return out.split("[dios] Tarea completada. Resumen:")[-1].strip()[:400]
        return out.strip()[:400]
    except Exception as e:
        print(f"⚠️ Dios falló: {e}")
        return ""

def publicar_comentario(texto):
    """Publica el comentario como mensaje independiente (sin preview)."""
    token = _env("TELEGRAM_BOT_TOKEN")
    cid = _env("TELEGRAM_CHANNEL_ID")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": cid,
        "text": texto,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }).encode()
    try:
        req = urllib.request.Request(url, data=data,
            headers={"Content-Type":"application/json"}, method="POST")
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read()).get("ok", False)
    except Exception as e:
        print(f"⚠️ {e}")
        return False

def main():
    if len(sys.argv) < 3:
        print("Uso: python3 scripts/comentar_y_publicar.py <tipo> <titulo> [url] [url_fuente]")
        sys.exit(1)

    tipo = sys.argv[1]
    titulo = sys.argv[2]
    url = sys.argv[3] if len(sys.argv) > 3 else ""
    url_fuente = sys.argv[4] if len(sys.argv) > 4 else ""

    print(f"📝 Generando comentario sobre: {titulo}")
    comentario = generar_comentario(titulo, tipo)

    if comentario:
        print(f"💬 Comentario: {comentario[:120]}...")
        ok = publicar_comentario(comentario)
        print(f"{'✅' if ok else '❌'} Comentario publicado")
    else:
        print("⚠️ Sin comentario, solo se publicará el link")

    # Publicar el post principal
    if url:
        try:
            from notificador_encuadre import publicar_analisis, publicar_dossier, publicar_short, publicar_podcast
            slug = url.rstrip("/").split("/")[-1]
            if tipo == "analisis":
                r = publicar_analisis(titulo, slug, "", url_fuente)
            elif tipo == "dossier":
                r = publicar_dossier(titulo, slug, "", url_fuente)
            elif tipo == "short":
                r = publicar_short(titulo, url_youtube=url)
            elif tipo == "podcast":
                r = publicar_podcast(titulo, url)
            else:
                from notificador_encuadre import _post
                r = _post("sendMessage", {
                    "chat_id": _env("TELEGRAM_CHANNEL_ID"),
                    "text": f"*{titulo}*\n\n🔗 {url}",
                    "parse_mode": "Markdown"
                })
            print(f"{'✅' if r.get('ok') else '❌'} Post principal publicado")
        except Exception as e:
            print(f"❌ {e}")

if __name__ == "__main__":
    main()
