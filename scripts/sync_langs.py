from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
#!/usr/bin/env python3
"""
Sincronización y traducción automática multi-idioma (ES -> EN, FR, DE, PT)
para Somos El Encuadre usando cascada Groq (1..4) + Gemini (1..4).

- Carga automáticamente ~/LofiProducer/.env si existe.
- En Groq prioriza openai/gpt-oss-120b y openai/gpt-oss-20b con fallback automático.
- En Gemini usa modelos vigentes (gemini-3.8-flash, gemini-3.5-flash-lite, gemini-4-hydrogen).
- Protege YAML frontmatter, código, etiquetas HTML y rutas de medios/enlaces.
- Caché incremental por archivo e idioma (.langs_sync_cache.json) con --force y --limit.
"""
import argparse
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
ENV_PATH = Path.home() / "LofiProducer" / ".env"
CACHE_FILE = ROOT / ".langs_sync_cache.json"

LANG_CONFIG = {
    "en": {"label": "English", "back_text": "Read original in Spanish"},
    "fr": {"label": "Français", "back_text": "Lire l'original en espagnol"},
    "de": {"label": "Deutsch", "back_text": "Original auf Spanisch lesen"},
    "pt": {"label": "Português", "back_text": "Ler original em espanhol"},
}

SKIP_PREFIXES = ("en/", "fr/", "de/", "pt/")
SKIP_EXACT = {"404.md", "privacidad.md", "proximamente.md", "contacto.md"}

PROTECT_PATTERN = re.compile(
    r"(```[\s\S]*?```|`[^`\n]+`|<[^>]+>|!\[[^\]]*\]\([^)]+\)|\[[^\]]+\]\([^)]+\)|/media/[^\s\"')<>]+)",
    re.MULTILINE,
)


def load_dotenv_if_present(env_file: Path) -> None:
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_frontmatter(raw: str):
    if raw.startswith("---"):
        m = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n?", raw)
        if m:
            return m.group(0), raw[m.end():]
    return "", raw


def protect_segments(text: str):
    placeholders = {}

    def _repl(match):
        key = f"@@EEPROT{len(placeholders)}@@"
        placeholders[key] = match.group(0)
        return key

    protected = PROTECT_PATTERN.sub(_repl, text)
    return protected, placeholders


def restore_and_validate(candidate: str, original_protected: str, placeholders: dict) -> str | None:
    if not candidate or not candidate.strip():
        return None
    cleaned = candidate.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            cleaned = "\n".join(lines[1:-1]).strip()

    # Quitar prefijos tipo "**Translation:**" si el modelo los incluye en la primera línea
    lines = cleaned.splitlines()
    if lines:
        lines[0] = re.sub(
            r"^\*{0,2}(?:translation|traducción|traduction|übersetzung|tradução)\*{0,2}\s*:\s*",
            "",
            lines[0].strip(),
            flags=re.IGNORECASE,
        ).strip()
        cleaned = "\n".join(lines).strip()

    bad_starts = (
        "here is the translation",
        "voici la traduction",
        "hier ist die übersetzung",
        "aqui está a tradução",
        "certainly!",
        "sure!",
        "here's the translation",
    )
    first_line = cleaned.splitlines()[0].strip().lower() if cleaned.splitlines() else ""
    if any(first_line.startswith(b) for b in bad_starts):
        return None

    restored = cleaned
    for key, val in placeholders.items():
        if key not in restored:
            m = re.search(re.escape(key), restored, flags=re.IGNORECASE)
            if not m:
                return None
            restored = restored[: m.start()] + val + restored[m.end():]
        else:
            restored = restored.replace(key, val)

    if "@@EEPROT" in restored:
        return None

    orig_len = max(len(original_protected), 1)
    if len(restored) > orig_len * 2.2 + 500:
        return None

    return restored


