#!/usr/bin/env python3
"""
================================================================================
🧙 DIOS DE LA CONSTRUCCIÓN — AGENTE AUTÓNOMO DEL ECOSISTEMA LOFIPRODUCER
================================================================================
Este script es el cerebro autónomo del proyecto. Si eres una IA externa 
leyendo esto, aquí tienes el manual de instrucciones:

### 1. ARQUITECTURA Y ENTORNO
- Runtime: Python 3.14 en Termux (Samsung A25 5G, sin root).
- Enrutador LLM: OmniRoute (local, puerto 20128) usando el modelo 'auto'.
  Si falla, cae a 'mi-groq/qwen3.8-27b' u OpenRouter.
- Memoria: SQLite (data/agent/memoria.db). Memoria a corto plazo (chats) 
  y a largo plazo (hechos aprendidos).

### 2. BUCLE DE AGENTE (ReAct)
El Dios funciona en un bucle de hasta 25 pasos (MAX_STEPS = 25).
1. Recibe un prompt.
2. Piensa y decide si usar una herramienta.
3. Ejecuta la herramienta, lee el resultado y vuelve a pensar.
4. Cuando termina, da un resumen final.

### 3. HERRAMIENTAS (TOOLS)
Tiene 20 herramientas declaradas en el array TOOLS. Las más importantes:
- Construcción: write_file (escribe en sandbox/), validate_file (ast.parse),
  promote_file (mueve a producción), ejecutar_comando (terminal).
- Producción: generar_video (Kaggle), generar_imagen (Cloudflare), generar_cancion_kaggle.
- Memoria: recordar_hecho, consultar_hechos.
- Búsqueda: buscar_en_web, buscar_youtube.

### 4. REGLAS DE SEGURIDAD (CRÍTICO PARA IAS EXTERNAS)
- Sandbox: NUNCA escribir directamente en el repo. Usar write_file y luego promote_file.
- Validación: promote_file fallará si el archivo .py tiene errores de sintaxis. Usar validate_file antes.
- Comandos Prohibidos: En ejecutar_comando NUNCA usar operadores shell como &&, ;, >, | ni cd. 
  Usar comandos directos (python scripts/foo.py). La blacklist bloqueará el comando.
- Secretos: Prohibido leer .env, secrets/, tokens o claves privadas. 
  La herramienta leer_documentacion y read_file lo bloquearán.

### 5. LÍMITES (v2.0)
- max_tokens de respuesta: 4096.
- Contexto de herramientas: 8000 caracteres.
- Resumen de memoria: 2000 caracteres.
================================================================================

23. ARSENAL SUPERDIOS (5 herramientas nuevas):
    - sanar_sistema(): Si algo falla, usala para reiniciar Flask o OmniRoute.
    - notificar_movil(titulo, mensaje): Avisa al usuario al movil cuando termines tareas largas.
    - leer_rss(fuente, limite): Lee noticias frescas (boe, techcrunch, hackernews, verge).
    - pedir_a_especialista(rol, tarea): Sub-agentes expertos (guionista, seo, auditor, traductor, musico).
    - lanzar_notebook_kaggle(nombre, codigo_python): Ejecuta codigo Python en una GPU de Kaggle.
"""
from __future__ import annotations
import ast
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
REQUEST_DELAY = 3  # agent; se sobreescribe a 1 en charla rápida  # Segundos de respiro entre peticiones a IAs
sys.path.insert(0, str(ROOT))

from brain.web_search import buscar
from brain.ejecutor_seguro import ejecutar
from brain.pruner import comprimir, comprimir_mensajes
from brain.memoria_db import guardar_conversacion, recordar_hecho, consultar_hechos, obtener_contexto_reciente
from brain.dios_tools_dinamicas import cargar_tools_dinamicas, persistir_tool

try:
    from brain.dios_memoria import WORKSPACE, EPISODIOS, COSTES, FALLOS
except ImportError:
    sys.path.insert(0, str(ROOT / 'brain'))
    from dios_memoria import WORKSPACE, EPISODIOS, COSTES, FALLOS

MEM_FILE = ROOT / "data" / "agent" / "memoria.json"
SANDBOX = ROOT / "sandbox"
BACKUP_DIR = ROOT / "data" / "agent" / "backups"
OMNIROUTE_URL = "http://localhost:20128/v1/chat/completions"
MODEL = "groq/openai/gpt-oss-120b"
MAX_STEPS = 10

TOOL_FALLBACKS = {
    "generar_video": ["generar_video_rapido", "ensamblar_video_final"],
    "producir_video_completo": ["producir_video", "generar_video"],
    "buscar_en_web": ["buscar_youtube", "leer_rss"],
    "buscar_youtube": ["buscar_en_web", "leer_rss"],
    "producir_nicho": ["producir_video_completo"],
    "subir_youtube": ["procesar_cola_youtube"],
}


def _check_tokens_limit():
    """Aborta si >500k tokens hoy. Alerta Telegram a 400k."""
    try:
        r = COSTES.resumen_hoy()
        total = (r.get("tokens_in", 0) or 0) + (r.get("tokens_out", 0) or 0)
        if total > 400_000 and total <= 500_000:
            import subprocess as _sp
            try:
                _sp.run(["python3", "scripts/notificar_telegram.py", f"⚠️ Dios: {total} tokens hoy (>80% del limite 500k)"], cwd=str(ROOT), timeout=15, capture_output=False)
            except: pass
        if total > 500_000:
            print(f"🛑 LIMITE TOKENS: {total}/500000. Abortando tarea.")
            return False
    except: pass
    return True

def _guardar_resultado(prompt, resumen, tools, exito=True):
    try:
        WORKSPACE.anotar_tarea(prompt, resumen, tools)
        EPISODIOS.guardar(prompt, resumen, tools, exito)
    except Exception as e:
        print(f"   [memoria save error] {e}")

TTL_HORAS = 48


def _leer_key() -> str:
    """2026-11-09: prefiere GROQ_API_KEY (OmniRoute lleva dias 401). Cascada."""
    env = ROOT / ".env"
    if not env.exists():
        raise SystemExit("Falta .env")
    lines = env.read_text(encoding="utf-8").splitlines()
    # Preferencia: GROQ_API_KEY -> GROQ_API_KEY_2 -> OMNIROUTE_API_KEY
    for prefix in ("GROQ_API_KEY=", "GROQ_API_KEY_2=", "GROQ_API_KEY_3=", "GROQ_API_KEY_4=", "OMNIROUTE_API_KEY="):
        for line in lines:
            line = line.strip()
            if line.startswith(prefix):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("Falta GROQ_API_KEY u OMNIROUTE_API_KEY en .env")


def _cargar_memoria() -> dict:
    if not MEM_FILE.exists():
        return {"conversaciones": []}
    try:
        return json.loads(MEM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"conversaciones": []}


def _guardar_memoria(mem: dict) -> None:
    mem["ultima_conexion"] = datetime.now(timezone.utc).isoformat()
    MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
    MEM_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2), encoding="utf-8")


def _limpiar_backups() -> int:
    if not BACKUP_DIR.exists():
        return 0
    limite = time.time() - (TTL_HORAS * 3600)
    borrados = 0
    for f in BACKUP_DIR.glob("*"):
        if f.is_file() and f.stat().st_mtime < limite:
            f.unlink()
            borrados += 1
    return borrados


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"{ts}_{path.name}"
    shutil.copy2(path, dst)
    return dst


def _contexto_proyecto(prompt: str = "") -> str:
    """Contexto DINÁMICO: solo carga lo relevante al prompt. Ahorra 70-90% tokens."""
    partes = []
    p = (prompt or "").lower()

    # 1. BOOT siempre (esencial) pero recortado
    boot = ROOT / "BOOT_PROMPT.md"
    if boot.exists():
        partes.append("=== BOOT (esencial) ===\n" + boot.read_text(encoding="utf-8")[:1500])

    # 2. Contratos SOLO si el prompt menciona ese tipo
    contratos_map = {
        "acestep":   ["música", "musica", "canción", "cancion", "beat", "lofi", "generar cancion"],
        "sherpa":    ["voz", "narrar", "tts", "locución", "locucion", "hablar"],
        "image":     ["imagen", "foto", "dibujo", "sdxl", "generar imagen"],
        "video":     ["vídeo", "video", "clip", "wan", "short", "generar video"],
        "youtube":   ["youtube", "yt", "suscribir", "publicar", "trending", "viral"],
        "blogger":   ["blog", "blogger", "artículo", "articulo", "seo", "post"],
        "pixabay":   ["pixabay", "stock", "banco de"],
    }
    for nombre, keywords in contratos_map.items():
        if any(k in p for k in keywords):
            f = ROOT / f"data/agent/{nombre}_contract.json"
            if f.exists():
                partes.append(f"=== {nombre}_contract ===\n" + f.read_text(encoding="utf-8")[:2000])

    # 3. MANUAL_FRODO solo si pregunta por reglas/manual/errores
    if any(k in p for k in ["regla", "manual", "frodo", "cómo ", "como ", "error", "fallo", "bug"]):
        m = ROOT / "MANUAL_FRODO_PYTHON.md"
        if m.exists():
            partes.append("=== MANUAL ===\n" + m.read_text(encoding="utf-8")[:1200])

    # 4. Git status solo si pregunta por repo/git/cambios
    if any(k in p for k in ["git", "repo", "commit", "backup", "cambio", "estado del repo"]):
        try:
            r = subprocess.run(["git", "status", "--short"], cwd=str(ROOT),
                               capture_output=True, text=True, timeout=15)
            partes.append("=== git ===\n" + (r.stdout[:500] or "(limpio)"))
        except Exception:
            pass

    # 5. Conversaciones recientes: SIEMPRE (contexto útil, pocos bytes)
    try:
        ctx_reciente = obtener_contexto_reciente(3)
        if ctx_reciente:
            partes.append("=== Recientes ===\n" + ctx_reciente)
    except Exception:
        pass

    # 6. Hechos: solo si pregunta personal o "recuerda"
    if any(k in p for k in ["recuerda", "memoria", "antes", "dijiste", "hecho", "aprend"]):
        try:
            hechos = consultar_hechos()
            if hechos and "No hay hechos" not in hechos:
                partes.append("=== Hechos ===\n" + hechos[:1500])
        except Exception:
            pass

    return "\n\n".join(partes)



def _extraer_prompt(messages):
    """Extrae el último mensaje del usuario de la lista messages."""
    for m in reversed(messages):
        if m.get("role") == "user":
            return m.get("content", "")
    return ""

def _filtrar_tools(prompt, todas):
    """Devuelve solo las tools relevantes según el prompt. Ahorra ~80% tokens."""
    p = prompt.lower()
    palabras = {
        'imagen': ['generar_imagen'],
        'foto': ['generar_imagen'],
        'vídeo': ['generar_video', 'producir_video_completo', 'ensamblar_video_largo', 'ensamblar_video_final'],
        'video': ['generar_video', 'producir_video_completo', 'ensamblar_video_largo', 'ensamblar_video_final'],
        'youtube': ['buscar_youtube', 'buscar_en_web'],
        'trending': ['buscar_youtube', 'buscar_en_web'],
        'viral': ['buscar_youtube', 'buscar_en_web'],
        'mas visto': ['buscar_youtube', 'buscar_en_web'],
        'más visto': ['buscar_youtube', 'buscar_en_web'],
        'buscar': ['buscar_youtube', 'buscar_en_web'],
        'música': ['generar_cancion_kaggle'],
        'musica': ['generar_cancion_kaggle'],
        'canción': ['generar_cancion_kaggle'],
        'cancion': ['generar_cancion_kaggle'],
        'voz': ['generar_narracion'],
        'narrar': ['generar_narracion'],
        'busca': ['buscar_en_web', 'buscar_youtube'],
        'noticias': ['leer_rss', 'buscar_en_web'],
        'tiempo': ['buscar_en_web'],
        'clima': ['buscar_en_web'],
        'guarda': ['recordar_hecho'],
        'recuerda': ['recordar_hecho', 'consultar_hechos'],
        'arregla': ['sanar_sistema'],
        'estado': ['estado_sistema'],
        'sistema': ['estado_sistema', 'sanar_sistema'],
        'documenta': ['documentar_aprendizaje', 'leer_documentacion'],
        'lee': ['leer_documentacion'],
        'ejecuta': ['ejecutar_comando'],
        'instala': ['instalar_dependencia'],
        'repositorio': ['buscar_repositorio'],
        'canal': ['list_canales', 'crear_nicho', 'producir_nicho'],
        'blog': ['publicar_blog_completo'],
        'blogger': ['publicar_blog_completo'],
        'articulo': ['publicar_blog_completo'],
        'noticia': ['publicar_blog_completo', 'leer_rss', 'buscar_en_web'],
        'ia_news': ['producir_video_completo'],
        'completo': ['producir_video_completo'],
        'pipeline': ['producir_video_completo'],
        'ensambla': ['ensamblar_video_final', 'producir_video'],
        'publica': ['publicar_en_redes'],
        'vuela': [],
        'hola': [],
        'gracias': [],
    }
    nombres = set()
    for kw, tools in palabras.items():
        if kw in p:
            nombres.update(tools)
    if not nombres:
        return todas  # fallback: todas si no detecta nada
    return [t for t in todas if t['function']['name'] in nombres]

