"""hacer_dia.py - Orquestador multi-canal diario."""
import sys, json, pathlib, time, datetime
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "brain"))

def obtener_canales_activos():
    nichos = json.loads((ROOT / "config" / "nichos.json").read_text())
    return [k for k in nichos.keys() if not k.startswith("_") and k != "nichos_template"]

def hacer_dia(dry=False):
    print(f"[hacer_dia] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", flush=True)
    canales = obtener_canales_activos()
    print(f"[hacer_dia] {len(canales)} canales activos: {canales}", flush=True)
    resultado = {"fecha": datetime.date.today().isoformat(), "canales": {}}
    
    for canal in canales:
        print(f"[hacer_dia] --- {canal} ---", flush=True)
        try:
            # 1. Investigar
            from investigador_redes import investigar
            inv = investigar(canal)
            resultado["canales"][canal] = {"investigacion_ok": True, "youtube_count": len(inv.get("youtube", []))}
            
            if dry:
                print(f"[hacer_dia] {canal} (dry) OK", flush=True)
                continue
            
            # 2. Informe editorial
            try:
                from informe_detective import generar_informe_visual
                generar_informe_visual(canal)
                resultado["canales"][canal]["informe_ok"] = True
                print(f"[hacer_dia] {canal} informe OK", flush=True)
            except Exception as e:
                print(f"[hacer_dia] {canal} informe fallo: {e}", flush=True)
                resultado["canales"][canal]["informe_ok"] = False
        except Exception as e:
            print(f"[hacer_dia] {canal} EXC: {e}", flush=True)
            resultado["canales"][canal] = {"error": str(e)}
    
    # Notificar
    total_ok = sum(1 for c in resultado["canales"].values() if c.get("investigacion_ok"))
    try:
        import subprocess
        subprocess.run(["termux-notification", "-t", f"Dia preparado", "-c", f"{total_ok}/{len(canales)} canales OK", "--priority", "high"], check=False, timeout=5)
    except Exception: pass
    
    print(f"[hacer_dia] RESULTADO: {total_ok}/{len(canales)} canales procesados", flush=True)
    return resultado

if __name__ == "__main__":
    dry = "--dry" in sys.argv
    print(json.dumps(hacer_dia(dry), indent=2, ensure_ascii=False))
