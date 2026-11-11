#!/usr/bin/env python3
"""reautorizar_youtube.py - Reautoriza el canal de YouTube.
Uso:
  1. python3 scripts/reautorizar_youtube.py
  2. Abre la URL en el navegador
  3. Autoriza con la cuenta de Somos El Encuadre Oficial
  4. Copia el código que te dé Google
  5. Pégalo cuando lo pida
"""
import json, urllib.request, urllib.parse, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN_FILE = ROOT / "data" / "youtube_encuadre_token.json"

# Credenciales del cliente OAuth (mismas que ya tienes)
CLIENT_ID = None
CLIENT_SECRET = None

# Leer del token actual (aunque esté revocado, las credenciales del cliente son válidas)
if TOKEN_FILE.exists():
    tok = json.loads(TOKEN_FILE.read_text())
    CLIENT_ID = tok.get("client_id")
    CLIENT_SECRET = tok.get("client_secret")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ No hay client_id/client_secret en data/youtube_encuadre_token.json")
    print("   Añádelos manualmente o crea el fichero con:")
    print('   {"client_id": "...", "client_secret": "..."}')
    sys.exit(1)

# Scopes que necesitamos
SCOPES = [
    "https://www.googleapis.com/auth/youtube",          # COMPLETO: subir + editar + manage
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/blogger",
]

# Generar URL de autorización
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "response_type": "code",
    "scope": " ".join(SCOPES),
    "access_type": "offline",  # CRÍTICO: para obtener refresh_token
    "prompt": "consent",        # CRÍTICO: fuerza consentimiento (si no, no da refresh_token)
}
auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)

print("=" * 70)
print("  REAUTORIZACIÓN DE YOUTUBE")
print("=" * 70)
print()
print("PASO 1: Abre esta URL en el navegador (o en el PC):")
print()
print(auth_url)
print()
print("PASO 2: Inicia sesión con la cuenta del canal OFICIAL")
print("       (somoselencuadre@gmail.com / @somoselencuadre.oficial)")
print()
print("PASO 3: Acepta los permisos")
print()
print("PASO 4: Copia el código de autorización que te dé Google")
print()

# Abrir URL automáticamente (si está en Termux)
try:
    import subprocess
    subprocess.run(["termux-open-url", auth_url], capture_output=True, timeout=5)
    print("✅ URL abierta en el navegador del móvil")
except Exception:
    pass

print()
code = input("PASO 5: Pega el código aquí: ").strip()
if not code:
    print("❌ Sin código")
    sys.exit(1)

# Intercambiar código por tokens
print()
print("🔄 Intercambiando código por tokens...")
data = urllib.parse.urlencode({
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
    "grant_type": "authorization_code",
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
try:
    r = json.loads(urllib.request.urlopen(req, timeout=15).read())
except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.read().decode()[:300]}")
    sys.exit(1)

if "refresh_token" not in r:
    print("❌ Google no devolvió refresh_token. Intenta con prompt=consent (ya está).")
    print(f"   Respuesta: {r}")
    sys.exit(1)

# Guardar tokens
nuevo_token = {
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "access_token": r["access_token"],
    "refresh_token": r["refresh_token"],
    "expires_at": time.time() + r.get("expires_in", 3600),
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": SCOPES,
}
TOKEN_FILE.write_text(json.dumps(nuevo_token, indent=2))
print()
print("=" * 70)
print("  ✅ REAUTORIZACIÓN COMPLETA")
print("=" * 70)
print(f"  access_token: {r['access_token'][:30]}...")
print(f"  refresh_token: {r['refresh_token'][:30]}...")
print(f"  expires_at: {time.ctime(nuevo_token['expires_at'])}")
print(f"  Guardado en: {TOKEN_FILE}")
print()
print("Ya puedes subir a YouTube:")
print("  python3 scripts/subir_youtube.py video.mp4 'Título'")