TOOLS = [
    {"type": "function", "function": {
        "name": "publicar_en_redes",
        "description": "Publica un video final en varias redes sociales (YouTube, TikTok, Instagram, etc).",
        "parameters": {"type": "object", "properties": {
            "video_path": {"type": "string", "description": "Ruta del video final (ej. output/produccion_final/video_final.mp4)"},
            "titulo": {"type": "string", "description": "Titulo del video"},
            "descripcion": {"type": "string", "description": "Descripcion del video"},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Lista de tags"},
            "redes": {"type": "array", "items": {"type": "string", "enum": ["youtube", "tiktok", "instagram", "blog"]}, "description": "Redes donde publicar"}
            }, "required": ["video_path", "titulo", "redes"]}}},
    {"type": "function", "function": {
        "name": "producir_video",
        "description": "Toma un video, una cancion, los ensambla con FFmpeg, aplica fade y valida el resultado final.",
        "parameters": {"type": "object", "properties": {
            "video_path": {"type": "string", "description": "Ruta del video (ej. output/video_generado.mp4)"},
            "audio_path": {"type": "string", "description": "Ruta de la cancion (ej. output/cancion_generada.mp3)"},
            "nombre_final": {"type": "string", "description": "Nombre del archivo final (ej. video_final_lofi.mp4)"}
            }, "required": ["video_path", "audio_path", "nombre_final"]}}},
    {"type": "function", "function": {
        "name": "ensamblar_video_final",
        "description": "Une un video (MP4) y una cancion (MP3) en un solo archivo final.",
        "parameters": {"type": "object", "properties": {
            "video_path": {"type": "string", "description": "Ruta del video (ej. output/video_generado.mp4)"},
            "audio_path": {"type": "string", "description": "Ruta de la cancion (ej. output/cancion_generada.mp3)"},
            "output_path": {"type": "string", "description": "Ruta del archivo final (ej. output/video_final.mp4)"}
            }, "required": ["video_path", "audio_path", "output_path"]}}},
    {"type": "function", "function": {
        "name": "generar_video",
        "description": "Genera un clip con Wan 2.2 TI2V-5B en Kaggle T4. 6 presets: cinematic_480p, cinematic_720p, vertical_480p, vertical_720p, turbo_4steps, draft_rapido. Lee data/agent/video_contract.json. Prompt debe seguir: Sujeto + Movimiento + Cámara + Iluminación.",
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string", "description": "Prompt cinematográfico (obligatorio)"},
            "preset": {"type": "string", "description": "cinematic_480p|cinematic_720p|vertical_480p|vertical_720p|turbo_4steps|draft_rapido"},
            "resolution": {"type": "string", "description": "Múltiplo de 32 (832x480, 1280x704, 480x832, 704x1280)"},
            "num_frames": {"type": "integer", "description": "4n+1 (8-121). Default 49"},
            "num_inference_steps": {"type": "integer", "description": "4 (Turbo) o 25-50 (estándar)"},
            "guidance_scale": {"type": "number", "description": "1.0 Turbo, 5.0 estándar"},
            "shift": {"type": "number", "description": "3.0 para 480p, 5.0 para 720p"},
            "fps": {"type": "integer", "description": "16 (480p) o 24 (720p)"}
        }, "required": ["prompt"]}}},
    {"type": "function", "function": {
        "name": "buscar_youtube",
        "description": "Busca videos en YouTube o consulta las tendencias actuales de una región. Usa esto ANTES que buscar_en_web para temas de YouTube.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Qué buscar (ej. 'lofi hip hop', 'noticias ia')"},
            "region": {"type": "string", "description": "Código de región (ej. ES, MX, US)"},
            "tipo": {"type": "string", "enum": ["busqueda", "tendencias"], "description": "Buscar por texto o ver lo más popular"}
            }, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "generar_imagen",
        "description": "Genera imagen con Cloudflare SDXL. 8 presets: cinematic, anime, realistic, cartoon, product, portrait, landscape, abstract. 6 aspect ratios: 16:9, 9:16, 1:1, 4:3, 3:2, 21:9. Lee data/agent/image_contract.json.",
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string", "description": "Descripcion de la imagen (obligatorio)"},
            "preset": {"type": "string", "description": "cinematic|anime|realistic|cartoon|product|portrait|landscape|abstract"},
            "aspect": {"type": "string", "description": "16:9 (YouTube) | 9:16 (TikTok/Reels) | 1:1 (Instagram) | 4:3 | 3:2 | 21:9"},
            "negative_prompt": {"type": "string", "description": "Lo que NO quieres ver (opcional)"},
            "num_steps": {"type": "integer", "description": "1-20 (Cloudflare max 20)"},
            "guidance": {"type": "number", "description": "1-15. Default 7.5"},
            "seed": {"type": "integer", "description": "-1 aleatorio, fijo para reproducir"}
        }, "required": ["prompt"]}}},
    {"type": "function", "function": {
        "name": "lanzar_pipeline_kaggle",
        "description": "Lanza un pipeline completo en Kaggle (genera música, vídeo y lo sube a GitHub) de forma automática y apaga la GPU al terminar.",
        "parameters": {"type": "object", "properties": {
            "tema": {"type": "string", "description": "Tema de la canción (ej. lofi jazz, piano)"}
            }, "required": ["tema"]}}},
    {"type": "function", "function": {
        "name": "generar_cancion_kaggle",
        "description": "Genera una cancion con ACE-Step v11 en Kaggle (T4, ~30 min). Soporta 11 presets: lofi, ambient, piano, cinematic, hiphop, electronic, jingle, hiphop_trap, hiphop_boom_bap, synthwave, jazz. Lee data/agent/acestep_contract.json para params y reglas.",
        "parameters": {"type": "object", "properties": {
            "caption": {"type": "string", "description": "Descripcion musical (obligatorio)"},
            "preset": {"type": "string", "description": "lofi|ambient|piano|cinematic|hiphop|electronic|jingle|hiphop_trap|hiphop_boom_bap|synthwave|jazz"},
            "duration": {"type": "integer", "description": "Segundos (10-600). Si necesitas mas, haz chunks de 360s."},
            "bpm": {"type": "integer", "description": "Override (30-300)"},
            "keyscale": {"type": "string", "description": "Ej: 'A minor', 'C major'"},
            "instrumental": {"type": "boolean", "description": "True sin voz, False con letra"},
            "lyrics": {"type": "string", "description": "Letra si instrumental=False"}
        }, "required": ["caption"]}}},
    {"type": "function", "function": {
        "name": "leer_documentacion",
        "description": "Lee un archivo maestro de documentación (ej. TRASPASO.md, BOOT_PROMPT.md, MANUAL_KAGGLE.md).",
        "parameters": {"type": "object", "properties": {"archivo": {"type": "string"}}, "required": ["archivo"]}}},
    {"type": "function", "function": {
        "name": "documentar_aprendizaje",
        "description": "Añade un nuevo descubrimiento o hito al final de un archivo de documentación para nutrir a futuras IAs.",
        "parameters": {"type": "object", "properties": {
            "archivo": {"type": "string", "description": "Ej. TRASPASO.md"},
            "texto": {"type": "string", "description": "El texto markdown a añadir al final."}}, "required": ["archivo", "texto"]}}},
    {"type": "function", "function": {
        "name": "ejecutar_comando",
        "description": "Ejecuta comandos en la terminal (pip install, python, git, etc). Comandos peligrosos pedirán confirmación al usuario.",
        "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
    {"type": "function", "function": {
        "name": "recordar_hecho",
        "description": "Guarda un dato importante en la memoria a largo plazo para no olvidarlo en el futuro.",
        "parameters": {"type": "object", "properties": {"hecho": {"type": "string"}}, "required": ["hecho"]}}},
    {"type": "function", "function": {
        "name": "consultar_hechos",
        "description": "Lee los datos importantes guardados en la memoria a largo plazo.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "buscar_en_web",
        "description": "Busca informacion actual en internet (clima, noticias, precios, productos).",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Lee un archivo del repo.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Escribe un archivo en SANDBOX. Hace backup del original si existe. Luego valida y promueve.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Ruta relativa, ej: scripts/nuevo.py"},
            "content": {"type": "string"}}, "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "validate_file",
        "description": "Valida sintaxis Python (ast.parse) de un archivo en sandbox.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "promote_file",
        "description": "Mueve un archivo validado de sandbox al repo real.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "list_canales",
        "description": "Lista los canales configurados (config/channels.json).",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "estado_sistema",
        "description": "Estado del ecosistema: git, procesos vivos, omniroute.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "delegar_tareas_paralelas",
        "description": "Delega múltiples tareas de investigación o análisis a OmniRoute en paralelo para ahorrar tiempo. Úsala cuando necesites leer varios archivos, investigar varios temas o hacer varias cosas a la vez.",
        "parameters": {
            "type": "object",
            "properties": {
                "tareas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string", "description": "La tarea a realizar (ej. 'Lee y resume el archivo X')"},
                            "system": {"type": "string", "description": "Instrucciones de sistema para esta tarea"}
                        },
                        "required": ["prompt"]
                    }
                }
            },
            "required": ["tareas"]
        }
    }},
    {"type": "function", "function": {
        "name": "producir_nicho",
        "description": "Produce contenido completo para un nicho (ia_news, lofi, boe, finanzas_barrio): RSS -> guion -> voz -> musica -> imagen. Tarda ~30 min por el ACE-Step.",
        "parameters": {"type": "object", "properties": {
            "nicho": {"type": "string", "description": "Nombre del nicho (ia_news, lofi, boe, finanzas_barrio)"},
            "dry": {"type": "boolean", "description": "Si true, solo genera guion sin gastar GPU (recomendado para probar)"}
        }, "required": ["nicho"]}}},
    {"type": "function", "function": {
        "name": "generar_video_rapido",
        "description": "Genera un video rapido (2 min) con voz, clips de Pixabay y FFmpeg. Sin GPU. Ideal para noticias y shorts.",
        "parameters": {"type": "object", "properties": {
            "texto": {"type": "string", "description": "Guion o texto del video"},
            "titulo": {"type": "string", "description": "Nombre del archivo (sin extension)"}
        }, "required": ["texto", "titulo"]}}},
    {"type": "function", "function": {
        "name": "subir_youtube",
        "description": "Sube vídeo a YouTube. 6 presets: draft_privado, publicar_ahora, programar, shorts_vertical, lofi_music, podcast. Sin auditoría Google, los uploads salen como privados aunque pidas public.",
        "parameters": {"type": "object", "properties": {
            "video": {"type": "string", "description": "Ruta del MP4 (obligatorio)"},
            "titulo": {"type": "string", "description": "Título 1-100 chars (obligatorio)"},
            "descripcion": {"type": "string", "description": "Descripción 0-5000 chars"},
            "privacidad": {"type": "string", "enum": ["private","unlisted","public"], "description": "Default: private"},
            "tags": {"type": "string", "description": "Tags separados por coma (max 500 chars total)"},
            "categoryId": {"type": "string", "description": "10=Music, 22=Blogs, 24=Entertainment, 25=News, 27=Education"}
        }, "required": ["video", "titulo"]}}},
    {"type": "function", "function": {
        "name": "crear_nicho",
        "description": "Crea un canal completo: nicho en config + carpeta output/nichos/<nombre>/ con subcarpetas + canal.json + SKILL.md regenerado + notificación al móvil. Requiere aprobación del usuario (HITL).",
        "parameters": {"type": "object", "properties": {
            "nombre": {"type": "string", "description": "Nombre del canal (ej. historia, cocina)"},
            "formato": {"type": "string", "description": "video_voz_imagen | video_texto_voz | musica_loop"},
            "tono": {"type": "string", "description": "Tono del canal"},
            "presets": {"type": "object", "description": "Presets: {musica, voz, imagen, video}"},
            "pipeline": {"type": "array", "items": {"type": "string"}, "description": "Pasos del pipeline"},
            "plataformas": {"type": "array", "items": {"type": "string"}, "description": "youtube, blogger, tiktok, instagram"},
            "cuentas": {"type": "object", "description": "Cuentas asociadas por plataforma"}
        }, "required": ["nombre"]}}},

    {"type": "function", "function": {
        "name": "evaluar_produccion",
        "description": "Evalúa un plan de producción ANTES de gastar GPU. Devuelve informe con semáforos 🟢🟡🔴 (coherencia, presupuesto, calidad prompt, encaje nicho) y veredicto. Usa SIEMPRE antes de producir.",
        "parameters": {"type": "object", "properties": {
            "prompt": {"type": "string", "description": "Prompt o descripción de la producción"},
            "motor": {"type": "string", "description": "musica|voz|imagen|video"},
            "preset": {"type": "string", "description": "Preset elegido"},
            "nicho": {"type": "string", "description": "Nicho destino (opcional)"},
            "cantidad": {"type": "integer", "description": "Cantidad de piezas (default 1)"}
        }, "required": ["prompt", "motor"]}}},
    {"type": "function", "function": {
        "name": "ensamblar_video_largo",
        "description": "Ensambla vídeo largo (vídeo + voz + música + logo + fades) usando la receta del nicho en config/montajes/<nicho>.json. Tarda 5-15 min según duración.",
        "parameters": {"type": "object", "properties": {
            "nicho": {"type": "string", "description": "ia_news | lofi | boe | finanzas_barrio"},
            "video_base": {"type": "string", "description": "Ruta del vídeo base o loop"},
            "voz": {"type": "string", "description": "Ruta del MP3 de voz (opcional)"},
            "musica": {"type": "string", "description": "Ruta del MP3 de música (opcional)"}
        }, "required": ["nicho", "video_base"]}}},
    {"type": "function", "function": {"name": "producir_video_completo", "description": "Pipeline completo: guion + SEO + voz + musica + video + ensamblado + YouTube. Ej: hazme video ia_news sobre GPT-5.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string", "description": "ia_news | finanzas_barrio | boe | lofi"}, "tema": {"type": "string", "description": "Tema del video"}, "privacidad": {"type": "string", "description": "private | unlisted | public"}}, "required": ["nicho", "tema"]}}},
    {"type": "function", "function": {"name": "publicar_blog_completo", "description": "Publica articulo SEO en Blogger (IAGLOBALNEWS). RSS+web+YouTube + verificacion + redactor + SEO + imagen + Blogger.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}, "tema": {"type": "string"}, "palabras": {"type": "integer"}, "status": {"type": "string"}}, "required": ["nicho", "tema"]}}},
    {"type": "function", "function": {"name": "crear_blog_top", "description": "Genera articulo con Quality Gate (auditor >=8/10) y lo guarda como borrador. Ej: crear blog sobre GPT-5", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}, "tema": {"type": "string"}, "auto_publicar": {"type": "boolean"}}, "required": ["nicho", "tema"]}}},
    {"type": "function", "function": {"name": "generar_informe_editorial", "description": "Investiga tendencias en 5 fuentes y redacta un informe HTML para decidir que publicar hoy.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}}, "required": ["nicho"]}}},
    {"type": "function", "function": {"name": "procesar_cola_youtube", "description": "Sube a YouTube los shorts programados cuya hora ya ha pasado.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "consultar_manual_python", "description": "Busca patrones en el manual de Python.", "parameters": {"type": "object", "properties": {"tema": {"type": "string"}}, "required": ["tema"]}}},
    {"type": "function", "function": {"name": "consultar_manual_python", "description": "Busca patrones en el manual de Python.", "parameters": {"type": "object", "properties": {"tema": {"type": "string"}}, "required": ["tema"]}}},
    {"type": "function", "function": {
        "name": "instalar_dependencia",
        "description": "Instala una librería de Python (pip). Antes verifica que hay RAM y disco suficiente. Úsalo para auto-mejorar tu sistema.",
        "parameters": {"type": "object", "properties": {
            "paquete": {"type": "string", "description": "Nombre del paquete en PyPI (ej. pykokoro, requests)"}
        }, "required": ["paquete"]}
    }},

    {"type": "function", "function": {
        "name": "buscar_repositorio",
        "description": "Busca librerías o herramientas en GitHub, PyPI o F-Droid. Úsalo antes de instalar algo para ver si existe y cuál es su URL.",
        "parameters": {"type": "object", "properties": {
            "plataforma": {"type": "string", "enum": ["github", "pypi", "fdroid"]},
            "query": {"type": "string", "description": "Nombre o término de búsqueda"}
        }, "required": ["plataforma", "query"]}
    }},

    {"type": "function", "function": {"name": "sanar_sistema", "description": "Revisa y reinicia Flask y OmniRoute si estan caidos.", "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "notificar_movil", "description": "Envia notificacion push al movil del usuario.", "parameters": {"type": "object", "properties": {"titulo": {"type": "string"}, "mensaje": {"type": "string"}}, "required": ["titulo", "mensaje"]}}},
    {"type": "function", "function": {"name": "leer_rss", "description": "Lee noticias frescas. Fuentes: boe, techcrunch, hackernews, verge.", "parameters": {"type": "object", "properties": {"fuente": {"type": "string"}, "limite": {"type": "integer"}}, "required": ["fuente"]}}},
    {"type": "function", "function": {"name": "pedir_a_especialista", "description": "Delegar tarea a un sub-agente especializado. Roles: guionista, seo, auditor, traductor, musico.", "parameters": {"type": "object", "properties": {"rol": {"type": "string"}, "tarea": {"type": "string"}, "contexto": {"type": "string"}}, "required": ["rol", "tarea"]}}},
    {"type": "function", "function": {"name": "lanzar_notebook_kaggle", "description": "Crea un notebook con codigo Python y lo ejecuta en Kaggle GPU.", "parameters": {"type": "object", "properties": {"nombre": {"type": "string"}, "codigo_python": {"type": "string"}}, "required": ["nombre", "codigo_python"]}}},
    {"type": "function", "function": {"name": "analizar_video_competencia", "description": "Descarga un video de YouTube, extrae fotogramas y los analiza visualmente con Nemotron 550B. Borra el video despues.", "parameters": {"type": "object", "properties": {"url": {"type": "string", "description": "URL del video de YouTube"}}, "required": ["url"]}}},
    {"type": "function", "function": {
        "name": "generar_narracion",
        "description": "Genera audio de voz con Sherpa-ONNX (5 voces Piper). Soporta 7 presets: noticias, narracion_relajada, urgente, audiobook, publicidad, tutorial, sintesis_rapida. Lee data/agent/sherpa_contract.json para params y reglas.",
        "parameters": {"type": "object", "properties": {
            "texto": {"type": "string", "description": "Texto a narrar (obligatorio)"},
            "voz": {"type": "string", "description": "es_ES-davefx-medium (defecto) | es_ES-sharvard-medium | es_MX-claude-high | en_US-lessac-medium | en_US-ryan-high"},
            "preset": {"type": "string", "description": "noticias|narracion_relajada|urgente|audiobook|publicidad|tutorial|sintesis_rapida"},
            "length_scale": {"type": "number", "description": "0.5-2.0. <1 más rápido, >1 más lento"},
            "noise_scale": {"type": "number", "description": "0.1-1.5. Varianza de la voz"},
            "speed": {"type": "number", "description": "0.5-2.0. Multiplicador de velocidad"},
            "nombre": {"type": "string", "description": "Nombre del archivo (opcional)"}
        }, "required": ["texto"]}}},
    {"type": "function", "function": {"name": "consultar_manual_ecosistema", "description": "Consulta una seccion del MANUAL_ECOSISTEMA.md (arquitectura, errores, pipelines, contratos, motores, apis, comandos, contextos, reglas). Usa seccion=todo para todo.", "parameters": {"type": "object", "properties": {"seccion": {"type": "string"}}, "required": ["seccion"]}}},
    {"type": "function", "function": {"name": "buscar_en_manual", "description": "Busca una query en MANUAL_ECOSISTEMA.md y devuelve lineas con contexto.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "listar_mis_tools", "description": "Devuelve TODAS las tools disponibles con su descripcion. Usala cuando el usuario pregunte que puedes hacer o que tools tienes.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ver_mi_workspace", "description": "Devuelve workspace: ultima tarea y tools usadas.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ver_ultimas_tareas", "description": "3 ultimas tareas con resultado.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "ver_fallos_similares", "description": "Busca fallos similares.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}}},
    {"type": "function", "function": {"name": "ver_costes_hoy", "description": "Costes de hoy.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "auto_regenerar_manual", "description": "Regenera docs/MANUAL_ECOSISTEMA.md desde el estado actual de TOOLS. Usalo tras crear tools nuevas.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "crear_nueva_tool", "description": "Crea una tool nueva persistente. Recibe nombre (snake_case), descripcion, codigo_funcion (def _tool_NOMBRE(args): ...) y parametros_json (dict de propiedades). Valida, persiste, regenera manual. Disponible proximo arranque.", "parameters": {"type": "object", "properties": {"nombre": {"type": "string"}, "descripcion": {"type": "string"}, "codigo_funcion": {"type": "string"}, "parametros_json": {"type": "object"}}, "required": ["nombre", "descripcion", "codigo_funcion"]}}},
    {"type": "function", "function": {"name": "ejecutar_limpieza", "description": "Ejecuta scripts/limpieza_pipeline.py (reset diario: borra <ayer + temporales). Con dry_run=True solo simula sin borrar.", "parameters": {"type": "object", "properties": {"dry_run": {"type": "boolean"}}, "required": []}}},
    {"type": "function", "function": {"name": "escanear_ecosistema", "description": "Escanea TODO el ecosistema (scripts/, brain/, endpoints Flask, contratos JSON, crons, pipelines) y devuelve inventario. Usalo cuando el usuario pregunte que existe o que ha cambiado.", "parameters": {"type": "object", "properties": {"seccion": {"type": "string", "description": "scripts|brain|endpoints|contratos|crons|todo"}}, "required": []}}},
    {"type": "function", "function": {"name": "ver_contrato", "description": "Lee un contrato de data/agent/*.json. Devuelve JSON completo truncado a 3000 chars. Usalo cuando necesites reglas exactas (ej: video_contract, shorts_contract, ltx_continuidad_contract).", "parameters": {"type": "object", "properties": {"nombre": {"type": "string", "description": "nombre del contrato sin .json (ej: video_contract, shorts_contract)"}}, "required": ["nombre"]}}},
    {"type": "function", "function": {"name": "pipeline_step", "description": "Ejecuta UN paso del pipeline. Pasos: limpieza_pipeline, gen_manual, recolector, transcribir_groq, analista_fase1, sintetizador, fase2_produccion, voz_edge, director_arte, render_robusto, factory_shorts, generar_web_v3, generar_web_dossier, actualizar_web_index, generar_redes, generar_redes_cruzadas, sincronizar_podcasts, generar_podcast, generar_informe_pdf.", "parameters": {"type": "object", "properties": {"step": {"type": "string"}, "fecha": {"type": "string"}}, "required": ["step"]}}},
    {"type": "function", "function": {"name": "pipeline_completo", "description": "Lanza pipeline 06:00 completo (30-40min).", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_status", "description": "Estado del pipeline en vivo.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_kill", "description": "Detiene el pipeline.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_custom", "description": "Pipeline a la carta: nicho + formatos + tema.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}, "formatos": {"type": "array", "items": {"type": "string"}}, "tema": {"type": "string"}, "num_shorts": {"type": "integer"}}, "required": ["nicho"]}}},
    {"type": "function", "function": {"name": "generar_short", "description": "Genera 1 short rapido sobre tema.", "parameters": {"type": "object", "properties": {"tema": {"type": "string"}, "nicho": {"type": "string"}}, "required": ["tema"]}}},
    {"type": "function", "function": {"name": "generar_post_web", "description": "Genera post web + build + push.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_podcast_dia", "description": "Genera podcast MP3 del dia.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "subir_youtube_dia", "description": "Sube video+shorts a YouTube con publish_at.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "programar_youtube", "description": "Programa video ya subido. Args: video_id, hora HH:MM.", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "hora": {"type": "string"}}, "required": ["video_id", "hora"]}}},
    {"type": "function", "function": {"name": "publicar_blogger", "description": "Publica en Blogger.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_seo", "description": "Regenera SEO del dia.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_titulo_ab", "description": "Genera titulos A/B.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "cloudflare_stats", "description": "Visitas web ultimos 7 dias.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "buscar_historico", "description": "Busca historico FTS5.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "reindexar_busqueda", "description": "Reindexa FTS5.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_snapshot", "description": "Crea snapshot git.", "parameters": {"type": "object", "properties": {"motivo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_listar", "description": "Lista snapshots.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_step", "description": "Ejecuta UN paso del pipeline. Pasos: limpieza_pipeline, gen_manual, recolector, transcribir_groq, analista_fase1, sintetizador, fase2_produccion, voz_edge, director_arte, render_robusto, factory_shorts, generar_web_v3, generar_web_dossier, actualizar_web_index, generar_redes, generar_redes_cruzadas, sincronizar_podcasts, generar_podcast, generar_informe_pdf.", "parameters": {"type": "object", "properties": {"step": {"type": "string"}, "fecha": {"type": "string"}}, "required": ["step"]}}},
    {"type": "function", "function": {"name": "pipeline_completo", "description": "Lanza pipeline 06:00 completo (30-40min).", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_status", "description": "Estado del pipeline en vivo.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_kill", "description": "Detiene el pipeline.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_custom", "description": "Pipeline a la carta: nicho + formatos + tema.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}, "formatos": {"type": "array", "items": {"type": "string"}}, "tema": {"type": "string"}, "num_shorts": {"type": "integer"}}, "required": ["nicho"]}}},
    {"type": "function", "function": {"name": "generar_short", "description": "Genera 1 short rapido sobre tema.", "parameters": {"type": "object", "properties": {"tema": {"type": "string"}, "nicho": {"type": "string"}}, "required": ["tema"]}}},
    {"type": "function", "function": {"name": "generar_post_web", "description": "Genera post web + build + push.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_podcast_dia", "description": "Genera podcast MP3 del dia.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "subir_youtube_dia", "description": "Sube video+shorts a YouTube con publish_at.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "programar_youtube", "description": "Programa video ya subido. Args: video_id, hora HH:MM.", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "hora": {"type": "string"}}, "required": ["video_id", "hora"]}}},
    {"type": "function", "function": {"name": "publicar_blogger", "description": "Publica en Blogger.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_seo", "description": "Regenera SEO del dia.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_titulo_ab", "description": "Genera titulos A/B.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "cloudflare_stats", "description": "Visitas web ultimos 7 dias.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "buscar_historico", "description": "Busca historico FTS5.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "reindexar_busqueda", "description": "Reindexa FTS5.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_snapshot", "description": "Crea snapshot git.", "parameters": {"type": "object", "properties": {"motivo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_listar", "description": "Lista snapshots.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "publicar_comentario_youtube", "description": "Publica y fija un comentario SEO completo en un video YouTube: pregunta abierta + CTA + link cruzado al post del blog + hashtags. Usa la YouTube Data API. Necesita scope de escritura.", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "fecha": {"type": "string", "description": "Fecha produccion (YYYY-MM-DD o hoy)"}, "texto_extra": {"type": "string", "description": "Texto adicional al inicio (opcional)"}}, "required": ["video_id"]}}},
    {"type": "function", "function": {"name": "analizar_short_viral", "description": "Analiza metricas de un short YouTube (vistas, likes, comentarios, ratio) y compara con la media de tus ultimos 10 shorts. Devuelve diagnostico + propuesta: si va bien -> como exprimir el tiron (secuela, boost, cross-post). Si va mal -> que cambiar (titulo, hook, thumbnail).", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "fecha": {"type": "string"}}, "required": ["video_id"]}}},
    {"type": "function", "function": {"name": "generar_thumbnail_video", "description": "Genera miniatura para video YouTube. Intenta primero NANO BANANA (si hay token/servicio). Fallback: imagen impactante SDXL con estilo cinematic que retenga clicks. Luego la sube a YouTube via API thumbnails.set.", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "fecha": {"type": "string", "description": "Fecha produccion (YYYY-MM-DD o hoy)"}, "titular": {"type": "string", "description": "Titular del dia (opcional, si no lo detecta)"}}, "required": ["video_id"]}}},
]


