"""Publica un post en WordPress via API REST."""
import os, sys, json, requests, pathlib

# Buscar credenciales en .env
env = {}
env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")

WP_URL = env.get("WORDPRESS_URL", "")
WP_USER = env.get("WORDPRESS_USER", "")
WP_PASS = env.get("WORDPRESS_APP_PASSWORD", "")

def publicar(titulo, contenido_html, estado="draft"):
    if not WP_URL or not WP_USER or not WP_PASS:
        return "ERROR: Faltan WORDPRESS_URL, WORDPRESS_USER o WORDPRESS_APP_PASSWORD en .env"
    
    endpoint = f"{WP_URL.rstrip('/')}/wp-json/wp/v2/posts"
    auth = (WP_USER, WP_PASS)
    payload = {"title": titulo, "content": contenido_html, "status": estado}
    
    try:
        r = requests.post(endpoint, auth=auth, json=payload, timeout=30)
        r.raise_for_status()
        return f"OK: Post publicado (ID {r.json().get('id')}). Estado: {estado}"
    except Exception as e:
        return f"ERROR: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python publicar_wordpress.py 'Titulo' 'Contenido HTML'")
        sys.exit(1)
    print(publicar(sys.argv[1], sys.argv[2]))
