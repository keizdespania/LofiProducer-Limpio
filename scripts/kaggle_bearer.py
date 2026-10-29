"""Cliente minimalista de Kaggle usando Bearer auth (KGAT_). Sin dependencias externas."""
import json, os, sys, urllib.request, urllib.error, pathlib

API = "https://www.kaggle.com/api/v1"
ROOT = pathlib.Path(__file__).resolve().parent.parent

def _token(cuenta=1):
    """Lee el token de la cuenta 1 o 2."""
    var_name = "KAGGLE_API_TOKEN_2" if cuenta == 2 else "KAGGLE_API_TOKEN"
    
    # 1. .env
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith(var_name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
                
    # 2. Fallback a kaggle.json o access_token (solo cuenta 1)
    if cuenta == 1:
        kaggle_json = pathlib.Path.home() / ".kaggle" / "kaggle.json"
        if kaggle_json.exists():
            try:
                return json.loads(kaggle_json.read_text()).get("key", "")
            except: pass
        access_token = pathlib.Path.home() / ".kaggle" / "access_token"
        if access_token.exists():
            return access_token.read_text().strip()
            
    return ""

def _req(path, method="GET", data=None, cuenta=1):
    token = _token(cuenta)
    if not token:
        return {"error": f"No hay token para la cuenta {cuenta} (revisa .env)"}
    
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    
    if data:
        req.data = json.dumps(data).encode()
    
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            body = r.read()
            try: return json.loads(body)
            except: return body
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read()[:300].decode(errors='replace')}"}
    except Exception as e:
        return {"error": str(e)}

def whoami():
    """Prueba de autenticación (lista competiciones)."""
    return _req("/competitions/list?page=1")

def listar_kernels(usuario=""):
    """Lista los kernels del usuario."""
    return _req(f"/kernels/list?user={usuario}&page=1")

def estado_kernel(slug):
    """Consulta el estado en cuenta 1; si da 404, prueba cuenta 2."""
    partes = slug.split("/")
    if len(partes) != 2:
        return {"error": "Slug invalido. Debe ser 'usuario/nombre'"}
    user, kernel = partes
    
    # Intento Cuenta 1
    r1 = _req(f"/kernels/status?userName={user}&kernelSlug={kernel}", cuenta=1)
    if not (isinstance(r1, dict) and ("error" in r1 or "status" not in r1)):
        return r1
    
    # Fallback Cuenta 2
    r2 = _req(f"/kernels/status?userName={user}&kernelSlug={kernel}", cuenta=2)
    if not (isinstance(r2, dict) and ("error" in r2 or "status" not in r2)):
        return r2
        
    # Si ambas fallan, devolvemos el error de la cuenta 1
    return r1

def push_kernel(slug, codigo, enable_gpu=True, enable_internet=True, dataset_sources=None):
    """Intenta subir a la cuenta 1. Si esta llena (max 2 GPUs), usa la cuenta 2."""
    payload = {
        "slug": slug, "newTitle": slug.split("/")[-1].replace("-", " ").title(),
        "text": codigo, "language": "python", "kernelType": "script",
        "isPrivate": True, "enableGpu": enable_gpu, "enableTpu": False,
        "enableInternet": enable_internet, "datasetDataSources": dataset_sources or [],
        "competitionDataSources": [], "kernelDataSources": [],
    }
    
    # Intentar cuenta 1
    print(f"[Rotator] Intentando cuenta 1 para {slug}...")
    res = _req("/kernels/push", method="POST", data=payload, cuenta=1)
    
    # Si falla por limite de GPU, probar cuenta 2
    if isinstance(res, dict) and res.get("hasError") and any(x in res.get("error", "") for x in ("Maximum batch GPU session count", "Maximum weekly GPU quota", "Maximum weekly")):
        print("[Rotator] Cuenta 1 llena. Usando cuenta 2...")
        res = _req("/kernels/push", method="POST", data=payload, cuenta=2)
    
    return res

def salida_kernel(slug):
    """Lista los archivos de salida de un kernel."""
    return _req(f"/kernels/output/{slug}")


def output_kernel(slug):
    """Lista archivos en cuenta 1; si da 404, prueba cuenta 2."""
    r1 = _req(f"/kernels/list/{slug}/files", cuenta=1)
    if not (isinstance(r1, dict) and "error" in r1):
        return r1
    
    r2 = _req(f"/kernels/list/{slug}/files", cuenta=2)
    if not (isinstance(r2, dict) and "error" in r2):
        return r2
        
    return r1



def stop_kernel(slug):
    """Detiene un kernel en ejecución (para ahorrar cuota)."""
    partes = slug.split("/")
    if len(partes) != 2:
        return {"error": "Slug inválido"}
    user, kernel = partes
    # Intentar en cuenta 1, luego cuenta 2
    for cuenta in (1, 2):
        try:
            r = _req(f"/kernels/stop/{user}/{kernel}", method="POST", cuenta=cuenta)
            if not (isinstance(r, dict) and r.get("hasError")):
                return {"status": "stopped", "detalle": r}
        except Exception:
            continue
    return {"error": "No se pudo parar el kernel"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python kaggle_bearer.py <comando>")
        print("Comandos: whoami, kernels, status <slug>, output <slug>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "whoami":
        r = whoami()
        if isinstance(r, dict) and "error" in r:
            print("❌", r["error"])
        elif isinstance(r, list):
            print(f"✅ Bearer auth OK. Competiciones: {len(r)}")
        else:
            print(f"✅ Bearer auth OK. Respuesta: {str(r)[:200]}")
    elif cmd == "kernels":
        r = listar_kernels()
        if isinstance(r, dict) and "error" in r:
            print("❌", r["error"])
        elif isinstance(r, list):
            for k in r[:10]:
                print(f"· {k.get('ref')} | {k.get('lastRunTime', '?')} | {k.get('status', '?')}")
        else:
            print(f"Respuesta: {str(r)[:200]}")
    elif cmd == "push" and len(sys.argv) > 3:
        slug = sys.argv[2]
        codigo = sys.argv[3]
        r = push_kernel(slug, codigo)
        print(r)
    elif cmd == "status" and len(sys.argv) > 2:
        print(estado_kernel(sys.argv[2]))
    elif cmd == "output" and len(sys.argv) > 2:
        print(salida_kernel(sys.argv[2]))
    else:
        print("Comando no reconocido")