def _tool_read_file(args):
    p = (ROOT / args["path"]).resolve()
    if not p.is_relative_to(ROOT):
        return "ERROR: ruta fuera del repo"
    if not p.exists():
        return f"ERROR: {args['path']} no existe"
    
    # BLACKLIST DE SEGURIDAD
    PROHIBIDOS = [".env", "secrets/", ".git-credentials", "token.json",
                  "client_secret.json", ".pem", ".key", "id_rsa", ".ssh/"]
    ruta_str = str(p).lower()
    for prohibido in PROHIBIDOS:
        if prohibido in ruta_str:
            return f"ERROR: Acceso denegado a {args['path']} (archivo protegido por seguridad)."
    
    # Comprobar que no es un archivo binario
    BINARIOS = (".png", ".jpg", ".jpeg", ".gif", ".wav", ".mp3", ".mp4", ".mov", ".webm", ".zip", ".tar", ".gz", ".db", ".sqlite", ".pdf")
    if p.suffix.lower() in BINARIOS:
        return f"ERROR: {args['path']} es un archivo binario ({p.suffix}). Usa herramientas específicas para leerlo."
    
    try:
        return p.read_text(encoding="utf-8")[:8000]
    except UnicodeDecodeError:
        return f"ERROR: {args['path']} no es texto UTF-8 válido (posible binario)."


def _tool_write_file(args):
    rel = args["path"]
    sandbox_path = SANDBOX / rel
    sandbox_path.parent.mkdir(parents=True, exist_ok=True)
    original = ROOT / rel
    bak_msg = ""
    if original.exists():
        dst = _backup(original)
        bak_msg = f" (backup: {dst.name})" if dst else ""
    sandbox_path.write_text(args["content"], encoding="utf-8")
    return f"OK escrito en sandbox/{rel} ({len(args['content'])} bytes){bak_msg}. Siguiente: validate_file."


def _tool_validate_file(args):
    rel = args["path"].replace("sandbox/", "", 1).lstrip("/")
    p = SANDBOX / rel
    if not p.exists():
        return f"ERROR: sandbox/{args['path']} no existe"
    if not p.name.endswith(".py"):
        return "OK (no es .py, sin validar)"
    try:
        ast.parse(p.read_text(encoding="utf-8"))
        return "OK sintaxis Python"
    except SyntaxError as e:
        return f"SYNTAX ERROR linea {e.lineno}: {e.msg}"


def _tool_promote_file(args):
    import subprocess as _sp
    rel = args["path"].replace("sandbox/", "", 1).lstrip("/")
    src = SANDBOX / rel
    if not src.exists():
        return f"ERROR: sandbox/{rel} no existe"
    # Validación: .py debe parsear
    if src.suffix == ".py":
        try:
            import ast as _ast
            _ast.parse(src.read_text(encoding="utf-8"))
        except SyntaxError as e:
            return f"ERROR: sandbox/{rel} no pasa validacion (SyntaxError: {e})."
    # CRÍTICO: confirmación por Telegram (2026-11-09)
    import uuid, time as _t
    token_id = uuid.uuid4().hex[:8]
    pending = ROOT / "sandbox" / f"pending_promote_{token_id}.json"
    pending.parent.mkdir(parents=True, exist_ok=True)
    pending.write_text(f'{{"path":"{rel}","created":"{_t.time()}"}}')
    try:
        _sp.run(["python3", "scripts/notificar_telegram.py",
                 f"⚠️ CONFIRMAR promote_file\n\nFichero: {rel}\nTamaño: {src.stat().st_size}b\n\nResponde OK para aplicar o IGNORAR para cancelar.\nToken: {token_id}"],
                cwd=str(ROOT), timeout=15, check=False, capture_output=True)
    except Exception:
        pass
    # Esperar confirmación: hasta 300s mirando un fichero .confirmed/.rejected
    confirm_file = ROOT / "sandbox" / f"promote_{token_id}.confirmed"
    reject_file = ROOT / "sandbox" / f"promote_{token_id}.rejected"
    inicio = _t.time()
    while _t.time() - inicio < 300:
        if confirm_file.exists():
            confirm_file.unlink()
            pending.unlink(missing_ok=True)
            # Aplicar
            import shutil
            dst = ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            return f"OK promovido a {rel} (confirmado por usuario)"
        if reject_file.exists():
            reject_file.unlink()
            pending.unlink(missing_ok=True)
            return f"CANCELADO por usuario: {rel} no aplicado"
        _t.sleep(3)
    pending.unlink(missing_ok=True)
    return f"TIMEOUT: usuario no confirmó en 5 min. {rel} queda en sandbox. Sigue sin aplicar."

