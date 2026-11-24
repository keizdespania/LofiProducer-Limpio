#!/usr/bin/env python3
"""
Sincronización incremental de espejos en inglés (docs/en/) a partir de docs/.
- Solo procesa archivos nuevos o modificados (usando caché en .en_sync_cache.json).
- Si se configura EN_TRANSLATE_CMD, traduce el texto preservando YAML y etiquetas HTML;
  si no, genera un espejo listo con enlace directo a la versión en español.
"""
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
EN_ROOT = DOCS / "en"
CACHE_FILE = ROOT / ".en_sync_cache.json"

SKIP_PREFIXES = ("en/",)
SKIP_EXACT = {"404.md", "privacidad.md", "proximamente.md", "contacto.md"}


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def maybe_translate_text(text: str) -> str:
    cmd = os.environ.get("EN_TRANSLATE_CMD", "").strip()
    if not cmd:
        return text
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            input=text,
            text=True,
            capture_output=True,
            timeout=60,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout
    except Exception:
        pass
    return text


def adapt_links_for_en(md_text: str) -> str:
    md_text = re.sub(r'src="(/media/[^"]+)"', r'src="../\1"', md_text)
    return md_text


def main() -> None:
    EN_ROOT.mkdir(parents=True, exist_ok=True)
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    updated = 0
    for src in sorted(DOCS.rglob("*.md")):
        rel = src.relative_to(DOCS).as_posix()
        if rel.startswith(SKIP_PREFIXES) or rel in SKIP_EXACT:
            continue

        h = file_hash(src)
        dst = EN_ROOT / rel
        if cache.get(rel) == h and dst.exists():
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        raw = src.read_text(encoding="utf-8", errors="ignore")
        adapted = adapt_links_for_en(raw)
        translated = maybe_translate_text(adapted)

        if rel.endswith("index.md"):
            es_link = "/" if rel == "index.md" else f"/{rel[:-8]}"
            banner = f"> 🌐 [Leer versión original en Español]({es_link})\n\n"
        else:
            banner = f"> 🌐 [Leer versión original en Español](/{rel[:-3]}/)\n\n"

        if translated.startswith("---"):
            end_fm = translated.find("\n---", 3)
            if end_fm != -1:
                fm = translated[: end_fm + 4]
                body = translated[end_fm + 4 :].lstrip()
                final_txt = f"{fm}\n\n{banner}{body}"
            else:
                final_txt = banner + translated
        else:
            final_txt = banner + translated

        dst.write_text(final_txt, encoding="utf-8")
        cache[rel] = h
        updated += 1

    CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"OK: sincronización EN completada. Archivos actualizados/creados: {updated}")


if __name__ == "__main__":
    main()
