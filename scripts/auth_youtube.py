import json, pathlib, urllib.request, urllib.parse, sys, time

env = {}
for line in pathlib.Path(".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")

CID = env["YOUTUBE_CLIENT_ID"]
CSEC = env["YOUTUBE_CLIENT_SECRET"]
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/blogger",
]
REDIRECT = "http://127.0.0.1:8080/"

if len(sys.argv) > 1:
    raw = sys.argv[1].strip()
    # Acepta tanto "4/0abc..." como URL completa con ?code=...
    if "code=" in raw:
        code = urllib.parse.parse_qs(urllib.parse.urlparse(raw).query)["code"][0]
    else:
        code = raw
else:
    auth_url = (
        "https://accounts.google.com/o/oauth2/auth?"
        + urllib.parse.urlencode({
            "client_id": CID,
            "redirect_uri": REDIRECT,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent select_account",
        })
    )
    print("\n🌐 Abre esta URL en Chrome (misma cuenta keizdespania@gmail.com):\n")
    print(auth_url)
    print("\n⚠️  IMPORTANTE: cuando Google pregunte por el canal,")
    print("   elige 'Somos El Encuadre', NO 'KeiZ Productions'.\n")
    print("Tras autorizar, el navegador irá a http://127.0.0.1:8080/?code=...")
    print("(dará error de conexión, es normal). Copia la URL completa")
    print("o solo el valor de code=, y ejecuta:")
    print("  python3 scripts/auth_youtube.py 'URL_O_CODE'\n")
    sys.exit(0)

data = urllib.parse.urlencode({
    "code": code, "client_id": CID, "client_secret": CSEC,
    "redirect_uri": REDIRECT, "grant_type": "authorization_code",
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=20).read())
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:300]); sys.exit(1)

TOKEN = pathlib.Path("data/youtube_encuadre_token.json")
TOKEN.parent.mkdir(exist_ok=True)
TOKEN.write_text(json.dumps({
    "client_id": CID, "client_secret": CSEC,
    "access_token": resp["access_token"], "refresh_token": resp["refresh_token"],
    "expires_at": time.time() + resp.get("expires_in", 3600),
    "token_uri": "https://oauth2.googleapis.com/token",
    "scopes": SCOPES,
}, indent=2))
print(f"\n✅ Token guardado en {TOKEN}")

req = urllib.request.Request(
    "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
    headers={"Authorization": f"Bearer {resp['access_token']}"},
)
ch = json.loads(urllib.request.urlopen(req, timeout=15).read())["items"][0]
print(f"📺 Canal conectado: {ch['snippet']['title']}")
print(f"   ID: {ch['id']}")
print(f"   Subs: {ch['statistics'].get('subscriberCount','?')} · Vídeos: {ch['statistics'].get('videoCount','?')}")

if "Somos" not in ch["snippet"]["title"] and "Encuadre" not in ch["snippet"]["title"]:
    print("\n⚠️  ATENCIÓN: el canal NO es 'Somos El Encuadre'.")
    print("   Vuelve a lanzar el OAuth y selecciona el canal correcto.")
    sys.exit(2)

# Escribir refresh_token en .env
env_path = pathlib.Path(".env")
lines = [l for l in env_path.read_text().splitlines() if not l.startswith("YOUTUBE_ENCUADRE_REFRESH_TOKEN=")]
lines.append(f"YOUTUBE_ENCUADRE_REFRESH_TOKEN={resp['refresh_token']}")
env_path.write_text("\n".join(lines) + "\n")
print("\n💾 YOUTUBE_ENCUADRE_REFRESH_TOKEN escrito en .env")