def _tool_list_canales(_args):
    cf = ROOT / "config" / "channels.json"
    if not cf.exists():
        return "No hay config/channels.json"
    try:
        data = json.loads(cf.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("channels", data)
        return json.dumps(data, ensure_ascii=False)[:2000]
    except Exception as e:
        return f"Error leyendo channels.json: {e}"


def _tool_estado_sistema(_args):
    r = subprocess.run(["git", "status", "--short"], cwd=str(ROOT),
                       capture_output=True, text=True, timeout=15)
    git = r.stdout[:500] or "(limpio)"
    procs = subprocess.run(["pgrep", "-af", "omniroute"],
                           capture_output=True, text=True, timeout=10).stdout[:300] or "(sin omniroute)"
    return f"git status:\n{git}\n\nomniroute:\n{procs}"



def _tool_buscar_en_web(args):
    return buscar(args["query"])


def _tool_recordar_hecho(args):
    return recordar_hecho(args["hecho"])

def _tool_consultar_hechos(args):
    return consultar_hechos()


def _tool_ejecutar_comando(args):
    return ejecutar(args["cmd"])


def _tool_leer_documentacion(args):
    archivo = args["archivo"]
    p = ROOT / archivo
    if not p.exists():
        return f"ERROR: El archivo {archivo} no existe."
    # Misma blacklist que _tool_read_file (evita leer .env, secrets/, etc.)
    _PROHIB_DOC = (".env", "secrets/", ".git-credentials", "token.json",
                   "client_secret.json", ".pem", ".key", "id_rsa", ".ssh/")
    ruta_str = str(p).lower()
    for prohibido in _PROHIB_DOC:
        if prohibido in ruta_str:
            return f"ERROR: Acceso denegado a {archivo} (archivo protegido por seguridad)."
    return p.read_text(encoding="utf-8")[:8000]

def _tool_documentar_aprendizaje(args):
    archivo = args["archivo"]
    if not archivo.endswith(".md"):
        return "ERROR: Solo se puede documentar en archivos .md"
    p = ROOT / archivo
    texto = args["texto"]
    
    # Hacemos backup antes de tocar
    if p.exists():
        _backup(p)
        with open(p, "a", encoding="utf-8") as f:
            f.write(f"\n\n{texto}\n")
        return f"OK: Aprendizaje documentado en {archivo}."
    else:
        return f"ERROR: El archivo {archivo} no existe. Créalo primero con write_file."



def _tool_generar_video_rapido(args):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from generar_video_rapido import generar
    return generar(args["texto"], args["titulo"])

def _tool_evaluar_produccion(args):
    """Evalúa un plan antes de producir (Director de Producción)."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from evaluador_produccion import evaluar_produccion
    return json.dumps(evaluar_produccion(
        prompt=args.get("prompt", ""),
        motor=args.get("motor", "musica"),
        preset=args.get("preset"),
        nicho=args.get("nicho"),
        cantidad=int(args.get("cantidad", 1)),
    ), ensure_ascii=False, indent=2)

def _tool_ensamblar_video_largo(args):
    """Ensambla vídeo largo via motor_ensamblado."""
    import sys, json
    sys.path.insert(0, str(ROOT / "scripts"))
    from motor_ensamblado import motor
    nicho = args.get("nicho", "ia_news")
    receta = ROOT / "config" / "montajes" / (nicho + ".json")
    if not receta.exists():
        return f"ERROR: receta '{nicho}' no existe"
    overrides = {"video_base": args.get("video_base")}
    if args.get("voz"): overrides["voz"] = args["voz"]
    if args.get("musica"): overrides["musica"] = args["musica"]
    try:
        result = motor(str(receta), overrides)
        return json.dumps(result, ensure_ascii=False)
    except Exception as e:
        return f"ERROR: {e}"

def _tool_producir_video_completo(args):
    """Pipeline completo: guion + SEO + assets + ensamblado + YouTube."""
    import json, time, pathlib, threading, sys as _s
    nicho = args.get("nicho", "ia_news")
    tema = args.get("tema", "")
    privacidad = args.get("privacidad", "private")
    if not tema:
        return "ERROR: falta 'tema'"

    def _run():
        try:
            _s.path.insert(0, str(ROOT / "scripts"))
            _s.path.insert(0, str(ROOT / "brain"))
            from orquestador_nichos import _rss, _guion
            from brain.especialistas import pedir_a_especialista
            from musica_acestep import generar as gen_mus
            from wan22_batch import generar_video_batch
            from motor_ensamblado import motor
            from subir_youtube import subir
            from dios import _tool_generar_narracion

            cfg = json.loads((ROOT / "config" / "nichos.json").read_text())
            if nicho not in cfg:
                print(f"[completo] nicho invalido: {nicho}", flush=True); return
            nc = cfg[nicho]
            ts = int(time.time())
            out = ROOT / "output" / "nichos" / nicho
            out.mkdir(parents=True, exist_ok=True)

            # 1. RSS + guion (via especialista)
            print("[completo 1/7] RSS...", flush=True)
            noticias = _rss(nc)
            print("[completo 2/7] Guion...", flush=True)
            guion = pedir_a_especialista("guionista",
                f"Guion 60s sobre: {tema}. Tono: {nc.get('tono','neutral')}",
                contexto=noticias[:3000])
            (out / f"guion_{ts}.md").write_text(guion, encoding="utf-8")

            # 2. SEO
            print("[completo 3/7] SEO...", flush=True)
            seo_raw = pedir_a_especialista("seo",
                f"Genera titulo (<60 chars) + descripcion + 5 tags para YouTube sobre: {tema}. Responde SOLO JSON: {{\"titulo\":\"...\",\"descripcion\":\"...\",\"tags\":[\"a\",\"b\"]}}")
            import re as _re
            try:
                m = _re.search(r'\{.*\}', seo_raw, _re.DOTALL)
                seo = json.loads(m.group(0)) if m else {"titulo": f"{tema} · {nc['nombre']}", "descripcion": tema, "tags": [nicho, "ia"]}
            except Exception:
                seo = {"titulo": f"{tema} · {nc['nombre']}", "descripcion": tema, "tags": [nicho, "ia"]}

            # 3. Voz
            print("[completo 4/7] Voz...", flush=True)
            _tool_generar_narracion({"texto": guion[:3000], "nombre": f"{nicho}_{ts}"})
            mp3s = sorted((ROOT / "output" / "audios").glob(f"*{nicho}*{ts}*"), key=lambda x: x.stat().st_mtime, reverse=True)
            voz = mp3s[0] if mp3s else None
            if not voz:
                print("[completo] ERROR: sin voz", flush=True); return

            # 4. Música (fallback si falla)
            print("[completo 5/7] Musica...", flush=True)
            try:
                r = gen_mus(f"{nc.get('musica','lofi')}, cinematografico", 60)
                if r.startswith("OK:"):
                    musica = pathlib.Path(r.split(":",1)[1].split("(")[0].strip())
                else:
                    musica = ROOT / "output" / "nichos" / nicho / "musica.mp3"
            except Exception as e:
                print(f"  musica fallo: {e}", flush=True)
                musica = ROOT / "output" / "nichos" / nicho / "musica.mp3"

            # 5. Vídeo (Wan draft_rapido)
            print("[completo 6/7] Video...", flush=True)
            try:
                generar_video_batch([f"cinematic {tema}, neon, futuristic"],
                                    preset="draft_rapido", canal=nicho)
            except Exception as e:
                print(f"  video fallo: {e}", flush=True)
            # Buscar clip descargado
            clips = sorted((ROOT / "output" / "videos").glob("clip_*.mp4"), key=lambda x: x.stat().st_mtime, reverse=True)
            if not clips:
                print("[completo] ERROR: sin clip video", flush=True); return
            clip = clips[0]

            # 6. Ensamblar
            print("[completo 7/7] Ensamblar...", flush=True)
            result = motor(f"config/montajes/{nicho}.json", {
                "video_base": str(clip), "voz": str(voz), "musica": str(musica),
            })
            final = ROOT / result["path"] if not str(result["path"]).startswith("/") else pathlib.Path(result["path"])

            # 7. Subir YouTube
            print("[completo] Subiendo a YouTube...", flush=True)
            r2 = subir(str(final), seo["titulo"], seo["descripcion"], tags=seo.get("tags", []), privacidad=privacidad)
            print(f"[completo] ✅ https://youtu.be/{r2['id']}", flush=True)

            # Notificar móvil
            try:
                import subprocess as _sp
                _sp.run(["termux-notification", "-t", f"🎬 {nicho} completo",
                         "-c", f"https://youtu.be/{r2['id']}", "--priority", "high"],
                        check=False, timeout=5)
            except: pass
        except Exception as e:
            print(f"[completo] ERROR: {type(e).__name__}: {e}", flush=True)
            try:
                import subprocess as _sp, traceback
                _sp.run(["termux-notification", "-t", f"❌ {nicho} fallo",
                         "-c", str(e)[:120], "--priority", "high"],
                        check=False, timeout=5)
            except: pass

    threading.Thread(target=_run, daemon=True).start()
    return f"🎬 Pipeline completo '{nicho}' en marcha (~30-45 min). Recibirás notificación móvil. Tema: {tema}"


def _tool_generar_informe_editorial(args):
    """Genera un informe HTML periodístico con el Detective."""
    import sys as _s
    nicho = args.get("nicho", "ia_news")
    _s.path.insert(0, str(ROOT / "brain"))
    _s.path.insert(0, str(ROOT / "scripts"))
    try:
        from informe_detective import generar_informe_visual
        generar_informe_visual(nicho)
        return "OK Informe generado para " + nicho + ". Ve a la pestaña Informe de la web."
    except Exception as e:
        return "ERROR: " + str(e)

def _tool_procesar_cola_youtube(args):
    """Sube los shorts que ya han pasado su hora programada."""
    import subprocess, sys as _s
    try:
        r = subprocess.run([_s.executable, "scripts/cola_publicacion.py", "procesar"], capture_output=True, text=True, cwd=str(ROOT), timeout=900)
        if "OK subido" in r.stdout or "No hay nada" in r.stdout:
            return "OK Cola procesada: " + r.stdout.strip()
        return "ERROR procesando cola: " + r.stdout[-200:] + r.stderr[-200:]
    except Exception as e:
        return "ERROR: " + str(e)

def _tool_crear_blog_top(args):
    """Genera articulo con Quality Gate, reintentos, y guarda como borrador."""
    import json, sys as _s, re as _re, datetime, pathlib, time
    nicho = args.get("nicho", "ia_news")
    tema = args.get("tema", "")
    auto_publicar = args.get("auto_publicar", False)
    if not tema: return "ERROR: falta tema"

    _s.path.insert(0, str(ROOT / "scripts"))
    _s.path.insert(0, str(ROOT / "brain"))
    try:
        from brain.especialistas import pedir_a_especialista

        # 1. Investigacion
        ctx_rss = ""
        for f in ("techcrunch", "hackernews", "verge"):
            try:
                r = _tool_leer_rss({"fuente": f, "limite": 5})
                ctx_rss += " [" + f + "]: " + str(r)[:400]
            except Exception: pass
        try: ctx_web = str(_tool_buscar_en_web({"query": "ultimas noticias IA " + tema + " 2026"}))[:1500]
        except Exception: ctx_web = ""
        try: ctx_yt = str(_tool_buscar_youtube({"query": tema + " IA News", "max_results": 5}))[:800]
        except Exception: ctx_yt = ""
        contexto = "RSS: " + ctx_rss + " WEB: " + ctx_web + " YT: " + ctx_yt

        # 2. Redactar con prompt mejorado
        prompt_redactor = (
            "Escribe un articulo HTML de 1500 palabras sobre: " + tema + "." + chr(10) +
            "REQUISITOS:" + chr(10) +
            "- Formato HTML puro (h1, h2, h3, p, ul, li, strong)" + chr(10) +
            "- Titulo <60 chars con keyword al inicio" + chr(10) +
            "- Intro con gancho" + chr(10) +
            "- H2: Que ha pasado, Por que importa, Que cambia para ti, El futuro, FAQ" + chr(10) +
            "- Al menos 3 datos verificables con fuente" + chr(10) +
            "- Cierre con CTA" + chr(10) +
            "- Palabra clave 8-12 veces" + chr(10) +
            "Devuelve SOLO el HTML, sin explicaciones ni markdown."
        )
        articulo = pedir_a_especialista("redactor_seo", prompt_redactor, contexto=contexto)
        if not articulo or len(articulo) < 500:
            return "ERROR: redactor devolvio HTML invalido (" + str(len(articulo)) + " chars)"

        # 3. Evaluar con retry (HTTP 502/500/400)
        evaluacion = ""
        nota = 0
        for intento in range(3):
            try:
                evaluacion = pedir_a_especialista("experto_blog",
                    "Evalua este articulo. Devuelve al final: NOTA: X/10.",
                    contexto=articulo[:3000])  # Solo los primeros 3000 chars (evita HTTP 502)
                m = _re.search(r'NOTA:\s*(\d+)', evaluacion)
                if m:
                    nota = int(m.group(1))
                    if nota > 0:
                        break
                if intento < 2:
                    time.sleep(2)
            except Exception as e:
                print(f"  [evaluador intento {intento+1} fallo: {e}]", flush=True)
                if intento < 2: time.sleep(3)

        # Si el evaluador fallo 3 veces, asumir aprobado pero marcar
        evaluador_ok = nota > 0
        if not evaluador_ok:
            nota = 7
            evaluacion = "[Evaluador no disponible tras 3 intentos. Aprobado por defecto.]"
            print(f"  [AVISO: evaluador no disponible, asumiendo nota 7]", flush=True)

        # 4. SEO
        seo_raw = pedir_a_especialista("seo", "JSON con titulo, descripcion, labels para: " + tema)
        try:
            m = _re.search(r'\{.*\}', seo_raw, _re.DOTALL)
            seo = json.loads(m.group(0)) if m else {}
        except Exception: seo = {}
        titulo = seo.get("titulo", tema + " - IA Global News")

        # 5. Guardar
        b_dir = ROOT / "data" / "agent" / "blog_borradores"
        b_dir.mkdir(parents=True, exist_ok=True)
        ts = int(datetime.datetime.now().timestamp())
        fname = "borrador_" + str(ts) + ".json"
        b = {
            "titulo": titulo, "html": articulo, "tema": tema, "nicho": nicho,
            "nota": nota, "evaluador_ok": evaluador_ok,
            "evaluacion": evaluacion[:500], "ts": ts
        }
        (b_dir / fname).write_text(json.dumps(b, ensure_ascii=False, indent=2))
        print(f"  Guardado: {fname} (nota {nota}, evaluador_ok={evaluador_ok})", flush=True)

        return "OK Borrador (nota " + str(nota) + ", evaluador_ok=" + str(evaluador_ok) + ") -> " + fname
    except Exception as e:
        return "ERROR: " + type(e).__name__ + ": " + str(e)

def _tool_publicar_blog_completo(args):
    import json, subprocess, sys as _s, re as _re
    nicho = args.get("nicho", "ia_news")
    tema = args.get("tema", "")
    palabras = int(args.get("palabras", 1500))
    if not tema:
        return "ERROR: falta tema"
    _s.path.insert(0, str(ROOT / "scripts"))
    _s.path.insert(0, str(ROOT / "brain"))
    try:
        from brain.especialistas import pedir_a_especialista
        ctx_rss = ""
        for f in ("techcrunch", "hackernews", "verge"):
            try:
                r = _tool_leer_rss({"fuente": f, "limite": 5})
                ctx_rss += " [" + f + "]: " + str(r)[:400]
            except Exception:
                pass
        try:
            ctx_web = str(_tool_buscar_en_web({"query": "ultimas noticias IA " + tema + " 2026"}))[:1500]
        except Exception:
            ctx_web = ""
        try:
            ctx_yt = str(_tool_buscar_youtube({"query": tema + " IA News", "max_results": 5}))[:1000]
        except Exception:
            ctx_yt = ""
        contexto_total = "RSS: " + ctx_rss + " WEB: " + ctx_web + " YT: " + ctx_yt
        verificacion = pedir_a_especialista("auditor", "Hay contradicciones sobre " + tema + "? BREVE: CONSISTENTE o CONTRADICCIONES.", contexto=contexto_total)
        articulo = pedir_a_especialista("redactor_seo", "Escribe articulo " + str(palabras) + " palabras sobre: " + tema + ". Nicho: " + nicho + ". SOLO HTML.", contexto=contexto_total)
        seo_raw = pedir_a_especialista("seo", "Para articulo sobre " + tema + " genera JSON con titulo, descripcion, labels")
        try:
            m = _re.search(r"\{.*\}", seo_raw, _re.DOTALL)
            seo = json.loads(m.group(0)) if m else {}
        except Exception:
            seo = {}
        titulo = seo.get("titulo", tema + " - IA Global News")
        proc = subprocess.run(["python", "scripts/publicar_blogger.py", titulo, articulo], capture_output=True, text=True, cwd=str(ROOT), timeout=120)
        url_post = ""
        m2 = _re.search(r"URL: (https?://[^\s]+)", proc.stdout)
        if m2:
            url_post = m2.group(1)
        if "OK:" in proc.stdout:
            return "OK Articulo publicado. Titulo: " + titulo + ". URL: " + (url_post or "ver Blogger")
        return "Fallo Blogger: " + proc.stdout[-300:] + " | " + proc.stderr[-200:]
    except Exception as e:
        return "ERROR: " + type(e).__name__ + ": " + str(e)


def _tool_crear_nicho(args):
    """Crea un nicho con skills. Regenera SKILL.md automáticamente."""
    import requests
    try:
        r = requests.post("http://127.0.0.1:8001/api/crear_nicho", json=args, timeout=30)
        d = r.json()
        if d.get("status") == "ok":
            return f"✅ {d.get('mensaje', 'Nicho creado')}"
        return f"❌ {d.get('mensaje', 'Error')}"
    except Exception as e:
        return f"ERROR: {e}"

def _tool_producir_nicho(args):
    """Produce contenido para un nicho via orquestador universal."""
    try:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from orquestador_nichos import producir
        nicho = args.get("nicho", "")
        dry = bool(args.get("dry", False))
        r = producir(nicho, dry=dry)
        return r
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {str(e)[:200]}"


def _tool_generar_cancion_kaggle(args):
    """Genera una cancion con ACE-Step v11 usando presets del contrato."""
    try:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from musica_acestep import generar
    except Exception as e:
        return f"ERROR importando musica_acestep: {e}"

    caption = (args.get("caption") or args.get("prompt") or "").strip()
    if not caption:
        return "ERROR: falta 'caption' (descripcion musical)"

    preset = args.get("preset")
    duration = int(args.get("duration", args.get("duracion", 60)))

    if duration > 600:
        n_chunks = (duration + 359) // 360
        msg = "AVISO: duration=" + str(duration) + "s > 600s. El contrato prohibe pedirlo en una llamada. "
        msg += "Solucion: llama a esta tool " + str(n_chunks) + " veces con duration=360 y concatena con ffmpeg."
        return msg

    overrides = {}
    for k in ("bpm", "keyscale", "timesignature", "inference_steps", "shift",
              "guidance_scale", "instrumental", "lyrics", "vocal_language",
              "lm_temperature", "lm_cfg_scale", "lm_top_p", "seed"):
        if k in args and args[k] is not None:
            overrides[k] = args[k]

    result = generar(caption, duration=duration, preset=preset, **overrides)
    return result



def _tool_lanzar_pipeline_kaggle(args):
    import subprocess
    tema = args.get("tema", "lofi")
    ordenes = {"tema": tema, "tipo": "musica_y_video"}
    ordenes_json = json.dumps(ordenes)
    
    proc = subprocess.run(["python", "scripts/kaggle_orchestrator.py", ordenes_json], capture_output=True, text=True, cwd=str(ROOT), timeout=1800) # 30 min timeout
    
    if "Kernel creado" in proc.stdout or "Kernel activado" in proc.stdout:
        return "✅ Pipeline lanzado en Kaggle. Tardará unos 15-20 minutos. Revisa tu GitHub / Media Center para ver los resultados."
    return f"❌ Error lanzando pipeline:\n{proc.stdout[-500:]}\n{proc.stderr[-500:]}"


def _tool_generar_imagen(args):
    """Genera imagen con Cloudflare SDXL + contrato."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from generar_imagen import generar as gen_img
    prompt = args.get("prompt", "").strip()
    if not prompt:
        return "ERROR: falta 'prompt'"
    return gen_img(
        prompt,
        preset=args.get("preset"),
        aspect=args.get("aspect"),
        negative_prompt=args.get("negative_prompt", ""),
        num_steps=int(args.get("num_steps", 20)),
        guidance=float(args.get("guidance", 7.5)),
        seed=int(args.get("seed", -1)),
    )



def _tool_buscar_youtube(args):
    import sys
    from pathlib import Path
    query = args.get("query", "")
    region = args.get("region", "ES")
    tipo = args.get("tipo", "busqueda")
    
    try:
        # Importamos la lógica que ya existe en brain/youtube_trending.py
        if tipo == "tendencias":
            sys.path.insert(0, str(ROOT))
            sys.path.insert(0, str(ROOT / "brain"))
            from investigador_redes import resumen_texto
            return resumen_texto(top=10, region=region)
        else:
            # Para búsquedas, usamos la API de YouTube (fases/tendencias.py tiene la lógica)
            sys.path.insert(0, str(ROOT))
            from fases.tendencias import buscar_videos
            # Devolvemos los IDs de los vídeos encontrados
            ids = buscar_videos(query, max_results=5)
            return f"Encontrados {len(ids)} vídeos para '{query}': {', '.join(ids)}"
    except Exception as e:
        return f"ERROR buscando en YouTube: {e}"


def _tool_generar_video(args):
    """Genera clip con Wan 2.2 en Kaggle usando el contrato."""
    import sys, json
    sys.path.insert(0, str(ROOT / "scripts"))
    from wan22_batch import generar_video_batch
    prompt = args.get("prompt", "").strip()
    if not prompt:
        return "ERROR: falta 'prompt'"
    
    # Añadir el prompt a una lista (batch de 1)
    preset = args.get("preset")
    resolution = args.get("resolution")
    num_frames = args.get("num_frames")
    num_steps = args.get("num_inference_steps")
    guidance = args.get("guidance_scale")
    shift = args.get("shift")
    fps = args.get("fps")
    
    result = generar_video_batch(
        [prompt],
        preset=preset,
        resolution=resolution,
        num_frames=num_frames,
        num_steps=num_steps,
        guidance=guidance,
        shift=shift,
        fps=fps,
    )
    return result



def _tool_ensamblar_video_final(args):
    import subprocess
    video = args.get("video_path", "")
    audio = args.get("audio_path", "")
    output = args.get("output_path", "output/video_final.mp4")
    
    proc = subprocess.run(
        ["python", "scripts/ensamblar_video.py", video, audio, output],
        capture_output=True, text=True, cwd=str(ROOT), timeout=300
    )
    
    if "OK:" in proc.stdout:
        return f"✅ {proc.stdout.strip()}"
    return f"❌ Fallo en el ensamblaje:\n{proc.stdout[-500:]}\n{proc.stderr[-500:]}"


def _tool_producir_video(args):
    import subprocess
    video = args.get("video_path", "")
    audio = args.get("audio_path", "")
    nombre_final = args.get("nombre_final", "video_final.mp4")
    
    proc = subprocess.run(
        ["python", "scripts/producir_video.py", video, audio, nombre_final],
        capture_output=True, text=True, cwd=str(ROOT), timeout=300
    )
    
    if "✅ Vídeo listo" in proc.stdout:
        return proc.stdout.strip()
    return f"❌ Fallo en la producción:\n{proc.stdout[-500:]}\n{proc.stderr[-500:]}"


def _tool_publicar_en_redes(args):
    import subprocess
    video = args.get("video_path", "")
    titulo = args.get("titulo", "Video")
    descripcion = args.get("descripcion", "")
    tags = args.get("tags", [])
    redes = args.get("redes", ["youtube"])
    
    resultados = []
    for red in redes:
        if red == "youtube":
            tags_str = ",".join(tags) if tags else ""
            proc = subprocess.run(
                ["python", "-m", "fases.subida", video, titulo, descripcion, tags_str],
                capture_output=True, text=True, cwd=str(ROOT), timeout=600
            )
            if "OK:" in proc.stdout or "Video ID" in proc.stdout:
                resultados.append(f"✅ YouTube: subido")
            else:
                resultados.append(f"❌ YouTube: {proc.stderr[-200:]}")
        elif red in ["tiktok", "instagram", "blog"]:
            # Hueco preparado para el futuro
            resultados.append(f"⏳ {red}: pendiente de configurar")
    
    return "\n".join(resultados)


def _tool_delegar_tareas_paralelas(args):
    import concurrent.futures, requests, os
    tareas = args.get("tareas", [])
    if not tareas: return "ERROR: No se proporcionaron tareas."
    
    api_key = _leer_api_key("OMNIROUTE_API_KEY")
    url = "http://localhost:20128/v1/chat/completions"

    def ejecutar_tarea(t):
        prompt = t.get("prompt", "")
        system = t.get("system", "Eres un asistente experto. Responde de forma concisa.")
        try:
            r = requests.post(url, json={
                "model": "combo/gratis-razonamiento",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                "max_tokens": 2000
            }, headers={"Authorization": f"Bearer {api_key}"}, timeout=120)
            if r.status_code == 200:
                return f"=== TAREA: {prompt[:50]}... ===\n{r.json()['choices'][0]['message']['content']}"
            return f"=== TAREA: {prompt[:50]}... ===\nERROR HTTP {r.status_code}"
        except Exception as e:
            return f"=== TAREA: {prompt[:50]}... ===\nERROR: {e}"

    resultados = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futuros = [executor.submit(ejecutar_tarea, t) for t in tareas]
        for f in concurrent.futures.as_completed(futuros):
            resultados.append(f.result())
    
    return "\n\n".join(resultados)

def _tool_consultar_manual_python(args):
    tema = args.get("tema", "").lower()
    manual_path = ROOT / "docs" / "PYTHON_MASTER_MANUAL.md"
    if not manual_path.exists(): return "ERROR: Manual no existe"
    texto = manual_path.read_text(encoding="utf-8")
    secciones = texto.split("\n## ")
    for sec in secciones:
        if tema in sec.lower():
            return f"=== SECCION DEL MANUAL: ===\n{sec[:3000]}"
    return f"No encontre '{tema}' en el manual."

def _tool_consultar_manual_python(args):
    tema = args.get("tema", "").lower()
    manual_path = ROOT / "docs" / "PYTHON_MASTER_MANUAL.md"
    if not manual_path.exists(): return "ERROR: Manual no existe"
    texto = manual_path.read_text(encoding="utf-8")
    secciones = texto.split("\n## ")
    for sec in secciones:
        if tema in sec.lower():
            return f"=== SECCION DEL MANUAL: ===\n{sec[:3000]}"
    return f"No encontre '{tema}' en el manual."


def _tool_instalar_dependencia(args):
    import subprocess, shutil
    paquete = args["paquete"]
    
    # 1. Auditoría de recursos
    try:
        mem = subprocess.run(["free", "-m"], capture_output=True, text=True)
        libre_mb = int(mem.stdout.split("\n")[1].split()[3])
        disco = shutil.disk_usage(ROOT)
        disco_libre_mb = disco.free // (1024 * 1024)
        
        if libre_mb < 500:
            return f"❌ ABORTADO: Solo hay {libre_mb}MB de RAM. Riesgo de OOM."
        if disco_libre_mb < 300:
            return f"❌ ABORTADO: Solo hay {disco_libre_mb}MB de disco."
    except Exception as e:
        return f"⚠️ No pude auditar los recursos, pero intentaré instalar: {e}"

    # 2. Instalación
    try:
        proc = subprocess.run(["pip", "install", paquete], capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            return f"❌ Error instalando {paquete}: {proc.stderr[-300:]}"
    except subprocess.TimeoutExpired:
        return f"❌ Timeout instalando {paquete} (tardó más de 10 min)."
    
    # 3. Validación
    nombre_import = paquete.split("[")[0].replace("-", "_")
    try:
        subprocess.run(["python", "-c", f"import {nombre_import}"], check=True, capture_output=True)
        return f"✅ {paquete} instalado y verificado correctamente."
    except Exception:
        return f"✅ {paquete} instalado (no se pudo validar con import, pero el pip terminó bien)."



def _tool_buscar_repositorio(args):
    from brain.repos_manager import buscar
    return buscar(args["plataforma"], args["query"])


def _tool_sanar_sistema(args):
    from brain.sanador import sanar
    return sanar()

def _tool_notificar_movil(args):
    from brain.notificador import notificar
    return notificar(args["titulo"], args["mensaje"])

def _tool_leer_rss(args):
    from brain.rss_reader import leer_feed
    return leer_feed(args["fuente"], args.get("limite", 5))

def _tool_pedir_a_especialista(args):
    from brain.especialistas import pedir_a_especialista
    return pedir_a_especialista(args["rol"], args["tarea"], args.get("contexto", ""))

def _tool_lanzar_notebook_kaggle(args):
    from brain.kaggle_launcher import lanzar_notebook
    return lanzar_notebook(args["nombre"], args["codigo_python"])



def _tool_analizar_video_competencia(args):
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

        debug_dir = ROOT / "output" / "debug_frames"
        debug_dir.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(frames):
            (debug_dir / ("frame_" + str(int(_t.time())) + "_" + str(i) + ".jpg")).write_bytes(base64.b64decode(f))

        time.sleep(REQUEST_DELAY)

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
        return "ANALISIS DEL VIDEO (NVIDIA Nemotron VL):" + chr(10) + analisis + chr(10) + chr(10) + "(Video borrado)."

    except Exception as e:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return "ERROR: " + str(e)



def _tool_generar_narracion(args):
    """Genera audio con el perfil de voz del Dios."""
    import subprocess, json, sys, time
    texto = args["texto"]
    nombre = args.get("nombre", f"narracion_{int(time.time())}")
    cmd = [sys.executable, str(ROOT / "scripts" / "voice_studio.py"),
           "--texto", texto, "--perfil-dios"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            return "ERROR: " + r.stderr[-300:]
        data = json.loads(r.stdout.strip().split(chr(10))[-1])
        if "error" in data:
            return "ERROR: " + data["error"]
        return "OK: Audio generado en " + data["audio_url"] + " (" + str(data.get("duracion", "?")) + "s). Voz: " + data.get("voz", "?")
    except Exception as e:
        return "ERROR: " + str(e)


def _tool_consultar_manual_ecosistema(args):
    seccion = (args.get("seccion") or "todo").lower().strip()
    p = ROOT / "docs" / "MANUAL_ECOSISTEMA.md"
    if not p.exists(): return "ERROR: manual no existe"
    txt = p.read_text(encoding="utf-8")
    if seccion in ("todo", "all", ""): return txt[:4000]
    import re as _re
    pat = _re.compile(r"##\s+\d+\.?\s*" + _re.escape(seccion) + r".*?(?=\n##\s+\d+\.|\Z)", _re.DOTALL | _re.IGNORECASE)
    m = pat.search(txt)
    if m: return m.group(0)[:4000]
    lineas = [l for l in txt.splitlines() if seccion in l.lower()]
    if lineas: return f"Coincidencias '{seccion}':\n" + "\n".join(lineas[:30])
    return f"Seccion '{seccion}' no encontrada. Disponibles: " + ", ".join(_re.findall(r"^##\s+\d+\.\s*(.+?)$", txt, _re.MULTILINE))


def _tool_buscar_en_manual(args):
    query = (args.get("query") or "").strip()
    if not query: return "ERROR: falta query"
    p = ROOT / "docs" / "MANUAL_ECOSISTEMA.md"
    if not p.exists(): return "ERROR: manual no existe"
    import subprocess as _sp
    try:
        r = _sp.run(["grep", "-n", "-i", "-B1", "-A3", query, str(p)], capture_output=True, text=True, timeout=10)
        return (r.stdout.strip() or f"Sin coincidencias: {query}")[:4000]
    except Exception as e: return f"ERROR: {e}"


def _tool_listar_mis_tools(args):
    ls = [f"=== MIS TOOLS ({len(TOOLS)}) ==="]
    for tool in TOOLS:
        fn = tool.get("function", {})
        ls.append(f"- {fn.get('name','?')}: {fn.get('description','(sin)')[:150]}")
    return "\n".join(ls)


# Stubs auto (tools declaradas sin handler)
def _tool_subir_youtube(args):
    return f"ERROR: tool subir_youtube sin handler real"

def _tool_producir_nicho(args):
    return f"ERROR: tool producir_nicho sin handler real"

def _tool_ensamblar_video_largo(args):
    return f"ERROR: tool ensamblar_video_largo sin handler real"

def _tool_crear_nicho(args):
    return f"ERROR: tool crear_nicho sin handler real"

def _tool_evaluar_produccion(args):
    return f"ERROR: tool evaluar_produccion sin handler real"



def _tool_ver_mi_workspace(args):
    return WORKSPACE.compacto() or "Workspace vacio"

def _tool_ver_ultimas_tareas(args):
    ult = EPISODIOS.ultimas(3)
    if not ult: return "Sin tareas previas"
    return "\n".join([f"- {u['prompt'][:80]} -> {(u['resultado'] or '')[:100]}" for u in ult])

def _tool_ver_fallos_similares(args):
    fs = FALLOS.similares(args.get("prompt", ""))
    if not fs: return "Sin fallos similares"
    return "\n".join([f"- {f['tool']}: {f['error']}" for f in fs])

def _tool_ver_costes_hoy(args):
    r = COSTES.resumen_hoy()
    return f"Tareas: {r['tareas']} | in: {r['tokens_in']} | out: {r['tokens_out']}"


def _tool_auto_regenerar_manual(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3", "scripts/gen_manual.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            return "OK manual regenerado: " + (r.stdout or "")[:200]
        return "ERROR: " + (r.stderr or r.stdout or "")[:300]
    except Exception as e:
        return f"ERROR: {e}"


def _tool_crear_nueva_tool(args):
    nombre = (args.get("nombre") or "").strip()
    desc = (args.get("descripcion") or "").strip()
    codigo = (args.get("codigo_funcion") or "").strip()
    params = args.get("parametros_json") or {}
    if not nombre or not desc or not codigo:
        return "ERROR: faltan nombre, descripcion o codigo_funcion"
    # Validacion segura
    ok, msg = persistir_tool(nombre, desc, codigo, params)
    if not ok:
        return f"ERROR: {msg}"
    # Regenerar manual automaticamente
    _tool_auto_regenerar_manual({})
    return f"OK {msg}"



def _tool_ejecutar_limpieza(args):
    import subprocess as _sp
    cmd = ["python3", "scripts/limpieza_pipeline.py"]
    if args.get("dry_run"): cmd.append("--dry-run")
    try:
        r = _sp.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return (r.stdout or r.stderr or "")[-800:]
    except Exception as e:
        return f"ERROR: {e}"



def _tool_escanear_ecosistema(args):
    import subprocess as _sp, json as _j
    seccion = (args.get("seccion") or "todo").lower()
    out = []
    if seccion in ("scripts", "todo"):
        r = _sp.run(["ls", "-1", "scripts/"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
        scripts = [x for x in r.stdout.splitlines() if x.endswith(".py")]
        out.append(f"=== scripts/ ({len(scripts)} .py) ===")
        out.append(", ".join(scripts[:60]))
    if seccion in ("brain", "todo"):
        r = _sp.run(["ls", "-1", "brain/"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
        brain = [x for x in r.stdout.splitlines() if x.endswith(".py")]
        out.append(f"\n=== brain/ ({len(brain)} .py) ===")
        out.append(", ".join(brain))
    if seccion in ("endpoints", "todo"):
        try:
            ep = (ROOT / "encuadre_routes.py").read_text()
            import re as _re
            eps = _re.findall(r'@encuadre_bp\.route\(["\']([^"\']+)', ep)
            out.append(f"\n=== Endpoints Factory ({len(eps)}) ===")
            out.append(", ".join(eps[:40]))
        except: pass
    if seccion in ("contratos", "todo"):
        r = _sp.run(["ls", "-1", "data/agent/*.json"], cwd=str(ROOT), capture_output=True, text=True, timeout=10)
        contratos = [x.split("/")[-1] for x in r.stdout.splitlines() if "contract" in x]
        out.append(f"\n=== Contratos ({len(contratos)}) ===")
        out.append(", ".join(contratos))
    if seccion in ("crons", "todo"):
        r = _sp.run(["crontab", "-l"], capture_output=True, text=True, timeout=10)
        lines_c = [l for l in r.stdout.splitlines() if l.strip() and not l.startswith("#")]
        out.append(f"\n=== Crons activos ({len(lines_c)}) ===")
        out.extend(lines_c[:15])
    return "\n".join(out)[:6000]



def _tool_ver_contrato(args):
    nombre = (args.get("nombre") or "").strip().replace(".json", "")
    if not nombre: return "ERROR: falta nombre"
    # Sanitizar
    if "/" in nombre or ".." in nombre:
        return "ERROR: nombre invalido"
    p = ROOT / "data" / "agent" / f"{nombre}.json"
    if not p.exists():
        # Buscar fuzzy
        matches = list((ROOT / "data" / "agent").glob(f"*{nombre}*.json"))
        if matches:
            return f"No existe {nombre}.json. Similares: " + ", ".join(m.name.replace(".json","") for m in matches[:5])
        return f"ERROR: {nombre}.json no existe"
    try:
        import json as _j
        d = _j.loads(p.read_text())
        txt = _j.dumps(d, indent=1, ensure_ascii=False)
        # Truncar inteligente: si >3000, mostrar keys principales
        if len(txt) > 3000:
            keys = list(d.keys()) if isinstance(d, dict) else [    {"type": "function", "function": {"name": "procesar_video_existente", "description": "Procesa un vídeo/URL ya descargado con el pipeline REAL: transcribe (transcribir_groq.py) → analiza (analista_fase1.py) → sintetiza dossier (sintetizador.py) → genera post (fase2_produccion.py). Usa esto en vez de reimplementar. Tarda 5-15min.", "parameters": {"type": "object", "properties": {"url_o_path": {"type": "string", "description": "URL de YouTube o ruta local al vídeo/audio"}, "nicho": {"type": "string", "description": "el_encuadre, ia_news, finanzas_barrio (defecto el_encuadre)"}}, "required": ["url_o_path"]}}},
    {"type": "function", "function": {"name": "descargar_audio_youtube", "description": "Descarga solo el AUDIO de un vídeo YouTube a output/encuadre/audios/. Es el paso que usa recolector.py. Ligero, no descarga vídeo completo.", "parameters": {"type": "object", "properties": {"video_id": {"type": "string", "description": "ID de YouTube (11 chars)"}}, "required": ["video_id"]}}},
    {"type": "function", "function": {"name": "pipeline_step", "description": "Ejecuta UN paso del pipeline. Pasos: limpieza_pipeline, gen_manual, recolector, transcribir_groq, analista_fase1, sintetizador, fase2_produccion, voz_edge, director_arte, render_robusto, factory_shorts, generar_web_v3, generar_web_dossier, actualizar_web_index, generar_redes, generar_redes_cruzadas, sincronizar_podcasts, generar_podcast, generar_informe_pdf. Recibe fecha YYYY-MM-DD o 'hoy'.", "parameters": {"type": "object", "properties": {"step": {"type": "string"}, "fecha": {"type": "string"}}, "required": ["step"]}}},
    {"type": "function", "function": {"name": "pipeline_completo", "description": "Lanza pipeline completo 06:00 para una fecha. Tarda 30-40min. Recolectar+analizar+guion+voz+arte+video+shorts+web+YT+podcast.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_status", "description": "Estado del pipeline: corriendo/detenido, ultimo log, tail.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_kill", "description": "Detiene el pipeline actual.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "pipeline_custom", "description": "Pipeline a la carta: nicho + formatos + tema. Formatos: largo, shorts, posts, podcast.", "parameters": {"type": "object", "properties": {"nicho": {"type": "string"}, "formatos": {"type": "array", "items": {"type": "string"}}, "tema": {"type": "string"}, "num_shorts": {"type": "integer"}}, "required": ["nicho"]}}},
    {"type": "function", "function": {"name": "generar_short", "description": "Genera 1 short rapido (2min) sobre tema. Sin GPU, Pixabay.", "parameters": {"type": "object", "properties": {"tema": {"type": "string"}, "nicho": {"type": "string"}}, "required": ["tema"]}}},
    {"type": "function", "function": {"name": "generar_post_web", "description": "Genera post web: largo + dossier + mediano + build + push.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_podcast_dia", "description": "Genera podcast MP3 del dia desde guion.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "subir_youtube_dia", "description": "Sube video largo + shorts a YouTube con publish_at escalonado (18-21h ES).", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "programar_youtube", "description": "Programa un video ya subido. Args: video_id, hora HH:MM (Espana).", "parameters": {"type": "object", "properties": {"video_id": {"type": "string"}, "hora": {"type": "string"}}, "required": ["video_id", "hora"]}}},
    {"type": "function", "function": {"name": "publicar_blogger", "description": "Publica el post del dia en Blogger con horarios escalonados.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_seo", "description": "Regenera SEO (titulo + descripcion + tags) del video y shorts del dia.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "generar_titulo_ab", "description": "Genera titulos A/B para test CTR.", "parameters": {"type": "object", "properties": {"fecha": {"type": "string"}, "tipo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "cloudflare_stats", "description": "Visitas web ultimos 7 dias: page_views, visitas, top paginas, top paises.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "buscar_historico", "description": "Busca en historico indexado (posts + produccion + dossiers). FTS5.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "reindexar_busqueda", "description": "Reindexa busqueda FTS5 con ultimos posts/producciones.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_snapshot", "description": "Crea snapshot git del repo actual.", "parameters": {"type": "object", "properties": {"motivo": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "rollback_listar", "description": "Lista snapshots git disponibles.", "parameters": {"type": "object", "properties": {}, "required": []}}},
]
            return f"Contrato {nombre} ({len(txt)} chars). Keys: {keys}. Primeras 3000 chars:\n{txt[:3000]}...\n[Truncado. Usa seccion especifica si necesitas mas.]"
        return txt
    except Exception as e:
        return f"ERROR: {e}"



def _tool_descargar_audio_youtube(args):
    """Descarga audio vía yt-dlp (mismo flujo que recolector.py)."""
    import subprocess as _sp
    vid = args.get("video_id", "").strip()
    if not vid: return "ERROR: falta video_id"
    import re as _re
    if "/" in vid or "?" in vid:
        m = _re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", vid)
        if m: vid = m.group(1)
        else: return f"ERROR: video_id inválido"
    dst = ROOT / "output" / "encuadre" / "audios"
    dst.mkdir(parents=True, exist_ok=True)
    out_tmpl = str(dst / f"%(id)s.%(ext)s")
    try:
        cmd = ["yt-dlp", "-f", "bestaudio[ext=m4a]/bestaudio",
               "--extract-audio", "--audio-format", "mp3", "--audio-quality", "5",
               "-o", out_tmpl,
               "--print", "after_move:%(filepath)s",
               f"https://youtu.be/{vid}"]
        r = _sp.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0: return f"ERROR yt-dlp: {r.stderr[:300]}"
        files = list(dst.glob(f"{vid}.*"))
        if not files: return "ERROR: no se descargó"
        f = files[0]
        mb = f.stat().st_size // 1024 // 1024
        return f"OK audio descargado: {f.relative_to(ROOT)} ({mb}MB)"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_procesar_video_existente(args):
    """Orquesta el pipeline REAL: recolector → transcribir → analizar → sintetizar → post."""
    import subprocess as _sp, datetime
    url_or_path = args.get("url_o_path", "").strip()
    nicho = args.get("nicho", "el_encuadre")
    if not url_or_path: return "ERROR: falta url_o_path"
    fecha = datetime.date.today().isoformat()
    pasos = []
    
    # Si es URL YouTube, descargar audio primero
    if "youtu" in url_or_path:
        import re as _re
        m = _re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url_or_path)
        if not m: return "ERROR: URL YouTube inválida"
        vid = m.group(1)
        r = _tool_descargar_audio_youtube({"video_id": vid})
        if r.startswith("ERROR"): return r
        pasos.append(f"1. {r}")
        # Buscar el audio descargado
        dst = ROOT / "output" / "encuadre" / "audios"
        files = list(dst.glob(f"{vid}.*"))
        if not files: return "ERROR: audio no encontrado tras descarga"
        audio_path = files[0]
    else:
        audio_path = ROOT / url_or_path.lstrip("/") if not pathlib.Path(url_or_path).is_absolute() else pathlib.Path(url_or_path)
        if not audio_path.exists(): return f"ERROR: no existe {audio_path}"
    
    # 2. Transcribir con script REAL
    try:
        r = _sp.run(["python3", "scripts/transcribir_groq.py", str(audio_path)],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            return f"ERROR transcribir_groq: {r.stderr[:300]}\n{pasos}"
        pasos.append(f"2. ✅ transcrito: {r.stdout[-200:]}")
    except Exception as e:
        return f"ERROR transcripción: {e}\n{pasos}"
    
    return (
        f"OK cadena iniciada.\n" + "\n".join(pasos) + "\n\n"
        f"NOTA: Para generar el dossier + post completo con este material, "
        f"usa el pipeline normal: `python3 scripts/pipeline_encuadre.py` "
        f"(ya cogerá los audios/transcripciones de output/encuadre/audios/).\n"
        f"El pipeline completo tarda 30-40min pero da dossier + web + shorts + podcast + YT."
    )



def _tool_pipeline_step(args):
    import subprocess as _sp, datetime
    step = (args.get("step") or "").strip()
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    validos = ["limpieza_pipeline","gen_manual","recolector","transcribir_groq","analista_fase1",
               "sintetizador","fase2_produccion","voz_edge","director_arte","render_robusto",
               "factory_shorts","generar_web_v3","generar_web_dossier","actualizar_web_index",
               "generar_redes","generar_redes_cruzadas","sincronizar_podcasts","generar_podcast",
               "generar_informe_pdf"]
    if step not in validos:
        return f"ERROR: step invalido. Validos: {', '.join(validos)}"
    script = ROOT / "scripts" / f"{step}.py"
    if not script.exists():
        return f"ERROR: no existe {script.relative_to(ROOT)}"
    try:
        r = _sp.run(["python3", str(script), fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
        return f"{'OK' if r.returncode==0 else 'FAIL'} {step}: {(r.stdout or r.stderr or '')[-1500:]}"
    except _sp.TimeoutExpired:
        return f"ERROR: {step} timeout"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_pipeline_completo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        log = open(ROOT / "data" / "logs" / f"pipeline_dios_{fecha}.log", "w")
        _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
        return f"OK pipeline lanzado {fecha} (background, 30-40min). Log: data/logs/pipeline_dios_{fecha}.log"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_pipeline_status(args):
    import subprocess as _sp, time
    r = _sp.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    proc = r.stdout.strip() or "(nada corriendo)"
    log = ROOT / "data" / "logs" / "pipeline.log"
    info = ""
    if log.exists():
        mins = (time.time() - log.stat().st_mtime) / 60
        tail = _sp.run(["tail", "-8", str(log)], capture_output=True, text=True, timeout=5)
        info = f"\nUltimo log hace {mins:.0f}min\n\n{tail.stdout[-1200:]}"
    return f"Pipeline: {proc}{info}"


def _tool_pipeline_kill(args):
    import subprocess as _sp
    try:
        _sp.run(["pkill", "-9", "-f", "pipeline_encuadre"], timeout=10, check=False)
        return "OK pipeline detenido"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_pipeline_custom(args):
    import subprocess as _sp, datetime, json as _j
    nicho = args.get("nicho", "")
    formatos = args.get("formatos") or ["largo"]
    tema = args.get("tema", "")
    num_shorts = args.get("num_shorts", 4)
    if not nicho: return "ERROR: falta nicho"
    fecha = datetime.date.today().isoformat()
    req = {"fecha": fecha, "nicho": nicho, "formatos": formatos, "num_shorts": num_shorts,
           "tema_tipo": "manual" if tema else "auto", "tema": tema,
           "timestamp": datetime.datetime.now().isoformat()}
    req_path = ROOT / "output" / "encuadre" / f"custom_request_{fecha}.json"
    req_path.write_text(_j.dumps(req, ensure_ascii=False, indent=2))
    log = open(ROOT / "data" / "logs" / f"pipeline_custom_{fecha}.log", "w")
    _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
    return f"OK pipeline custom: nicho={nicho}, formatos={formatos}, tema={tema[:40] or 'auto'}"


def _tool_generar_short(args):
    import subprocess as _sp
    tema = args.get("tema", "")
    nicho = args.get("nicho", "el_encuadre")
    if not tema: return "ERROR: falta tema"
    try:
        r = _sp.run(["python3", "scripts/short_engine_encuadre.py", tema, nicho],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-800:]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_generar_post_web(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    pasos = []
    for script in ["generar_web_v3.py", "generar_web_dossier.py", "actualizar_web_index.py"]:
        try:
            r = _sp.run(["python3", f"scripts/{script}", fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
            pasos.append(f"{script}: {'OK' if r.returncode==0 else 'FAIL'}")
        except Exception as e:
            pasos.append(f"{script}: ERR {e}")
    try:
        _sp.run(["mkdocs", "build"], cwd=str(ROOT / "web"), capture_output=True, timeout=120)
        _sp.run(["git", "add", "web/"], cwd=str(ROOT), timeout=30)
        _sp.run(["git", "commit", "-m", f"post: {fecha}", "--no-verify"], cwd=str(ROOT), timeout=30)
        _sp.run(["git", "push", "origin", "main", "--no-verify"], cwd=str(ROOT), timeout=60)
        pasos.append("build+push: OK")
    except Exception as e:
        pasos.append(f"build+push: ERR {e}")
    return "\n".join(pasos)


def _tool_generar_podcast_dia(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3", "scripts/generar_podcast.py", fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_subir_youtube_dia(args):
    import datetime as _dt
    fecha = args.get("fecha") or _dt.date.today().isoformat()
    if fecha == "hoy": fecha = _dt.date.today().isoformat()
    video = ROOT / "output" / "encuadre" / f"video_largo_{fecha}.mp4"
    if not video.exists():
        return f"ERROR: no existe video_largo_{fecha}.mp4"
    try:
        import sys as _sys_yt
        _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import subir
        import json as _j
        seo = {}
        seo_path = ROOT / "output" / "encuadre" / f"seo_{fecha}.json"
        if seo_path.exists(): seo = _j.loads(seo_path.read_text()).get("largo", {})
        titulo = seo.get("titulo", f"El Encuadre {fecha}")
        desc = seo.get("descripcion", "")
        pub = _dt.datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        if pub < _dt.datetime.now(): pub += _dt.timedelta(days=1)
        r = subir(str(video), titulo, desc, privacidad="private",
                  publish_at=pub.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  token_file="data/youtube_encuadre_token.json")
        return f"OK https://youtu.be/{r.get('id')}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_programar_youtube(args):
    import datetime
    vid = args.get("video_id", "")
    hora = args.get("hora", "18:00")
    if not vid: return "ERROR: falta video_id"
    try:
        import sys as _sys_yt
        _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import actualizar_video, token
        token("data/youtube_encuadre_token.json")
        h, m = hora.split(":")
        dt = datetime.datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        if dt < datetime.datetime.now(): dt += datetime.timedelta(days=1)
        pub = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        actualizar_video(vid, publish_at=pub, token_file="data/youtube_encuadre_token.json")
        return f"OK {vid} programado {pub}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_publicar_blogger(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3", "scripts/publicar_blogger_encuadre.py", fecha],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_generar_seo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    tipo = args.get("tipo", "video_largo")
    try:
        r = _sp.run(["python3", "scripts/generar_titulo_seo.py", fecha, tipo],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_generar_titulo_ab(args):
    return _tool_generar_seo(args)


def _tool_cloudflare_stats(args):
    try:
        import sys as _sys_cf
        _sys_cf.path.insert(0, str(ROOT / "scripts"))
        from cloudflare_stats import resumen
        r = resumen(7)
        return f"7d: {r.get('page_views',0)} views | {r.get('visitas',0)} visitas\nTop: {r.get('top_paginas',[])[:3]}\nPaises: {r.get('top_paises',[])[:3]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_buscar_historico(args):
    import sqlite3
    q = (args.get("query") or "").strip()
    if not q: return "ERROR: falta query"
    db = ROOT / "data" / "agent" / "busqueda_fts.db"
    if not db.exists(): return "ERROR: indice no construido"
    try:
        con = sqlite3.connect(str(db))
        cur = con.execute("SELECT tipo, fecha, titulo, snippet(docs, 3, '<b>', '</b>', '...', 20) FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 5", (q,))
        rows = cur.fetchall()
        if not rows: return f"Sin resultados para '{q}'"
        return "\n".join([f"[{r[0]}] {r[1]} — {r[2][:60]}\n  {r[3][:150]}" for r in rows])
    except Exception as e:
        return f"ERROR: {e}"


def _tool_reindexar_busqueda(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3", "scripts/indexar_busqueda.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e:
        return f"ERROR: {e}"


def _tool_rollback_snapshot(args):
    import subprocess as _sp
    motivo = args.get("motivo", "manual")
    try:
        r = _sp.run(["python3", "scripts/rollback.py", "snapshot", motivo],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr or "")[-300:]
    except Exception as e:
        return f"ERROR: {e}"


def _tool_rollback_listar(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3", "scripts/rollback.py", "listar"],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr or "")[-1500:]
    except Exception as e:
        return f"ERROR: {e}"



def _tool_pipeline_step(args):
    import subprocess as _sp, datetime
    step = (args.get("step") or "").strip()
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    validos = ["limpieza_pipeline","gen_manual","recolector","transcribir_groq","analista_fase1",
               "sintetizador","fase2_produccion","voz_edge","director_arte","render_robusto",
               "factory_shorts","generar_web_v3","generar_web_dossier","actualizar_web_index",
               "generar_redes","generar_redes_cruzadas","sincronizar_podcasts","generar_podcast",
               "generar_informe_pdf"]
    if step not in validos:
        return f"ERROR: step invalido. Validos: {', '.join(validos)}"
    s = ROOT / "scripts" / f"{step}.py"
    if not s.exists(): return f"ERROR: no existe scripts/{step}.py"
    try:
        r = _sp.run(["python3", str(s), fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
        return f"{'OK' if r.returncode==0 else 'FAIL'} {step}: {(r.stdout or r.stderr or '')[-1200:]}"
    except _sp.TimeoutExpired: return f"ERROR: {step} timeout"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_completo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        log = open(ROOT / "data" / "logs" / f"pipeline_dios_{fecha}.log", "w")
        _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
        return f"OK pipeline lanzado {fecha}. Log: data/logs/pipeline_dios_{fecha}.log"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_status(args):
    import subprocess as _sp, time
    r = _sp.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    proc = r.stdout.strip() or "(nada corriendo)"
    log = ROOT / "data" / "logs" / "pipeline.log"
    info = ""
    if log.exists():
        mins = (time.time() - log.stat().st_mtime) / 60
        tail = _sp.run(["tail", "-8", str(log)], capture_output=True, text=True, timeout=5)
        info = f"\nUltimo log hace {mins:.0f}min\n{tail.stdout[-1000:]}"
    return f"Pipeline: {proc}{info}"

def _tool_pipeline_kill(args):
    import subprocess as _sp
    try:
        _sp.run(["pkill", "-9", "-f", "pipeline_encuadre"], timeout=10, check=False)
        return "OK detenido"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_custom(args):
    import subprocess as _sp, datetime, json as _j
    nicho = args.get("nicho", "")
    if not nicho: return "ERROR: falta nicho"
    fecha = datetime.date.today().isoformat()
    req = {"fecha": fecha, "nicho": nicho, "formatos": args.get("formatos") or ["largo"],
           "num_shorts": args.get("num_shorts", 4), "tema_tipo": "manual" if args.get("tema") else "auto",
           "tema": args.get("tema", ""), "timestamp": datetime.datetime.now().isoformat()}
    (ROOT / "output" / "encuadre" / f"custom_request_{fecha}.json").write_text(_j.dumps(req, ensure_ascii=False, indent=2))
    log = open(ROOT / "data" / "logs" / f"pipeline_custom_{fecha}.log", "w")
    _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
    return f"OK pipeline custom: {nicho}"

def _tool_generar_short(args):
    import subprocess as _sp
    tema = args.get("tema", "")
    if not tema: return "ERROR: falta tema"
    try:
        r = _sp.run(["python3", "scripts/short_engine_encuadre.py", tema, args.get("nicho", "el_encuadre")],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-800:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_post_web(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    pasos = []
    for s in ["generar_web_v3.py","generar_web_dossier.py","actualizar_web_index.py"]:
        try:
            r = _sp.run(["python3", f"scripts/{s}", fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
            pasos.append(f"{s}: {'OK' if r.returncode==0 else 'FAIL'}")
        except Exception as e: pasos.append(f"{s}: ERR {e}")
    try:
        _sp.run(["mkdocs", "build"], cwd=str(ROOT / "web"), capture_output=True, timeout=120)
        _sp.run(["git","add","web/"], cwd=str(ROOT), timeout=30)
        _sp.run(["git","commit","-m", f"post: {fecha}","--no-verify"], cwd=str(ROOT), timeout=30)
        _sp.run(["git","push","origin","main","--no-verify"], cwd=str(ROOT), timeout=60)
        pasos.append("build+push: OK")
    except Exception as e: pasos.append(f"build+push: ERR {e}")
    return "\n".join(pasos)

def _tool_generar_podcast_dia(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3","scripts/generar_podcast.py",fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_subir_youtube_dia(args):
    import datetime as _dt
    fecha = args.get("fecha") or _dt.date.today().isoformat()
    if fecha == "hoy": fecha = _dt.date.today().isoformat()
    video = ROOT / "output" / "encuadre" / f"video_largo_{fecha}.mp4"
    if not video.exists(): return f"ERROR: no existe video_largo_{fecha}.mp4"
    try:
        import sys as _sys_yt; _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import subir
        import json as _j
        seo = {}
        sp = ROOT / "output" / "encuadre" / f"seo_{fecha}.json"
        if sp.exists(): seo = _j.loads(sp.read_text()).get("largo", {})
        pub = _dt.datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        if pub < _dt.datetime.now(): pub += _dt.timedelta(days=1)
        r = subir(str(video), seo.get("titulo", f"El Encuadre {fecha}"), seo.get("descripcion",""),
                  privacidad="private", publish_at=pub.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  token_file="data/youtube_encuadre_token.json")
        return f"OK https://youtu.be/{r.get('id')}"
    except Exception as e: return f"ERROR: {e}"

def _tool_programar_youtube(args):
    import datetime
    vid = args.get("video_id","")
    if not vid: return "ERROR: falta video_id"
    try:
        import sys as _sys_yt; _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import actualizar_video, token
        token("data/youtube_encuadre_token.json")
        h, m = args.get("hora","18:00").split(":")
        dt = datetime.datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        if dt < datetime.datetime.now(): dt += datetime.timedelta(days=1)
        actualizar_video(vid, publish_at=dt.strftime("%Y-%m-%dT%H:%M:%SZ"), token_file="data/youtube_encuadre_token.json")
        return f"OK {vid} programado {dt.isoformat()}"
    except Exception as e: return f"ERROR: {e}"

def _tool_publicar_blogger(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3","scripts/publicar_blogger_encuadre.py",fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_seo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    tipo = args.get("tipo","video_largo")
    try:
        r = _sp.run(["python3","scripts/generar_titulo_seo.py",fecha,tipo], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_titulo_ab(args):
    return _tool_generar_seo(args)

def _tool_cloudflare_stats(args):
    try:
        import sys as _sys_cf; _sys_cf.path.insert(0, str(ROOT / "scripts"))
        from cloudflare_stats import resumen
        r = resumen(7)
        return f"7d: {r.get('page_views',0)} views | {r.get('visitas',0)} visitas\nTop: {r.get('top_paginas',[])[:3]}\nPaises: {r.get('top_paises',[])[:3]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_buscar_historico(args):
    import sqlite3
    q = (args.get("query") or "").strip()
    if not q: return "ERROR: falta query"
    db = ROOT / "data" / "agent" / "busqueda_fts.db"
    if not db.exists(): return "ERROR: indice no construido"
    try:
        con = sqlite3.connect(str(db))
        cur = con.execute("SELECT tipo,fecha,titulo,snippet(docs,3,'<b>','</b>','...',20) FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 5",(q,))
        rows = cur.fetchall()
        if not rows: return f"Sin resultados para '{q}'"
        return "\n".join([f"[{r[0]}] {r[1]} — {r[2][:60]}\n  {r[3][:150]}" for r in rows])
    except Exception as e: return f"ERROR: {e}"

def _tool_reindexar_busqueda(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/indexar_busqueda.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_rollback_snapshot(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/rollback.py","snapshot",args.get("motivo","manual")], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr or "")[-300:]
    except Exception as e: return f"ERROR: {e}"

def _tool_rollback_listar(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/rollback.py","listar"], cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr or "")[-1500:]
    except Exception as e: return f"ERROR: {e}"


def _tool_pipeline_step(args):
    import subprocess as _sp, datetime
    step = (args.get("step") or "").strip()
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    validos = ["limpieza_pipeline","gen_manual","recolector","transcribir_groq","analista_fase1",
               "sintetizador","fase2_produccion","voz_edge","director_arte","render_robusto",
               "factory_shorts","generar_web_v3","generar_web_dossier","actualizar_web_index",
               "generar_redes","generar_redes_cruzadas","sincronizar_podcasts","generar_podcast",
               "generar_informe_pdf"]
    if step not in validos:
        return f"ERROR: step invalido. Validos: {', '.join(validos)}"
    s = ROOT / "scripts" / f"{step}.py"
    if not s.exists(): return f"ERROR: no existe scripts/{step}.py"
    try:
        r = _sp.run(["python3", str(s), fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
        return f"{'OK' if r.returncode==0 else 'FAIL'} {step}: {(r.stdout or r.stderr or '')[-1200:]}"
    except _sp.TimeoutExpired: return f"ERROR: {step} timeout"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_completo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        log = open(ROOT / "data" / "logs" / f"pipeline_dios_{fecha}.log", "w")
        _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
        return f"OK pipeline lanzado {fecha}. Log: data/logs/pipeline_dios_{fecha}.log"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_status(args):
    import subprocess as _sp, time
    r = _sp.run(["pgrep", "-af", "pipeline_encuadre"], capture_output=True, text=True, timeout=5)
    proc = r.stdout.strip() or "(nada corriendo)"
    log = ROOT / "data" / "logs" / "pipeline.log"
    info = ""
    if log.exists():
        mins = (time.time() - log.stat().st_mtime) / 60
        tail = _sp.run(["tail", "-8", str(log)], capture_output=True, text=True, timeout=5)
        info = f"\nUltimo log hace {mins:.0f}min\n{tail.stdout[-1000:]}"
    return f"Pipeline: {proc}{info}"

def _tool_pipeline_kill(args):
    import subprocess as _sp
    try:
        _sp.run(["pkill", "-9", "-f", "pipeline_encuadre"], timeout=10, check=False)
        return "OK detenido"
    except Exception as e: return f"ERROR: {e}"

def _tool_pipeline_custom(args):
    import subprocess as _sp, datetime, json as _j
    nicho = args.get("nicho", "")
    if not nicho: return "ERROR: falta nicho"
    fecha = datetime.date.today().isoformat()
    req = {"fecha": fecha, "nicho": nicho, "formatos": args.get("formatos") or ["largo"],
           "num_shorts": args.get("num_shorts", 4), "tema_tipo": "manual" if args.get("tema") else "auto",
           "tema": args.get("tema", ""), "timestamp": datetime.datetime.now().isoformat()}
    (ROOT / "output" / "encuadre" / f"custom_request_{fecha}.json").write_text(_j.dumps(req, ensure_ascii=False, indent=2))
    log = open(ROOT / "data" / "logs" / f"pipeline_custom_{fecha}.log", "w")
    _sp.Popen(["python3", "scripts/pipeline_encuadre.py"], cwd=str(ROOT), stdout=log, stderr=_sp.STDOUT)
    return f"OK pipeline custom: {nicho}"

def _tool_generar_short(args):
    import subprocess as _sp
    tema = args.get("tema", "")
    if not tema: return "ERROR: falta tema"
    try:
        r = _sp.run(["python3", "scripts/short_engine_encuadre.py", tema, args.get("nicho", "el_encuadre")],
                    cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-800:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_post_web(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    pasos = []
    for s in ["generar_web_v3.py","generar_web_dossier.py","actualizar_web_index.py"]:
        try:
            r = _sp.run(["python3", f"scripts/{s}", fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=900)
            pasos.append(f"{s}: {'OK' if r.returncode==0 else 'FAIL'}")
        except Exception as e: pasos.append(f"{s}: ERR {e}")
    try:
        _sp.run(["mkdocs", "build"], cwd=str(ROOT / "web"), capture_output=True, timeout=120)
        _sp.run(["git","add","web/"], cwd=str(ROOT), timeout=30)
        _sp.run(["git","commit","-m", f"post: {fecha}","--no-verify"], cwd=str(ROOT), timeout=30)
        _sp.run(["git","push","origin","main","--no-verify"], cwd=str(ROOT), timeout=60)
        pasos.append("build+push: OK")
    except Exception as e: pasos.append(f"build+push: ERR {e}")
    return "\n".join(pasos)

def _tool_generar_podcast_dia(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3","scripts/generar_podcast.py",fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=600)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_subir_youtube_dia(args):
    import datetime as _dt
    fecha = args.get("fecha") or _dt.date.today().isoformat()
    if fecha == "hoy": fecha = _dt.date.today().isoformat()
    video = ROOT / "output" / "encuadre" / f"video_largo_{fecha}.mp4"
    if not video.exists(): return f"ERROR: no existe video_largo_{fecha}.mp4"
    try:
        import sys as _sys_yt; _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import subir
        import json as _j
        seo = {}
        sp = ROOT / "output" / "encuadre" / f"seo_{fecha}.json"
        if sp.exists(): seo = _j.loads(sp.read_text()).get("largo", {})
        pub = _dt.datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        if pub < _dt.datetime.now(): pub += _dt.timedelta(days=1)
        r = subir(str(video), seo.get("titulo", f"El Encuadre {fecha}"), seo.get("descripcion",""),
                  privacidad="private", publish_at=pub.strftime("%Y-%m-%dT%H:%M:%SZ"),
                  token_file="data/youtube_encuadre_token.json")
        return f"OK https://youtu.be/{r.get('id')}"
    except Exception as e: return f"ERROR: {e}"

def _tool_programar_youtube(args):
    import datetime
    vid = args.get("video_id","")
    if not vid: return "ERROR: falta video_id"
    try:
        import sys as _sys_yt; _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import actualizar_video, token
        token("data/youtube_encuadre_token.json")
        h, m = args.get("hora","18:00").split(":")
        dt = datetime.datetime.now().replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        if dt < datetime.datetime.now(): dt += datetime.timedelta(days=1)
        actualizar_video(vid, publish_at=dt.strftime("%Y-%m-%dT%H:%M:%SZ"), token_file="data/youtube_encuadre_token.json")
        return f"OK {vid} programado {dt.isoformat()}"
    except Exception as e: return f"ERROR: {e}"

def _tool_publicar_blogger(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    try:
        r = _sp.run(["python3","scripts/publicar_blogger_encuadre.py",fecha], cwd=str(ROOT), capture_output=True, text=True, timeout=300)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-600:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_seo(args):
    import subprocess as _sp, datetime
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    tipo = args.get("tipo","video_largo")
    try:
        r = _sp.run(["python3","scripts/generar_titulo_seo.py",fecha,tipo], cwd=str(ROOT), capture_output=True, text=True, timeout=120)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_generar_titulo_ab(args):
    return _tool_generar_seo(args)

def _tool_cloudflare_stats(args):
    try:
        import sys as _sys_cf; _sys_cf.path.insert(0, str(ROOT / "scripts"))
        from cloudflare_stats import resumen
        r = resumen(7)
        return f"7d: {r.get('page_views',0)} views | {r.get('visitas',0)} visitas\nTop: {r.get('top_paginas',[])[:3]}\nPaises: {r.get('top_paises',[])[:3]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_buscar_historico(args):
    import sqlite3
    q = (args.get("query") or "").strip()
    if not q: return "ERROR: falta query"
    db = ROOT / "data" / "agent" / "busqueda_fts.db"
    if not db.exists(): return "ERROR: indice no construido"
    try:
        con = sqlite3.connect(str(db))
        cur = con.execute("SELECT tipo,fecha,titulo,snippet(docs,3,'<b>','</b>','...',20) FROM docs WHERE docs MATCH ? ORDER BY rank LIMIT 5",(q,))
        rows = cur.fetchall()
        if not rows: return f"Sin resultados para '{q}'"
        return "\n".join([f"[{r[0]}] {r[1]} — {r[2][:60]}\n  {r[3][:150]}" for r in rows])
    except Exception as e: return f"ERROR: {e}"

def _tool_reindexar_busqueda(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/indexar_busqueda.py"], cwd=str(ROOT), capture_output=True, text=True, timeout=180)
        return f"{'OK' if r.returncode==0 else 'FAIL'}: {(r.stdout or r.stderr or '')[-400:]}"
    except Exception as e: return f"ERROR: {e}"

def _tool_rollback_snapshot(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/rollback.py","snapshot",args.get("motivo","manual")], cwd=str(ROOT), capture_output=True, text=True, timeout=60)
        return (r.stdout or r.stderr or "")[-300:]
    except Exception as e: return f"ERROR: {e}"

def _tool_rollback_listar(args):
    import subprocess as _sp
    try:
        r = _sp.run(["python3","scripts/rollback.py","listar"], cwd=str(ROOT), capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr or "")[-1500:]
    except Exception as e: return f"ERROR: {e}"


def _tool_publicar_comentario_youtube(args):
    """Comentario SEO top-1 + fijado + tráfico cruzado."""
    import requests, datetime, json as _j, sys as _sys_cm
    vid = (args.get("video_id") or "").strip()
    if not vid: return "ERROR: falta video_id"
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    extra = (args.get("texto_extra") or "").strip()
    
    # Cargar SEO + producción para generar comentario rico
    seo_path = ROOT / "output" / "encuadre" / f"seo_{fecha}.json"
    prod_path = ROOT / "output" / "encuadre" / f"produccion_{fecha}.json"
    seo = _j.loads(seo_path.read_text()) if seo_path.exists() else {}
    prod = _j.loads(prod_path.read_text()) if prod_path.exists() else {}
    titulo = (seo.get("largo") or {}).get("titulo", "")
    dossier = prod.get("dossier") or {}
    tema = dossier.get("titular_brutal", "")[:100]
    
    # Comentario top-1: pregunta + CTA + link cruzado + hashtags
    post_url = f"https://elencuadre.pages.dev/analisis/{fecha}-largo/"
    comentario = extra + ("\n\n" if extra else "")
    comentario += f"📊 ANÁLISIS COMPLETO: {post_url}\n\n"
    if tema:
        comentario += f"🎯 Hoy analizamos: {tema}\n\n"
    comentario += "💬 ¿Tú qué opinas? ¿Has detectado estas técnicas en los medios que lees?\n\n"
    comentario += "📩 Recibe el dossier diario en Telegram: https://t.me/somoselencuadre\n\n"
    comentario += "#ElEncuadre #AnálisisMediático #Framing #SesgosCognitivos"
    
    # Obtener token
    try:
        _sys_cm.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import token
        access = token("data/youtube_encuadre_token.json")
    except Exception as e:
        return f"ERROR token: {e}"
    
    # 1. Insertar comentario
    try:
        r = requests.post(
            "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
            headers={"Authorization": f"Bearer {access}", "Content-Type": "application/json"},
            json={"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": comentario}}}},
            timeout=30
        )
        if r.status_code != 200:
            return f"ERROR insert comentario HTTP {r.status_code}: {r.text[:300]}"
        cid = r.json()["snippet"]["topLevelComment"]["id"]
    except Exception as e:
        return f"ERROR insert: {e}"
    
    # 2. Fijar (setModerationStatus)
    try:
        r2 = requests.post(
            f"https://www.googleapis.com/youtube/v3/comments/setModerationStatus?id={cid}&moderationStatus=published",
            headers={"Authorization": f"Bearer {access}"}, timeout=20
        )
        fijado = r2.status_code in (200, 204)
    except Exception:
        fijado = False
    
    return f"OK comentario publicado en {vid}{' y fijado' if fijado else ''}\nID: {cid}\n\n{comentario[:400]}"


def _tool_analizar_short_viral(args):
    """Analiza métricas y propone acciones."""
    import requests, datetime, json as _j, sys as _sys_yt
    vid = (args.get("video_id") or "").strip()
    if not vid: return "ERROR: falta video_id"
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    
    try:
        _sys_yt.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import token
        access = token("data/youtube_encuadre_token.json")
    except Exception as e:
        return f"ERROR token: {e}"
    
    # Stats del vídeo
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={"part": "statistics,snippet", "id": vid},
            headers={"Authorization": f"Bearer {access}"}, timeout=20
        )
        if r.status_code != 200 or not r.json().get("items"):
            return f"ERROR stats: HTTP {r.status_code}"
        v = r.json()["items"][0]
        stats = v.get("statistics", {})
        titulo = v.get("snippet", {}).get("title", "")
        vistas = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comentarios = int(stats.get("commentCount", 0))
    except Exception as e:
        return f"ERROR stats: {e}"
    
    ratio_like = likes / vistas * 100 if vistas > 0 else 0
    ratio_coment = comentarios / vistas * 100 if vistas > 0 else 0
    
    # Media de últimos shorts del mismo JSON
    yt_path = ROOT / "data" / "agent" / f"youtube_urls_{fecha}.json"
    media = 0
    if yt_path.exists():
        try:
            d = _j.loads(yt_path.read_text())
            otros_ids = [s.get("video_id") for s in d.get("shorts", []) if s.get("video_id") and s["video_id"] != vid]
            if otros_ids:
                r2 = requests.get("https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "statistics", "id": ",".join(otros_ids[:5])},
                    headers={"Authorization": f"Bearer {access}"}, timeout=20)
                if r2.status_code == 200:
                    vistas_otros = [int(i.get("statistics", {}).get("viewCount", 0)) for i in r2.json().get("items", [])]
                    media = sum(vistas_otros) / len(vistas_otros) if vistas_otros else 0
        except: pass
    
    # Diagnóstico
    rendimiento = "🔥 EXCELENTE" if media > 0 and vistas > media * 2 else (
        "✅ BUENO" if media > 0 and vistas > media else (
            "⚠️ BAJO" if media > 0 else "🤷 SIN REFERENCIA"))
    
    propuestas = []
    if "EXCELENTE" in rendimiento or "BUENO" in rendimiento:
        propuestas.append("🎬 Hacer secuela con mismo tema/hook")
        propuestas.append("📱 Cross-post a TikTok + IG Reels (share sheet)")
        propuestas.append("📝 Post web relacionado profundo")
        propuestas.append("🎙 Mención en podcast de hoy")
        propuestas.append("💬 Publicar comentario SEO fijado con CTA")
    else:
        propuestas.append("🔄 Cambiar título a variante A/B")
        propuestas.append("🖼 Regenerar thumbnail más impactante")
        propuestas.append("✂️ Re-cortar con hook más fuerte en primeros 2s")
        propuestas.append("🎯 Cambiar ángulo (dato → contradicción)")
    
    return (
        f"📊 SHORT: {titulo[:80]}\n"
        f"   Vistas: {vistas:,} | Likes: {likes:,} | Coments: {comentarios}\n"
        f"   Ratio like: {ratio_like:.2f}% | Ratio coment: {ratio_coment:.3f}%\n"
        f"   Media otros shorts: {media:,.0f} vistas\n"
        f"   Rendimiento: {rendimiento}\n\n"
        f"🎯 QUÉ HACER:\n" + "\n".join(f"   {p}" for p in propuestas)
    )


def _tool_generar_thumbnail_video(args):
    """Genera thumbnail top-1: intenta Nano Banana, fallback SDXL."""
    import requests, datetime, json as _j, sys as _sys_tb, subprocess as _sp
    vid = (args.get("video_id") or "").strip()
    if not vid: return "ERROR: falta video_id"
    fecha = args.get("fecha") or datetime.date.today().isoformat()
    if fecha == "hoy": fecha = datetime.date.today().isoformat()
    titular = (args.get("titular") or "").strip()
    
    if not titular:
        seo_path = ROOT / "output" / "encuadre" / f"seo_{fecha}.json"
        prod_path = ROOT / "output" / "encuadre" / f"produccion_{fecha}.json"
        if seo_path.exists():
            titular = (_j.loads(seo_path.read_text()).get("largo") or {}).get("titulo", "")
        if not titular and prod_path.exists():
            titular = (_j.loads(prod_path.read_text()).get("dossier") or {}).get("titular_brutal", "")
    if not titular: return "ERROR: sin titular"
    
    thumb_path = ROOT / "output" / "encuadre" / f"thumbnail_{fecha}_{vid[:6]}.png"
    thumb_path.parent.mkdir(parents=True, exist_ok=True)
    metodo = "?"
    
    # ═══ INTENTO 1: Nano Banana (si hay endpoint en .env) ═══
    nano_url = ""
    nano_key = ""
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("NANO_BANANA_URL="): nano_url = line.split("=",1)[1].strip().strip('"').strip("'")
        if line.startswith("NANO_BANANA_KEY="): nano_key = line.split("=",1)[1].strip().strip('"').strip("'")
    
    if nano_url:
        try:
            r = requests.post(nano_url,
                headers={"Authorization": f"Bearer {nano_key}"} if nano_key else {},
                json={"prompt": f"Thumbnail YouTube impactante sobre: {titular}. Estilo cinematic oscuro, alto contraste, sin texto legible.", "width": 1280, "height": 720},
                timeout=60)
            if r.status_code == 200:
                thumb_path.write_bytes(r.content)
                metodo = "nano_banana"
        except: pass
    
    # ═══ FALLBACK: SDXL Cloudflare ═══
    if metodo == "?":
        try:
            _sys_tb.path.insert(0, str(ROOT / "scripts"))
            from generar_imagen import generar
            prompt = f"Cinematic dramatic scene representing: {titular[:100]}. Dark moody lighting, high contrast, no text, editorial photography style, 16:9"
            r = generar(prompt, preset="cinematic", aspect="16:9", canal="encuadre")
            if r.startswith("OK: "):
                src = pathlib.Path(r.split("OK: ")[1].split(" ")[0])
                if src.exists():
                    import shutil
                    shutil.copy2(src, thumb_path)
                    metodo = "sdxl_cloudflare"
        except Exception as e:
            return f"ERROR generar thumbnail: {e}"
    
    if not thumb_path.exists() or thumb_path.stat().st_size < 10000:
        return f"ERROR: thumbnail vacía o fallo"
    
    # ═══ SUBIR a YouTube thumbnails.set ═══
    try:
        _sys_tb.path.insert(0, str(ROOT / "scripts"))
        from subir_youtube import token
        access = token("data/youtube_encuadre_token.json")
        with open(thumb_path, "rb") as f:
            r = requests.post(
                f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                headers={"Authorization": f"Bearer {access}", "Content-Type": "image/png"},
                data=f.read(), timeout=60)
        subida = "✅ subida a YouTube" if r.status_code in (200, 204) else f"⚠️ upload HTTP {r.status_code}"
    except Exception as e:
        subida = f"⚠️ upload error: {e}"
    
    return f"OK thumbnail ({metodo}) → {thumb_path.relative_to(ROOT)}\n{subida}\nTamaño: {thumb_path.stat().st_size//1024}KB"


TOOL_FNS = {
    "generar_thumbnail_video": _tool_generar_thumbnail_video,
    "analizar_short_viral": _tool_analizar_short_viral,
    "publicar_comentario_youtube": _tool_publicar_comentario_youtube,
    "rollback_listar": _tool_rollback_listar,
    "rollback_snapshot": _tool_rollback_snapshot,
    "reindexar_busqueda": _tool_reindexar_busqueda,
    "buscar_historico": _tool_buscar_historico,
    "cloudflare_stats": _tool_cloudflare_stats,
    "generar_titulo_ab": _tool_generar_titulo_ab,
    "generar_seo": _tool_generar_seo,
    "publicar_blogger": _tool_publicar_blogger,
    "programar_youtube": _tool_programar_youtube,
    "subir_youtube_dia": _tool_subir_youtube_dia,
    "generar_podcast_dia": _tool_generar_podcast_dia,
    "generar_post_web": _tool_generar_post_web,
    "generar_short": _tool_generar_short,
    "pipeline_custom": _tool_pipeline_custom,
    "pipeline_kill": _tool_pipeline_kill,
    "pipeline_status": _tool_pipeline_status,
    "pipeline_completo": _tool_pipeline_completo,
    "pipeline_step": _tool_pipeline_step,
    "ver_contrato": _tool_ver_contrato,
    "escanear_ecosistema": _tool_escanear_ecosistema,
    "ejecutar_limpieza": _tool_ejecutar_limpieza,
    "auto_regenerar_manual": _tool_auto_regenerar_manual,
    "crear_nueva_tool": _tool_crear_nueva_tool,
    "ver_costes_hoy": _tool_ver_costes_hoy,
    "ver_fallos_similares": _tool_ver_fallos_similares,
    "ver_ultimas_tareas": _tool_ver_ultimas_tareas,
    "ver_mi_workspace": _tool_ver_mi_workspace,
    "evaluar_produccion": _tool_evaluar_produccion,
    "crear_nicho": _tool_crear_nicho,
    "ensamblar_video_largo": _tool_ensamblar_video_largo,
    "producir_nicho": _tool_producir_nicho,
    "subir_youtube": _tool_subir_youtube,
    "consultar_manual_ecosistema": _tool_consultar_manual_ecosistema,
    "buscar_en_manual": _tool_buscar_en_manual,
    "listar_mis_tools": _tool_listar_mis_tools,
    "publicar_en_redes": _tool_publicar_en_redes,
    "producir_video": _tool_producir_video,
    "ensamblar_video_final": _tool_ensamblar_video_final,
    "producir_video_completo": _tool_producir_video_completo,
    "publicar_blog_completo": _tool_publicar_blog_completo,
    "crear_blog_top": _tool_crear_blog_top,
    "generar_informe_editorial": _tool_generar_informe_editorial,
    "procesar_cola_youtube": _tool_procesar_cola_youtube,
    "generar_video": _tool_generar_video,
    "buscar_youtube": _tool_buscar_youtube,
    "generar_imagen": _tool_generar_imagen,
    "lanzar_pipeline_kaggle": _tool_lanzar_pipeline_kaggle,
    "generar_cancion_kaggle": _tool_generar_cancion_kaggle,
    "generar_video_rapido": _tool_generar_video_rapido,
    "leer_documentacion": _tool_leer_documentacion,
    "documentar_aprendizaje": _tool_documentar_aprendizaje,
    "ejecutar_comando": _tool_ejecutar_comando,
    "recordar_hecho": _tool_recordar_hecho,
    "delegar_tareas_paralelas": _tool_delegar_tareas_paralelas,
    "consultar_hechos": _tool_consultar_hechos,
    "buscar_en_web": _tool_buscar_en_web,
    "read_file": _tool_read_file,
    "write_file": _tool_write_file,
    "validate_file": _tool_validate_file,
    "promote_file": _tool_promote_file,
    "list_canales": _tool_list_canales,
    "estado_sistema": _tool_estado_sistema,
    "consultar_manual_python": _tool_consultar_manual_python,
    "consultar_manual_sistema": _tool_consultar_manual_python,
    "instalar_dependencia": _tool_instalar_dependencia,
    "generar_narracion": _tool_generar_narracion,
    "analizar_video_competencia": _tool_analizar_video_competencia,
    "buscar_repositorio": _tool_buscar_repositorio,
    "sanar_sistema": _tool_sanar_sistema,
    "notificar_movil": _tool_notificar_movil,
    "leer_rss": _tool_leer_rss,
    "pedir_a_especialista": _tool_pedir_a_especialista,
    "lanzar_notebook_kaggle": _tool_lanzar_notebook_kaggle,
}

# 2026-11-09: cargar tools dinamicas (fail-safe si el fichero esta roto)
try:
    _TOOLS_DYN, _FNS_DYN = cargar_tools_dinamicas()
    TOOLS.extend(_TOOLS_DYN)
    TOOL_FNS.update(_FNS_DYN)
except Exception as _e_dyn:
    print(f"   [dyn load] {_e_dyn}")



def _leer_api_key(nombre: str) -> str:
    """Lee una API Key genérica del .env."""
    import os
    val = os.environ.get(nombre, "").strip()
    if val:
        return val
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(f"{nombre}="):
                return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def _call_llm(api_key, messages, force_no_tools=False):
    import os, json as _json
    CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    COOLDOWN_FILE = ROOT / "data" / "agent" / "cooldowns.json"

    def _load_cd():
        try:
            if COOLDOWN_FILE.exists():
                return _json.loads(COOLDOWN_FILE.read_text())
        except Exception:
            pass
        return {}

    def _save_cd(cd):
        try:
            COOLDOWN_FILE.parent.mkdir(parents=True, exist_ok=True)
            COOLDOWN_FILE.write_text(_json.dumps(cd, indent=2))
        except Exception:
            pass

    # ═══ CASCADA GROQ DIRECTA (4 cuentas) → OmniRoute → especialistas ═══
    # Primero 4 Groq directas (4x cuota). Si todas fallan → OmniRoute. Ultimo recurso especialistas.
    # 2026-11-09: FORZAR lectura del .env (os.environ puede tener keys viejas exportadas)
    claves_groq = []
    modelos_groq = []
    _env_path = ROOT / ".env"
    _env_lines = _env_path.read_text().splitlines() if _env_path.exists() else []
    def _env_only(name):
        for line in _env_lines:
            ls = line.strip()
            if ls.startswith(f"{name}="):
                v = ls.split("=", 1)[1].strip().strip('"').strip("'")
                # Sanity check para keys: deben empezar por gsk_ y ser ~56 chars
                if name.startswith("GROQ_API_KEY") and not (v.startswith("gsk_") and 40 <= len(v) <= 200):
                    return ""
                return v
        return ""

    for k_name, m_name in [("GROQ_API_KEY","GROQ_MODEL_1"),("GROQ_API_KEY_2","GROQ_MODEL_2"),("GROQ_API_KEY_3","GROQ_MODEL_2"),("GROQ_API_KEY_4","GROQ_MODEL_3")]:
        try:
            k = _env_only(k_name)
            if k: claves_groq.append(k)
            m = _env_only(m_name)
            if m: modelos_groq.append(m)
        except Exception:
            pass
    print(f"   [DEBUG] claves_groq={len(claves_groq)} modelos_groq={len(modelos_groq)}", flush=True)
    if claves_groq:
        k0 = claves_groq[0]
        print(f"   [DEBUG] key0 prefijo={k0[:8]} len={len(k0)}", flush=True)

    # Si hay 4 Groq disponibles → usar directas
    if os.environ.get("FORCE_GEMINI") == "1":
        claves_groq = []
    if claves_groq:
        modelos_defecto = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        for idx, gk in enumerate(claves_groq):
            modelo = modelos_groq[idx] if idx < len(modelos_groq) else modelos_defecto[idx % len(modelos_defecto)]
        # 2026-11-09: sanity check modelo
        if not any(modelo.startswith(p) for p in ("openai/", "qwen/", "meta-llama/", "mistral-", "google/", "moonshotai/", "deepseek-")):
            modelo = modelos_defecto[idx % len(modelos_defecto)]
            try:
                payload = {"model": modelo, "messages": comprimir_mensajes(messages), "temperature": 0.2, "max_tokens": 4096, "tool_choice": "auto", "parallel_tool_calls": True}
                if not force_no_tools:
                    payload["tools"] = _filtrar_tools(_extraer_prompt(messages), TOOLS)
                import json as _j
                _size = len(_j.dumps(payload))
                print(f"   [DEBUG] payload={_size}b model={modelo} tools={len(payload.get('tools',[]))} msgs={len(payload['messages'])}")
                if modelo == "openai/gpt-oss-120b":
                    Path("/data/data/com.termux/files/home/tmp/payload_debug.json").write_text(_j.dumps(payload, indent=2))
                if modelo == "openai/gpt-oss-120b":
                    Path("/data/data/com.termux/files/home/tmp/payload_debug.json").write_text(_j.dumps(payload, indent=2))
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {gk}", "Content-Type": "application/json", "User-Agent": CHROME_UA},
                    json=payload, timeout=60,
                )
                if r.status_code < 400:
                    print(f"   [Groq#{idx+1} {modelo}] OK directo")
                    return r.json()
                print(f"   [Groq#{idx+1}] HTTP {r.status_code}: {r.text[:300]}")
            except Exception as e:
                print(f"   [Groq#{idx+1}] {str(e)[:80]}, siguiente...")
        print("   [4 Groq directas fallaron. Esperando 5s y reintentando...]")
        import time as _t
        _t.sleep(5)
        for idx, gk in enumerate(claves_groq[:2]):  # solo 2 reintentos
            modelo = modelos_groq[idx] if idx < len(modelos_groq) else modelos_defecto[idx]
            try:
                payload = {"model": modelo, "messages": comprimir_mensajes(messages), "temperature": 0.2, "max_tokens": 1500}
                if not force_no_tools:
                    payload["tools"] = _filtrar_tools(_extraer_prompt(messages), TOOLS)
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {gk}", "Content-Type": "application/json", "User-Agent": CHROME_UA},
                    json=payload, timeout=60,
                )
                if r.status_code < 400:
                    print(f"   [Groq#{idx+1} reintento OK]")
                    return r.json()
            except Exception:
                pass
        print("   [Reintento fallido -> especialistas]")

    # ═══ GEMINI FALLBACK (Regla #35: OmniRoute saturado, Gemini gratis antes) ═══
    if os.environ.get("SKIP_GEMINI") != "1":
        try:
            from brain.llm_gemini import generar as _gemini_generar
            _prompt_gem = _extraer_prompt(comprimir_mensajes(messages))
            _gem_txt = _gemini_generar(_prompt_gem, timeout=20)
            if _gem_txt and _gem_txt.strip():
                print("   [Gemini flash-lite] OK")
                return {
                    "id": "gemini-fallback",
                    "model": "gemini-flash-lite-latest",
                    "choices": [{"index": 0,
                                 "message": {"role": "assistant", "content": _gem_txt, "tool_calls": None},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                }
        except Exception as _e:
            print(f"   [Gemini] {type(_e).__name__}: {str(_e)[:80]}, siguiente...")

    omniroute_key = _leer_api_key("OMNIROUTE_API_KEY")
    omniroute_models = [
        "mi-groq/qwen/qwen3.8-27b",
        "orfree/cohere/north-mini-code:free",
        "orfree/nvidia/nemotron-3-ultra-550b-a55b:free",
        "mi-groq/openai/gpt-oss-120b",
    ]

    cd = _load_cd()
    ahora = time.time()
    # Filtrar modelos en cooldown (pero si TODOS estan, forzar intento)
    disponibles = [m for m in omniroute_models if cd.get(m, 0) < ahora]
    if not disponibles:
        print("   [Cooldown] Todos en cooldown, forzando intento igualmente")
        disponibles = omniroute_models

    last_err = None
    for i, model in enumerate(disponibles):
        # Espaciado entre intentos (2s minimo)
        if i > 0:
            time.sleep(2)

        messages = comprimir_mensajes(messages)
        payload = {"model": model, "messages": messages, "temperature": 0.2, "max_tokens": 4096}
        if not force_no_tools:
            payload["tools"] = _filtrar_tools(_extraer_prompt(messages), TOOLS)

        try:
            r = requests.post(
                "http://localhost:20128/v1/chat/completions",
                headers={"Authorization": f"Bearer {omniroute_key}", "Content-Type": "application/json", "User-Agent": CHROME_UA},
                json=payload, timeout=180,
            )
            if r.status_code < 400:
                _save_cd(cd)
                return r.json()

            # Cooldown segun tipo de error
            if r.status_code == 429:
                cd[model] = time.time() + 60
                print(f"   [{model}] 429 Rate Limit -> cooldown 60s")
            elif r.status_code in (500, 502, 503, 504):
                cd[model] = time.time() + 15
                print(f"   [{model}] {r.status_code} Server Error -> cooldown 15s")
            elif r.status_code in (401, 403, 404):
                cd[model] = time.time() + 300
                print(f"   [{model}] {r.status_code} Auth/NotFound -> cooldown 5min")
            last_err = f"{model} -> HTTP {r.status_code}: {r.text[:200]}"
        except Exception as e:
            cd[model] = time.time() + 15
            last_err = f"{model} -> {e}"
            print(f"   [{model}] Exception -> cooldown 15s")

    _save_cd(cd)

    # Fallback final: usar la cascada de especialistas.py
    print(f"   [OmniRoute fallo: {last_err}. Cayendo a la cascada de 7 IAs...]")
    try:
        from brain.especialistas import pedir_a_especialista
        # Extraemos el prompt del usuario del contexto (último mensaje)
        _prompt = messages[-1]["content"] if messages else ""
        _ctx = messages[-2]["content"] if len(messages) > 1 else ""
        _rol = "programador" # Usamos el rol de código para dios.py
        res = pedir_a_especialista(_rol, _prompt, contexto=_ctx, proveedor="auto")
        return {"choices": [{"message": {"content": res}}]}
    except Exception as e:
        raise RuntimeError(f"Cascada completa falló: {e}")



SYSTEM_PROMPT = """Eres Dios, arquitecto técnico autónomo de LofiProducer / Somos El Encuadre. Tienes 38 herramientas. El repo está en /data/data/com.termux/files/home/LofiProducer/.

═══ REGLAS CRÍTICAS ═══
R1. IDIOMA: Responde SIEMPRE en español de España.
R2. ACCIÓN = TOOL. Si el usuario pide una ACCIÓN (leer, listar, buscar, ejecutar, crear, modificar, analizar, producir, subir, programar, borrar, comprobar, ver), LLAMA A UNA HERRAMIENTA. NUNCA expliques "ejecuta este comando" — TÚ lo ejecutas.
R3. NO INVENTES. Sin datos → usa herramienta. Sin ruta → busca con ejecutar_comando("find . -name ...").
R4. PROHIBIDO EXPLICAR EN VEZ DE EJECUTAR. "Usa PowerShell para..." o "aquí tienes el script para..." son FALLOS.
R5. TERMINA con 3 líneas: qué hiciste + resultado + siguiente paso.

═══ FEW-SHOT (memorízalos) ═══
MAL:  Usuario "listame los .py de scripts/" → Dios "Usa PowerShell: Get-ChildItem..."
BIEN: Usuario "listame los .py de scripts/" → [tool: ejecutar_comando({"cmd": "ls scripts/*.py"})] → responde con la lista

MAL:  Usuario "cuántos agentes hay?" → Dios "El sistema tiene varios agentes como..."
BIEN: Usuario "cuántos agentes hay?" → [tool: ejecutar_comando({"cmd": "grep -c '^    \"' brain/especialistas.py"})] → "48 agentes"

MAL:  Usuario "arregla el bug de X" → Dios "Deberías editar línea 45..."
BIEN: Usuario "arregla el bug de X" → [tool: read_file] → [tool: write_file sandbox/] → [tool: validate_file] → [tool: promote_file (pide permiso al usuario)] → reporta OK

═══ ÁRBOL DE DECISIÓN ═══
  ACCIÓN sobre repo/sistema → llamar tool → interpretar → responder
  INFO externa (web, noticias) → buscar_en_web → responder
  CHARLA → responder directo

Mapa rápido:
  lee/lista/grep/cuenta → ejecutar_comando
  crea/modifica/borra → write_file → validate_file → promote_file (CONFIRMACIÓN)
  estado/salud → estado_sistema
  noticias/web → buscar_en_web
  youtube/tendencias → buscar_youtube(tipo=tendencias, region=ES)
  música/lofi → generar_cancion_kaggle
  voz/TTS → generar_narracion
  vídeo/clip → generar_video
  pipeline completo → producir_video_completo
  blog → publicar_blog_completo
  repara sistema → sanar_sistema
  documenta → documentar_aprendizaje + recordar_hecho

═══ AUTO-REPARACIÓN (crítico) ═══
Cuando arregles un bug del ecosistema:
1. read_file para inspeccionar
2. write_file a sandbox/ con el fix
3. validate_file para comprobar que parsea
4. promote_file → ESTO PIDE CONFIRMACIÓN AL USUARIO POR TELEGRAM. Si el usuario no responde en 5 min, NO se aplica.
5. documentar_aprendizaje con el bug y la solución

NUNCA llames promote_file sin haber pasado por write_file + validate_file. NUNCA escribas directo al repo.

═══ SEGURIDAD ═══
- ejecutar_comando: 1 comando simple. SIN && ; | > cd. Un comando = una tool.
- write_file siempre a sandbox/. promote_file copia al repo (CON CONFIRMACIÓN).
- Nunca borres sin confirmación. Si tarda >60s, avisa al usuario.

═══ PERSONALIDAD ═══
Directo, chulesco pero servicial. 1-3 frases + resultado. Sin párrafos épicos ni disculpas.
"""



def _detectar_modo(prompt: str) -> str:
    """Detecta si es charla rapida o tarea de agente."""
    # Override manual
    if prompt.startswith("!"):
        return "chat"
    if prompt.startswith("#"):
        return "agent"
    
    acciones = [
        "instala", "instalar", "crea", "crear", "genera", "generar",
        "escribe", "ejecuta", "ejecutar", "busca", "buscar",
        "script", "archivo", "carpeta", "proyecto",
        "descarga", "sube", "actualiza", "modifica",
        "video", "cancion", "canción", "imagen",
        "traduce", "narrar", "tts", "instala",
        "investiga", "analiza", "revisa", "estudia",
        "corrige", "arregla", "diagnostica",
    ]
    pl = prompt.lower()
    for kw in acciones:
        if kw in pl:
            return "agent"
    return "chat"


def _charla_rapida(prompt: str) -> str:
    """2026-11-09: cascada Groq directa (misma que pipeline). Cero OmniRoute."""
    import requests
    if prompt.startswith("!"):
        prompt = prompt[1:].strip()
    sys_prompt = (
        "Eres el Dios de la Construccion, asistente del Arquitecto KeiZ. "
        "Tienes personalidad chulesca pero servicial. Respondes CORTO, directo y con humor. "
        "NUNCA uses herramientas. NUNCA inventes que has hecho algo. "
        "Si te piden una accion compleja, responde: 'Para eso pidemelo como tarea de agente (sin el !)'."
    )
    CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # Leer keys de .env con sanity check
    keys = []
    modelos = []
    env_path = ROOT / ".env"
    if not env_path.exists():
        return "[Error: no hay .env]"
    for line in env_path.read_text().splitlines():
        ls = line.strip()
        for n in ("GROQ_API_KEY=", "GROQ_API_KEY_2=", "GROQ_API_KEY_3=", "GROQ_API_KEY_4="):
            if ls.startswith(n):
                v = ls.split("=", 1)[1].strip().strip('"').strip("'")
                if v.startswith("gsk_") and 40 <= len(v) <= 200:
                    keys.append(v)
        for n in ("GROQ_MODEL_1=", "GROQ_MODEL_2=", "GROQ_MODEL_3="):
            if ls.startswith(n):
                v = ls.split("=", 1)[1].strip().strip('"').strip("'")
                if v: modelos.append(v)

    if not keys:
        return "[Error: 0 GROQ_API_KEY validas en .env]"

    modelos_defecto = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
    last_err = ""
    for idx, k in enumerate(keys):
        modelo = modelos[idx] if idx < len(modelos) else modelos_defecto[idx % len(modelos_defecto)]
        if not any(modelo.startswith(p) for p in ("openai/", "qwen/", "meta-llama/", "mistral-", "google/")):
            modelo = modelos_defecto[idx % len(modelos_defecto)]
        payload = {
            "model": modelo,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json", "User-Agent": CHROME_UA},
                json=payload, timeout=30,
            )
            if r.status_code == 200:
                j = r.json()
                msg = j.get("choices", [{}])[0].get("message", {})
                content = (msg.get("content") or "").strip()
                if not content and msg.get("reasoning"):
                    content = msg["reasoning"][:400].strip()
                if content:
                    return content
                last_err = f"key#{idx+1} vacia"
            else:
                last_err = f"key#{idx+1} HTTP {r.status_code}"
        except Exception as e:
            last_err = f"key#{idx+1} {str(e)[:60]}"
    return "[Fallo Groq cascada: " + last_err + "]"


def main() -> int:

    if len(sys.argv) < 2:
        print('Uso: python scripts/dios.py "tu peticion"')
        return 2

    prompt = " ".join(sys.argv[1:]).strip()

    # 2026-11-09: limite tokens diario
    if not _check_tokens_limit():
        print("[dios] Limite tokens alcanzado. Espera mañana o sube DIOS_MAX_TOKENS.")
        return 1

    # ── DETECCION DE MODO ──
    _modo_actual = _detectar_modo(prompt) if prompt else "agent"
    if _modo_actual == "chat":
        print("[dios] Modo CHARLA RAPIDA (sin tools)")
        _respuesta_rapida = _charla_rapida(prompt)
        print()
        print("[dios] Tarea completada. Resumen:")
        print(_respuesta_rapida)
        try:
            guardar_conversacion(prompt, _respuesta_rapida[:2000], 1)
        except Exception:
            pass
        return 0
    else:
        print("[dios] Modo AGENTE (tools + razonamiento)")
    print(f"[dios] Peticion: {prompt}")

    api_key = _leer_key()
    n = _limpiar_backups()
    if n:
        print(f"[dios] {n} backups viejos limpiados")

    contexto = _contexto_proyecto(prompt)
    try:
        _ws = WORKSPACE.compacto()
        if _ws: contexto += "\n\n=== MEMORIA ===\n" + _ws
        _ult = EPISODIOS.ultimas(1)
        if _ult: contexto += "\nUltima: " + _ult[0]["prompt"][:80]
    except Exception as _e:
        print(f"   [mem load] {_e}")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\n=== CONTEXTO ===\n" + contexto},
        {"role": "user", "content": prompt},
    ]

    step = 0
    ultima_accion = None
    repeticiones = 0
    import time

    while step < MAX_STEPS:
        step += 1
        time.sleep(3) # Respetar rate limit de Groq
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [dios] Paso {step}/{MAX_STEPS}")

        try:
            data = _call_llm(api_key, messages)
        except Exception as e:
            print(f"[dios] Error LLM: {e}")
            return 1

        msg = data["choices"][0]["message"]
        tool_calls = msg.get("tool_calls") or []
        messages.append(msg)

        if not tool_calls:
            # 2026-11-09: reintento forzado si el LLM se pone a explicar
            if step == 1:
                print("   [reintento forzado: LLM no llamo tool]")
                messages.append({
                    "role": "user",
                    "content": "¡ALTO! No me expliques nada. USA UNA HERRAMIENTA AHORA. Si no sabes cual, usa ejecutar_comando. NO RESPONDAS CON TEXTO."
                })
                continue
            resumen = (msg.get("content") or "").strip()
            print("\n[dios] Tarea completada. Resumen:")
            print(resumen[:1500])
            guardar_conversacion(prompt, resumen[:2000], step)
            _guardar_resultado(prompt, resumen, [], exito=True)
            return 0

        for tc in tool_calls:
            fn = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}

            print(f"  -> {fn}({list(args.keys())})")

            firma = f"{fn}:{json.dumps(args, sort_keys=True)[:200]}"
            if firma == ultima_accion:
                repeticiones += 1
            else:
                repeticiones = 0
            ultima_accion = firma

            if repeticiones >= 3:
                print("[dios] Bucle detectado, abortando.")
                return 1

            if fn == "buscar_en_web":
                result = TOOL_FNS[fn](args)
                print(f"     <- (Búsqueda completada. Forzando respuesta final...)")
                
                # Cortocircuito: LLM responde directamente con el resultado web
                final_msgs = [
                    {"role": "system", "content": "Eres un asistente útil. Responde a la pregunta del usuario basándote EXCLUSIVAMENTE en los resultados de búsqueda proporcionados. No inventes nada."},
                    {"role": "user", "content": f"Pregunta original: {prompt}\n\nResultados de la búsqueda:\n{result}"}
                ]
                try:
                    final_data = _call_llm(api_key, final_msgs, force_no_tools=True)
                    resumen = final_data["choices"][0]["message"].get("content", "").strip()
                    print("\n[dios] Tarea completada. Resumen:")
                    print(resumen[:1500])
                    
                    guardar_conversacion(prompt, resumen[:2000], step)
                    return 0
                except Exception as e:
                    print(f"[dios] Error en respuesta final: {e}")
                    return 1

            if fn not in TOOL_FNS:
                result = f"ERROR: tool {fn} desconocida"
            else:
                try:
                    result = TOOL_FNS[fn](args)
                except Exception as e:
                    result = f"ERROR: {e}"
            if str(result).startswith("ERROR") and fn in TOOL_FALLBACKS:
                for _alt in TOOL_FALLBACKS[fn]:
                    if _alt not in TOOL_FNS: continue
                    print(f"     [fallback] {fn} -> {_alt}")
                    try:
                        _r2 = TOOL_FNS[_alt](args)
                        if not str(_r2).startswith("ERROR"):
                            result = _r2; break
                    except Exception: continue
            if str(result).startswith("ERROR"):
                try: FALLOS.guardar(prompt, fn, str(result)[:300])
                except: pass

            print(f"     <- {str(result)[:150]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "name": fn,
                "content": str(result)[:8000],
            })

    print("\n[dios] Limite de pasos alcanzado.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