def get_cascade_nodes():
    nodes = []

    groq_keys = []
    for var_name in ("GROQ_API_KEY", "GROQ_API_KEY_2", "GROQ_API_KEY_3", "GROQ_API_KEY_4"):
        val = os.environ.get(var_name, "").strip()
        if val and val not in groq_keys:
            groq_keys.append(val)

    groq_url = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions").strip()
    custom_fallback = os.environ.get("GROQ_FALLBACK_MODEL", "").strip()

    for idx, key in enumerate(groq_keys[:4]):
        env_model = os.environ.get(f"GROQ_MODEL_{idx+1}", "").strip()
        candidates = []
        for m in [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            env_model,
            custom_fallback,
            "llama-3.3-70b-versatile",
        ]:
            if m and m not in candidates:
                candidates.append(m)
        nodes.append(("groq", f"groq-{idx+1}", key, candidates, groq_url))

    gem_keys = []
    for var_name in ("GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4"):
        val = os.environ.get(var_name, "").strip()
        if val and val not in gem_keys:
            gem_keys.append(val)

    gem_base_model = os.environ.get("GEMINI_MODEL", "").strip()
    for idx, key in enumerate(gem_keys[:4]):
        env_gem = os.environ.get(f"GEMINI_MODEL_{idx+1}", "").strip()
        candidates = []
        for m in [
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-4-hydrogen",
            env_gem,
            gem_base_model,
        ]:
            if m and m not in candidates:
                candidates.append(m)
        nodes.append(("gemini", f"gemini-{idx+1}", key, candidates, ""))

    return nodes


def call_openai_compat(api_key, model, base_url, target_label, text):
    import time, urllib.error, http.client
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"
    prompt = (
        f"Translate strictly to {target_label}. "
        f"Preserve Markdown formatting and keep every placeholder like @@EEPROT0@@ untouched.\n\n{text}"
    )
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    for _attempt in range(2):
        try:
            req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=35) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            return data["choices"][0]["message"]["content"]
        except (OSError, TimeoutError, urllib.error.URLError, http.client.HTTPException, json.JSONDecodeError, KeyError, IndexError, ValueError):
            if _attempt == 0:
                time.sleep(1.5)
                continue
            return None

def call_gemini(api_key, model, target_label, text):
    import time, urllib.error, http.client
    for _attempt in range(2):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            prompt = (
                f"Translate strictly to {target_label}. "
                f"Preserve Markdown formatting and keep every placeholder like @@EEPROT0@@ untouched.\n\n{text}"
            )
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}]
            }).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (OSError, TimeoutError, urllib.error.URLError, http.client.HTTPException, json.JSONDecodeError, KeyError, IndexError, ValueError):
            if _attempt == 0:
                time.sleep(1.5)
                continue
            return None

def split_into_chunks(text: str, max_chars: int = 3800) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    blocks = re.split(r"(\n\s*\n)", text)
    chunks = []
    cur = ""
    for blk in blocks:
        if len(cur) + len(blk) <= max_chars or not cur:
            cur += blk
        else:
            chunks.append(cur)
            cur = blk
    if cur:
        chunks.append(cur)
    return chunks


def translate_body_cascade(body: str, lang_code: str, nodes) -> tuple[str, str]:
    protected, placeholders = protect_segments(body)
    target_label = LANG_CONFIG[lang_code]["label"]
    chunks = split_into_chunks(protected)

    out_chunks = []
    engines_used = []

    for ch in chunks:
        ch_placeholders = {k: v for k, v in placeholders.items() if k in ch}
        ch_done = None
        ch_engine = None
        for kind, node_label, key, models, url in nodes:
            for model in models:
                raw_out = (
                    call_openai_compat(key, model, url, target_label, ch)
                    if kind == "groq"
                    else call_gemini(key, model, target_label, ch)
                )
                valid = restore_and_validate(raw_out or "", ch, ch_placeholders)
                if valid is not None:
                    ch_done = valid
                    ch_engine = f"{node_label}({model})"
                    break
            if ch_done is not None:
                break

        if ch_done is None:
            out_chunks.append(ch)
            if "partial-fallback" not in engines_used:
                engines_used.append("partial-fallback")
            continue

        out_chunks.append(ch_done)
        if ch_engine and ch_engine not in engines_used:
            engines_used.append(ch_engine)

    return "".join(out_chunks), "+".join(engines_used) if engines_used else "ok"



def _run_tasks_pool(tasks, worker_fn, workers=4):
    lock = threading.Lock()
    results = []
    def _wrapped(idx, item):
        out = worker_fn(item)
        with lock:
            results.append((idx, out))
        return out
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_wrapped, i, t) for i, t in enumerate(tasks)]
        for f in as_completed(futs):
            f.result()
    results.sort(key=lambda x: x[0])
    return [x[1] for x in results]

_SYNC_LOCK = threading.Lock()

