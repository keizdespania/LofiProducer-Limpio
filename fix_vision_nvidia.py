"""Reescribe la herramienta de vision para usar NVIDIA Directo (con reasoning)."""
import pathlib, re, ast

p = pathlib.Path("scripts/dios.py")
t = p.read_text()

patron = re.compile(
    r'def _tool_analizar_video_competencia\(args\):.*?return "ERROR: " \+ str\(e\)\n',
    re.DOTALL
)

nueva_funcion = '''def _tool_analizar_video_competencia(args):
    """Descarga video, extrae 3 frames y los analiza con NVIDIA Nemotron VL (directo)."""
    import subprocess, base64, requests, shutil, time as _t
    url = args["url"]
    tmp_dir = ROOT / "sandbox" / "tmp_video"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    video_path = tmp_dir / "video.mp4"

    try:
        subprocess.run(["yt-dlp", "-f", "worst[ext=mp4]", "-o", str(video_path), url],
                       check=True, capture_output=True, timeout=120)

        frames = []
        for i, sec in enumerate([5, 15, 30]):
            frame_path = tmp_dir / ("frame_" + str(i) + ".jpg")
            subprocess.run(["ffmpeg", "-y", "-ss", str(sec), "-i", str(video_path),
                            "-vframes", "1", "-vf", "scale=640:-1", str(frame_path)],
                           check=True, capture_output=True)
            if frame_path.exists():
                frames.append(base64.b64encode(frame_path.read_bytes()).decode("utf-8"))

        if not frames:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return "ERROR: No se pudieron extraer fotogramas."

        # Debug frames
        debug_dir = ROOT / "output" / "debug_frames"
        debug_dir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(frames):
            (debug_dir / ("frame_" + str(int(_t.time())) + "_" + str(i) + ".jpg")).write_bytes(base64.b64decode(f))

        time.sleep(REQUEST_DELAY)

        # Llamar a NVIDIA NIM Directo
        nkey = _leer_api_key("NVIDIA_API_KEY")
        if not nkey:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return "ERROR: Falta NVIDIA_API_KEY en .env"

        content_parts = [{"type": "text", "text": "Analiza estos 3 fotogramas de un video de YouTube. Describe: 1) Que persona sale (genero, pelo, ropa, expresion). 2) Que se ve de fondo. 3) Que tipo de video es. Se concreto y visual."}]
        for f in frames:
            content_parts.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + f}})

        payload = {
            "model": "nvidia/nemotron-3.5-super-vl-120b-a12b",
            "messages": [{"role": "user", "content": content_parts}],
            "max_tokens": 2000
        }
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            json=payload,
            headers={"Authorization": "Bearer " + nkey, "Content-Type": "application/json"},
            timeout=120
        )

        if r.status_code != 200:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            return "ERROR NVIDIA HTTP " + str(r.status_code) + ": " + r.text[:200]

        data = r.json()
        try:
            msg = data["choices"][0]["message"]
            analisis = msg.get("content") or msg.get("reasoning_content") or str(data)
        except Exception:
            analisis = str(data)[:500]

        shutil.rmtree(tmp_dir, ignore_errors=True)
        return "ANALISIS DEL VIDEO (NVIDIA Nemotron VL):\\n" + analisis + "\\n\\n(Video borrado)."

    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return "ERROR: " + str(e)
'''

if patron.search(t):
    t = patron.sub(nueva_funcion, t)
    p.write_text(t)
    ast.parse(t)
    print("OK: Herramienta reescrita para NVIDIA Directo con max_tokens=2000")
    print("OK: Parser maneja content y reasoning_content")
    print("OK: Sintaxis OK")
else:
    print("ERROR: No se encontro la funcion antigua")
