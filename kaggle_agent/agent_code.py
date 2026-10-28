"""
Agente constructor - codigo que se ejecuta en Kaggle.

Flujo:
  1. Lee prompt de /tmp/prompt.txt
  2. Carga Qwen2.5-Coder-7B
  3. Lee el repo clonado en /tmp/lofi
  4. Pide al LLM: que archivo modificar y que diff proponer
  5. Devuelve JSON con {archivo, diff, razon}

NO aplica cambios. Solo propone.
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path


REPO = Path("/tmp/lofi")
MODEL_PATH = "/tmp/qwen7b.gguf"
MODEL_URL = (
    "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF"
    "/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf"
)


def log(msg: str) -> None:
    print(f"[agent] {msg}", file=sys.stderr, flush=True)


def setup_model() -> "Llama":
    """Descarga el modelo si no existe y lo carga en GPU."""
    if not os.path.exists(MODEL_PATH):
        log(f"descargando modelo ({MODEL_URL.split('/')[-1]})")
        subprocess.run(f"wget -q {MODEL_URL} -O {MODEL_PATH}", shell=True, check=True)
    log(f"cargando modelo desde {MODEL_PATH}")
    from llama_cpp import Llama
    return Llama(model_path=MODEL_PATH, n_ctx=8192, n_gpu_layers=-1, verbose=False)


def listar_py() -> list[str]:
    """Lista todos los .py del repo (relativo a REPO)."""
    out = []
    for root, _, files in os.walk(REPO):
        for f in files:
            if f.endswith(".py"):
                rel = Path(root, f).relative_to(REPO)
                out.append(str(rel))
    return sorted(out)


def leer(rel: str) -> str:
    """Lee un archivo del repo (protegido contra traversal)."""
    p = (REPO / rel).resolve()
    if not str(p).startswith(str(REPO.resolve())):
        raise ValueError(f"path fuera del repo: {rel}")
    return p.read_text(encoding="utf-8")


def inferir(llm: "Llama", system: str, user: str, max_tokens: int = 512) -> str:
    prompt = (
        f"<|im_start|>system\n{system}<|im_end|>\n"
        f"<|im_start|>user\n{user}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )
    resp = llm(prompt, max_tokens=max_tokens, temperature=0.1, stop=["<|im_end|>"])
    return resp["choices"][0]["text"].strip()


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("uso: python -m kaggle_agent.agent_code <prompt_file>")

    t0 = time.time()
    prompt = Path(sys.argv[1]).read_text(encoding="utf-8").strip()
    log(f"prompt: {prompt[:100]}...")

    if not REPO.exists():
        raise SystemExit(f"repo no clonado en {REPO}")

    llm = setup_model()
    log(f"modelo listo en {time.time()-t0:.1f}s")

    # 1. Pedir al LLM que elija UN archivo
    files = listar_py()
    log(f"repo tiene {len(files)} archivos .py")

    system_sel = "Eres un arquitecto de software conciso. Respondes solo con la ruta exacta del archivo a modificar, sin comentarios."
    user_sel = (
        f"Archivos del repo:\n" + "\n".join(files) + "\n\n"
        f"Peticion del usuario: {prompt}\n\n"
        f"Responde SOLO con la ruta de UN archivo de la lista (sin backticks, sin explicacion)."
    )
    archivo_rel = inferir(llm, system_sel, user_sel, max_tokens=80)
    archivo_rel = archivo_rel.strip().strip("`'\"").lstrip("./")
    log(f"archivo elegido: {archivo_rel}")

    if archivo_rel not in files:
        out = {
            "ok": False,
            "error": f"El LLM eligio un archivo que no existe: {archivo_rel!r}",
            "archivos_disponibles": files[:20],
        }
        print(json.dumps(out, ensure_ascii=False))
        return

    # 2. Leer el archivo y pedir un diff unificado
    contenido = leer(archivo_rel)

    system_diff = (
        "Eres un programador senior. Devuelves SOLO un diff unificado "
        "en formato git (lineas con prefijo + y -, con @@ hunk headers). "
        "No añadas explicaciones ni markdown. Si no hay cambios posibles, devuelve string vacio."
    )
    user_diff = (
        f"Archivo: {archivo_rel}\n\n"
        f"Contenido actual:\n```\n{contenido[:12000]}\n```\n\n"
        f"Peticion: {prompt}\n\n"
        f"Devuelve el diff unificado."
    )
    diff = inferir(llm, system_diff, user_diff, max_tokens=1024)
    log(f"diff generado ({len(diff)} chars) en {time.time()-t0:.1f}s")

    # 3. Devolver JSON limpio
    out = {
        "ok": True,
        "archivo": archivo_rel,
        "diff": diff,
        "razon": prompt[:200],
        "tiempo_total_s": round(time.time() - t0, 1),
    }
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