def main():
    load_dotenv_if_present(ENV_PATH)

    parser = argparse.ArgumentParser(description="Sincroniza y traduce documentos a EN/FR/DE/PT.")
    parser.add_argument("--langs", nargs="+", default=list(LANG_CONFIG.keys()), choices=list(LANG_CONFIG.keys()))
    parser.add_argument("--force", action="store_true", help="Reprocesa aunque exista caché.")
    parser.add_argument("--limit", type=int, default=0, help="Límite máximo de archivos a procesar en esta pasada (0 = todos).")
    parser.add_argument("--only-missing-or-fallback", action="store_true", help="Solo traduce los que aún no están traducidos.")
    args = parser.parse_args()

    nodes = get_cascade_nodes()
    cache = {}
    if CACHE_FILE.exists() and not args.force:
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    processed = 0
    translated_count = 0
    fallback_count = 0
    used_engines = {}

    sources = [
        s for s in sorted(DOCS.rglob("*.md"))
        if not s.relative_to(DOCS).as_posix().startswith(SKIP_PREFIXES)
        and s.relative_to(DOCS).as_posix() not in SKIP_EXACT
    ]
    total_targets = len(sources) * len(args.langs)

    pending_tasks = []
    for src in sources:
        rel = src.relative_to(DOCS).as_posix()
        if rel.startswith(SKIP_PREFIXES) or rel in SKIP_EXACT:
            continue

        h = file_hash(src)
        raw = src.read_text(encoding="utf-8", errors="ignore")
        fm, body = split_frontmatter(raw)

        for lang in args.langs:
            if args.limit and len(pending_tasks) >= args.limit:
                break

            cache_key = f"{lang}:{rel}"
            dst = DOCS / lang / rel
            prev = cache.get(cache_key)

            should_run = (
                args.force
                or not dst.exists()
                or not isinstance(prev, dict)
                or prev.get("hash") != h
                or (prev.get("engine") == "fallback-es" and len(nodes) > 0)
            )
            if (
                args.only_missing_or_fallback
                and isinstance(prev, dict)
                and prev.get("engine") != "fallback-es"
                and prev.get("hash") == h
                and dst.exists()
            ):
                should_run = False

            if should_run:
                pending_tasks.append((lang, rel, h, fm, body, dst, cache_key))

        if args.limit and len(pending_tasks) >= args.limit:
            break

    step_counter = 0

    def _run_one(task):
        nonlocal step_counter, processed, translated_count, fallback_count
        lang, rel, h, fm, body, dst, cache_key = task
        with _SYNC_LOCK:
            step_counter += 1
            cur_step = step_counter
            print(f"[{cur_step}/{len(pending_tasks)} de {total_targets}] -> {lang.upper()} | {rel} ...", flush=True)

        t0 = time.monotonic()
        out_body, engine = translate_body_cascade(body, lang, nodes)
        dt = time.monotonic() - t0

        if rel.endswith("index.md"):
            es_link = "/" if rel == "index.md" else f"/{rel[:-8]}"
        else:
            es_link = f"{'../' * len(Path(rel).parts)}{rel[:-3]}.md"

        back_label = LANG_CONFIG[lang]["back_text"]
        banner = f"> 🌐 [{back_label}]({es_link})\n\n"
        final_doc = f"{fm}\n{banner}{out_body.lstrip()}" if fm else f"{banner}{out_body.lstrip()}"

        with _SYNC_LOCK:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(final_doc, encoding="utf-8")
            cache[cache_key] = {"hash": h, "engine": engine}
            CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
            processed += 1
            used_engines[engine] = used_engines.get(engine, 0) + 1
            if engine == "fallback-es":
                fallback_count += 1
            else:
                translated_count += 1
            estado = "FALLBACK" if engine == "fallback-es" else "OK"
            print(f"[{cur_step}/{len(pending_tasks)}] [{estado}] {lang.upper()} | {rel} | motor={engine} | {dt:.1f}s", flush=True)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futs = [pool.submit(_run_one, t) for t in pending_tasks]
        for fut in as_completed(futs):
            fut.result()

    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"OK: procesados={processed} | traducidos_ia={translated_count} | "
        f"fallback={fallback_count} | nodos_activos={len(nodes)} | motores={used_engines}",
        flush=True,
    )


if __name__ == "__main__":
    main()
