"""subir_tiktok.py - OAuth y subida de borradores a TikTok."""
import json, urllib.request, urllib.parse, sys, pathlib, hashlib, secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env = {}
for l in (ROOT / ".env").read_text().splitlines():
    if "=" in l and not l.startswith("#"):
        k,v = l.split("=",1); env[k.strip()] = v.strip()

CLIENT_KEY = env["TIKTOK_CLIENT_KEY"]
CLIENT_SECRET = env["TIKTOK_CLIENT_SECRET"]
REDIRECT_URI = "https://rockfish-unclog-delay.ngrok-free.dev/callback/"
VERIFIER_FILE = ROOT / "data" / "tiktok_verifier.txt"

def _pkce():
    verifier = secrets.token_urlsafe(48)
    challenge = hashlib.sha256(verifier.encode()).hexdigest()
    VERIFIER_FILE.write_text(verifier)
    return challenge

if len(sys.argv) < 2:
    challenge = _pkce()
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": CLIENT_KEY,
        "scope": "user.info.basic,video.upload",
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "state": "encuadre_auth",
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print("\n🌐 Abre esta URL en Chrome:\n")
    print(url)
    print("\nCopia la URL de redirección (ngrok) y ejecútala:")
    print("  python3 scripts/subir_tiktok.py 'URL_CON_CODE'")
    sys.exit(0)

# Intercambio de código por token
code = urllib.parse.parse_qs(urllib.parse.urlparse(sys.argv[1]).query).get("code", [""])[0]
verifier = VERIFIER_FILE.read_text().strip()

data = urllib.parse.urlencode({
    "client_key": CLIENT_KEY, "client_secret": CLIENT_SECRET,
    "code": code, "grant_type": "authorization_code",
    "redirect_uri": REDIRECT_URI, "code_verifier": verifier,
}).encode()

req = urllib.request.Request("https://open.tiktokapis.com/v2/oauth/token/", data=data,
                              headers={"Content-Type": "application/x-www-form-urlencoded"})
try:
    r = json.loads(urllib.request.urlopen(req, timeout=15).read())
    if "access_token" in r:
        (ROOT / "data" / "tiktok_token.json").write_text(json.dumps(r, indent=2))
        print("✅ Token de TikTok guardado en data/tiktok_token.json")
    else:
        print("❌ Error:", r)
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:300])
