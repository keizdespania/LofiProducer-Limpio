"""crear_paquete_blog.py - Multiplicador: 1 articulo -> 4 Shorts + 1 guion podcast."""
import sys, json, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "brain"))

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_VIDEOS = ROOT / "output" / "videos"
OUT_PODCAST = ROOT / "output" / "podcast"
OUT_PODCAST.mkdir(parents=True, exist_ok=True)

ANGULOS = ["dato", "contradiccion", "prediccion", "tutorial"]

def generar_paquete(tema, canal="ia_news"):
    ts = int(time.time())
    print(f"[paquete] Generando para: {tema} ({len(ANGULOS)} shorts)", flush=True)
    # 0. Investigar tendencias del nicho
    print(f"[paquete] Investigando tendencias del nicho...", flush=True)
    try:
        from investigador_redes import investigar
        inv = investigar(canal)
        top3 = sorted(inv.get("youtube", []), key=lambda x: x.get("vistas", 0), reverse=True)[:3]
        print(f"[paquete] Top 3 tendencias:", flush=True)
        for v in top3:
            print(f"  {v.get(chr(118)+chr(105)+chr(115)+chr(116)+chr(97)+chr(115), 0):>10,} | {v.get(chr(116)+chr(105)+chr(116)+chr(117)+chr(108)+chr(111), chr(63))[:60]}", flush=True)
    except Exception as e:
        print(f"[paquete] Investigador fallo (sigo sin contexto): {e}", flush=True)
        inv = {}

    from short_engine import crear_short
    from especialistas import pedir_a_especialista
    from cola_publicacion import encolar
    paquete = {"tema": tema, "canal": canal, "shorts": [], "podcast_guion": None}
    for i, angulo in enumerate(ANGULOS, 1):
        print(f"[paquete] Short {i}/4 ({angulo})...", flush=True)
        try:
            r = crear_short(tema, canal, max_clips=3, angulo=angulo)
            if r.get("status") == "ok":
                paquete["shorts"].append(r)
                print(f"[paquete] OK {angulo} -> {r.get(chr(39)+chr(112)+chr(97)+chr(116)+chr(104)+chr(39))}", flush=True)
                # Encolar para YouTube
                titulos = {
                    "dato": f"El dato de {tema} que lo cambia todo",
                    "contradiccion": f"Lo que NADIE te dice sobre {tema}",
                    "prediccion": f"Lo que pasara con {tema} en 6 meses",
                    "tutorial": f"Como aprovechar {tema} hoy mismo"
                }
                titulo = titulos.get(angulo, f"{tema} - Short {i}")
                encolar(r["path"], titulo, desc=f"Short generado sobre {tema}", tags="ia,noticias,shorts")
            else:
                print(f"[paquete] Fallo {angulo}: {r.get(chr(39)+chr(101)+chr(114)+chr(114)+chr(111)+chr(114)+chr(39))}", flush=True)
        except Exception as e:
            print(f"[paquete] Exc {angulo}: {e}", flush=True)
    print("[paquete] Generando guion podcast...", flush=True)
    try:
        guion = pedir_a_especialista("redactor_seo", f"Guion podcast 5 min sobre: {tema}. Conversacional, 3 bloques, 700-900 palabras.", contexto=f"Articulo sobre {tema}")
        paquete["podcast_guion"] = guion
        (OUT_PODCAST / f"podcast_{canal}_{ts}_guion.txt").write_text(guion, encoding="utf-8")
        print(f"[paquete] Guion podcast: {len(guion.split())} palabras", flush=True)
        
        # Generar audio del podcast
        print("[paquete] Generando audio del podcast (Sherpa)...", flush=True)
        import subprocess, sys
        out_audio = OUT_PODCAST / f"podcast_{canal}_{ts}.mp3"
        cmd = [sys.executable, str(ROOT/"scripts"/"voice_studio.py"), "--texto", guion, "--voz", "es_ES-davefx-medium", "--preset", "narracion_relajada", "--formato", "mp3"]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
        if "OK:" in r.stdout:
            print("[paquete] Podcast audio generado.", flush=True)
    except Exception as e:
        print(f"[paquete] Fallo podcast: {e}", flush=True)
    manifest = OUT_VIDEOS / f"paquete_{canal}_{ts}.json"
    manifest.write_text(json.dumps(paquete, indent=2, ensure_ascii=False))
    print(f"[paquete] Manifest: {manifest}", flush=True)
    return paquete

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: crear_paquete_blog.py <tema> [canal]"); sys.exit(1)
    tema = sys.argv[1]
    canal = sys.argv[2] if len(sys.argv) > 2 else "ia_news"
    print(json.dumps(generar_paquete(tema, canal), indent=2, ensure_ascii=False))