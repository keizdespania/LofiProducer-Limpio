"""
Cajon 133 - KeiZ Command Center (Backend API + Static Server).
"""
from __future__ import annotations
import json
import threading
import time
import uuid
import subprocess
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'brain'))
from especialistas import pedir_a_especialista
import sys
import urllib.parse
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brain.analytics_youtube import obtener_stats_canal

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path, content_type: str):
        if not path.exists() or not path.is_file():
            self.send_response(404)
            self.end_headers()
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/":
            self._send_file(ROOT / "assets" / "index.html", "text/html; charset=utf-8")
        elif path == "/assets/app.js":
            self._send_file(ROOT / "assets" / "app.js", "application/javascript; charset=utf-8")
        elif path == "/assets/style.css":
            self._send_file(ROOT / "assets" / "style.css", "text/css; charset=utf-8")
        elif path == "/assets/logo.png":
            self._send_file(ROOT / "assets" / "logo.png", "image/png")
        elif path == "/assets/manifest.json":
            self._send_file(ROOT / "assets" / "manifest.json", "application/json")
        elif path == "/api/docs":
            qs = urllib.parse.parse_qs(parsed.query)
            filename = qs.get("file", ["MANUAL_DE_USO.md"])[0]
            if ".." in filename or "/" in filename:
                self.send_response(403); self.end_headers(); return
            self._send_file(ROOT / filename, "text/plain; charset=utf-8")
        elif path == "/api/media":
            self._send_json(self._list_media())
        elif path == "/api/analytics":
            self._send_json(self._get_analytics())
        elif path.startswith("/media/"):
            filename = path.replace("/media/", "", 1)
            filepath = ROOT / "output" / filename
            if not filepath.exists():
                filepath = ROOT / "assets" / filename
            ctype = "audio/mpeg" if filename.endswith(".mp3") else "video/mp4" if filename.endswith(".mp4") else "image/jpeg"
            self._send_file(filepath, ctype)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = {}

        if self.path == "/api/chat":
            self._send_json(self._chat(payload.get("message", "")))
        elif self.path == "/api/crear_canal":
            self._send_json(self._crear_canal(payload))
        elif self.path == "/api/prompt":
            self._send_json(self._mejorar_prompt(payload.get("prompt", ""), payload.get("tipo", "visual")))
        elif self.path == "/api/generar_musica":
            self._send_json(self._generar_musica(payload))
        elif self.path == "/api/documentar":
            self._send_json(self._documentar(payload))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args): pass

    # --- Lógica de Negocio ---
    def _list_media(self):
        media = {"audio": [], "video": [], "image": []}
        dirs = [ROOT / "output", ROOT / "assets"]
        for d in dirs:
            if not d.exists(): continue
            for f in d.rglob("*"):
                if not f.is_file(): continue
                if f.suffix in (".mp3", ".wav"): media["audio"].append(f.name)
                elif f.suffix in (".mp4", ".mov"): media["video"].append(f.name)
                elif f.suffix in (".png", ".jpg", ".jpeg"): media["image"].append(f.name)
        return {k: list(set(v)) for k, v in media.items()}

    def _get_analytics(self):
        import os
        size_mb = sum(f.stat().st_size for f in ROOT.rglob('*') if f.is_file()) / (1024*1024)
        py_files = len(list(ROOT.rglob("*.py")))
        try:
            import sqlite3
            db = sqlite3.connect(ROOT / "data" / "agent" / "memoria.db")
            convs = db.execute("SELECT COUNT(*) FROM conversaciones").fetchone()[0]
            db.close()
        except Exception:
            convs = 0
        # Obtener datos de YouTube
        yt = obtener_stats_canal()
        if "error" not in yt:
            yt_data = {
                "nombre_canal": yt.get("nombre_canal", "KeiZ Productions"),
                "Suscriptores YT": yt["suscriptores"],
                "Visitas YT": yt["visitas_totales"],
                "Vídeos YT": yt["videos_totales"],
                "Ultimos Videos": yt.get("ultimos_videos", [])
            }
        else:
            yt_data = {"YouTube": "Fallo API"}

        return {
            "Tamaño Repo (MB)": f"{size_mb:.1f}",
            "Archivos Python": str(py_files),
            "Conversaciones Dios": str(convs),
            "Estado Kaggle": "Conectado",
            **yt_data
        }

    def _chat(self, msg):
        if not msg: return {"status": "error", "mensaje": "Vacio"}
        try:
            proc = subprocess.run(["python", "scripts/dios.py", msg], capture_output=True, text=True, cwd=str(ROOT), timeout=1200)
            out = proc.stdout
            if "[dios] Tarea completada. Resumen:" in out:
                reply = out.split("[dios] Tarea completada. Resumen:")[-1].strip()
            else:
                reply = out[-1500:] if out else proc.stderr[-1500:]
            return {"status": "ok", "reply": reply}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    def _crear_canal(self, payload):
        try:
            proc = subprocess.run(["python", "-m", "brain.crear_canal", payload["nombre"], payload["nicho"], payload["rpm"]], capture_output=True, text=True, cwd=str(ROOT), timeout=60)
            if proc.returncode != 0: raise RuntimeError(proc.stderr[-500:])
            import ast
            return ast.literal_eval(proc.stdout.strip().splitlines()[-1])
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

    def _mejorar_prompt(self, prompt, tipo="visual"):
        if not prompt: return {"status": "error", "mensaje": "Prompt vacio"}
        try:
            import os, requests
            api_key = os.environ.get("GROQ_API_KEY", "")
            if not api_key:
                # Leer del .env si no está en el entorno
                env = ROOT / ".env"
                if env.exists():
                    for line in env.read_text().splitlines():
                        if line.startswith("GROQ_API_KEY="):
                            api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
            
            systems = {
                "visual": "Eres un experto en prompts para modelos de video (LTX, Midjourney). Añade iluminación, cámara, textura y estilo cinematográfico. SOLO el prompt.",
                "estrategia": "Eres un estratega de contenido. Da 3-5 viñetas con nichos, monetización y canales. Concreto.",
                "seo": "Eres experto en YouTube. Genera: 1) Título viral. 2) Descripción con keywords. 3) Guion de 30s (Hook, Desarrollo, CTA).",
                "musica": "Eres experto en ACE-Step. Describe estilo, BPM, instrumentos y atmósfera. SOLO el prompt."
            }
            system = systems.get(tipo, systems["visual"])
            payload = {
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                              json=payload, timeout=30)
            if r.status_code >= 400:
                return {"status": "error", "mensaje": f"Groq Error {r.status_code}: {r.text[:100]}"}
            reply = r.json()["choices"][0]["message"]["content"]
            return {"status": "ok", "reply": reply.strip()}
        except Exception as e:
            return {"status": "error", "mensaje": str(e)}

class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    port = 8000
    print(f"✨ KeiZ Command Center (Full) iniciado en: http://127.0.0.1:8000{port}")
    ReuseHTTPServer(("127.0.0.1", port), Handler).serve_forever()
